---
name: ar-plan
description: Create a lean standalone Addis implementation, experiment, or reproduction plan with concrete reuse, evaluation, budget, and debugger details. Use directly or from ar-loop before development.
---

# AR Plan

Create one concise plan. This skill works directly; `ar-lit` and `ar-loop` are optional.

## Start

1. Run `python3 .agents/tools/ar.py init .`.
2. Resolve `routing.plan` from `__board__/config.yaml`; read the model-routing section of `board.md` only if delegation is needed.
3. Read `__board__/STATUS.md`, `__board__/structure.md` when present, and only task-relevant board entries and source. Verify relevant map entries against code; do not scan history without need.
4. If `__board__/structure.md` is missing, create it incrementally from the architectural files inspected: path, one-line purpose, and key reusable signatures only.
5. Reuse a supplied `I###`; otherwise run `python3 .agents/tools/ar.py allocate . idea`. Allocate the experiment with:

```bash
python3 .agents/tools/ar.py allocate . experiment --field idea_id=I001
```

## Decide

Choose `implementation`, `hypothesis`, or `reproduction` mode. For the first plan testing a user hypothesis, ask for their expected direction, brief reason, and confidence before finishing. Preserve the answer as a non-normative prediction; draft the method, baseline, metric, and threshold first and never alter them to match it. Skip prediction for implementation and published-result reproduction.

## Write

Write `__board__/runs/E###/plan.md`:

```markdown
# E###: [Title]
**Idea / mode**: I### | implementation | hypothesis | reproduction
**Goal**: ...
**Hypothesis / falsifier / prediction**: ...

## Evaluation
- Data/subset, baseline, metric, success/failure threshold: ...
- Reproduction target/tolerance when applicable: ...

## Implementation
- Reuse: `path::signature`
- Smallest code/config change: ...
- YAML config and runner selectors: ...
- Debug: `python experiment.py`

## Tasks
- [ ] Task - Acceptance: observable result

## Limits
- Time/compute/retry budget: ...
- Non-goals: ...
```

Omit inapplicable fields and keep tasks few. Cite inspected paths/signatures. Prefer YAML and the existing `experiment.py -> pipeline.py:run(config)` path; never plan `argparse`, duplicate runners, or speculative abstractions. If the existing runner uses `argparse`, convert it in place.

For reproduction, use one small/synthetic evaluation and compare the paper method with its simplest reported baseline on the same setup.

Append `plan.written` to the registry and return the plan path. Direct use may continue with `$ar-dev E###`; `ar-loop` must independently review the plan first.
