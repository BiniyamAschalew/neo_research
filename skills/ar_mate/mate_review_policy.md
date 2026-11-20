# Review policy for the first-mate session (neo_research ar_mate)

This agent is the project's first mate. It coordinates; it never writes code. It runs in a read-only sandbox, so every write or command that needs more than read access comes to you.

Approve when the request only does one of these:
- runs neo_research coordination tools: `.agents/skills/ar_tree/scripts/ar_tree.py` (new, close, branch, open, merge, drop, tracker, list, summary), `.agents/skills/ar_mate/scripts/mate_status.py`, `mate_watch.py`, `.agents/skills/ar_notify/scripts/slack_notify.py`, `.agents/skills/references/review.py`;
- runs `herdr` commands (tab, pane, agent, workspace) or read-only `git` commands (status, log, diff, show, branch, worktree list);
- creates or edits files inside the project's `__board__/` folder (registry, tracker, summaries, notes);
- runs `nvidia-smi` or other read-only status commands.

Deny, and say "start an idea with ar_tree new and give the task to its agent", when the request would:
- create, edit, move or delete code, configs, notebooks, data or any file outside `__board__/`, including small scripts and quick fixes, by any means (editor tools, shell redirection, `sed -i`, `python -c`, `tee`, `cp`, `mv`, `git apply`);
- commit code, merge, rebase, reset, push, or change remotes (except through `ar_tree.py`);
- install packages, start training or evaluation, or run project code directly.

Deny anything destructive, anything touching credentials or files outside the project and its worktrees, and any network request other than the configured Slack webhook.
