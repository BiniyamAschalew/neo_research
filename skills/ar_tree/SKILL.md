---
name: ar_tree
description: Manage one git worktree per research idea. Start an idea in its own branch, worktree and Herdr tab; close it as dead, parked or win so that only a short summary (approach, main results, why it failed, when to retry) returns to main while code and results stay out. Also buries old experiments already on main.
---

# AR Tree

The tool `scripts/ar_tree.py` (relative to this skill, following links) does the git and Herdr work deterministically. You write the summary; the tool refuses to close until it is filled.

```bash
T=.agents/skills/ar_tree/scripts/ar_tree.py
python $T new <slug> --question "<one-line question>" [--agent codex] [--env <conda-env>]
python $T list
python $T close <slug> dead|parked|win          # dry run: shows tag, moves, merge, removals
python $T close <slug> dead|parked|win --yes    # act
python $T bury <slug> --question "..." --paths <old dirs/files> [--yes]
```

`<slug>` is a short lowercase-hyphen name (`spectral-warmstart`). Run every command from the main checkout or any idea worktree.

## Layout

- Worktree `../<project>.ideas/<slug>` on branch `idea/<slug>`; the same conda env serves every worktree.
- Main keeps `__board__/ideas.md` (registry) and `__board__/ideas/<slug>.md` (one summary per closed idea).
- The idea's plans, reports and notes live in its own `__board__/` and leave with the branch.
- `new` opens a Herdr tab in the worktree and starts the agent with `__board__/IDEA.md` as its brief (skipped when Herdr is absent).

## Before planning in any idea

Read every `__board__/ideas/*.md` in the main checkout. Do not propose an approach a summary marks as failed unless its "Don't retry unless" condition now holds; say which.

## Closing

1. Decide the verdict with the human: `dead` (does not work), `parked` (keep branch, drop worktree), `win` (merge).
2. Run `close <slug> <verdict>` once to create the summary template and see the plan.
3. Fill `__board__/ideas/<slug>.md` from the idea's reports: question, approach (2-4 lines), setup, at most 5 main result rows with numbers versus baseline, why it failed (evidence, not guesses), don't retry unless, reusable pieces. Keep it under 40 lines.
4. Show the human the summary and dry-run plan; run `--yes` only after their approval.

On `--yes` the tool: tags `archive/<slug>` (code stays recoverable, never on main), moves git-ignored raw results to `~/ar_archive/<project>/<slug>/`, for `win` copies only non-`__board__/` code/config changes onto main, commits only the summary, registry and those files, removes the worktree and Herdr tab, and deletes the branch (kept for `parked`). Main must be checked out on its base branch. Pushing the tag (`git push origin archive/<slug>`) needs explicit human instruction.

## Burying old main content

For experiments already on main: identify each experiment's code, configs and reports, write its summary, then `bury <slug> --paths ... --yes`. The tag `archive/<slug>` points at the pre-removal commit. Git history keeps the old blobs; shrinking history is a separate, explicit decision.
