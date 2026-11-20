#!/usr/bin/env python3
"""Claude PreToolUse hook for the mate session: the mate never edits files outside __board__/.

Installed by the ar_mate launcher through `claude --settings`; reads the hook JSON on stdin and
denies Edit/Write/NotebookEdit/MultiEdit on any path outside the project's __board__/ folder.
"""

import json
from pathlib import Path
import sys

REASON = ("You are the first mate: hand file changes to an agent. For routine maintenance, use "
          "`python .agents/skills/ar_mate/scripts/mate_task.py \"<task>\"`; no research workflow is needed. "
          "For research ideation or experiments, use `ar_tree new <slug> --question \"...\" --task \"...\"`.")


def main():
    event = json.load(sys.stdin)
    path = (event.get("tool_input") or {}).get("file_path") or (event.get("tool_input") or {}).get("notebook_path") or ""
    target = (Path(event.get("cwd") or ".") / path).resolve() if path else None
    board = (Path(event.get("cwd") or ".") / "__board__").resolve()
    if target is not None and (target == board or board in target.parents):
        return 0  # registry, tracker and summaries are the mate's own files
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": REASON}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
