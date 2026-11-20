#!/usr/bin/env python3
"""First-mate watcher: posts to Slack when something in an idea needs or deserves your attention.

    python .agents/skills/ar_mate/scripts/mate_watch.py            # run in its own Herdr tab (or nohup)
    python .agents/skills/ar_mate/scripts/mate_watch.py --once     # one check, then exit
    python .agents/skills/ar_mate/scripts/mate_watch.py --ensure   # start in the background unless already running

Every --interval seconds it checks each open idea worktree. Slack gets only what a task's own final
report does not cover: an idea agent turning blocked -> "needs you" (Herdr state, best effort).
A task (ar_metaplan -> ar_plan -> ar_dev) sends exactly one Slack message itself, its final report; an
ar_goal loop sends its own summary. Costs no tokens.
Every event (plus an agent finishing its turn) is also appended to an inbox in the git common
dir (.git/ar_mate_inbox.md), which the mate reads with `mate_status.py --inbox` instead of polling agents.
"""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATUS = load("mate_status", HERE / "mate_status.py")
SLACK = load("slack_notify", HERE.parents[1] / "ar_notify/scripts/slack_notify.py")
AR_TREE = STATUS.AR_TREE


def watched_files(tree):
    board = tree / "__board__"
    for kind, pattern in (("plan", "plans/*.md"), ("report", "reports/*/*.md"), ("goal", "goal/summary.md")):
        for path in board.glob(pattern):
            yield kind, path


def message(project, slug, kind, path):
    if kind == "goal":
        return f"{project}/{slug}: ar_goal finished", SLACK.to_slack(path.read_text())[:3000]
    title, card = SLACK.from_report(path)
    label = "plan ready for review" if kind == "plan" else "experiment done"
    return f"{project}/{slug}: {label} — {title}", card


def inbox_path(root):
    """Machine-local event log, kept next to the watcher state in the git common dir (never committed)."""
    return (root / AR_TREE.git("rev-parse", "--git-common-dir", cwd=root)).resolve() / "ar_mate_inbox.md"


def to_inbox(root, slug, title, path=None):
    inbox = inbox_path(root)
    inbox.parent.mkdir(parents=True, exist_ok=True)
    where = f" ({path})" if path else ""
    with inbox.open("a") as handle:
        handle.write(f"- {time.strftime('%Y-%m-%d %H:%M')} {slug}: {title}{where}\n")


def check(root, state, send=True):
    """Return the Slack messages for changes since the last check; log every change to the inbox."""
    out = []
    for row in AR_TREE.read_rows(root):
        tree = Path(row["worktree"]) if row["worktree"] else None
        if row["status"] != "active" or not tree or not tree.exists():
            continue
        for kind, path in watched_files(tree):
            key = str(path)
            mtime = path.stat().st_mtime_ns
            if state["files"].get(key) == mtime or (kind == "plan" and key in state["files"]):
                state["files"][key] = mtime  # plans are announced once; your edits don't re-notify
                continue
            first_sight = key not in state["files"] and not state["started"]
            state["files"][key] = mtime
            if first_sight:
                continue
            title, text = message(root.name, row["slug"], kind, path)
            to_inbox(root, row["slug"], title.split(": ", 1)[-1], path.relative_to(tree))
        agent = STATUS.agent_state(row["pane"])
        previous = state["agents"].get(row["slug"])
        state["agents"][row["slug"]] = agent
        if agent in ("blocked", "done") and previous not in (None, agent):
            to_inbox(root, row["slug"], "agent needs you" if agent == "blocked" else "agent finished its turn")
        if agent == "blocked" and previous not in (None, "blocked"):
            out.append((None, f"{root.name}/{row['slug']}: agent needs you", f"Open Herdr tab `{root.name}:{row['slug']}`."))
    state["started"] = True
    if send:
        for path, title, text in out:
            result = SLACK.notify(title, text)
            if path and result["status"] == "sent":
                SLACK.mark_sent(path)
            print(json.dumps({"title": title, **result}), flush=True)
    return out


def git_head(path):
    result = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], text=True, capture_output=True)
    return result.stdout.strip()


def running(pid_path):
    try:
        pid = int(pid_path.read_text())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--ensure", action="store_true", help="Start in the background unless already running")
    args = parser.parse_args()
    root = AR_TREE.main_root()
    common = (root / AR_TREE.git("rev-parse", "--git-common-dir", cwd=root)).resolve()
    state_path, pid_path = common / "ar_mate_watch.json", common / "ar_mate_watch.pid"
    pid = running(pid_path)
    if args.ensure:
        if pid:
            print(f"mate watcher already running for {root.name} (pid {pid})")
            return
        with open(common / "ar_mate_watch.log", "a") as log:
            child = subprocess.Popen([sys.executable, __file__, "--interval", str(args.interval)], cwd=root,
                                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        print(f"mate watcher started for {root.name} (pid {child.pid}); log: {common / 'ar_mate_watch.log'}")
        return
    if pid and not args.once and pid != os.getpid():
        print(f"mate watcher already running for {root.name} (pid {pid})")
        return
    if not args.once:
        pid_path.write_text(str(os.getpid()))
    state = json.loads(state_path.read_text()) if state_path.exists() else {"files": {}, "agents": {}, "started": False}
    neo = HERE.parents[2]  # scripts/ -> ar_mate/ -> skills/ -> neo_research/
    version = git_head(neo)
    print(f"watching {root.name} ideas every {args.interval}s; Slack settings: {SLACK.env_file(root)}", flush=True)
    while True:
        check(root, state)
        state_path.write_text(json.dumps(state))
        if args.once:
            return
        time.sleep(args.interval)
        if git_head(neo) != version:  # neo_research was updated (git pull): restart on the new code
            print("neo_research updated; restarting watcher", flush=True)
            os.execv(sys.executable, [sys.executable, str(Path(__file__).resolve()), "--interval", str(args.interval)])


if __name__ == "__main__":
    main()
