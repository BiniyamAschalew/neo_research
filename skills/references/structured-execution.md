# Structured code and portable experiment execution

Read this when planning or developing executable research code. Apply the conventions to the maintained codebase; preserve historical reports and unrelated legacy workflows.

Code organization, configs and the run entrypoint follow [code style](code-style.md); this file covers profiles, fixtures, devices and acceptance evidence.

## Two execution profiles, one pipeline

For each main experiment, compose its configuration from entity configs plus an experiment file (`configs/expt/<name>.yaml`) and select a profile overlay (`configs/profile/tiny.yaml` or `full.yaml`), as described in [code style](code-style.md). The root run.py holds visible EXPERIMENT and PROFILE constants and runs the shared pipeline; it must not use argparse or other command-line parsing, because the debugger should launch `python run.py` with no arguments. Default debug runs to tiny and refresh structure.md when source changes. Resolve paths relative to the project/config location rather than the shell working directory.

Full preserves the chosen experiment's source versions, splits, seeds, model architecture/checkpoint, preprocessing, selection objective, budgets and training settings. Tiny calls the same loader/model/method/optimizer/scorer, reducing data, task/repetition counts and iteration limits only. Record resolved differences. Never substitute a mock, saved predictions or a different model architecture for a successful real-model tiny run. Prefer one batch or about 16 real rows; use the smallest larger excerpt necessary for valid roles, classes or context constraints. Default to two optimizer updates for methods that train. Frozen models run actual forward/in-context inference; do not describe fit() as gradient training without evidence.

Keep tiny outputs under the chosen report directory's ignored local/debug/ namespace; they are not scientific results. Avoid launching full acquisition by default from an example run file. Shared functions must not branch into separate scientific algorithms based on the profile name.

## Tracked real-data fixtures

Use an eligible, redistributable excerpt of the actual source that full consumes, with the same schema and preprocessing contract. Prefer development/training rows; never reveal sealed assessment targets to create a debugging case. Record source/version, permission to redistribute, role-aware row selection, transforms, shapes/schema, sizes and SHA-256 hashes in a small manifest.json. List every fixture file by relative path. For sensitive or restricted data, establish redistribution eligibility; a small excerpt is not automatically publishable. Preserve class/role constraints and avoid outcome-selected fixture creation. For historically unblinded datasets, explicitly record that fact. If full consumes cached prepared arrays, state that the fixture tests that prepared-input contract rather than raw preparation.

Reuse a fixture across experiments sharing a contract. Add fixtures for distinct schemas or demonstrated regression cases. Prefer <=1MiB per fixture; keep each fixture bundle <=2MiB by default, with justified explicit overrides when needed. Full datasets, checkpoints, environments and complete logs remain ignored. If an actual excerpt cannot be redistributed, document the unmet portability requirement and an eligible alternative rather than silently calling synthetic data a real excerpt.

## Devices and dependencies

Centralize explicit device resolution. Support CUDA and Apple's MPS when the actual model supports them; automatic mode may choose an available accelerator. An explicitly requested unavailable/unsupported accelerator must fail with a clear message unless a fallback is explicitly configured. Record actual device and precision; isolate CUDA-only kernels, synchronization and multiprocess setup. CPU numerical preprocessing is compatible with using MPS for model execution.

Weights remain external, with documented official source/version/hash/cache prerequisites. Tiny must not fetch full datasets or silently download large assets. Include necessary runtime dependencies or installation instructions; do not rely on ignored source helpers. Record unsupported model/backend combinations and actual-device test status. Never mark MPS verified from CUDA/CPU or mocked capability checks.

## Acceptance evidence

Ar_plan specifies module reuse/refactoring, the full/tiny differences, fixture/source/role selection, device/weight prerequisites and scoped verification gates. Ar_dev implements them and reports actual outcomes. Respect the repository verification policy: these applicable acceptance checks belong in executable-work plans; unrelated test suites remain optional. Ar_metaplan identifies feasibility requirements and information boundaries without prescribing an implementation before the research design is settled.

Verify: production path on tiny excerpts with large local data unavailable; finite model forward outputs; finite gradients and parameter updates for trainable methods; explicit unsupported-device behavior; separate outputs; full-profile setting preservation; refactor parity; and fixture hashes/size. Run on available real hardware and label other hardware unverified. Save the selected config and a concise runtime/dependency record. Keep figure-only reproduction as a separate standalone gate; tiny execution is not plot replay.

Prefer shared tracked fixtures under tests/fixtures/<semantic-contract>/ with manifest.json; reports may reference that manifest instead of duplicating data. Report-local fixtures/ may also be published with a manifest when allowed by the project artifact policy. Plan narrow Git exceptions for eligible fixtures when necessary; do not force-add ignored assets. Never use these paths to publish full cohorts, checkpoints or full run outputs; verify manifest hashes and size before staging. Keep private and cache paths ignored. Follow the active project's report layout and backing-table convention; use the [publication defaults](artifact-policy.md) when none is defined. If an artifact policy or bundle checker is introduced or already present, keep its eligible layouts consistent with Git rules. Preserve existing reports and unrelated tracking rules.
