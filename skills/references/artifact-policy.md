# Artifact policy for future experiments

Shared defaults for newly created experiments when the active project has no artifact policy. Local instructions and an established publication contract take precedence. Directory examples use the plan basename; retain a project's version-directory convention when required. Preserve existing reports, local outputs, tracked artifacts, and Git history. It limits future repository growth; it does not shrink past commits.

## Local execution and published results

Generate and retain everything needed to run, resume, audit, and fully reanalyze the experiment locally. Configure raw output paths under the report's ignored `local/` directory from the start. At finalization, export only the evidence needed to interpret reported conclusions and redraw the published figures. Do not automatically copy every CSV, image, JSON file, or source module.

```text
__board__/reports/vN.experiment/
  vN.experiment.md       # methods, results, captions, reproduction commands
  DATA.md               # optional table dictionary / detailed metric definitions
  SUPPLEMENT.md         # optional selected, captioned supplementary results
  metadata.json         # compact protocol and provenance; essential fields below
  config.json           # optional compact scientific configuration
  requirements.txt      # pinned dependencies needed for plotting the saved CSVs
  artifacts.csv         # published-file paths, byte sizes, SHA-256 hashes
  figures/              # selected main and supplementary images
  tables/               # selected CSV or CSV.gz backing those results
  code/                 # selected .py method/metric code (nested packages allowed) and portable plot.py
  fixtures/             # optional bounded real-data excerpts plus manifest.json
  local/                # ignored: complete raw and supplementary outputs
    run/                # predictions, shards, checkpoints, inputs, labels, caches
    analysis/           # full intermediate tables / large pairwise effects
    figures/            # all generated figures, including unselected variants
    provenance/         # complete environment, hashes, inventories, logs
```

Root Markdown documents, the named metadata/config/dependency/manifest files, supported images in `figures/`, CSV/CSV.gz in `tables/` (or `figures/` for an established same-stem convention), Python files recursively under `code/`, and manifest-listed small data files under `fixtures/` are eligible for Git. Configure project Git rules to keep other report outputs local; ignore patterns are project configuration, not installed automatically by this reference. Never force-add raw artifacts to bypass this layout. Do not migrate earlier experiments during unrelated work.

## Choosing what to publish

- **Reports and plots:** Include every figure needed to judge the primary comparisons, uncertainty, and material limitations. Additional supplements should support a stated result. Prefer PNG for raster charts and SVG for compact vector charts; use JPEG for photographs. Keep one format per figure by default; retain a second format only for an identified need.
- **Tables:** Export the exact data each published plot reads, preserving identifiers, units, precision, seeds, denominators, exclusions, and interval information. Keep per-dataset/per-run/per-seed results sufficient to inspect replication and aggregation. Large row-by-row or query-by-source matrices remain local unless essential to the published claim. For heatmaps, export the exact displayed matrix as CSV; for summarized distributions, export the plotted bins or quantiles plus counts and describe the reduction. Do not replace inference-level evidence with only a grand mean.
- **Core code:** Select the executed method, metric, and analysis implementations needed to understand the experiment, with original paths and hashes in metadata. Include a small portable plotting entrypoint. Keep generic job launchers, monitoring, download utilities, scratch scripts, whole-package snapshots, source ZIPs, and unrelated tests locally. Avoid rewriting scientific code into an unverified illustrative version. A small dependency directly required by the core method may be included; explain any omitted runtime dependencies and the limits of full experiment replay.
- **Metadata:** Write one concise `metadata.json`, generated from the actual frozen configuration and completed run rather than manually reconstructed guesses. Required top-level fields are `experiment_id`, `created_utc`, `protocol`, `provenance`, and `reproduction`. Under `protocol`, record datasets/versions and acquisition references, sample/context/query sizes, split construction, seeds and their meaning, methods/baselines, metrics, aggregation, uncertainty, exclusions, and completion counts. Under `provenance`, record relevant package/model versions, checkpoint and dataset fingerprints when available, source commit/dirty state, and selected core source paths/hashes. Under `reproduction`, record plotting commands, backing-table/figure mapping, scientific rerun commands and prerequisites, and which raw artifacts remain local. Use relative paths and publicly meaningful identifiers; do not require a machine-specific absolute path for plot reproduction. Full environment dumps, every-shard seals, and large inventories stay local.
- **Local-only files:** Preserve NPZ/NPY arrays, checkpoints, serialized models, raw data, detailed JSON/JSONL, logs, full supplementary matrices, and duplicate renderings in `local/`. Describe their role in the report as local-only text; do not create broken Markdown links to them. A Git clone supports interpreting results and redrawing selected figures; full reanalysis may require these local artifacts or rerunning inference.

