---
name: ar-review
description: Independently critique an Addis idea, plan, implementation/evaluation, result, or claim with cross-family model routing, evidence checks, content hashes, stale-verdict detection, and durable receipts. Use at every research acceptance gate.
---

# AR Review

Read `.agents/references/board.md` and `.agents/references/review.md`, then initialize the board.

## Resolve

1. Resolve `E###` and gate: `idea`, `plan`, `code`, `result`, or `claim`.
2. Read the target plan/report/code/raw artifacts directly and identify the primary author or executor family.
3. Read `routing.critique` and select a reviewer from a different family. If unavailable or ambiguous, record `blocked`; never silently fall back.
4. Allocate `R###` and hash every reviewed target with `.agents/tools/ar.py hash`.

Use a fresh reviewer session for this gate. Reuse it only for another round on the same target. Pass paths and neutral questions, not an executor summary. Do not expose human/agent predictions before technical judgment.

## Review

Ask only gate-relevant questions:

- **Idea**: closest work, redundancy, coherence, fastest falsifier, likely information gain.
- **Plan**: claim scope, baseline strength, metric meaning, success/failure criteria, cost, leakage risk.
- **Code**: implementation/evaluation correctness, split integrity, YAML config use, seeds, and an argument-free debugger path with no runner `argparse`.
- **Result/claim**: traceability, fair baseline, reproduced-paper fidelity, supported scope, caveats.

For result/claim review, run deterministic evidence checks for each cited number first. Immediate missing paths/values cannot be accepted. The independent model still judges whether verified values support the claim.

Append the full receipt to `__board__/runs/E###/review.md` using the shared template. Verdicts are `accept | revise | reject | blocked | error`; scientific outcomes are `positive | mixed | negative | inconclusive`.

## Finish

- If hashes differ from the last accepted receipt, mark it stale and review again.
- Continue revisions for at most `max_review_rounds`; then request a human decision.
- Record human overrides append-only with author, reason, timestamp, and scope.
- Append `review.<gate>.<verdict>` to the registry with review ID, model/family, path, and hashes.
- On accepted `result`/`claim`, set the run state to `accepted`. Acceptance validates the evidence process even when the outcome is negative.

Do not edit the reviewed target. Return the verdict, blocking findings, current receipt path, and required next action.
