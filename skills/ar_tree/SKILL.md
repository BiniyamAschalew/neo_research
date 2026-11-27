---
name: ar_tree
description: Manage research worktrees and branches. Main is the paper, branches b<i>/<name> are its few general method sections, worktrees are candidate ideas inside a section. Start ideas in worktrees, close failed ones (summary only), open branches, drop branches, keep __board__/TRACKER.md current. Moving code up is done by the ar_branch (worktree -> branch) and ar_merge (branch -> main) skills, which call this tool.
---

# AR Tree

```text
main                       the paper: refined code + every summary + __board__/TRACKER.md
 ├─ b1/ensembles           a method section: a long-lived git branch, few and general
 │   └─ worktree idea/<slug>   a candidate idea inside that section
 └─ worktree idea/<slug>   a candidate idea that may open a new section
```

```bash
T=.agents/skills/ar_tree/scripts/ar_tree.py
python $T new <slug> --question "..." [--from main|b2] [--agent codex]   # candidate idea: worktree + tab
python $T close <slug> dead|parked [--yes]     # failed/paused: summary only reaches main
python $T branch <slug> [--into b2|--new <name>] [--yes]   # used by ar_branch (needs compaction + review)
python $T open b2                               # worktree on a branch (used by ar_merge)
python $T merge b2 [--yes]                      # used by ar_merge (needs compaction + review)
python $T drop b2 [--yes]                       # abandoned branch: summary only, archived as a tag
python $T tracker | list [--json]
python $T bury <slug> --question "..." --paths <old dirs/files> [--yes]   # clean old experiments off main
```

Branches are named by number (`b2`), full name (`b2/ensembles`) or short name. Numbers are never reused. At most 4 branches are active (`AR_MAX_BRANCHES`); a new one needs a 1-3 word general name (`ensembles`, `context-compression`), never a specific trick. Destructive commands are dry runs until `--yes`, which needs the human's approval.

## Before planning anything

New worktrees receive an ID-bearing living idea and `IDEA.md` pointer. Read `ar_idea` before planning; `--quick` may reuse existing evidence but cannot bypass grounding. With the results-only Git policy, worktrees do not inherit ignored code: inspect the parent checkout's local source and copy only the needed source/configs into the worktree, preserving asset symlinks and excluding datasets/checkpoints/caches. Record the source paths/fingerprints. A branch/tag archives board evidence; ignored source is retained in the local archive when retiring a worktree.

Read `__board__/TRACKER.md`, then `__board__/ideas/*.md` and `__board__/branches/*.md` in the main checkout. Do not repeat a failed approach unless its "Don't retry unless" condition now holds; say which. Agree with the human where a new idea starts: inside the branch it belongs to (`--from b2`), or from main only when it fits no existing section.

## Closing and summaries

Every exit writes one summary in the main checkout: `__board__/ideas/<slug>.md` (close, branch) or `__board__/branches/b<i>-<name>.md` (merge, drop). The dry run creates the template; fill it from the reports in under 40 lines: question, approach, setup, ≤5 result rows vs baseline, why it failed (or "Did not fail"), don't retry unless, reusable pieces. The tool refuses unfilled summaries.

`close --yes` tags `archive/<slug>`, moves git-ignored raw results to `~/ar_archive/<project>/<slug>/`, commits summary, registry and tracker to main, and removes the worktree, tab and (except `parked`) the idea branch. `drop --yes` does the same for a branch (tag `archive/b<i>-<name>`). The main checkout stays on main with no uncommitted tracked changes. Pushing tags or branches needs explicit human instruction.

## Burying old main content

For experiments already on main: identify each experiment's code, configs and reports, write its summary, then `bury <slug> --paths ... --yes`. Tag `archive/<slug>` points at the pre-removal commit; shrinking git history is a separate, explicit decision.
