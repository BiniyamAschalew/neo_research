---
name: ar_branch
description: Move a working candidate idea from its worktree into its parent branch b<i>/<name> (a method section), or rarely start the next branch. Compacts the code with parity proof, runs a cross-agent review discussion until ACCEPT, then squash-merges with ar_tree. Use when an idea in a worktree has worked and the human wants it kept.
---

# AR Branch: worktree → branch

Run inside the idea's worktree. The human approves what survives, unresolved review disagreements and the final `--yes`.

Under the results-only Git policy, squash merges transfer board evidence. Before retiring a worktree, explicitly transfer the approved compacted source/configs into the target's local checkout (open the target worktree if needed), verify fingerprints/parity there, and preserve the replaced local source in `__board__/notes/local/`. Git tags do not contain ignored code. Never force-add it to restore the old tracked-code behavior.

1. **Where it goes.** By default the branch the idea started from (see `__board__/IDEA.md` and `__board__/TRACKER.md` in the main checkout). If it started from main: join the existing branch whose method section it belongs to (`--into b2`); propose a new branch (`--new <name>`, 1-3 general words such as `ensembles`) only when it opens a genuinely new section, and say which existing branches you considered.
2. **Compact**: follow [compaction](../references/compaction.md) with target = that branch.
3. **Review**: follow [review](../references/review.md) with `review.py branch`.
4. **Summary**: `python .agents/skills/ar_tree/scripts/ar_tree.py branch <slug> [--into b2 | --new <name>]` (dry run) creates `__board__/ideas/<slug>.md` in the main checkout; fill it from the reports (under 40 lines: question, approach, setup, ≤5 result rows vs baseline, "Did not fail", don't retry unless, reusable pieces).
5. **Move**: show the human the summary and dry-run plan, then rerun with `--yes`. The idea is squash-merged into the branch without its bookkeeping (`IDEA.md`, `STATUS.md`, `goal/`, `COMPACTION.md`, `REVIEW.md`); a merge conflict changes nothing (merge the branch into the worktree, resolve, commit, compact and review again). The worktree, tab and idea branch are retired; the code stays in tag `archive/<slug>`; the tracker updates.
