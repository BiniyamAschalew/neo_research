---
name: ar-record
description: Fold an Addis experiment's reviewed outcome into the living research record, append lifecycle events, and refresh concise status without duplicating reports. Use after result review or to preserve a failed run.
---

# AR Record

Read `.agents/references/board.md`, then initialize the board.

## Workflow

1. Resolve `E###` and read its plan, report when present, review, state, and evidence links.
2. Hash the report. If `registry.jsonl` already has `record.updated` for the same experiment/report hash, return without changing files.
3. Determine the scientific outcome: `positive | mixed | negative | inconclusive | failed`.
4. Require current accepted result review or explicit human override before promoting any claim. Always retain negative, mixed, inconclusive, and failed outcomes.
5. Update only the relevant sections of `record.md`:
   - idea status and decision
   - one-paragraph experiment result
   - accepted/narrowed claim or failed-idea memory
   - evidence links and open question
6. Append `record.updated` with idea ID, experiment ID, outcome, report hash/path, and review path.
7. Refresh `STATUS.md` with the active phase, latest outcome, blockers, and next action. Keep it a projection, not another report.

Do not copy plans, full tables, logs, or review prose into `record.md`. Link primary files. When result review accepted the run but state is not yet `accepted`, set it now.

Return the updated paths, recorded outcome, promoted claim if any, and next research question.

