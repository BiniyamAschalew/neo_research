# Board And Routing Contract

Use the current working directory as the project root unless the human gives another root. Generated research state belongs only under `__board__/`; behavior belongs under `.agents/`, `.claude/`, and `.codex/`.

## Bootstrap

Run this only after an Addis skill is invoked:

```bash
python3 .agents/tools/ar.py init .
```

It creates only the central files that are missing:

```text
__board__/
  STATUS.md
  config.yaml
  record.md
  registry.jsonl
```

Never overwrite existing board content. Create `runs/E###/`, `notes/`, and `artifacts/` only when their workflow needs them.
Planning creates a populated `structure.md` when missing; bootstrap must not create an empty map.

## Authority

- `registry.jsonl`: append-only IDs, lifecycle events, and links; latest event for an ID wins.
- `runs/E###/state.json`: active execution state.
- `record.md`: literature, experiments, failures, and accepted claims.
- `STATUS.md`: concise human-readable projection.
- `structure.md`: concise, source-verified map of architectural files and reusable signatures.
- plans, reports, reviews, and raw artifacts: primary evidence.

Use the helper for deterministic operations:

```bash
python3 .agents/tools/ar.py allocate . idea
python3 .agents/tools/ar.py allocate . experiment --field idea_id=I001
python3 .agents/tools/ar.py allocate . review --field target=E001
python3 .agents/tools/ar.py event . plan.written --id E001 --field path=__board__/runs/E001/plan.md
python3 .agents/tools/ar.py state . E001 running
python3 .agents/tools/ar.py resume . --idea I001
python3 .agents/tools/ar.py hash . path/to/file another/file
python3 .agents/tools/ar.py evidence . path/to/results.csv 0.91 --id claim-1
```

Do not add another state script unless this helper has become a demonstrated bottleneck.

## Run Lifecycle

```text
allocated -> planned -> running -> failed | done -> accepted
```

`done` means execution finished. Only a current independent result review or explicit human override can make a run `accepted`. A failed run resumes at execution; a done run resumes at result review.

Update `STATUS.md` at stage transitions, background-job start/finish/failure, and human handoff. Keep it short and resolve disagreement in favor of registry/run evidence.

## Model Routing

Read `__board__/config.yaml`. Resolve the requested stage through `routing`, then resolve its model slot under `models`. Do not hard-code a model in a skill.

The project root is one shared trust boundary. Every routed agent receives the same project-root read scope as the invoking agent; do not maintain per-agent or per-stage file allowlists. Never extend this implicit access outside the project root.

Infer family from the model label:

- `codex`: labels containing `gpt`, `codex`, or an `o`-series model.
- `opus`: labels containing `opus` or `claude`.

If the current agent matches both the routed model and family, execute locally. Otherwise delegate once with the installed CLI from the project root. Send paths and questions, not copied executor summaries, and do not recursively re-delegate the same stage.

Codex example:

```bash
codex exec -C . -s read-only --skip-git-repo-check \
  -m gpt-5.6-sol -c 'model_reasoning_effort="xhigh"' \
  'Read the listed project files directly and perform the requested review.'
```

Opus example:

```bash
claude -p --model opus --effort high --permission-mode plan \
  --output-format json \
  'Read the listed project files directly and perform the requested review.'
```

For development delegation, use the same routed model with workspace editing enabled. Never use a bypass-permissions flag. Capture the model, effort, session/thread ID when available, prompt, response, and paths in the run review or report.

If a routed CLI/model is unavailable or its family is ambiguous, mark the stage `blocked`. Never silently replace an independent reviewer with the author/executor family.

Host security can still require consent before local files are transmitted to another model provider. Before an autonomous cross-provider loop, verify that project-wide sharing is authorized. If the host permits only per-payload approval, block during preflight instead of interrupting a later review gate; repository instructions cannot override that boundary.

## Token Saving

When `save_token: true`, read only `STATUS.md`, relevant `record.md` entries, the active plan/report/review, and blocking evidence. Prefer targeted literature updates and concise responses. Do not reduce `loop_size` or skip baseline reproduction, provenance, evidence checks, or independent acceptance.
