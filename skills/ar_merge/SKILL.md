---
name: ar_merge
description: Merge the best version of a branch b<i>/<name> (a method section) into main (the paper). Opens a worktree on the branch, compacts it with parity proof (including one full-profile rerun of the headline result), runs a cross-agent review discussion until ACCEPT, then squash-merges into main as one commit with ar_tree. Use when a branch is mature enough for the paper.
---

# AR Merge: branch → main

Main receives only the best, compacted, reviewed version. The human approves what survives, unresolved review disagreements and the final `--yes`.

1. **Open**: `python .agents/skills/ar_tree/scripts/ar_tree.py open b2` creates `../<project>.branches/b2-<name>` (with a tab); work there.
2. **Compact**: follow [compaction](../references/compaction.md) with target = main. Keep only what the paper claims from this section; rerun the headline experiment's full profile once.
3. **Review**: follow [review](../references/review.md) with `review.py merge`; the reviewer judges paper-readiness.
4. **Summary**: `ar_tree.py merge b2` (dry run) creates `__board__/branches/b2-<name>.md` in the main checkout; fill it (the section's thesis, the ideas that built it, ≤5 headline results, what did not work, reusable pieces). The dry run also lists files changed on main since the branch started.
5. **Merge**: show the human the summary and plan, then `merge b2 --yes`: one squash commit on main with code, configs, plans and reports, bookkeeping kept out, raw results moved into main, branch archived as tag `archive/b2-<name>` and deleted (`--keep` to continue the section afterwards). Conflicts change nothing: merge main into the branch worktree, resolve, commit, compact and review again.
