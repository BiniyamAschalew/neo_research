"""How to start each supported coding agent. The single place to add a new agent.

    interactive  command for a tab you talk to
    headless     one-shot command that edits files and exits (ar_goal iterations)
    prefix       how skills are invoked in a prompt: /ar_plan (Claude) or $ar_plan (Codex)
    rules        extra arguments that make a file part of the session's standing instructions,
                 so they survive long sessions (used by the ar_mate launcher)
"""

import json
import os
from pathlib import Path
import shutil

AGENTS = {
    "claude": {
        "interactive": ["claude"],
        "headless": ["claude", "-p", "--permission-mode", "acceptEdits"],
        "prefix": "/",
        "rules": lambda path: ["--append-system-prompt-file", str(path)],
    },
    "codex": {
        "interactive": ["codex"],
        "headless": ["codex", "exec", "-s", "workspace-write"],
        "prefix": "$",
        "rules": lambda path: ["-c", "developer_instructions=" + json.dumps(Path(path).read_text())],
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
    return {"interactive": [name], "headless": None, "prefix": "/", "rules": None}


def skill(name, agent=None):
    """How to call a skill in this agent: skill('ar_plan', 'codex') -> '$ar_plan'."""
    return f"{spec(agent)['prefix']}{name}"
