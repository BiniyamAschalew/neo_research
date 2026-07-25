---
description: "AutoResearch: optionally send Telegram notification"
argument-hint: "[optional focus or extra note]"
---

Send a concise completion notification if Telegram credentials are configured.
This command does not create board files.

## Steps

1. Write a 2-5 line summary covering goal, key changes/results, and follow-ups or blockers.
2. If `~/.config/claude-notify.env` exists and provides `TG_BOT_TOKEN` and `TG_CHAT_ID`, send the summary with Telegram.
3. If notification credentials are absent or sending fails, tell the human notification was skipped.

## Optional Extra Context

$ARGUMENTS
