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
    code, process, pending = 1, None, b""
    try:
        # unbuffered child + raw chunk passthrough: progress bars and logs appear live
        env = {**os.environ, "PYTHONUNBUFFERED": "1", **SLACK.tracking_env(SLACK.load_keys())}
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        while chunk := process.stdout.read1(65536):
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
            pending += chunk
            *lines, pending = pending.replace(b"\r", b"\n").split(b"\n")
            tail.extend(l.decode(errors="replace").rstrip()[:200] for l in lines if l.strip())
        code = process.wait()
    except KeyboardInterrupt:
        if process:
            process.terminate()
        code = 130
    except OSError as error:  # command not found / not executable
        tail.append(f"could not start: {error}")
        code = 127
    finally:
        if pending.strip():
            tail.append(pending.decode(errors="replace").rstrip()[:200])
        report = new_report(args.report_glob, started)
        title, text = message(args.name, shlex.join(command), code, time.time() - started, list(tail), report)
        result = SLACK.notify(title, text)
        if report and result["status"] == "sent":
            SLACK.mark_sent(report)
        print(f"[ar_notify] {json.dumps(result)}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
