#!/usr/bin/env python3
"""Send a concise text summary to Slack through an Incoming Webhook. Never fails a run.

Settings are per project: <main checkout>/__board__/project.env (never committed), found
from the current directory, so idea worktrees use their project's webhook. AR_SLACK_ENV
overrides the file. Markdown tables are sent as aligned monospace text tables.

    python slack_notify.py --report __board__/reports/v3.x/v3.x.md
    python slack_notify.py --title "E12 done" --text "AUC +0.01"
"""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

PROJECT_ENV = "__board__/project.env"
MAX_TEXT = 3500
LEDGER = Path(os.environ.get("AR_NOTIFY_LEDGER", Path.home() / ".cache/ar/notified.tsv"))
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)\s*")


def env_file(cwd=None):
    """The project's settings file: <main checkout>/__board__/project.env (or AR_SLACK_ENV)."""
    if os.environ.get("AR_SLACK_ENV"):
        return Path(os.environ["AR_SLACK_ENV"])
    listing = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=cwd, text=True, capture_output=True)
    root = Path(listing.stdout.splitlines()[0].split(" ", 1)[1]) if listing.returncode == 0 and listing.stdout else Path(cwd or ".").resolve()
    return root / PROJECT_ENV


def load_keys(path=None):
    """SLACK_WEBHOOK_URL, TRACKING_URL, WANDB_ENTITY, WANDB_PROJECT ... for this project."""
    path = Path(path) if path else env_file()
    keys = {"_file": str(path)}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                name, value = line.split("=", 1)
                keys[name.strip()] = value.strip().strip('"').strip("'")
    keys.setdefault("SLACK_WEBHOOK_URL", "")
    if not keys.get("TRACKING_URL") and keys.get("WANDB_ENTITY") and keys.get("WANDB_PROJECT"):
        host = (keys.get("WANDB_BASE_URL") or "https://wandb.ai").rstrip("/")
        keys["TRACKING_URL"] = f"{host}/{keys['WANDB_ENTITY']}/{keys['WANDB_PROJECT']}"
    keys.setdefault("TRACKING_URL", "")
    return keys


def tracking_env(keys):
    """W&B variables to pass to experiment processes, so runs log to this project's workspace."""
    return {k: v for k, v in keys.items() if k.startswith("WANDB_") and v}


def text_table(lines):
    """Markdown table rows -> aligned monospace table inside a code block."""
    rows = [[c.strip().replace("**", "").replace("`", "") for c in l.strip().strip("|").split("|")]
            for l in lines if not re.match(r"^\|?\s*:?-{2,}", l.strip().strip("|").strip())]
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    sizes = [min(max(len(r[i]) for r in rows), 48) for i in range(width)]
    out = ["  ".join(cell[:48].ljust(sizes[i]) for i, cell in enumerate(r)).rstrip() for r in rows]
    if len(out) > 1:
        out.insert(1, "  ".join("-" * s for s in sizes))
    return "```\n" + "\n".join(out) + "\n```"


def to_slack(markdown):
    """Markdown -> Slack mrkdwn: text tables, bold headings, no images."""
    out, table = [], []
    for line in IMAGE.sub("", markdown).splitlines():
        if line.strip().startswith("|"):
            table.append(line)
            continue
        if table:
            out.append(text_table(table))
            table = []
        heading = re.match(r"^#{1,6}\s+(.*)", line)
        line = f"*{heading.group(1)}*" if heading else re.sub(r"\*\*(.+?)\*\*", r"*\1*", line)
        out.append(line)
    if table:
        out.append(text_table(table))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def from_report(report):
    """Title and top section (Experiment Card / At a Glance, before ======) of a report."""
    report = Path(report)
    body = report.read_text()
    title = next((l[2:].strip() for l in body.splitlines() if l.startswith("# ")), report.stem)
    top = body.split("\n======", 1)[0]
    start = re.search(r"^## (Experiment Card|At a Glance).*$", top, re.M)
    section = top[start.start():] if start else top
    return title, to_slack(section) + f"\n\nReport: `{report}`"


def _key(path):
    path = Path(path).resolve()
    return f"{path}\t{path.stat().st_mtime_ns}"


def already_sent(path):
    """True if this exact version of a plan/report was already posted (by an agent, notify_run or the mate)."""
    return LEDGER.exists() and _key(path) in LEDGER.read_text().splitlines()


def mark_sent(path):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a") as handle:
        handle.write(_key(path) + "\n")


def notify(title, text, keys=None, dry_run=False):
    keys = keys or load_keys()
    message = f"*{title}*\n{text}".strip()
    if keys.get("TRACKING_URL"):
        message += f"\nTracking: {keys['TRACKING_URL']}"
    if len(message) > MAX_TEXT:
        message = message[:MAX_TEXT - 4] + "\n…"
    if dry_run:
        return {"status": "dry_run", "message": message}
    if not keys["SLACK_WEBHOOK_URL"]:
        return {"status": "skipped", "reason": f"no SLACK_WEBHOOK_URL in {keys.get('_file', PROJECT_ENV)}"}
    try:
        request = urllib.request.Request(keys["SLACK_WEBHOOK_URL"], json.dumps({"text": message}).encode(),
                                         {"Content-Type": "application/json"})
        urllib.request.urlopen(request, timeout=30).read()
        return {"status": "sent"}
    except Exception as error:  # a notification must never break the experiment
        return {"status": "failed", "reason": str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", type=Path, help="Report .md: sends its title and top card")
    parser.add_argument("--title")
    parser.add_argument("--text", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    title, text = args.title or "AutoResearch", to_slack(args.text)
    if args.report:
        title, card = from_report(args.report)
        title = args.title or title
        text = f"{text}\n{card}".strip()
    result = notify(title, text, dry_run=args.dry_run)
    if args.report and result["status"] == "sent":
        mark_sent(args.report)
    print(json.dumps(result))


if __name__ == "__main__":
    sys.exit(main())
