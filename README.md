# Addis Research

A lean Codex + Opus research engine that searches prior work, reproduces one faithful baseline, tests claims, and improves an idea through independently reviewed experiments.

## Symlink Into Projects

Use absolute links so any base-engine update reaches every project:

```bash
BASE=/absolute/path/to/addis_research
PROJECT=/absolute/path/to/p1

ln -s "$BASE/.agents" "$PROJECT/.agents"
ln -s "$BASE/.claude" "$PROJECT/.claude"
ln -s "$BASE/.codex" "$PROJECT/.codex"
ln -s "$BASE/AGENTS.md" "$PROJECT/AGENTS.md"
```

Repeat for `p2`, `p3`, or other projects. Skills run from the project working directory, so each project lazily creates its own `__board__/`. To initialize before the first skill:

```bash
cd "$PROJECT"
python3 .agents/tools/ar.py init .
```

`.agents`, `.claude`, `.codex`, `AGENTS.md`, and the helper update immediately with the base symlinks. Generated board files remain independent and are never overwritten; existing project configs do not inherit later default-config changes. Newly required board files are created lazily by the updated helper. No shell scripts are included.

## Configure

Edit the generated `__board__/config.yaml`:

```yaml
models:
  think1: { model: gpt-5.6-sol, effort: xhigh }
  think2: { model: opus, effort: high }
  dev1:   { model: gpt-5.5, effort: high }

routing:
  lit: think1
  plan: think1
  critique: [think1, think2]
  dev: dev1
  result: think1
  record: think1
  loop: think1

settings:
  loop_size: 3
  max_review_rounds: 2
  save_token: false
  artifact_budget: { figures: 3, tables: 3 }
```

Install and authenticate both `codex` and `claude` CLIs when cross-family routing is required. A missing reviewer blocks acceptance; it does not trigger silent fallback.

All routed agents share the project root by default; there is no per-agent file allowlist in Addis. A host may still require authorization before sending those files to another provider. Configure project-wide cross-provider sharing before an unattended loop; if the host supports only per-payload approval, the loop blocks at preflight instead of halfway through a run.

## Full Loop

```text
Codex:  $ar-loop "Can uncertainty-aware sampling improve calibration?"
Claude: /ar_loop "Can uncertainty-aware sampling improve calibration?"
```

The loop asks once for your prediction, then:

```text
literature
-> reproduce one close paper method + its simplest baseline
-> cycle 1: smallest decisive pilot
-> cycles 2..N: evidence-driven improvement or pivot
-> final experiment-to-idea lineage
```

Reproduction uses one preselected small dataset excerpt or paper-backed synthetic evaluation. It aims to recover the paper result and the method-over-baseline direction. The same evaluation is reused across cycles when valid; one close reproduction is preferred over weak coverage of several datasets.

Example output for `loop_size: 3`:

```text
__board__/
  STATUS.md
  config.yaml
  record.md
  registry.jsonl
  structure.md                  # concise code and reuse map
  runs/E001/                 # paper reproduction
  runs/E002/                 # user-idea pilot
  runs/E003/                 # evidence-driven direction
  runs/E004/                 # final cycle
  notes/loop_E001_E004.md    # result -> next-idea lineage
```

## Skills

| Purpose | Codex | Claude | Main output |
|---|---|---|---|
| Literature | `$ar-lit "idea"` | `/ar_lit "idea"` | `record.md` literature synthesis + reproduction target |
| Plan | `$ar-plan "test X"` | `/ar_plan "test X"` | `runs/E###/plan.md` |
| Review | `$ar-review E002 result` | `/ar_review E002 result` | append-only `runs/E002/review.md` |
| Develop | `$ar-dev E002` | `/ar_dev E002` | `report.md`, `state.json`, optional `artifacts/` |
| Compact | `$ar-compact "models/"` | `/ar_compact "models/"` | reusable source structure + updated `structure.md` |
| Record | `$ar-record E002` | `/ar_record E002` | updated `record.md`, registry, and status |
| Note | `$ar-note E002 "finding"` | `/ar_note E002 "finding"` | optional run note or final loop lineage |
| Loop | `$ar-loop "idea"` | `/ar_loop "idea"` | reviewed E-runs + `notes/loop_<start>_<end>.md` |

`ar-plan` asks for a non-binding human prediction before the first user-hypothesis test. Reviewers and developers ignore it until after result judgment.

The first planning pass creates `__board__/structure.md`; `ar-dev` updates it when architecture changes. It lists important files, one-line responsibilities, debugger paths, and key reusable signatures rather than every symbol.

Experiment runners never use `argparse`. Parameters live in YAML, while visible constants such as `EXPERIMENT_ID`, `CONFIG_PATH`, `MODEL_IDS`, and `SEEDS` select the run. The debugger starts the file directly with `python experiment.py`; no arguments need to be reconstructed.

## Manual Experiment

Lean direct use:

```text
$ar-plan "smallest useful implementation or experiment"
$ar-dev E001
```

This produces a completed run without external review. For independently accepted research:

```text
$ar-lit "idea"
$ar-plan "smallest falsifying test"
$ar-review E001 plan
$ar-dev E001
$ar-review E001 result
$ar-record E001
```

Use the matching underscore commands in Claude.

For behavior-preserving cleanup, run `$ar-compact "scope"`. It consolidates proven duplication into shared modules, YAML, and builders only where multiple variants exist. It creates no report by default; source history stays in Git and affected `structure.md` entries become the extension guide.

## Deterministic Helper

`.agents/tools/ar.py` handles only operations that benefit from deterministic code:

```bash
python3 .agents/tools/ar.py allocate . experiment --field idea_id=I001
python3 .agents/tools/ar.py state . E001 running
python3 .agents/tools/ar.py resume . --idea I001
python3 .agents/tools/ar.py hash . __board__/runs/E001/plan.md
python3 .agents/tools/ar.py evidence . results.csv 0.91 --id C1
```

Run its tests with:

```bash
python3 -m unittest discover -s .agents/tools -p 'test_*.py' -v
```

See `AGENTS.md` for project rules and `.agents/references/` for the shared board and review contracts.
