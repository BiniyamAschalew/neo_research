#!/usr/bin/env python3
"""Hand routine maintenance to an agent in the existing checkout, without research artifacts.

    python mate_task.py "Create a .gitignore for Python caches" [--agent codex] [--cwd PATH]
"""

import argparse
import importlib.util
import json
from pathlib import Path
import shlex

TREE = Path(__file__).resolve().parents[2] / "ar_tree/scripts/ar_tree.py"
SPEC = importlib.util.spec_from_file_location("ar_tree", TREE)
AR_TREE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AR_TREE)


def launch(task, agent, cwd=None):
    root = AR_TREE.main_root()
    checkout = Path(cwd).expanduser().resolve() if cwd else root
    if not checkout.is_dir():
        raise SystemExit(f"Not a directory: {checkout}")
    prompt = (f"Routine maintenance task: {task}\n\n"
              f"Work in {checkout} and complete only the requested task with ordinary tools. "
              "Do not invoke ar_metaplan, ar_plan or ar_dev, create an experiment worktree, "
              "or produce research plans, reports, W&B runs or Slack notifications. "
              "Follow the project's asset-link rules for datasets and checkpoints. "
              "Preserve unrelated changes, verify the result proportionately and give a short completion summary. "
              "Do not extend the task into experiment implementation or analysis.")
    command = shlex.join([*AR_TREE.agent_command(agent), prompt])
    activate = AR_TREE.SLACK.activation(AR_TREE.SLACK.load_keys(AR_TREE.SLACK.env_file(root)), interactive=True)
    if activate:
        command = f"{activate} && {command}"
    created = AR_TREE.create_herdr_tab(checkout, f"{root.name}:maintenance")
    result = (created or {}).get("result", {})
    pane = result.get("root_pane", {}).get("pane_id")
    if not pane:
        raise SystemExit("Herdr did not return a maintenance pane; no task was sent.")
    if AR_TREE.herdr("pane", "run", pane, command) is None:
        raise SystemExit(f"Could not confirm the handoff to {pane}; inspect it before retrying.")
    return {"tab": result.get("tab", {}).get("tab_id"), "pane": pane,
            "agent": agent, "cwd": str(checkout)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", help="Complete, concrete maintenance request")
    parser.add_argument("--agent", default=AR_TREE.AGENTS.DEFAULT)
    parser.add_argument("--cwd", help="Existing checkout/directory (default: main checkout)")
    args = parser.parse_args()
    print(json.dumps(launch(args.task, args.agent, args.cwd), indent=2))


if __name__ == "__main__":
    main()
