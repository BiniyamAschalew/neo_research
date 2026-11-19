# Skills quick reference

Claude: `/ar_<name>`. Codex: `$ar_<name>`. Scripts run from the project root; `.agents/skills/` is linked by `ar_init`.

## Setup (once per project, per machine)

```bash
cd neo_research && ./ar_init ../my-project      # --dry-run to preview, --replace to back up conflicts
```

Links the shared agent files, creates `__board__/` and `__board__/PROJECT.md` (fill in env, data, conventions). Optional: paste a Slack Incoming Webhook URL into `neo_research/secrets/slack.env`.

## Typical flow

```text
/ar_mate "start an idea: does X improve Y?"     (tab 0, main checkout)
  -> ar_tree new x-idea                          new worktree + Herdr tab with its own agent
  -> /ar_metaplan -> /ar_plan                     you edit the Experiment Card
  -> /ar_dev                                      runs via notify_run.py -> Slack on completion
  -> /ar_goal (optional, overnight tuning)
  -> ar_tree close x-idea dead|parked|win         only the summary reaches main
```

## New skills

### `ar_tree`: one worktree per idea
```bash
T=.agents/skills/ar_tree/scripts/ar_tree.py
python $T new <slug> --question "..." [--agent codex] [--env <conda-env>]
python $T list
python $T close <slug> dead|parked|win     # dry run: shows the plan, creates the summary template
python $T close <slug> dead|parked|win --yes
python $T bury <slug> --question "..." --paths old_dir/ [--yes]   # clean old experiments off main
```
- Worktree `../<project>.ideas/<slug>`, branch `idea/<slug>`, Herdr tab `<project>:<slug>`.
- Close needs a filled `__board__/ideas/<slug>.md` (question, approach, main results, why it failed, don't retry unless). Code stays in tag `archive/<slug>`; raw results move to `~/ar_archive/`; `win` merges code only.

### `ar_mate`: first mate across ideas
```bash
/ar_mate status
python .agents/skills/ar_mate/scripts/mate_status.py [--json]
```
Run in Herdr tab 0 on the main checkout. Shows every idea's agent state, phase, latest report/goal progress and GPU use; starts ideas, hands instructions to idea tabs (`herdr pane run`), and escalates card approvals, closes, merges and pushes to you. Never edits idea code.

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
`notify_run.py` posts status, exit code, duration and the new report card (or the output tail) when the run ends, and returns the run's exit code. Tables are sent as text tables. Without a webhook it prints `skipped`.

## Existing skills (changed)

| Skill | Run | What changed |
|---|---|---|
| `ar_metaplan` | `/ar_metaplan "<idea>"` | Reads closed-idea summaries; handoff starts with a draft Experiment Card |
| `ar_plan` | `/ar_plan "<task>"` | Plan opens with a 20-line **Experiment Card** (Question, Change, Flow, Compare, Runs, Metric, Decide, Budget, Edit me). Edit it before running; the card wins over the appendix |
| `ar_dev` | `/ar_dev [vN]` | Follows the card; launches runs via `notify_run.py`; report opens with the card as **Planned vs Actual**; sends it to Slack |
| `ar_note` | `/ar_note "<topic>"` | Unchanged |

## Machine rules

GPU rules for a server (for example `persist.py` claims) live in `~/.config/ar/host.md`; `ar_init` installs it from `hosts/` when it recognizes the machine. Agents read it with `__board__/PROJECT.md` at startup.
