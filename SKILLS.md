# Skills quick reference

Claude: `/ar_<name>`. Codex: `$ar_<name>`. Default agent: `claude`, or `AR_AGENT=codex`. Scripts run from the project root; `.agents/skills/` is linked by `ar_init`.

## Setup (once per project, per machine)

```bash
cd neo_research && ./install                     # once per machine: ar_init / ar_mate on your PATH
ar_init ../my-project                            # also upgrades an older setup; --dry-run to preview, --untrack for old committed links
```

Links the shared agent files and creates `__board__/PROJECT.md` (env, data, conventions) and `__board__/project.env` (never committed: this project's `SLACK_WEBHOOK_URL` and `WANDB_URL`).

## Typical flow

```text
ar_mate [codex], then "start an idea: does X improve Y?"   (tab 0, main checkout)
  -> ar_tree new x-idea                          new worktree + Herdr tab with its own agent
  -> /ar_metaplan -> /ar_plan                     you edit the Experiment Card
  -> /ar_dev                                      runs via notify_run.py -> Slack on completion
  -> /ar_goal (optional, overnight tuning)
  -> ar_tree close x-idea dead|parked|win         dead/parked: summary only; win: code + results merged
```

## New skills

### `ar_tree`: one worktree per idea
```bash
T=.agents/skills/ar_tree/scripts/ar_tree.py
python $T new <slug> --question "..." [--agent claude|codex] [--env <conda-env>]
python $T list
python $T close <slug> dead|parked|win     # dry run: shows the plan, creates the summary template
python $T close <slug> dead|parked|win --yes
python $T bury <slug> --question "..." --paths old_dir/ [--yes]   # clean old experiments off main
```
- Worktree `../<project>.ideas/<slug>`, branch `idea/<slug>`, Herdr tab `<project>:<slug>`.
- Close needs a filled `__board__/ideas/<slug>.md` (question, approach, main results, why it failed, don't retry unless). Code stays in tag `archive/<slug>`; raw results move to `~/ar_archive/`; `win` squash-merges the idea's code, configs, plans and reports into main (stops on conflicts, changes nothing).

### `ar_mate`: first mate across ideas
```bash
cd my-project && ar_mate [claude|codex] [--ask]  # stays the mate through long sessions; auto approvals unless --ask
/ar_mate status                                  # inside an existing session (rules may fade when compacted)
python .agents/skills/ar_mate/scripts/mate_status.py [--json]
python .agents/skills/ar_mate/scripts/mate_watch.py --ensure   # Slack watcher in the background
```
Run in Herdr tab 0 on the main checkout. It keeps the Slack watcher running in the background (`mate_watch.py --ensure`), which posts to Slack (no tokens) when a plan is ready for review, a report lands, a goal loop ends or an idea agent is blocked. Shows every idea's agent state, phase, latest report/goal progress and GPU use; starts ideas, hands instructions to idea tabs (`herdr pane run`), and escalates card approvals, closes, merges and pushes to you. Never edits idea code.

### `ar_goal`: overnight improvement loop
```bash
cp .agents/skills/ar_goal/goal.example.yaml __board__/goal.yaml   # edit, then commit
python .agents/skills/ar_goal/scripts/goal.py __board__/goal.yaml --dry-run   # baseline + noise threshold
python .agents/skills/ar_goal/scripts/goal.py __board__/goal.yaml             # run / resume
```
Inside an idea worktree only. Each iteration: fresh agent → one change in `allowed` files → eval on val → commit if better than best by more than the noise, else revert. Stops at goal, `max_iters`, `max_hours` or 3 failures; evaluates the sealed test once at the end; writes `__board__/goal/summary.md`; Slack summary (also on crash or Ctrl+C). Your eval must honor `AR_GOAL_SPLIT=val|test` and write `metrics_file`.

### `ar_notify`: Slack text notifications
```bash
python .agents/skills/ar_notify/scripts/notify_run.py --name "v3 full" -- python run.py   # always notifies at the end
python .agents/skills/ar_notify/scripts/slack_notify.py --report __board__/reports/v3/v3.md
```
`notify_run.py` posts status, exit code, duration and the new report card (or the output tail) to this project's channel when the run ends, passes the W&B entity/project from `WANDB_URL` to the run, and returns the run's exit code. Every message ends with the `WANDB_URL` link. Without a webhook it prints `skipped`.

## Existing skills (changed)

| Skill | Run | What changed |
|---|---|---|
| `ar_metaplan` | `/ar_metaplan "<idea>"` | Reads closed-idea summaries; handoff starts with a draft Experiment Card |
| `ar_plan` | `/ar_plan "<task>"` | Plan opens with a 20-line **Experiment Card** (Question, Change, Flow, Compare, Runs, Metric, Decide, Budget, Edit me). Edit it before running; the card wins over the appendix |
| `ar_dev` | `/ar_dev [vN]` | Follows the card; launches runs via `notify_run.py`; report opens with the card as **Planned vs Actual**; sends it to Slack |
| `ar_note` | `/ar_note "<topic>"` | Unchanged |

## W&B logging

Follow [skills/references/tracking.md](skills/references/tracking.md): run names `<plan>-<idea>-<case>-<profile>-s<seed>`, group = plan, curves only along a real x-axis, final numbers in `run.summary`, condition × dataset × seed results in one `wandb.Table` with a chart, benchmarks as raw / summary (mean ± std over seeds) / leaderboard tables, debug runs separate.

## Machine rules

GPU rules for a server (for example `persist.py` claims) live in `~/.config/ar/host.md`; `ar_init` installs it from `hosts/` when it recognizes the machine. Agents read it with `__board__/PROJECT.md` at startup.
