---
name: ar_dev
description: "Implement and run an AutoResearch plan from __board__/plans/: follow its Experiment Card, reuse and extend the entity-organized code base, run the tiny profile through run.py, launch runs through notify_run.py (Slack on completion), log curated W&B results, refresh structure.md, and write a report that opens with the card as Planned vs Actual. For research work, not routine downloads or repository housekeeping."
---

# AR Dev

Use this workflow for research ideation or experiments. For routine maintenance such as downloading a specified file or creating `.gitignore`, complete the task with ordinary tools and a short verification; do not create an experiment plan or report.

Work in the active project (or idea worktree). Read [board conventions](../references/board.md), `__board__/PROJECT.md` and `__board__/STATUS.md`. Project instructions and explicit human amendments override the defaults here. Record the actual agent as author. Do not `git push` without explicit instruction.

## 1. Select and read the plan

Use the named plan (`vN.slug`, filename or path) or the highest-numbered `__board__/plans/vN.*.md`; with none, ask for `ar_plan`. The **Experiment Card is the contract**: where the human edited it and the appendix disagrees, follow the card and note the conflict in the report. Follow the tasks in order; record any deviation. Ambiguity: take the smallest reasonable decision and record it; ask only if it expands scope.

## 2. Implement

Read [code style](../references/code-style.md) and, for executable work, [structured execution](../references/structured-execution.md).

- Start from `structure.md`, verified against the source you touch. Extend existing entities (`models/`, `methods/`, `data/`, `utils/<topic>/`) and register new ones in `_build.py`; never copy code per version or experiment.
- One experiment file `configs/expt/<name>.yaml` per case (entity choices + overrides); entity YAML only for new entities; `configs/profile/{tiny,full}.yaml`.
- Root `run.py`: visible `EXPERIMENT` and `PROFILE` constants, then `pipeline.run(build_config(EXPERIMENT, PROFILE))`; no argparse anywhere in the run path.
- Plain, readable code: checks only at real boundaries (external input, data/label/split contracts) as one-line errors; no try/except that only re-raises or swallows; no wrappers for safety alone; no optional paths the plan does not need.
- Datasets, checkpoints and large outputs reused across runs live behind `assets.links` soft links (add a line and rerun `ar_init .` for a new one); write checkpoints there, never into git.
- Delete code and configs this plan makes obsolete.
- Refresh `structure.md` for changed files: one-line purpose per file, every class/method/function signature with a one-line description, and the flow `run.py -> pipeline.run -> build_* -> fit/predict`.

## 3. Run

- Tiny first: `python run.py` with `PROFILE = "tiny"` on the tracked real-data fixture, actual model forward passes and (for trainable methods) a couple of optimizer updates, outputs isolated from results. Report the device actually used; never claim untested backends.
- Every run, tiny or full, goes through the run wrapper, which passes the project's W&B entity/project to it:
  `python .agents/skills/ar_notify/scripts/notify_run.py --name "<plan> <profile>" -- python run.py` (put the GPU claim helper from `~/.config/ar/host.md` inside it when required). Runs stay quiet; the task's one Slack message is the final report below. Add `--notify` only for a run you leave running after the task ends.
- Full profile only for scientific acquisition the plan authorizes. Long runs: start in a Herdr tab or `nohup`, never block the session on them.
- Tests: run those the plan lists or the human requests; otherwise write `Verification: not required by plan or request`. No broad extra suites, no test-only installs.
- W&B: follow [tracking](../references/tracking.md) (descriptive names and groups, curves only on a real x-axis, one-off results in `run.summary` or tables, debug runs separate). Training runs log train/val quantities during training every `log_every`/`eval_every` steps, then final values as summary and tables; before the full run, confirm the tiny run's history has several points per curve, and report the logged keys and point counts in Planned vs Actual.

## 4. Report

Write `__board__/reports/<plan-basename>/<plan-basename>.md` (keep a project's established layout). Line 1: `Debug entrypoint: run.py | Command: python run.py`. Then title and metadata (date, author, plan, experiment config + profile, **commit SHA**), then:

```markdown
## Experiment Card — Planned vs Actual

| | Planned | Actual |
|---|---|---|
| **Question** | [plan] | [unchanged / how it shifted] |
| **Change** | [plan] | [what was implemented] |
| **Flow** | [plan] | [actual shapes, counts, steps] |
| **Compare** | [A vs B] | [configs actually run] |
| **Runs** | [planned] | [completed / failed] |
| **Metric** | [definition] | [A, B, Δ with uncertainty] |
| **Decide** | [rule] | [passed / failed / inconclusive] |
| **Budget** | [planned] | [actual GPU-hours, device] |

**Verdict**: [one line with the deciding number]
**Next**: [one line]

![Main result](figures/<main>.png)
*Figure 1. [Self-contained caption: experiment, axes, comparison, uncertainty, population, bounded takeaway.] Backing data: [`<main>.csv`](tables/<main>.csv).*

======
```

After `======`: **Methods and metrics** (question, compared methods, data/splits, controls, seeds and replication unit, metric definitions with direction and aggregation, uncertainty method); **Findings** (one subsection per result family, each figure/table introduced, captioned and interpreted with effect size, uncertainty and whether the decision rule passed; at most 3 main figures, every plot with its backing CSV); **Reproduction** (commit, experiment config, profile, environment, seeds, fixture manifest, W&B run/group link); **Changes and structure** (reused/added/deleted code, config layout); **Caveats** (failed runs, limits, unverified backends, exact commands and numbers). Never fabricate artifacts or report a tiny run as a scientific result.

End the report (after Caveats) with the Slack message, at most 7 sentences in all, focused on the results:

```markdown
## Slack summary
- **Plan**: [one sentence: what was tested, on what data, against which baseline]
- **Results**: [1-3 sentences: the decisive numbers with uncertainty]
- **Takeaways**: [1-2 sentences: what it means for the question and what comes next]
- **W&B**: [run or group URL of these results]
```

For scientific results, publish per [artifact policy](../references/artifact-policy.md) (selected figures, backing tables, core code, `metadata.json`; raw outputs stay in ignored `local/`) and run its bundle check.

## 5. Finish

Update `STATUS.md` (see board conventions). Commit the code, configs and board files of this iteration in the current worktree or branch (never push, never commit data or secrets). Then, only when the task produced experiment results (not for a plan, a tiny/debug-only run or a failed run), send its Slack summary: `python .agents/skills/ar_notify/scripts/slack_notify.py --report <report.md>` (a `skipped`, `failed` or `refused` status never changes the outcome; fix a `refused` summary and resend once).
