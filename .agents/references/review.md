# Review Contract

Agents may execute and measure; they may not self-accept research quality.

## Independence

- Start a fresh reviewer session for each gate: idea, plan, code/evaluation, result, or claim.
- Reuse that session only for revisions of the same unchanged target.
- Require a reviewer family different from the primary author or executor.
- Make the reviewer read target files and raw artifacts directly.
- Ignore `Human Prediction` and `Agent Prediction` until technical judgment is complete.
- Do not lead the reviewer with an executor-written defense or selected evidence summary.

## Receipt

Append every round to the run's single `review.md`:

```markdown
## [Gate] Review - Round [N]

**Review ID**: R###
**Model / effort / family**: ...
**Session**: ...
**Targets**: [path -> sha256]
**Verdict**: accept | revise | reject | blocked | error

### Prompt
[Exact prompt.]

### Response
[Full response.]
```

Hash reviewed files with `.agents/tools/ar.py hash`. If any target hash changes, its acceptance is stale and the gate must run again.

After `max_review_rounds`, unresolved `revise`, `blocked`, or disagreement goes to the human. Record an override in `review.md` with author, timestamp, reason, and scope; never rewrite reviewer history.

## Gate Focus

- **Idea**: coherence, redundancy, closest work, fastest falsifier, information gain.
- **Plan**: claim scope, baseline, metric, success threshold, failure interpretation, cost.
- **Code/evaluation**: semantic correctness, leakage, metric meaning, data split, reproducibility, and an argument-free YAML-backed runner with no `argparse`.
- **Result/claim**: evidence existence, fair comparison, claim support, limitations.

Use deterministic facts to drive review, never to acquit it.

## Result Precheck

Before result judgment, verify every cited value against its source:

```bash
python3 .agents/tools/ar.py evidence . __board__/runs/E002/artifacts/results.csv 0.91 --id C1
```

`verified` means the value exists, not that it supports the claim. A missing path or value cannot be defended by a reviewer.

Record evaluation type as `real`, `synthetic`, `simulation`, `self-supervised`, or `human`. Cap claim scope to that evidence. Keep scientific outcome (`positive | mixed | negative | inconclusive`) separate from review verdict.

For a result gate, judge the evidence first, then compare it with the frozen human/agent prediction and record agreement, surprise, bias, or a useful next hypothesis.
