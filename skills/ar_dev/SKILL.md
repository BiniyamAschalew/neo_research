---
name: ar_dev
description: Execute an AutoResearch plan with reuse-first modular code, versioned full/tiny YAML experiment configs, tracked real-data fixtures, debugger-ready run files, scoped verification, an updated repository structure.md, and a versioned report bundle under __board__/reports/.
---

Execute an AutoResearch plan from `__board__/plans/`.

## Shared Installation and Project Context

Use the active project as the working root, even when this skill resolves through a link into another repository. Read its applicable AGENTS.md or Claude instructions, status and relevant artifact policy. Project instructions, explicit user amendments and established experiment contracts take precedence over the defaults below. Never move generated research state into the shared skill repository merely because the skill is installed there.

Codex invokes `$ar_plan`/`$ar_dev`/`$ar_metaplan`; Claude uses `/ar_plan`/`/ar_dev`/`/ar_metaplan`. Record the actual assistant as author. Resolve this skill's supporting references and scripts relative to its installation, following links; resolve research/code/config paths against the active project.

Use targeted reads of the affected source and board references. Inspect actual implementations rather than relying on the code map. Preserve historical reports and frozen acquisition protocols; apply new execution conventions to new work or explicitly requested migrations.

## Board Bootstrap

Before starting:

1. Treat the current working directory as the project root unless the user gives a different root.
2. Do not create `__board__/` during ordinary session startup. Create it only when this skill is invoked.
3. Ensure only `__board__/` and `__board__/plans/` exist initially, creating them if missing.
4. If `__board__/STATUS.md` is missing, create it from the default template below.
5. Do not create `reports/`, `notes/`, or `refs/` merely for completeness. Create report directories only after selecting an executable plan; read optional directories only if they exist.
6. Save generated research artifacts under `__board__/`; maintain root `structure.md` as project documentation.

```markdown
# Project Status

**Last Updated**: YYYY-MM-DD (initialized)
**Current Phase**: Setup

## Recently Completed

_No completed iterations yet._

## In Progress

_None._

## Next Steps

- [ ] Create the first AutoResearch plan.

## Known Issues

_None yet._

## Notes

_Shared observations for Claude, Codex, and the human._
```

## Plan Selection

- If the user names a plan, resolve it under `__board__/plans/`. Accept `vN.slug`, `vN.slug.md`, or a full path.
- If no plan is named, execute the highest-numbered `vN.*.md` plan.
- If no plan exists, stop and ask the human to run `$ar_plan`.

## Core Development Invariants

- Treat the selected plan, its dependencies, acceptance criteria, and out-of-scope section as the execution contract.
- Follow the plan in order unless source or dependency reality requires a different order; document any deviation.
- Keep changes scoped to the plan and preserve unrelated behavior, user work, and repository conventions.
- When a requirement is ambiguous, make the smallest reasonable decision and document it. Ask the human if the choice would materially expand scope or authority.
- Do not run `git push` without explicit human instruction.

## Shared Execution Conventions

For executable work, read [structured execution conventions](../references/structured-execution.md). Implement semantic utility reuse and bounded restructuring, full/tiny profiles through the same production pipeline, tracked real-data excerpts and explicit device handling. Record actual forwards/optimizer updates and actual hardware status. Preserve frozen full settings and historical artifacts.

## Verification Policy

The default development path follows the selected plan: implementation, the repository-root debug run, and the tests or checks explicitly included in that plan. Do not add broad verification that is unrelated to the plan.

- Run unit tests when they are part of the selected plan or when the human explicitly requests tests or verification.
- Treat an **extra verification bundle** as opt-in for checks beyond the plan. Keep it small and relevant to the task; do not automatically run every possible config, compile, artifact, or reproducibility check.
- If no tests or checks are included in the plan and none are requested, record `Verification: not required by plan or request` in the report and continue with the primary debug run when the plan includes an experiment.
- For new executable work, the plan should include the applicable tiny-profile acceptance checks in the shared conventions. Run these as part of the root debug path, with full local data unavailable and dependencies/weights explicit. If an older plan lacks them, add only the bounded checks needed for the requested portability work and document the decision; do not silently expand an unrelated archived plan.
- Do not install test-only dependencies unless planned tests or an explicit verification request requires them.

## Version Resolution

Resolve `<version>` in this order:

