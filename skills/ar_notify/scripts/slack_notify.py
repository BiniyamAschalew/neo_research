#!/usr/bin/env python3
"""Send a concise run summary (text + up to 3 figures) to Slack. Never fails a run.

Keys live in <neo_research>/secrets/slack.env (gitignored) or the file named by
AR_SLACK_ENV. A webhook can post text only; figure upload needs a bot token.

    python slack_notify.py --report __board__/reports/v3.x/v3.x.md
    python slack_notify.py --title "E12 done" --text "AUC +0.01" --figure a.png
"""

import argparse
import json
import os
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
KEY_FILE = Path(os.environ.get("AR_SLACK_ENV", ROOT / "secrets/slack.env"))
MAX_TEXT = 2500
MAX_FIGURES = 3
IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")


def load_keys(path=KEY_FILE):
    keys = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                name, value = line.split("=", 1)
                keys[name.strip()] = value.strip().strip('"').strip("'")
    for name in ("SLACK_WEBHOOK_URL", "SLACK_BOT_TOKEN", "SLACK_CHANNEL_ID"):
        keys[name] = os.environ.get(name) or keys.get(name, "")
    return keys


def from_report(report):
    """Title, top section (card / At a Glance, before ======) and its first figures."""
    report = Path(report)
    lines = report.read_text().splitlines()
    title = next((l[2:].strip() for l in lines if l.startswith("# ")), report.stem)
    body = "\n".join(lines)
    top = body.split("\n======", 1)[0]
    start = re.search(r"^## (Experiment Card|At a Glance).*$", top, re.M)
    section = top[start.start():] if start else top
    figures = IMAGE.findall(section) or IMAGE.findall(body)
    paths = [(report.parent / f).resolve() for f in figures]
    paths = [p for p in paths if p.suffix.lower() in {".png", ".jpg", ".jpeg"} and p.exists()]
    text = IMAGE.sub("", section).strip()
    text = f"{text}\n\nReport: `{report}`"
    return title, text, paths[:MAX_FIGURES]


def slack_api(method, token, data=None, payload=None):
    if payload is not None:
        request = urllib.request.Request(
            f"https://slack.com/api/{method}", json.dumps(payload).encode(),
            {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"})
    else:
        request = urllib.request.Request(
            f"https://slack.com/api/{method}", urllib.parse.urlencode(data).encode(),
            {"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read())
    if not result.get("ok"):
        raise RuntimeError(f"{method}: {result.get('error')}")
    return result


def send_with_token(token, channel, message, figures):
    if not figures:
        slack_api("chat.postMessage", token, payload={"channel": channel, "text": message})
        return
    uploaded = []
    for path in figures:
        data = path.read_bytes()
        ticket = slack_api("files.getUploadURLExternal", token, {"filename": path.name, "length": len(data)})
        request = urllib.request.Request(ticket["upload_url"], data, {"Content-Type": "application/octet-stream"})
        urllib.request.urlopen(request, timeout=60).read()
        uploaded.append({"id": ticket["file_id"], "title": path.stem})
    slack_api("files.completeUploadExternal", token, payload={
        "files": uploaded, "channel_id": channel, "initial_comment": message})


def send_webhook(url, message, figures):
    if figures:
        message += "\n\nFigures (webhook cannot attach; add SLACK_BOT_TOKEN):\n" + "\n".join(f"• `{p}`" for p in figures)
    request = urllib.request.Request(url, json.dumps({"text": message}).encode(), {"Content-Type": "application/json"})
    urllib.request.urlopen(request, timeout=30).read()


def notify(title, text, figures, keys=None, dry_run=False):
    keys = keys or load_keys()
    message = f"*{title}*\n{text}"
    if len(message) > MAX_TEXT:
        message = message[:MAX_TEXT - 1] + "…"
    figures = [Path(f) for f in figures][:MAX_FIGURES]
    if dry_run:
        return {"status": "dry_run", "message": message, "figures": [str(f) for f in figures]}
    try:
        if keys["SLACK_BOT_TOKEN"] and keys["SLACK_CHANNEL_ID"]:
            send_with_token(keys["SLACK_BOT_TOKEN"], keys["SLACK_CHANNEL_ID"], message, figures)
            return {"status": "sent", "via": "bot", "figures": len(figures)}
        if keys["SLACK_WEBHOOK_URL"]:
            send_webhook(keys["SLACK_WEBHOOK_URL"], message, figures)
            return {"status": "sent", "via": "webhook", "figures": 0}
        return {"status": "skipped", "reason": f"no Slack keys in {KEY_FILE}"}
    except Exception as error:  # a notification must never break the experiment
        return {"status": "failed", "reason": str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", type=Path, help="Report .md: uses its title, top card and first figures")
    parser.add_argument("--title")
    parser.add_argument("--text", default="")
    parser.add_argument("--figure", action="append", default=[], type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    title, text, figures = args.title or "AutoResearch", args.text, args.figure
    if args.report:
        title, text, found = from_report(args.report)
        title, figures = args.title or title, args.figure or found
        text = f"{args.text}\n{text}".strip()
    print(json.dumps(notify(title, text, figures, dry_run=args.dry_run)))


if __name__ == "__main__":
    sys.exit(main())
