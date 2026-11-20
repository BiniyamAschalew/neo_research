#!/usr/bin/env python3
"""First-mate watcher: logs what changed in each idea to the mate's inbox. Never posts to Slack.

    python .agents/skills/ar_mate/scripts/mate_watch.py            # run in its own Herdr tab (or nohup)
    python .agents/skills/ar_mate/scripts/mate_watch.py --once     # one check, then exit
    python .agents/skills/ar_mate/scripts/mate_watch.py --ensure   # start in the background unless already running

Every --interval seconds it appends to .git/ar_mate_inbox.md (read by `mate_status.py --inbox`): a new plan,
a new report, a finished ar_goal loop, an idea agent blocked or finished. Costs no tokens. Slack only ever
gets completed work: a task's final report (ar_dev) and a completed ar_goal loop.
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
    """Log changes since the last check to the inbox; return them as (path, title) pairs."""
    out = []
    for row in AR_TREE.read_rows(root):
        tree = Path(row["worktree"]) if row["worktree"] else None
        if row["status"] != "active" or not tree or not tree.exists():
            continue
        for kind, path in watched_files(tree):
            key = str(path)
            mtime = path.stat().st_mtime_ns
            if state["files"].get(key) == mtime or (kind == "plan" and key in state["files"]):
                state["files"][key] = mtime  # plans are logged once; edits don't re-log
                continue
            first_sight = key not in state["files"] and not state["started"]
            state["files"][key] = mtime
            if first_sight:
                continue
            title = message(root.name, row["slug"], kind, path)[0].split(": ", 1)[-1]
            to_inbox(root, row["slug"], title, path.relative_to(tree))
            out.append((path, title))
        agent = STATUS.agent_state(row["pane"])
        previous = state["agents"].get(row["slug"])
        state["agents"][row["slug"]] = agent
        if agent in ("blocked", "done") and previous not in (None, agent):
            title = "agent needs you" if agent == "blocked" else "agent finished its turn"
            to_inbox(root, row["slug"], title)
            out.append((None, title))
    state["started"] = True
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