1. Use the version in the plan heading, such as `v3` from `# Plan v3: ...` or `v1.0` from `# Plan v1.0: ...`.
2. Otherwise, use the leading version token in the plan filename.
3. If neither location is unambiguous, ask the human instead of guessing.

Use the exact version for directories, such as `config/v1.0/` and `__board__/reports/v1.0/`. For Python filenames, normalize dots and hyphens to underscores, such as `runs/run_v1_0.py`.

## Modularity and Organization Contract

Before adding code:

1. Read root `structure.md` if it exists and verify relevant entries against source.
2. Inspect existing modules, utilities, tests, configs, and run files for reusable interfaces.
3. Reuse or generalize focused utilities instead of copying experiment logic.
4. When a new function or file would duplicate or fragment existing behavior, perform the smallest safe reorganization that consolidates responsibilities.
5. Keep experiment entrypoints thin and move reusable behavior into cohesive modules.
6. Prefer small explicit functions, clear inputs and outputs, repository-consistent typing, deterministic seeds, and errors that preserve debugging context.
7. Organize by responsibility in folders; avoid root clutter, oversized modules, catch-all utility files, hidden global state, and unrelated refactors.
8. Write for human readability. A researcher should be able to read, step through and edit the code easily, so keep it concise and direct.

## Readability and Safety Checks

Too many defensive checks and safety wrappers make code hard to read and work with. Add a check only when it is necessary:

- **Keep a check when** it guards real external input (user configs, files, downloaded data, network or hardware availability), or a scientific invariant whose silent violation would corrupt results (split leakage, checkpoint or source identity, label alignment, shape or count contracts at a data boundary).
- **Drop a check when** it guards values the code itself just created, repeats one already made upstream, or covers a case that cannot occur. Do not add `if x is None` branches for arguments that are never `None`. Let ordinary Python errors (`KeyError`, shape mismatch) surface for programmer mistakes instead of pre-checking them.
- **Do not wrap code** in try/except that only re-raises, logs and continues, or swallows errors. Do not add wrapper functions or classes whose only purpose is safety or indirection.
- **Prefer plain code**: direct indexing over defensive `.get()` chains with fallbacks, and one fail-fast check at the boundary over repeated checks deep inside the code. Do not add optional parameters or fallback paths the plan does not need.
- When a check is necessary, make it one short line with an error message that names the problem.

Do not treat `structure.md` as a substitute for inspecting code. If the plan's architecture conflicts with source reality, choose the most concise safe design and document the decision.

## `structure.md` Contract

Create root `structure.md` during the first development run if it is absent. Refresh it after every run that changes code.

Keep it concise, current, and organized by repository-relative file path. Update changed/new/retired files and directly affected signatures incrementally; do not regenerate the entire map by default. For every documented maintained source file, include:

- A one-sentence file purpose.
- Every class signature and a one-sentence description.
- Every method signature and a one-sentence description.
- Every function signature and a one-sentence description.
- The debug/run entrypoint and shared callable relationship when applicable.

The repository-root `run.py` is the primary debugger entrypoint. Include its version macro, builder function, and imported versioned `main()` relationship in the map. Version-specific modules remain under `runs/`, but final validation must invoke the root runner.

Use language-native signatures, including parameters and return annotations when present. Include source files, tests, and experiment run files. Exclude dependencies, caches, generated build output, datasets, and `__board__/` artifacts. For files without classes or functions, record the file purpose and relevant entrypoint behavior.

Use this compact shape:

```markdown
# Code Structure

## `path/to/file.py`

Purpose: [One sentence.]

- `class Example(Base)` — [One sentence.]
  - `method(self, value: T) -> R` — [One sentence.]
- `function(config: Config) -> Result` — [One sentence.]
```

Verify documented signatures against the final source and remove stale entries for files or symbols changed by the selected plan.

## Experiment Config and Debug Contract

Use these defaults for new Python experiments; honor an established root entrypoint or layout specified by project instructions or the selected plan. Adapt to another language when appropriate. Code-only work needs no fabricated experiment configs or runner.


For every distinct experiment case:

1. Provide `config/<version>/<case>/full.yaml` and `tiny.yaml` derived from shared scientific defaults. Preserve the full settings; tiny changes input and work limits through the same pipeline. Reuse the same thin run module for both profiles.
2. Put run parameters in YAML rather than duplicating them in Python. Include seeds and other reproducibility-critical settings.
3. Use portable repository-relative paths; never store secrets or machine-specific absolute paths.
4. Keep a thin version-specific Python entrypoint under `runs/`:
   - One case: `runs/run_<version-id>.py`
   - Multiple cases: `runs/run_<version-id>_<case>.py`
   It must expose a no-argument `main()` callable and may retain an `if __name__ == "__main__"` compatibility block.
