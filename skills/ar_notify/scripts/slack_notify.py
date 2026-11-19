#!/usr/bin/env python3
"""Send a concise text summary to Slack through an Incoming Webhook. Never fails a run.

The webhook URL lives in <neo_research>/secrets/slack.env (gitignored) or the file
named by AR_SLACK_ENV. Markdown tables are sent as aligned monospace text tables.

    python slack_notify.py --report __board__/reports/v3.x/v3.x.md
    python slack_notify.py --title "E12 done" --text "AUC +0.01"
"""

import argparse
import json
import os
from pathlib import Path
import re
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
KEY_FILE = Path(os.environ.get("AR_SLACK_ENV", ROOT / "secrets/slack.env"))
MAX_TEXT = 3500
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)\s*")


def load_keys(path=KEY_FILE):
    keys = {}
    if Path(path).exists():
        for line in Path(path).read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                name, value = line.split("=", 1)
                keys[name.strip()] = value.strip().strip('"').strip("'")
    keys["SLACK_WEBHOOK_URL"] = os.environ.get("SLACK_WEBHOOK_URL") or keys.get("SLACK_WEBHOOK_URL", "")
    return keys


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


def notify(title, text, keys=None, dry_run=False):
    keys = keys or load_keys()
    message = f"*{title}*\n{text}".strip()
    if len(message) > MAX_TEXT:
        message = message[:MAX_TEXT - 4] + "\n…"
    if dry_run:
        return {"status": "dry_run", "message": message}
    if not keys["SLACK_WEBHOOK_URL"]:
        return {"status": "skipped", "reason": f"no SLACK_WEBHOOK_URL in {KEY_FILE}"}
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
    print(json.dumps(notify(title, text, dry_run=args.dry_run)))


if __name__ == "__main__":
    sys.exit(main())
