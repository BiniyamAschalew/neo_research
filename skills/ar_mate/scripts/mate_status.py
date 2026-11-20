#!/usr/bin/env python3
"""One-screen status of every idea in the project: phase, agent state, latest result, GPUs.

    python mate_status.py [--json]
    python mate_status.py --inbox      # only events since you last asked (plans, reports, goals, blocked/finished agents)
"""

import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess

TREE = Path(__file__).resolve().parents[2] / "ar_tree/scripts/ar_tree.py"
SPEC = importlib.util.spec_from_file_location("ar_tree", TREE)
AR_TREE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AR_TREE)
STATES = {"idle", "working", "blocked", "done", "unknown"}


def field(text, name):
    match = re.search(rf"\*\*{name}\*\*:\s*(.+)", text)
    return match.group(1).strip() if match else ""


def newest(folder, pattern="*.md"):
    files = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime) if folder.exists() else []
    return files[-1] if files else None


def agent_state(pane):
    if not pane or not shutil.which("herdr"):
        return ""
    result = subprocess.run(["herdr", "pane", "get", pane], text=True, capture_output=True)
    found = re.findall(r'"(?:agent_)?(?:status|state)"\s*:\s*"(\w+)"', result.stdout)
    return next((s for s in found if s in STATES), "unknown")


def goal_progress(tree):
    log = tree / "__board__/goal/log.tsv"
    if not log.exists():
        return ""
    rows = [line.split("\t") for line in log.read_text().splitlines()[1:] if line.strip()]
    kept = [r for r in rows if len(r) > 3 and r[3] == "kept"]
    return f"goal: {len(rows)} iters, {len(kept)} kept" + (f", best {kept[-1][2]}" if kept else "")


def idea_status(row):
    tree = Path(row["worktree"]) if row["worktree"] else None
    info = {"slug": row["slug"], "kind": row.get("kind") or "idea", "branch": row["branch"],
            "status": row["status"], "question": row["question"]}
    if not tree or not tree.exists():
        return info
    status = (tree / "__board__/STATUS.md").read_text() if (tree / "__board__/STATUS.md").exists() else ""
    report = newest(tree / "__board__/reports", "*/*.md")
    plan = newest(tree / "__board__/plans")
    info.update(phase=field(status, "Current Phase"), updated=field(status, "Last Updated"),
                agent=agent_state(row["pane"]), latest_plan=str(plan.relative_to(tree)) if plan else "",
                latest_report=str(report.relative_to(tree)) if report else "", goal=goal_progress(tree),
                dirty=bool(AR_TREE.git("status", "--porcelain", cwd=tree)))
    return info


def gpus():
    if not shutil.which("nvidia-smi"):
        return []
    out = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.used,memory.total,utilization.gpu",
                          "--format=csv,noheader,nounits"], text=True, capture_output=True).stdout
    return [dict(zip(["gpu", "mem_used_mib", "mem_total_mib", "util_pct"], [c.strip() for c in l.split(",")]))
            for l in out.splitlines() if l.strip()]


def unread(root):
    """Inbox lines written by mate_watch since the last call; advances the read cursor."""
    common = (root / AR_TREE.git("rev-parse", "--git-common-dir", cwd=root)).resolve()
    inbox = common / "ar_mate_inbox.md"
    cursor = common / "ar_mate_inbox.pos"
    text = inbox.read_text() if inbox.exists() else ""
    start = int(cursor.read_text()) if cursor.exists() else 0
    start = start if start <= len(text) else 0
    cursor.write_text(str(len(text)))
    return [line for line in text[start:].splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--inbox", action="store_true", help="Print new watcher events only")
    args = parser.parse_args()
    root = AR_TREE.main_root()
    if args.inbox:
        lines = unread(root)
        print("\n".join(lines) if lines else "no new events")
        return
    ideas = [idea_status(r) for r in AR_TREE.read_rows(root) if r["status"] in {"active", "parked"}]
    report = {"project": str(root), "ideas": ideas, "gpus": gpus(),
              "closed": sum(1 for r in AR_TREE.read_rows(root) if r["status"] not in {"active", "parked"})}
    if args.json:
        print(json.dumps(report, indent=2))
        return
    print(f"Project {root.name}: {len(ideas)} open ideas, {report['closed']} closed summaries")
    print(f"{'idea':<24} {'agent':<8} {'phase':<22} {'latest report / goal'}")
    for i in ideas:
        last = i.get("goal") or i.get("latest_report") or i.get("latest_plan") or "-"
        print(f"{(i['branch'] if i['kind'] in ('branch', 'direction') else i['slug']):<24} {i.get('agent') or '-':<8} {(i.get('phase') or i['status'])[:22]:<22} {last}"
              + ("  [uncommitted]" if i.get("dirty") else ""))
    for g in report["gpus"]:
        print(f"GPU{g['gpu']}: {g['mem_used_mib']}/{g['mem_total_mib']} MiB, {g['util_pct']}% (persist.py filler counts as used)")


if __name__ == "__main__":
    main()
