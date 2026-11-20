"""How to start each supported coding agent. The single place to add a new agent.

    interactive  command for a tab you talk to
    headless     one-shot command that edits files and exits (ar_goal iterations)
    review       one-shot, read-only command for an independent reviewer (references/review.py)
    prefix       how skills are invoked in a prompt: /ar_plan (Claude) or $ar_plan (Codex)
    rules        extra arguments that make a file part of the session's standing instructions,
                 so they survive long sessions (used by the ar_mate launcher)
    guard        extra arguments that stop the mate from editing files outside __board__/:
                 Claude: a PreToolUse hook; Codex: read-only sandbox + a mate-specific review policy
    mate         default permission flags for the mate session (ar_mate --ask drops them):
                 Claude auto mode (a classifier approves safe actions, asks for risky ones);
                 Codex "Approve for me" (workspace-write sandbox, approvals sent to automatic review)
"""

import json
import os
from pathlib import Path
import shutil

AGENTS = {
    "claude": {
        "interactive": ["claude"],
        "headless": ["claude", "-p", "--permission-mode", "acceptEdits"],
        "review": ["claude", "-p", "--permission-mode", "plan"],
        "prefix": "/",
        "rules": lambda path: ["--append-system-prompt-file", str(path)],
        "mate": ["--permission-mode", "auto"],
        "guard": lambda script: ["--settings", json.dumps({"hooks": {"PreToolUse": [{
            "matcher": "Edit|Write|NotebookEdit|MultiEdit",
            "hooks": [{"type": "command", "command": f"python3 {script}"}]}]}})],
    },
    "codex": {
        "interactive": ["codex"],
        "headless": ["codex", "exec", "-s", "workspace-write"],
        "review": ["codex", "exec", "-s", "read-only"],
        "prefix": "$",
        "rules": lambda path: ["-c", "developer_instructions=" + json.dumps(Path(path).read_text())],
        "mate": ["-c", 'approval_policy="on-request"', "-c", 'approvals_reviewer="auto_review"'],
        "guard": lambda policy: ["-c", "hide_agent_reasoning=true", "-c", 'sandbox_mode="read-only"', "-c", 'approval_policy="on-request"',
                                 "-c", "auto_review.policy=" + json.dumps(Path(policy).read_text())],
    },
}
DEFAULT = os.environ.get("AR_AGENT", "claude")


def spec(name=None):
    """Known agent, or a best-effort entry for any other CLI (no standing rules, `/` skills)."""
    name = name or DEFAULT
    if name in AGENTS:
        return AGENTS[name]
    if not shutil.which(name):
        raise SystemExit(f"Unknown agent '{name}': not installed. Known: {', '.join(AGENTS)}")
    return {"interactive": [name], "headless": None, "review": None, "prefix": "/", "rules": None, "mate": [], "guard": None}


def other(name):
    """The reviewer for an author: a different agent family when one is available."""
    candidates = [a for a in AGENTS if a != name and shutil.which(AGENTS[a]["review"][0])]
    return candidates[0] if candidates else None


def skill(name, agent=None):
    """How to call a skill in this agent: skill('ar_plan', 'codex') -> '$ar_plan'."""
    return f"{spec(agent)['prefix']}{name}"
