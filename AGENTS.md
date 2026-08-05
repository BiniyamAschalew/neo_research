# Addis Research

This project uses Addis Research to coordinate Codex, Opus, and the human through a shared board.

## Startup

1. Read `__board__/STATUS.md` when it exists.
2. For an active experiment, read its plan, current review, state, and report.
3. Before planning or development, read `__board__/structure.md` when it exists and verify relevant entries against source.
4. Read only relevant entries from `__board__/record.md` and `registry.jsonl`.
5. Do not create board files during ordinary startup; invoked skills bootstrap lazily.

## Skills

| Skill | Purpose |
|---|---|
| `$ar-lit` | Map current work and select a small faithful reproduction. |
| `$ar-plan` | Write a claim-driven `E###` plan. |
| `$ar-review` | Independently review an idea, plan, code, result, or claim. |
| `$ar-dev` | Implement and run an `E###` plan; loops require review. |
| `$ar-compact` | Remove structural duplication without changing behavior. |
| `$ar-record` | Update durable research memory and lifecycle state. |
| `$ar-note` | Write focused run notes or final loop lineage. |
| `$ar-loop` | Reproduce prior work and run iterative research cycles. |

Claude exposes matching underscore commands such as `/ar_loop` and `/ar_compact`.

## Invariants

- Read `__board__/config.yaml` for every model route; do not hard-code routing.
- Treat the project root as one shared workspace: every routed agent may read any project file available to the invoking agent.
- Execution may self-check machine facts but cannot self-accept research quality.
- Keep one debugger-friendly entrypoint and shared `pipeline.py:run(config)` when orchestration is needed.
- Experiment runners use YAML plus visible module-level selectors and run without arguments; never use `argparse` in them.
- Keep `__board__/structure.md` as the concise map of architectural files and reusable signatures.
- Prefer config/reuse over new source files. Create semantic folders and abstractions only after real need appears.
- Keep source history in Git and research history under `__board__/`.
- Direct `$ar-plan` and `$ar-dev` use the lean path; only autonomous loops require plan and result review gates.
- Do not push Git changes without explicit human instruction.

Shared board and review contracts live in `.agents/references/`. The only engine helper is `.agents/tools/ar.py`; do not add shell wrappers unless repeated failures prove they are necessary.
