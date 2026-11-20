---
name: ar_compact
description: Compact an idea worktree or a direction branch before it is promoted (worktree -> direction branch) or graduated (direction branch -> main). Keep only the components the result depends on, rewrite them to be shorter, clearer and more efficient with identical behavior, prove parity, refresh structure.md and write __board__/COMPACTION.md, which ar_tree requires before promote/graduate.
---

# AR Compact

A promotion moves code up one tier: exploration worktree → direction branch → main. Each move is a compression: what arrives must be smaller and cleaner than what left, with the same results. Read [code style](../references/code-style.md) first.

## 1. Decide what survives (with the human)

1. Read the idea's reports or the direction's idea summaries, `structure.md` and the diff against the base: `git diff --stat <base>...HEAD`.
2. List the components the claimed result actually depends on: the winning variant, its data path, metric and the configs that reproduce the headline result. Everything else (rejected variants, sweeps, debug scaffolding, one-off analysis, duplicated helpers) is removed.
3. Show the human this keep/remove list and the target result to preserve (experiment name, metric, value) before rewriting.

## 2. Freeze the reference

Before editing, on the current commit, run the target experiment's tiny profile (and the planned tests) with fixed seeds; save the resolved config and outputs (metrics, and predictions when cheap) to `__board__/compaction/before/`.

## 3. Rewrite

- Delete removed components and their configs; fold the survivors into the existing entity folders, base classes and `utils/<topic>/` per code style; register them in `_build.py`.
- Merge duplicated logic, remove dead branches, flags for variants that no longer exist, needless defensive checks and wrappers; prefer vectorized and batched operations over Python loops where the result is identical.
- Keep the public behavior: same config keys for the surviving experiment (or an explicit, documented rename), same seeds, same metric definitions.
- Do not change algorithms, defaults, data splits or metrics. A change in results is a bug in the compaction unless the human approves it as a separate decision.

## 4. Prove parity

Rerun the same tiny profile and tests; save to `__board__/compaction/after/`. Metrics must match exactly or within the stated numerical tolerance (and predictions where saved). When the human asks or the result is about to graduate to main, also rerun the full profile of the headline experiment once and compare against its report.

## 5. Record

Refresh `structure.md`. Write `__board__/COMPACTION.md`:

```markdown
# Compaction: <idea or direction> -> <target branch>

**Date**: YYYY-MM-DD | **Agent**: ... | **Base**: <base branch>@<sha>
**Kept**: <components, one line each>
**Removed**: <components and configs>
**Size**: files A -> B, lines A -> B (`git diff --stat <base>...HEAD` before/after)
**Parity**: <experiment, profile, seeds>: <metric before> -> <metric after> (tolerance ...), tests <n passed>
**Full-profile check**: <done/not done and result>
```

Commit the rewrite and `COMPACTION.md` together, then run `ar_review`. `ar_tree promote` / `graduate` refuse if any code was committed after `COMPACTION.md`, so compaction is always the final step before moving up. Keep `__board__/compaction/` outputs local (they are git-ignored by convention under `local/` if large).