5. Define a visible module-level `CONFIG_PATH` constant in the version-specific module, defaulting to the case's `tiny.yaml`. Normal debugging requires only editing this variable; select `full.yaml` explicitly before scientific acquisition.
   **No argparse rule:** The main run files (root `run.py` and every `runs/run_<version>[_<case>].py`) must not use argparse or any other command-line parsing at all. Define the run settings as visible module-level variables inside the Python file — only the config path/name and similar general variables (for example `VERSION` and `CONFIG_PATH`), never experiment parameters, which belong in YAML. To run a different experiment, open the file and edit those variables. Reason: argparse is inconvenient with a Python debugger, which should launch `run.py` with no arguments. If an existing main run file you touch still parses arguments, flag it in the report.
6. Maintain a repository-root `run.py` as the sole primary debugger entrypoint. It must define a visible macro variable such as `VERSION = "v1"`, set to the latest implemented version, and provide `build_main(version: str) -> Callable[[], object]`. The builder imports the matching `runs.run_<version>` module or matching `runs.run_<version>_*` case module and returns its `main()` callable.
7. Run and debug from the repository root with `python run.py`; do not use a `runs/...` path for the final debug execution.

A root `run.py` should be equivalent to:

```python
from importlib import import_module
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent
VERSION = "v1"

def build_main(version: str) -> Callable[[], object]:
    module = import_module(f"runs.run_{version}")
    return module.main

if __name__ == "__main__":
    build_main(VERSION)()
```

Use eligible tracked real-data excerpts and a provenance/hash manifest, preferably reused under `tests/fixtures/<contract>/`. Tiny performs actual model execution and, for trainable methods, bounded optimizer updates; isolate its outputs from scientific results. Document external weights and dependencies so it runs without full datasets or ignored source helpers.

Keep model, data, training, evaluation, and plotting logic out of both runner layers. Validate that every YAML file loads, contains required fields, and is actually the config used by the versioned `main()`.

## Versioned Result Bundle

Follow the active project's report convention. Default new iterations to `__board__/reports/<plan-basename>/<plan-basename>.md`; preserve established `__board__/reports/<version>/<plan-basename>.md` layouts when specified. In the template below, `<report-id>` is the chosen directory name.

Create only this version's report directory and artifact subdirectories actually needed by the completed iteration.

```text
__board__/reports/<report-id>/
├── <same-filename-as-plan>.md
├── figures/
│   ├── <descriptive-plot-name>.png
│   └── <descriptive-plot-name>.csv
└── tables/
    └── <descriptive-table-name>.csv
```

- Always place the report inside the version directory, even without experiment artifacts.
- Save every published plot with adequate backing CSV data. Prefer `tables/` for backing data; preserve an established same-stem `figures/` CSV convention when required.
- Retain complete raw tables locally; publish the backing CSVs and per-run evidence needed to assess reported claims. Do not automatically track every intermediate table.
- Use stable filenames, clear CSV headers, and report-relative artifact links.
- Do not fabricate artifacts. Omit empty artifact directories when appropriate.
- Preserve existing board artifacts and never overwrite another iteration's files.

## Scientific Publication

For new scientific experiments, read the active project's `__board__/ARTIFACT_POLICY.md` when present; otherwise use the [publication defaults](../references/artifact-policy.md). Keep complete outputs locally under the report's ignored `local/`. Publish selected figures, adequate per-unit/per-run backing CSVs, essential executed scientific/plotting code, and compact configuration/provenance metadata. Nested scientific packages and bounded manifest-backed fixtures are supported; avoid whole-source snapshots and generic utility bundles.

For curated Python bundles, run this skill's `scripts/check_report_bundle.py` against the active project's report directory, with `--write-manifest --export <fresh-directory-outside-project>`. Use `--report-file <plan-basename>.md` when the report filename differs from the report directory. Its default budgets are 20 MiB total, 5 MiB per file and 2 MiB report-local fixtures; document necessary explicit overrides. Recreate the published plots from the isolated export with project PYTHONPATH unset and record the result and bundle size. A checker pass validates inventory/metadata/hashes/size, not scientific correctness. Follow an established local equivalent when its format differs; preserve old bundles unchanged. Non-experiment work can omit scientific artifacts and publication checks, explaining why.

