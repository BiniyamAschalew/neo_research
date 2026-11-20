# Code style: a codebase a human can still run and debug

Read before planning, implementing or compacting research code. Goal: however many ideas are tried, each branch stays small enough that a researcher can read it, step through it with a debugger, and extend it without an agent. Project instructions (`__board__/PROJECT.md`) may adapt names, not the principles.

## Principles

1. **Reuse before adding.** Read `structure.md` and the relevant source first. Extend an existing entity (a model, method, dataset, metric) before creating a new one; generalize a function before copying it.
2. **One entity, one home.** Code is organized by what it is, not by which experiment introduced it. There are no per-experiment or per-version code copies (`runs/run_v38.py`, `config/v38/`, `model_v2.py`); experiment history lives in git commits and reports.
3. **Configs, not arguments.** Every run is selected by YAML. Entry files set visible module-level constants and never parse command-line arguments, so the debugger starts `python run.py` with no setup.
4. **Restructure continuously.** When a second variant appears, extract the shared part into the entity's base class or a `utils/` sub-module; when a variant dies, delete its code and config.
5. **Compact at every promotion.** Exploration code may be rough; code that moves to a direction branch or to main is first rewritten for clarity and efficiency with unchanged behavior (`ar_compact`).

## Layout

```text
run.py                      EXPERIMENT = "gnn_citation"; PROFILE = "tiny"  ->  pipeline.run(config)
pipeline.py                 run(config) -> results: build data, model, method; fit; evaluate
structure.md                every maintained file: purpose + signatures (see below)
configs/
  expt/<name>.yaml          one experiment = entity choices + overrides
  model/<name>.yaml         one file per model entity (defaults)
  method/<name>.yaml        one file per training/adaptation/inference method
  data/<name>.yaml          one file per dataset family
  profile/{full,tiny}.yaml  tiny only shrinks data/steps; full keeps scientific settings
models/
  _base.py                  abstract interface shared by all models
  _build.py                 build_model(config): name -> class registry
  <name>/<name>.py          one folder per model; split into <name>_base.py (nn.Module) when useful
methods/                    same pattern (_base.py, _build.py, <name>/)
data/                       same pattern: loaders, splits, transforms
utils/<topic>/              shared infrastructure split by topic: config, train, metrics, layers, io, tracking
tests/                      fast checks and tracked tiny fixtures
```

Create a folder only when it has content; keep a flat module until a second file justifies a sub-package. Never `misc.py`, `helpers2.py`, `new_utils.py`, `version_x/`.

## Configs (hierarchical)

```yaml
# configs/expt/gnn_citation.yaml
model: gnn            # -> configs/model/gnn.yaml
method: dann          # -> configs/method/dann.yaml
data: citation        # -> configs/data/citation.yaml
overrides:            # only what this experiment changes
  model: {hid_dim: 128}
  expt: {seeds: [0, 1, 2], source: ACMv9, target: DBLPv7}
```

`utils/config.py` provides `load(path)`, `deep_update(base, update)` and `build_config(expt_name, profile)`: load each chosen entity file under its key, apply `overrides`, then the profile. The resolved config is saved with every run and logged to W&B.

- A new config file only for a new entity. A variant of an existing entity is an override in an experiment file, not a new entity file.
- Experiment files are cheap and deletable; entity files are the maintained defaults.
- Tuned hyper-parameters go in an experiment file or `configs/tuned/<data>/<model>.yaml`, never in code.
- Paths are repository-relative or come from `__board__/PROJECT.md` / environment; no secrets in configs.

## Entities

- Each entity type has an abstract `_base.py` defining the interface (for example `fit(data)`, `predict(data)`), and shared behavior (loaders, early stopping, layer factories) lives there once.
- `_build.py` maps the config `name` to the class; adding a variant = one implementation file + one registry line + one YAML file.
- Constructors read their own section of the config (`config["model"]`); they do not reach into unrelated sections without passing values explicitly.

## `structure.md`

Repository-root map, refreshed after every code change: for each maintained file its one-line purpose and every class, method and function signature with a one-line description, plus the entry flow (`run.py -> pipeline.run -> build_* -> fit/predict`). Read it before planning; verify relevant entries against source.

## What leaves the codebase

When an experiment or variant is no longer part of what this branch claims, delete its code, entity file and experiment config in the same change that records its result (report or idea summary). Reports record the commit and experiment config that produced them, so any old result stays reproducible with `git checkout <commit>`.
