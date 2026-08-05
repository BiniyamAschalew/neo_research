---
name: ar-lit
description: Research an idea against current and foundational literature, synthesize methods and results, assess overlap, and select one small faithful paper reproduction. Use for literature review, prior-work search, novelty context, baseline selection, or the literature stage of an Addis research loop.
---

# AR Literature

Read `.agents/references/board.md`, then initialize the board.

## Workflow

1. Resolve the input as an existing `I###` or check `record.md` and `registry.jsonl` before allocating a new idea ID.
2. Freeze the problem, proposed mechanism, claim, and useful query aliases.
3. Search local papers/notes first, then current external primary sources. Read methods and evaluation sections for the closest candidates; do not rely only on search snippets or abstracts.
4. Verify title, authors, year, venue, URL/DOI, code, and data links. Mark uncertain entries `unverified` rather than completing them from memory.
5. Synthesize what methods were tried, under which assumptions, on what data/metrics, with what results and limitations.
6. Rank reproduction candidates by:
   1. mechanism and claim similarity to the idea
   2. recency
   3. relevance of an evaluation to the claim
   4. code/data availability and runtime
7. Select one reference paper, one decisive evaluation, its method, and the simplest baseline used in that evaluation.

Prefer the paper's own small or synthetic evaluation. Otherwise choose a deterministic excerpt of its most relevant dataset. Prefer one faithful comparison over shallow coverage of several datasets.

## Output

Update only the idea's `Literature Synthesis` in `__board__/record.md`:

```markdown
### I###: [Idea]

**Current pattern**: [What the field consistently finds.]
**Disagreements/gaps**: [Conflicts, limitations, and open question.]
**Idea overlap/delta**: [Closest overlap and remaining distinction.]

| Work | Method | Evaluation | Result | Limitation | Verified source |
|---|---|---|---|---|---|

**Smallest faithful reproduction**
- Reference paper/method: ...
- Evaluation and planned subset/synthetic setup: ...
- Simplest paper baseline: ...
- Published method value, baseline value, and gap: ...
- Official code/data/config: ...
```

Append a `literature.updated` registry event with the idea ID. Do not create per-paper notes or download PDFs unless deeper reading cannot be done otherwise. Later loop calls should search only the new mechanism, failure, or evidence gap and append genuinely new evidence.

Return the idea ID, closest paper, chosen reproduction, and any unverified freshness/novelty risk. Literature synthesis informs review; it does not accept novelty by itself.

