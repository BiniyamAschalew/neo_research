---
name: ar_tree
description: Manage the three tiers of research code. If main is the paper, branches b<i>/<name> are its method sections (few, general directions like b1/ensembles, b2/context-compression) and worktrees are candidate ideas inside a section. Failed worktrees return only a summary; working ones are compacted, reviewed and promoted into a branch; a branch's best version graduates to main. __board__/TRACKER.md on main always shows every branch and worktree.
---

# AR Tree

```text
main                       the paper: refined code + every summary + __board__/TRACKER.md
 ├─ b1/ensembles           a method section: one general direction, long-lived git branch
 │   └─ worktree idea/<slug>   a candidate idea inside that section
 ├─ b2/context-compression
 └─ worktree idea/<slug>   a candidate idea that may start a new section
```

Keep branches **few and general** (default limit 4 active, `AR_MAX_BRANCHES`): a new branch is a new method section, named in 1-3 general words (`ensembles`, `context-compression`), never a specific trick (`cosine-lr-warmup`). A specific idea that works joins the branch it belongs to with `--into`. Unrelated trends never share a branch. Every move up goes through `ar_compact` (same results, less code) and `ar_review` (cross-agent discussion until ACCEPT or a human decision).

The tool `scripts/ar_tree.py` (relative to this skill, following links) does the git and Herdr work and rewrites `__board__/TRACKER.md` on every change; you write summaries and run compaction and review. Destructive commands are dry runs until `--yes`, which needs the human's approval. Branches can be named by number (`b2`), full name (`b2/ensembles`) or short name (`ensembles`).

```bash
T=.agents/skills/ar_tree/scripts/ar_tree.py
python $T new <slug> --question "..." [--from main|b2] [--agent codex]   # candidate idea in a worktree + tab
python $T close <slug> dead|parked [--yes]       # failed/paused: summary only reaches main
python $T promote <slug> --into b2 [--yes]        # works: joins an existing branch (the usual case)
python $T promote <slug> --new <name> [--yes]     # works and opens a new section: next b<i>/<name> (rare)
python $T open b2                                 # worktree ../<project>.branches/b2-<name> for compaction/review
python $T graduate b2 [--yes]                     # best version of the branch -> main
python $T drop b2 [--yes]                         # abandoned branch: summary only, archived as a tag
python $T tracker | list [--json]
python $T bury <slug> --question "..." --paths <old dirs/files> [--yes]   # clean old experiments off main
```

## Before planning anything

Read `__board__/TRACKER.md`, then `__board__/ideas/*.md` and `__board__/branches/*.md` in the main checkout. Do not repeat a failed approach unless its "Don't retry unless" condition now holds; say which. Decide with the human where a new idea starts: inside the branch it belongs to (`--from b2`), or from main only when it does not fit any existing section.

## Summaries

Every exit writes one summary in the main checkout: `__board__/ideas/<slug>.md` (close/promote) or `__board__/branches/b<i>-<name>.md` (graduate/drop). The dry run creates the template; fill it from the reports: question, approach (2-4 lines), setup, at most 5 main result rows with numbers versus baseline, why it failed (or "Did not fail"), don't retry unless, reusable pieces. Under 40 lines. The tool refuses to act on an unfilled summary.

## What each command does on `--yes`

- **close**: tags `archive/<slug>`, moves git-ignored raw results to `~/ar_archive/<project>/<slug>/`, commits the summary, registry and tracker to main, removes worktree, tab and (except `parked`) branch.
- **promote**: requires `__board__/COMPACTION.md` committed after every code change and an accepting `__board__/REVIEW.md` from another agent family committed after both (`--skip-compaction` / `--skip-review` are human overrides). `--new` refuses beyond the branch limit (`--force-new` is a human override) and names that are not 1-3 general words. Squash-merges the idea into the branch, keeping bookkeeping (`IDEA.md`, `STATUS.md`, `goal/`, `COMPACTION.md`, `compaction/`, `REVIEW.md`) out; stops on merge conflicts without changing anything. Then summary to main, tag, retire the worktree.
- **graduate**: same compaction and review gates on the branch (compact and review it in the `open` worktree), then squash-merges it into main as one commit with code, configs, plans and reports, keeps bookkeeping out, moves raw results into main, tags `archive/b<i>-<name>` and deletes the branch (`--keep` keeps it for further sections of work).
- **drop**: summary to main, tag `archive/b<i>-<name>`, branch and worktree removed.

Branch numbers are never reused. The main checkout stays on main with no uncommitted tracked changes (registry and tracker edits excepted). Pushing tags or branches needs explicit human instruction.

## Burying old main content

For experiments already on main: identify each experiment's code, configs and reports, write its summary, then `bury <slug> --paths ... --yes`. The tag `archive/<slug>` points at the pre-removal commit. Git history keeps the old blobs; shrinking history is a separate, explicit decision.