## Execution Workflow

1. Read `__board__/STATUS.md` and the selected plan fully.
2. Read referenced reports, notes, and refs when those paths exist.
3. Read and verify `structure.md`, or inventory the source directly if this is the first development run.
4. Inspect all source, tests, utilities, configs, and entrypoints relevant to the plan.
5. Resolve the version, config directory, run filenames, and result-bundle path.
6. Implement the smallest reuse-first design; consolidate duplicated or fragmented logic when required. Follow **Readability and Safety Checks**: concise, readable code with safety checks only where necessary.
7. Create the planned full/tiny YAML pair and shared defaults, real-data fixture/manifest, and one thin debug entrypoint per experiment case.
8. Prefer `uv` for Python package management when available, but allow `pip install` when necessary. Record installs.
9. Run the tests and checks required by the selected plan, plus any explicitly requested checks. Skip unrelated extra verification. Capture exact commands and output for checks that ran.
10. Run the tiny profile through the repository-root debugger entrypoint (`python run.py`) with full data unavailable; record finite forwards/updates, resolved configuration, output isolation and actual device. Use the same entrypoint with full config only for authorized scientific acquisition. Do not report a tiny run as a completed full experiment or infer MPS support from a CUDA/CPU run.
11. Export selected figures, adequate backing tables, core executed code and compact metadata into the chosen result bundle. Run the applicable publication check and isolated plot replay for scientific results.
12. Create or refresh root `structure.md` from the final source.
13. Write the report under the chosen report directory, with the same basename as the plan.
14. Verify the report's first line, config/run mappings, artifact links, CSV headers, any planned or requested verification output, and `structure.md` signatures.
15. Update `__board__/STATUS.md`.

## Experiment Reporting Requirements

Write the report's methods and results like a concise experiments section of a research paper. Make it self-contained enough that a reader can understand each reported number and figure without opening the source code.

### Experimental methods and metrics

- Briefly explain each experiment or evaluation block: its question, compared methods, data/splits, controls or baselines, fixed conditions, and sample or cell count.
- Define every primary metric and important guardrail in plain language. State how it is computed, whether higher or lower is better, its evaluation grain, and how repeats/models/cells are aggregated.
- Explain interval, hypothesis-test, and multiplicity calculations when used. State the resampling or pairing unit and distinguish descriptive, exploratory, and confirmatory analyses.
- Record important metric handling such as multiclass averaging, calibration binning, undefined values, exclusions, ties, and reconstruction from saved predictions.
- Keep this concise: use short prose, a compact table, or the essential formula only when it materially helps interpretation.

### Results and figures

- Give each distinct experiment or result family its own short subsection.
- Before each table or plot, explain what experiment produced it and what comparison the reader should inspect.
- For every plot, include:
  1. A relative Markdown image link.
  2. A numbered caption immediately below it in the form `*Figure N. [Caption].*`
  3. A caption that identifies the experiment, axes or visual encodings, comparison/reference line, uncertainty display, evaluation population, and the bounded takeaway.
  4. A relative link to the backing CSV or source artifact when one exists.
- Explain the result shown by every table and figure in prose, including effect direction, uncertainty, guardrail status, and whether the declared decision rule passed. Do not merely restate the title or list values.
- Keep captions factual and independently understandable. Do not put unsupported causal or generalization claims in captions.
- If no experiment or plot exists, say so explicitly rather than inventing methods, metrics, or captions.

## Two-Part Report Structure

After the title and metadata, write each report in two parts:

1. **At a Glance:** Aim for two short paragraphs in plain language for a human reading in a rush. Lead with the question and actual outcome, then explain what the evidence supports, whether the planned criterion passed, the main limitation and its practical implication. Put key numbers, scope and verification facts in a compact table or simple diagram when useful. Keep effect sizes and uncertainty faithful to the detailed results, including negative, inconclusive or incomplete findings; leave implementation inventories and full experimental detail to the second part.
2. Put the exact separator `======` on its own line, with blank lines around it. Then retain the complete detailed report structure below, starting with Summary. The overview supplements the detailed report; all methods, metric definitions, results, captioned figures, reproduction information and caveats still belong in that part. Both parts must agree.

## Report Structure

The absolute first line names the actual primary debugger entrypoint and direct command. For the default root `run.py` convention, use this form:

