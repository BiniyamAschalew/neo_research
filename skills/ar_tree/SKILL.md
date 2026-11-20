---
name: ar_tree
description: Manage the three tiers of research code. Explorations live in git worktrees; ideas that work become direction branches (dir/<name>) for deeper exploration; only the best, compacted version of a direction graduates to main. Failed explorations and dropped directions return only a short summary to main. Use to start, close, promote, open, graduate or drop ideas and directions, and to bury old experiments on main.
---

# AR Tree

```text
main            refined, paper-worthy code + every summary (__board__/ideas/, __board__/directions/)
 ├─ dir/<name>  a direction that works (e.g. dir/context-compression, dir/ensembling), explored deeper
 │   └─ worktree idea/<slug>  an exploration branched from the direction
 └─ worktree idea/<slug>      an exploration branched from main
```

Every move up (worktree → direction, direction → main) goes through `ar_compact` first: same results, less and cleaner code. Unrelated trends are separate directions; never mix them in one branch.

The tool `scripts/ar_tree.py` (relative to this skill, following links) does the git and Herdr work; you write summaries and run compaction. Destructive commands are dry runs until `--yes`, which needs the human's approval.

```bash
T=.agents/skills/ar_tree/scripts/ar_tree.py
python $T new <slug> --question "..." [--from main|<direction>] [--agent codex]   # exploration worktree + tab
python $T close <slug> dead|parked [--yes]          # failed/paused: summary only reaches main
python $T promote <slug> --new <direction> [--yes]   # works: becomes dir/<direction> (after ar_compact)
python $T promote <slug> --into <direction> [--yes]  # deepens an existing direction (after ar_compact)
python $T open <direction>                           # worktree ../<project>.dirs/<direction> for compaction/review
python $T graduate <direction> [--yes]               # best version -> main (after ar_compact in the opened worktree)
python $T drop <direction> [--yes]                   # abandoned direction: summary only, branch archived as a tag
python $T list [--json]
python $T bury <slug> --question "..." --paths <old dirs/files> [--yes]   # clean old experiments off main
```

## Before planning anything

Read every `__board__/ideas/*.md` and `__board__/directions/*.md` in the main checkout. Do not repeat a failed approach unless its "Don't retry unless" condition now holds; say which. Decide with the human where a new exploration starts: from main for a new trend, from `<direction>` to go deeper in one.

## Summaries

Every exit writes one summary in the main checkout: `__board__/ideas/<slug>.md` (close/promote) or `__board__/directions/<name>.md` (graduate/drop). The dry run creates the template; fill it from the reports: question, approach (2-4 lines), setup, at most 5 main result rows with numbers versus baseline, why it failed (or "Did not fail"), don't retry unless, reusable pieces. Under 40 lines. The tool refuses to act on an unfilled summary.

## What each command does on `--yes`

- **close**: tags `archive/<slug>`, moves git-ignored raw results to `~/ar_archive/<project>/<slug>/`, commits the summary and registry to main, removes worktree, tab and (except `parked`) branch.
- **promote**: requires `__board__/COMPACTION.md` committed after every code change on the idea branch (`--skip-compaction` is a human override). Squash-merges the idea into `dir/<direction>` (created from the idea's base with `--new`), keeping bookkeeping (`IDEA.md`, `STATUS.md`, `goal/`, `COMPACTION.md`, `compaction/`) out; stops on merge conflicts without changing anything. Then summary to main, tag, retire the worktree.
- **graduate**: same compaction gate on the direction branch (compact it in the `open` worktree), then squash-merges it into main as one commit with code, configs, plans and reports, keeps bookkeeping out, moves raw results into main, tags `archive/dir-<direction>` and deletes the branch (`--keep` to keep it).
- **drop**: summary to main, tag `archive/dir-<direction>`, branch and worktree removed.

The main checkout stays on main with no uncommitted tracked changes (registry edits excepted). Pushing tags (`git push origin --tags`) or branches needs explicit human instruction.

## Burying old main content

For experiments already on main: identify each experiment's code, configs and reports, write its summary, then `bury <slug> --paths ... --yes`. The tag `archive/<slug>` points at the pre-removal commit. Git history keeps the old blobs; shrinking history is a separate, explicit decision.
