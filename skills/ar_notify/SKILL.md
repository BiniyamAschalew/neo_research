---
name: ar_notify
description: Send a concise Slack summary (title, short text, 1-3 main figures) when an experiment run, ar_goal loop or ar_tree close finishes. Use at the end of every run; skip silently when Slack keys are absent.
---

# AR Notify

Send one message per finished run. Never let a notification failure change the run's outcome.

## Command

From the project root, resolving this skill's install path through its link:

```bash
python .agents/skills/ar_notify/scripts/slack_notify.py --report __board__/reports/<id>/<id>.md
```

`--report` uses the report title, its top section (Experiment Card or At a Glance, everything before `======`) and the first 1-3 figures in that section. Without a report:

```bash
python .agents/skills/ar_notify/scripts/slack_notify.py --title "<idea>: <run> done" \
  --text "<2-4 lines: question, result with numbers, decision, next>" --figure <main.png>
```

Add `--dry-run` to preview. The script prints JSON with `status`: `sent`, `skipped` (no keys), or `failed`.

## Message content

- Title: idea slug and run name.
- Text, 2-4 lines: what ran, the headline number versus baseline with uncertainty, whether the card's decision rule passed, the next step.
- Figures: 1-3 of the main result figures, never synthetic previews.

## Keys

`secrets/slack.env` in the neo_research checkout (gitignored; copy `secrets/slack.env.example`) or the file named by `AR_SLACK_ENV`. A webhook (`SLACK_WEBHOOK_URL`) sends text only; figures need `SLACK_BOT_TOKEN` (scopes `chat:write`, `files:write`) and `SLACK_CHANNEL_ID`. Report `skipped` or `failed` in one line and continue.
