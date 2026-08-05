---
name: ar-compact
description: Reorganize a cluttered codebase into fewer, semantic, reusable modules without changing behavior. Use when similar files duplicate a shared flow, variants should become YAML/config selections, or existing implementations need a canonical builder/extension pattern.
---

# AR Compact

Compact code without changing algorithms, defaults, data flow, metrics, seeds, outputs, or public behavior. This skill works standalone and uses `routing.dev`.

## Inspect

1. Run `python3 .agents/tools/ar.py init .`. Resolve `routing.dev`; read the model-routing section of `board.md` only if delegation is needed.
2. Read `__board__/structure.md`, Git status/diff when available, and only the requested files plus their callers, configs, and targeted tests. Preserve unrelated user work.
3. Find concrete duplicated structure or fragmented ownership. Two or three similar files are a signal, not an automatic reason to abstract.
4. Capture the cheapest existing behavior baseline: targeted tests or a small deterministic smoke run. Do not launch an expensive experiment merely to reorganize code.

If no change would reduce duplication or make ownership clearer, stop with a concise no-op finding.

## Compact

- Extract the genuinely shared sequence into one focused function, class, or pipeline step; inject only the differing component.
- Move parameter-only differences into YAML. Keep behavior in code.
- Add a builder/registry only when multiple real implementations are selected by a stable config key. Remove it if only one implementation remains.
- Group files by semantic responsibility and create folders only when populated. Never create version, `misc`, or catch-all utility folders.
- Keep one argument-free `experiment.py` with visible config/ID selectors; never introduce `argparse` or another runner.
- Migrate imports/configs, then delete superseded internal files. Preserve public interfaces unless all consumers are migrated safely.
- Prefer fewer concepts and lines, not merely fewer files. Do not merge unrelated responsibilities or add speculative base classes.

The surviving shared module, builder, and config shape is the template for future variants. Do not create a separate template file.

## Verify

1. Run the same targeted baseline after refactoring and compare relevant outputs.
2. Inspect the diff for accidental logic/default/value changes and stale imports or paths.
3. Update only affected entries in `__board__/structure.md`: current paths, purposes, key signatures, debug flow, and one concise extension pattern such as `new variant = YAML + builder registration + implementation only when behavior differs`.
4. Return consolidated/deleted paths, the reusable extension path, before/after checks, and any behavior-preservation uncertainty. Create no extra board report unless requested.
