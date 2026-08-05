# Addis Research Claude Adapter

Use the shared Addis board under `__board__/`. Never write research state into `.claude/`, `.codex/`, or `.agents/`.

At startup, read `__board__/STATUS.md` if it exists and the active run files when relevant. Do not bootstrap the board until an Addis command is invoked.

## Commands

| Command | Purpose |
|---|---|
| `/ar_lit` | Map literature and choose a faithful reproduction. |
| `/ar_plan` | Create a claim-driven experiment plan. |
| `/ar_review` | Run an independent research gate. |
| `/ar_dev` | Implement and run an `E###` plan; loops require review. |
| `/ar_compact` | Remove structural duplication without changing behavior. |
| `/ar_record` | Update research memory and state. |
| `/ar_note` | Write focused or loop-lineage notes. |
| `/ar_loop` | Run the autonomous research loop. |

Read model routes from `__board__/config.yaml`. Delegate to Codex when routed there; do not silently substitute Opus for an independent Codex gate. Follow `AGENTS.md` and `.agents/references/` for shared invariants.
