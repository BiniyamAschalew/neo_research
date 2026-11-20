# Experiment tracking (W&B) conventions

Read when planning or implementing code that logs to W&B (or a W&B-compatible tracker such as CoreWeave). The project's `__board__/project.env` supplies `WANDB_ENTITY`/`WANDB_PROJECT`; runs launched through `notify_run.py` receive them automatically. The dashboard must be readable by someone who never saw the code.

## The one rule: a chart needs an x-axis

Use `wandb.log` only for quantities that change along a real axis (step, epoch, iteration, context size, budget). A value computed once per run never goes through `wandb.log`: it renders as a whole chart with a single dot.

| What you have | Where it goes |
|---|---|
| Loss/metric during training or optimization | `wandb.log({...}, step=...)` with `wandb.define_metric` for the axis |
| Metric over a swept variable (n_context, budget, noise level) | `wandb.log` with that variable as the defined x-axis, or one table + `wandb.plot.line` |
| Final scalar of this run (the decision metric, test AUC) | `run.summary["test/auc"] = ...` (shows in the runs table; compare runs there) |
| Several conditions/methods evaluated once (e.g. sampled vs same-model vs permuted vs oracle) | **one** `wandb.Table` (one row per condition × dataset × seed) + one bar chart with error bars; the key contrast also in `run.summary` |
| Per-seed / per-dataset results | rows of that table, never separate metric keys like `ds3_seed2_auc` |
| Report figures | `wandb.Image(path)` of the same figure the report uses, logged once under `figures/` |

Bad (the "one dot per chart" dashboard):

```python
wandb.log({"q4/sampled_mean_G": 0.105, "q4/same_model_mean_G": 0.115, "q4/permuted_mean_G": 0.27, ...})
```

Good:

```python
table = wandb.Table(columns=["condition", "dataset", "seed", "mean_G", "ci_low", "ci_high"], data=rows)
run.log({"q4_mechanism/results": table,
         "q4_mechanism/mean_G_by_condition": wandb.plot.bar(table, "condition", "mean_G", title="Q4 mean G by condition")})
run.summary["q4_mechanism/same_minus_cross_G"] = -0.004
```

## Naming and grouping

- **Run name**: `<plan-version>-<idea>-<case>-<profile>[-s<seed>]`, lowercase, descriptive: `v38-qmcr-sampled-full-s3`. Never W&B's random names or bare plan names.
- **group** = the plan (`v38-query-mediated-context-reconstruction`), so seeds and cases aggregate together; **job_type** = `train`, `eval`, `ablation`, `goal`, or `debug`; **tags** = idea slug, profile, dataset.
- **config** = the full resolved YAML config (`wandb.config.update(config)`), so every run is reproducible from the dashboard.
- Metric keys are namespaced by split and purpose: `train/loss`, `val/auc`, `test/auc`, `<question>/<metric>`. Keep the same key for the same quantity across plans.

## Hygiene

- Tiny/debug profiles: `job_type="debug"` and tag `tiny`, or `mode="disabled"`; never mix them with scientific runs in the default view.
- One run per training/evaluation job (per case × seed). Pure analysis over saved predictions: one run per experiment holding the tables.
- Call `run.finish()`; put the run (or group) URL in the report's Reproduction section.
- Log the same tables/figures that the report publishes; the report and the dashboard must agree.
