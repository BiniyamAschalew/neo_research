# Experiment tracking (W&B) conventions

Read when planning or implementing code that logs to W&B (or a W&B-compatible tracker such as CoreWeave). The project's `__board__/project.env` supplies `WANDB_URL` (`https://wandb.ai/<entity>/<project>`), from which `WANDB_ENTITY`/`WANDB_PROJECT` are derived; runs launched through `notify_run.py` receive them automatically. The dashboard must be readable by someone who never saw the code.

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

## Benchmarks: models × datasets × seeds

Benchmark results always go to W&B as tables (CSV stays the published backing data). Log, in one `benchmark` run grouped with the plan:

1. `benchmark/raw`: long format, one row per model × dataset × seed (`model, dataset, seed, metric, value`, plus runtime if measured). Filterable and sortable in the UI.
2. `benchmark/summary`: one row per model × dataset with `mean, std, n_seeds, ci_low, ci_high`, the same aggregation the report uses.
3. `benchmark/leaderboard`: one row per model with the mean over datasets, mean rank, wins, and the gap to the reference baseline.
4. One chart per primary metric: `wandb.plot.bar` of the leaderboard, or the report's grouped bar/heatmap figure as `wandb.Image`.

```python
raw = results_df                                    # model, dataset, seed, metric, value
summary = (raw.groupby(["model", "dataset", "metric"])["value"]
              .agg(mean="mean", std="std", n_seeds="count").reset_index())
summary["rank"] = summary.groupby(["dataset", "metric"])["mean"].rank(ascending=False)  # higher is better
board = (summary.groupby(["model", "metric"])
            .agg(mean_over_datasets=("mean", "mean"), mean_rank=("rank", "mean")).reset_index()
            .sort_values("mean_rank"))
run.log({"benchmark/raw": wandb.Table(dataframe=raw),
         "benchmark/summary": wandb.Table(dataframe=summary),
         "benchmark/leaderboard": wandb.Table(dataframe=board),
         "benchmark/mean_rank": wandb.plot.bar(wandb.Table(dataframe=board[board.metric == PRIMARY]),
                                               "model", "mean_rank", title=f"Mean rank on {PRIMARY} (lower is better)")})
run.summary.update({f"leaderboard/{m}": v for m, v in board[board.metric == PRIMARY][["model", "mean_over_datasets"]].values})
```

State the metric direction in table titles or column names, use the same seeds and datasets for every model (or mark missing cells, never silently drop them), and keep model and dataset names identical to the report.

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
