---
name: ar-note
description: Write a focused Addis run observation only when it does not belong in the report/record, or create the mandatory concise experiment-to-idea lineage note at loop completion. Use for durable technical observations and loop trace summaries.
---

# AR Note

Read `.agents/references/board.md`, then initialize the board.

## Run Note

For `E### <observation>`, read its plan/report/review and write or append `__board__/runs/E###/notes.md`:

```markdown
## [Date]: [Topic]

**Observation**: [Grounded finding.]
**Evidence**: [Paths and exact conditions.]
**Implication**: [Action or unresolved question.]
```

Do not create the file when the observation belongs in the report or living record. Label speculation.

## Loop Lineage

For a completed loop `I###`, read registry membership and every member plan/report/review. Compute the numeric minimum and maximum experiment IDs, including reproduction and cycle runs. Create:

```text
__board__/notes/loop_<start_id>_<end_id>.md
```

Example: `__board__/notes/loop_E001_E005.md`.

Keep it concise:

```markdown
# Loop E001-E005

**Idea**: I### - ...
**Experiments**: E001, E002, E004, E005

| Experiment | Hypothesis | Validation | Reviewed result | Result -> next idea |
|---|---|---|---|---|

## Final Position
- Best supported claim: ...
- Failed directions: ...
- Strongest next direction: ...
```

List exact members because IDs may be non-contiguous. Link each plan/report/review; do not duplicate details or create a second loop report. Append `note.written` or `loop.note.written` to the registry and return the path.

