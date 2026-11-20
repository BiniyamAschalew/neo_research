---
name: ar_notify
description: Slack text notifications for finished experiments. Launch every experiment run through notify_run.py so its completion (success, failure or interrupt) always posts a summary; send the report card after writing a report. Text and text tables only.
---

# AR Notify

Every experiment completion must reach Slack. Notification failures never change a run's outcome.

## 1. Launch runs through the wrapper (automatic trigger)

Run any experiment, tiny or full, foreground or in a Herdr tab, as:

```bash
python .agents/skills/ar_notify/scripts/notify_run.py --name "<idea> v3 full" -- python run.py
# with the GPU claim helper:
python .agents/skills/ar_notify/scripts/notify_run.py --name "<run>" -- python <persist_notify.py> run -- python run.py
```

When the command ends it posts: project/branch, run name, finished / FAILED (exit code) / interrupted, duration, host, and either the card of a report written during the run or the last 15 output lines. It exits with the command's own code. `ar_goal` notifies by itself at the end of a loop, including on crash or Ctrl+C.

## 2. Send the report card after writing a report

```bash
python .agents/skills/ar_notify/scripts/slack_notify.py --report __board__/reports/<id>/<id>.md
```

Sends the report title and its top card (everything before `======`), with markdown tables converted to aligned text tables. Free-form: `--title "..." --text "..."`. Add `--dry-run` to preview. The script prints JSON `status`: `sent`, `skipped` (no webhook) or `failed`; mention it in one line and continue.

## Keys

Per project, in the main checkout's `__board__/project.env` (created by `ar_init`, never committed, shared by idea worktrees): `SLACK_WEBHOOK_URL` and `WANDB_URL` (the W&B project page `https://wandb.ai/<entity>/<project>`; its entity, project and, for dedicated servers, base URL are passed as `WANDB_ENTITY`/`WANDB_PROJECT`/`WANDB_BASE_URL` to runs launched through `notify_run.py` and `ar_goal`, and the link is appended to every message). Never print the webhook or copy it elsewhere.
