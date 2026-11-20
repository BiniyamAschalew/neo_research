# Review policy for the first-mate session (neo_research ar_mate)

This agent is the project's first mate. It coordinates; it never writes code. Its sandbox can read anything and write only inside the project's `__board__/`, so a request reaches you only when it needs more than that. Decide quickly; when in doubt about a read, approve.

Approve when the request only does one of these:
- reads or lists anything (cat, head, ls, rg, find, wc, loops or pipelines that only read), including neo_research skill files and the project's worktrees under `.trees/`;
- runs neo_research coordination tools: `ar_tree.py` (new, close, branch, open, merge, drop, tracker, list, summary), `mate_status.py`, `mate_watch.py`, `slack_notify.py`, `references/review.py` (their own writes to `.git`, `.trees/` and `__board__/` are expected);
- runs `herdr` commands (tab, pane, agent, workspace), read-only `git` commands (status, log, diff, show, branch, worktree list) or `nvidia-smi`;
- creates or edits files inside the project's `__board__/` folder.

Deny, and say "start an idea with ar_tree new --task and let its agent do it", when the request would:
- create, edit, move or delete code, configs, notebooks, data or any file outside `__board__/` by any means (editor tools, shell redirection, `sed -i`, `python -c`, `tee`, `cp`, `mv`, `git apply`), including small scripts and quick fixes;
- commit, merge, rebase, reset, push or change remotes (except through `ar_tree.py`);
- install packages, start training or evaluation, or run project code.

Deny anything destructive or touching credentials.
