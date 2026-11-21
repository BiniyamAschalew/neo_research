#!/usr/bin/env python3
"""Run an experiment command with the project's W&B settings; with --notify, post a Slack summary when it ends.

    python .agents/skills/ar_notify/scripts/notify_run.py -- python run.py                 # quiet: part of a task
    python .agents/skills/ar_notify/scripts/notify_run.py --notify --name "v3 full" -- python persist_notify.py run -- python run.py

Inside an ar_plan/ar_dev task the runs stay quiet: the task sends one Slack message, its final report.
Use --notify only for a run that outlives the task (launched in the background and left running); it posts
only if the run completes (exit 0), never for errors or Ctrl+C.

Output streams to the terminal as usual; the wrapper exits with the command's exit code.
If a report under __board__/reports/ was written during the run, its ## Slack summary is sent;
otherwise Slack stays silent. Raw output is never sent.
"""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

SPEC = importlib.util.spec_from_file_location("slack_notify", Path(__file__).resolve().parent / "slack_notify.py")
SLACK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SLACK)


def new_report(pattern, since):
    files = [p for p in Path.cwd().glob(pattern) if p.stat().st_mtime >= since]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", help="Run label (Slack uses the final report title)")
    parser.add_argument("--notify", action="store_true", help="On success, send a new final report summary if present; otherwise stay silent")
    parser.add_argument("--report-glob", default="__board__/reports/*/*.md")
    parser.add_argument("--tail", type=int, default=15, help=argparse.SUPPRESS)  # legacy flag; logs stay local
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- <command ...>")
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("give the command after --")
    started = time.time()
    code, process = 1, None
    try:
        # unbuffered child + raw chunk passthrough: progress bars and logs appear live
        env = {**os.environ, "PYTHONUNBUFFERED": "1", **SLACK.tracking_env(SLACK.load_keys())}
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        while chunk := process.stdout.read1(65536):
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
        code = process.wait()
    except KeyboardInterrupt:
        if process:
            process.terminate()
        code = 130
    except OSError as error:  # command not found / not executable
        print(f"could not start: {error}", file=sys.stderr)
        code = 127
    finally:
        if args.notify and code == 0:
            report = new_report(args.report_glob, started)
            if report:
                result = SLACK.notify(report=report)
                print(f"[ar_notify] {json.dumps(result)}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