For large experiments, export compact figure-specific tables from local results. The plotting entrypoint must read only the published CSV/CSV.gz and compact metadata, resolve paths relative to the bundle, and work without GPUs, private raw data, or ignored project utilities. Pin only its needed dependencies in `requirements.txt`; record the broader execution environment in metadata and local provenance.

## Finalization and size check

Aim for at most **20 MiB per experiment** and **5 MiB per published file**. These are practical defaults for new reports, not a reason to reduce dataset scale, replication, or evidence needed to support a conclusion. Compress CSVs, remove duplicate renderings, and export appropriate figure data first. When a necessary result still exceeds a default, document the reason and use explicit checker budget overrides; no additional approval is required within an authorized experiment.

1. Finish and verify the full local experiment. Export selected tables/figures and core code; create compact metadata from the actual run. Include table schemas, metric definitions, figure captions, and portable reproduction commands in the report.
2. From the repository root, run:

   ```bash
   python .agents/skills/ar_dev/scripts/check_report_bundle.py \
     __board__/reports/vN.experiment --write-manifest \
     --export /tmp/vN-experiment-publication-check
   ```

   Use a fresh, unique export path. Add `--report-file <plan-basename>.md` when the report filename differs from its directory. The helper inventories only Git-eligible files (plus already tracked files), rejects unexpected artifacts, checks required files/metadata and size limits, and writes `artifacts.csv`. It never deletes raw outputs, stages files, or changes Git history. It is a workflow helper; do not copy it into each experiment's `code/`.
3. In that isolated export, install the plotting requirements in a separate environment when needed and run the report's plotting command with project-specific `PYTHONPATH` unset. Confirm every published figure regenerates from exported data, the plotted values match, and all report links resolve within the published repository. The helper does not execute experiment code or validate scientific correctness. Record this check and bundle size in the report. Regenerate the manifest if published files change afterward.
4. Review the proposed Git diff for unexpected files and inspect `artifacts.csv` before staging the report. A checker pass does not commit anything. Do not use `git add -f` for ignored experiment outputs.

Changes to this workflow do not remove already tracked raw data. Any later cleanup of historical outputs or Git history is a separate task.

## Portable debugging fixtures and structured code

Future executable experiments provide full/tiny configurations through one maintained pipeline and a tracked real-data excerpt. The primary runner selects a config path in a variable; tiny exercises the actual model and applicable optimizer steps, not saved-output replay. Preserve full scientific settings and make backend/weight prerequisites explicit. Report actual CUDA/MPS validation independently. See [structured execution conventions](structured-execution.md).

Prefer shared tracked project fixtures when their contracts match; metadata may reference their manifest instead of duplicating them in each report. A report-local fixtures/ directory must have manifest.json containing source/provenance/row-selection information and a complete files list of relative paths and SHA-256 hashes. Eligible data formats are JSON, CSV/CSV.gz, NPY/NPZ and Parquet. No pickle, checkpoints or generic source bundles belong there. Target <=1MiB per fixture and <=2MiB report-local fixtures combined; document an explicit checker budget override when a valid minimum case requires more. Fixture bytes count toward the existing20MiB report/5MiB file limits. Nested scientific Python packages under code/ are permitted; keep private local/ state ignored. Existing reports need no migration.
