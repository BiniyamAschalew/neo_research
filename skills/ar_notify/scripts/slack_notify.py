#!/usr/bin/env python3
"""Send a concise text summary to Slack through an Incoming Webhook. Never fails a run.

Settings are per project: <main checkout>/__board__/project.env (never committed), found
from the current directory, so idea worktrees use their project's webhook. AR_SLACK_ENV
overrides the file. Markdown tables are sent as aligned monospace text tables.

    python slack_notify.py --report __board__/reports/v3.x/v3.x.md   # posts the report's ## Slack summary
"""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.parse
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
    """SLACK_WEBHOOK_URL and WANDB_URL (plus the entity/project/server derived from it) for this project."""
    path = Path(path) if path else env_file()
    keys = {"_file": str(path)}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                name, value = line.split("=", 1)
                keys[name.strip()] = value.strip().strip('"').strip("'")
    keys.setdefault("SLACK_WEBHOOK_URL", "")
    keys["WANDB_URL"] = keys.get("WANDB_URL") or keys.get("TRACKING_URL", "")  # TRACKING_URL: older name
    keys.update({k: v for k, v in parse_wandb_url(keys["WANDB_URL"]).items() if not keys.get(k)})
    return keys


def parse_wandb_url(url):
    """https://wandb.ai/<entity>/<project>[/...] -> WANDB_ENTITY, WANDB_PROJECT (+ WANDB_BASE_URL off wandb.ai)."""
    parts = urllib.parse.urlparse(url)
    segments = [s for s in parts.path.split("/") if s]
    if not parts.netloc or len(segments) < 2:
        return {}
    found = {"WANDB_ENTITY": segments[0], "WANDB_PROJECT": segments[1]}
    if parts.netloc not in {"wandb.ai", "www.wandb.ai"}:  # dedicated / CoreWeave-hosted server
        found["WANDB_BASE_URL"] = f"{parts.scheme}://{parts.netloc}"
    return found


def activation(keys, interactive=False):
    """Shell snippet that activates the project's code environment ('' when none is configured).
    CONDA_ENV=<name> or ENV_ACTIVATE=<any shell command, e.g. source .venv/bin/activate>."""
    if keys.get("ENV_ACTIVATE"):
        return keys["ENV_ACTIVATE"]
    if keys.get("CONDA_ENV"):
        hook = "" if interactive else 'eval "$(conda shell.bash hook)" && '
        return f"{hook}conda activate {keys['CONDA_ENV']}"
    return ""


def tracking_env(keys):
    """W&B variables to pass to experiment processes, so runs log to this project's workspace."""
    return {k: v for k, v in keys.items() if k.startswith("WANDB_") and k != "WANDB_URL" and v}


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


SUMMARY = ("Plan", "Results", "Takeaways", "W&B")
MAX_SENTENCES = 7


def result_summary(report):
    """The Slack message of a finished experiment: the report's `## Slack summary` lines Plan, Results,
    Takeaways (at most MAX_SENTENCES sentences in all) and W&B (run or group link). Plans are never posted."""
    report = Path(report)
    if report.parent.parent.name != "reports" or report.parent.parent.parent.name != "__board__":
        raise ValueError(f"{report} is not a report under __board__/reports/; only finished experiments are posted")
    body = report.read_text()
    title = next((l[2:].strip() for l in body.splitlines() if l.startswith("# ")), report.stem)
    section = re.search(r"^## Slack summary[^\n]*\n(.*?)(?=^#{1,2} |^======|\Z)", body, re.M | re.S)
    found = dict(re.findall(r"^[-*\s]*\**(Plan|Results|Takeaways|W&B)\**:\**\s*(.+?)\s*$", section.group(1), re.M)) if section else {}
    if missing := [k for k in SUMMARY if not found.get(k)]:
        raise ValueError(f"{report} has no complete '## Slack summary' (missing {', '.join(missing)})")
    sentences = sum(len(re.findall(r"[.!?](?=\s|$)", found[k])) or 1 for k in SUMMARY[:3])
    if sentences > MAX_SENTENCES:
        raise ValueError(f"Slack summary has {sentences} sentences; keep it to {MAX_SENTENCES}")
    return title, "\n".join(f"*{k}:* {found[k]}" for k in SUMMARY)


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


SENT_LOG = LEDGER.parent / "slack_sent.tsv"
MAX_PER_HOUR = int(os.environ.get("AR_SLACK_MAX_PER_HOUR", "3"))


def throttled(webhook, message):
    """Hard guard against floods: per webhook, never the same message twice in a day, at most MAX_PER_HOUR an hour."""
    import hashlib
    hook = hashlib.sha1(webhook.encode()).hexdigest()[:12]
    digest = hashlib.sha1(message.encode()).hexdigest()[:12]
    now = time.time()
    rows = [line.split("\t") for line in SENT_LOG.read_text().splitlines()] if SENT_LOG.exists() else []
    rows = [r for r in rows if len(r) == 3 and now - float(r[0]) < 86400]
    mine = [r for r in rows if r[1] == hook]
    if any(r[2] == digest for r in mine):
        return "duplicate of a message sent in the last 24 h"
    if sum(now - float(r[0]) < 3600 for r in mine) >= MAX_PER_HOUR:
        return f"over {MAX_PER_HOUR} messages this hour (AR_SLACK_MAX_PER_HOUR)"
    SENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    SENT_LOG.write_text("".join("\t".join(r) + "\n" for r in [*rows, [f"{now:.0f}", hook, digest]]))
    return ""


def notify(title="", text="", keys=None, dry_run=False, link=True, report=None):
    """Only a validated final report can reach Slack; legacy free-text calls are refused."""
    if report is None:
        return {"status": "refused", "reason": "Slack is reserved for final ar_dev report summaries; use --report"}
    try:
        title, text = result_summary(report)
    except (OSError, ValueError) as error:
        return {"status": "refused", "reason": str(error)}
    keys = keys or load_keys()
    message = f"*{title}*\n{text}".strip()
    if len(message) > MAX_TEXT:
        message = message[:MAX_TEXT - 4] + "\n…"
    if dry_run:
        return {"status": "dry_run", "message": message}
    if not keys["SLACK_WEBHOOK_URL"]:
        return {"status": "skipped", "reason": f"no SLACK_WEBHOOK_URL in {keys.get('_file', PROJECT_ENV)}"}
    if already_sent(report):
        return {"status": "suppressed", "reason": "this report version was already sent"}
    if reason := throttled(keys["SLACK_WEBHOOK_URL"], message):
        return {"status": "suppressed", "reason": reason}
    try:
        request = urllib.request.Request(keys["SLACK_WEBHOOK_URL"], json.dumps({"text": message}).encode(),
                                         {"Content-Type": "application/json"})
        urllib.request.urlopen(request, timeout=30).read()
        mark_sent(report)
        return {"status": "sent"}
    except Exception as error:  # a notification must never break the experiment
        return {"status": "failed", "reason": str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", type=Path, help="Report .md: sends its title and ## Slack summary")
    parser.add_argument("--title")
    parser.add_argument("--text", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = notify(report=args.report, dry_run=args.dry_run)
    print(json.dumps(result))


if __name__ == "__main__":
    sys.exit(main())
