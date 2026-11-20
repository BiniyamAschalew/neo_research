# Skills quick reference

Claude `/ar_<name>`, Codex `$ar_<name>`; scripts run from the project root (`.agents/skills/` is linked by `ar_init`). Default agent `claude`, or set `AR_AGENT=codex`.

## Flow

```text
ar_mate [codex]                                    tab 0, main checkout: the first mate
  ar_tree new <slug> --from b1|main                candidate idea: worktree + tab + agent
  ar_metaplan -> ar_plan                           you edit the Experiment Card
  ar_dev                                           runs via notify_run.py; one Slack message: the final report
  ar_goal                                          optional overnight tuning
  ar_tree close <slug> dead|parked                 failed: summary only reaches main
  ar_branch <slug>                                 works: compact + review + into its branch
  ar_merge b1                                      mature branch: compact + review + into main
```

## `ar_tree`
```bash
T=.agents/skills/ar_tree/scripts/ar_tree.py
python $T new <slug> --question "..." [--from main|b2] [--agent claude|codex] [--env <conda-env>]   # also links assets.links
python $T close <slug> dead|parked [--yes]
python $T branch <slug> [--into b2 | --new <name>] [--yes]   # step 5 of ar_branch
python $T open b2                                            # branch worktree ../<project>.branches/b2-<name>
python $T merge b2 [--keep] [--yes]                          # step 5 of ar_merge
python $T drop b2 [--yes]
python $T tracker | list [--json] | bury <slug> --question "..." --paths <old paths> [--yes]
```
- Worktrees `<project>/.trees/<slug>` (git-ignored, inside the project) on branch `idea/<slug>`; branches `b<i>/<name>`, numbers never reused, ≤4 active (`AR_MAX_BRANCHES`), names 1-3 general words.
- Every exit needs a filled summary in main (`__board__/ideas/<slug>.md` or `__board__/branches/b<i>-<name>.md`); code stays in tag `archive/<slug>` / `archive/b<i>-<name>`; raw results go to `~/ar_archive/` (or into main on merge). `--yes` acts; without it, a dry run.
- `__board__/TRACKER.md` on main is regenerated on every change.

## `ar_branch` and `ar_merge`
1. Compact ([compaction](skills/references/compaction.md)): agree what survives, freeze tiny outputs, rewrite, prove parity, commit `__board__/COMPACTION.md` last.
2. Review ([review](skills/references/review.md)): `python .agents/skills/references/review.py branch|merge` runs the other agent family read-only and appends a round to `__board__/REVIEW.md`; answer blocking findings, repeat up to 3 rounds, else the human decides.
3. Summary + `ar_tree branch|merge ... --yes` after the human approves. The gates refuse when code changed after `COMPACTION.md` or the review, or when the review is not an ACCEPT from another agent family (`--skip-compaction`, `--skip-review` are human overrides). Merges are squash merges that leave bookkeeping (`IDEA.md`, `STATUS.md`, `goal/`, `COMPACTION.md`, `REVIEW.md`) behind and stop on conflicts without changing anything.

## `ar_mate`
```bash
ar_mate [claude|codex] [--ask] [--project <path>] [-- <agent flags>]
python .agents/skills/ar_mate/scripts/mate_status.py [--json]       # ideas, agent states, latest results, GPUs
python .agents/skills/ar_mate/scripts/mate_watch.py --ensure        # inbox watcher (started by ar_mate)
```
The mate discusses and coordinates only: every coding task, however small, becomes `ar_tree new` + a new tab running `ar_plan`, then `ar_dev` after you approve the card (enforced: Claude by a hook, Codex by a read-only sandbox whose escalations are reviewed against `skills/ar_mate/mate_review_policy.md`). The watcher posts when a plan is ready, a report lands, a goal loop ends or an agent is blocked; it restarts itself after `git pull`.

## `ar_goal`
```bash
cp .agents/skills/ar_goal/goal.example.yaml __board__/goal.yaml      # edit and commit
python .agents/skills/ar_goal/scripts/goal.py __board__/goal.yaml --dry-run   # baseline + noise threshold
python .agents/skills/ar_goal/scripts/goal.py __board__/goal.yaml             # run / resume
```
Inside an idea worktree: each iteration a fresh agent (`agent: claude|codex`) makes one change in `allowed` files; kept only if validation beats the best by more than the measured noise. Stops at goal, iterations, hours or 3 failures; sealed test once at the end; Slack summary; one W&B run with progress curves. Your eval reads `AR_GOAL_SPLIT=val|test` and writes `metrics_file`.

## `ar_notify`
```bash
python .agents/skills/ar_notify/scripts/notify_run.py --notify --name "v3 full" -- python run.py
python .agents/skills/ar_notify/scripts/slack_notify.py --report __board__/reports/v3/v3.md
```
`notify_run.py` streams output live, passes the project's W&B entity/project and keeps the run's exit code. It is quiet by default (a task's one Slack message is its final report); with `--notify` it posts status, duration and the new report card (or output tail) when the run ends. Messages are text with text tables and end with the `WANDB_URL` link; no webhook means `skipped`.

## Planning, running, notes
| Skill | Run | Notes |
|---|---|---|
| `ar_metaplan` | `ar_metaplan "<idea>"` | evidence map, theory, design; ends with a draft card and a planning prompt |
| `ar_plan` | `ar_plan "<task>"` | Experiment Card (≤20 lines, ≤2 synthetic previews) + implementation appendix; edit the card before running |
| `ar_dev` | `ar_dev [vN]` | follows the card; tiny first; report = Planned vs Actual card, then methods, findings, reproduction (commit SHA) |
| `ar_note` | `ar_note "<topic>"` | `__board__/notes/NN.<slug>.md` with a TL;DR |
