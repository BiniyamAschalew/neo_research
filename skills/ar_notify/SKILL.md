---
name: ar_notify
description: Slack text notification when ar_dev finishes with experiment results: the report's Slack summary (plan, results, takeaways, W&B link; at most 7 sentences). Never for plans. Launch runs through notify_run.py for the project's W&B settings.
---

# AR Notify

Slack gets one message per finished experiment, sent at the end of ar_dev; never for a plan, a metaplan or a debug-only run. Notification failures never change a run's outcome.

## 1. Launch runs through the wrapper (quiet)

```bash
python .agents/skills/ar_notify/scripts/notify_run.py --name "<idea> v3 full" -- python run.py
```

It passes the project's W&B settings and exits with the command's code. It posts nothing unless `--notify` is given, which is only for a run left running after the task; it then posts on success only, using the Slack summary of a report written during the run (or the last output lines). `ar_goal` posts by itself when a loop completes.

## 2. Send the Slack summary when ar_dev ends with results

```bash
python .agents/skills/ar_notify/scripts/slack_notify.py --report __board__/reports/<id>/<id>.md
```

Sends the report title and its `## Slack summary`: Plan, Results, Takeaways (at most 7 sentences together) and the W&B run/group link, nothing else. It refuses (`status: refused`) a file outside `__board__/reports/`, a missing or incomplete summary, or more than 7 sentences. Add `--dry-run` to preview. Other statuses: `sent`, `skipped` (no webhook), `suppressed` (flood guard), `failed`; mention it in one line and continue.

## Keys

Per project, in the main checkout's `__board__/project.env` (created by `ar_init`, never committed, shared by idea worktrees): `SLACK_WEBHOOK_URL` and `WANDB_URL` (the W&B project page `https://wandb.ai/<entity>/<project>`; its entity, project and, for dedicated servers, base URL are passed as `WANDB_ENTITY`/`WANDB_PROJECT`/`WANDB_BASE_URL` to runs launched through `notify_run.py` and `ar_goal`, and the link is appended to every message). Never print the webhook or copy it elsewhere.
