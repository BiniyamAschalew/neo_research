#!/usr/bin/env python3
"""Run an experiment command and send a Slack text summary when it ends (success, failure or Ctrl+C).

    python .agents/skills/ar_notify/scripts/notify_run.py -- python run.py
    python .agents/skills/ar_notify/scripts/notify_run.py --name "v3 full" -- python persist_notify.py run -- python run.py

Output streams to the terminal as usual; the wrapper exits with the command's exit code.
If a report under __board__/reports/ was written during the run, its card is included;
otherwise the last lines of output are.
"""

import argparse
from collections import deque
import importlib.util
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import sys
import time

SPEC = importlib.util.spec_from_file_location("slack_notify", Path(__file__).resolve().parent / "slack_notify.py")
SLACK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SLACK)


def duration(seconds):
    hours, rest = divmod(int(seconds), 3600)
    return f"{hours}h{rest // 60:02d}m" if hours else f"{rest // 60}m{rest % 60:02d}s"


def git_label():
    try:
        # main checkout name, so idea worktrees still show which project they belong to
        first = subprocess.run(["git", "worktree", "list", "--porcelain"], text=True, capture_output=True, check=True).stdout.splitlines()[0]
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True, capture_output=True).stdout.strip()
        return f"{Path(first.split(' ', 1)[1]).name}/{branch}"
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
        return Path.cwd().name


def new_report(pattern, since):
    files = [p for p in Path.cwd().glob(pattern) if p.stat().st_mtime >= since]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def message(name, command, code, seconds, tail, report):
    status = "finished" if code == 0 else ("interrupted" if code in (130, -2) else f"FAILED (exit {code})")
    title = f"{git_label()}: {name or command[:60]} {status} in {duration(seconds)}"
    text = f"`{command}` on {socket.gethostname()}"
    if report:
        _, card = SLACK.from_report(report)
        text += "\n" + card
    elif tail:
        text += "\nLast output:\n```\n" + "\n".join(tail) + "\n```"
    return title, text


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", help="Short run label for the Slack title")
    parser.add_argument("--report-glob", default="__board__/reports/*/*.md")
    parser.add_argument("--tail", type=int, default=15)
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- <command ...>")
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("give the command after --")
    started = time.time()
    tail = deque(maxlen=args.tail)
    code = 1
    try:
        env = {**os.environ, **SLACK.tracking_env(SLACK.load_keys())}  # runs log to this project's W&B workspace
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
        for line in process.stdout:
            sys.stdout.write(line)
            tail.append(line.rstrip()[:200])
        code = process.wait()
    except KeyboardInterrupt:
        process.terminate()
        code = 130
    finally:
        title, text = message(args.name, shlex.join(command), code, time.time() - started, list(tail),
                              new_report(args.report_glob, started))
        report = new_report(args.report_glob, started)
        result = SLACK.notify(title, text)
        if report and result["status"] == "sent":
            SLACK.mark_sent(report)
        print(f"[ar_notify] {json.dumps(result)}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