````markdown
Debug entrypoint: `run.py` | Command: `python run.py`

# Report: [report name]

**Date**: YYYY-MM-DD
**Author**: [Actual assistant and invocation]
**Plan**: `__board__/plans/<plan-file>.md`
**Result Bundle**: `__board__/reports/<report-id>/`
**Primary Config**: `config/<version>/<case>/tiny.yaml` [record actual selected profile]

## At a Glance

[Short paragraph: what was investigated or changed, the headline outcome and whether the planned criterion passed.]

[Short paragraph: what the result means, its main uncertainty or limitation, and the practical implication or next decision.]

[When useful, add a compact table like the one below or a simple diagram. Adapt or omit rows; for non-experiment work, report implementation and verification status rather than invented metrics.]

| Detail | Finding |
|---|---|
| Scope / comparison | [Evaluation population and compared methods, or implementation scope] |
| Main result | [Effect size and uncertainty, or completion status] |
| Guardrails / verification | [Material caveat, guardrail outcome and relevant checks] |

======

## Summary

[Write one concise opening paragraph stating the experiment's core idea, how it was implemented and run, a rudimentary pseudo-example such as `load(CONFIG_PATH) -> run_experiment(config) -> evaluate(result)`, and the headline result.]

## Verification Results

Include this section when tests or checks were required by the selected plan or explicitly requested. If neither applies, write `Verification: not required by plan or request` under Validation, Issues & Caveats instead.

**Command**: `[exact requested verification command(s)]`

**Result**: [exact result and counts when applicable]

```text
[Include actual concise output for the requested checks. Do not replace output with an unsupported pass/fail claim.]
```

## Experimental Methods and Metric Computation

[For each experiment: question, compared methods, data/splits, controls, fixed settings, population and run counts. Define metrics, direction, aggregation and uncertainty/pairing units. Separate debug validation from scientific results. For non-experiment work, state that no scientific experiment ran.]

## Main Findings

[Move from the overall outcome to detailed evidence. Discuss only the three most important plots or tables when many artifacts exist.]

### [Finding 1]

[Explain the experiment, then interpret its effect, uncertainty, guardrails and decision status.]

![Descriptive alt text](figures/plot.png)

*Figure 1. [Self-contained caption: experiment, encodings, comparison, uncertainty, population and bounded takeaway]. Backing data: [`plot.csv`](figures/plot.csv).*

### [Finding 2]

[Repeat for another major finding.]

### [Finding 3]

[Include only when materially useful.]

## Reproduction and Debugging

| Case | Config | Debug entrypoint | Command |
|------|--------|------------------|---------|
| `[case]` | `../../../config/<version>/<case>/{tiny,full}.yaml` | `../../../run.py` | `python run.py` |

[State repository-root working directory, environment, seeds, data scope, key debugger checkpoints and how to set CONFIG_PATH. List every case and full/tiny differences; link the fixture manifest, document weight/cache prerequisites and isolated debug output location, and report actual CUDA/MPS/CPU validation separately. Tiny execution and figure-only replay are distinct.]

## Artifact Index

[List all generated figures and CSVs with report-relative links and one-line purposes.]

## Implementation and Structure Notes

[Summarize reused signatures, consolidated code, new interfaces, config/run organization, dependency installs, and the `structure.md` update. Keep routine file lists brief.]

## Validation, Issues & Caveats

[Report the primary debug-run result, planned/requested verification status, limitations, failed runs, technical debt, and unresolved issues with exact commands and numbers.]

## Suggested Next Steps

- [ ] [Concrete next action]
- [ ] [Concrete next action]
````

If the iteration has no experiment, use the most relevant executable validation entrypoint on the first line. Use `N/A` only when no runnable entrypoint exists, and explain why under caveats. Keep the opening overview concise and the main findings selective. Retain the complete detailed methods, metrics, captions and caveats after the `======` separator. Keep the existing first-line debugger declaration before the title; place At a Glance after the metadata.

## Status Update Rules

Update `__board__/STATUS.md`:

1. Set **Last Updated** to today's date and mention the plan.
2. Update **Current Phase** if appropriate.
3. Add the iteration and versioned result-bundle path to **Recently Completed**; keep only the last 3 items.
4. Update **In Progress**.
5. Replace **Next Steps** with the report's suggested next steps.
6. Update **Known Issues** based on test and experiment results.
