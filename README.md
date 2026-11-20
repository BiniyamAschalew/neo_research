# neo_research

Shared research workflows for Claude Code and Codex. One checkout serves all your projects: skills are linked in, while each project keeps its own `__board__/` (plans, reports, idea summaries, Slack and tracking settings).

## Quick start

```bash
git clone https://github.com/BiniyamAschalew/neo_research.git
cd neo_research && ./ar_init ../my-project        # once per project per machine; safe to rerun
```

Then fill in two files in `my-project/__board__/`:

| File | Committed | Contents |
|---|---|---|
| `PROJECT.md` | yes | conda env, data paths, conventions |
| `project.env` | **never** | `SLACK_WEBHOOK_URL` (this project's channel), `TRACKING_URL` (W&B / CoreWeave dashboard), `WANDB_ENTITY`, `WANDB_PROJECT` |

Requirements: git, Python 3.8+, Claude Code and/or Codex. Optional: [Herdr](https://herdr.dev), a Slack [Incoming Webhook](https://api.slack.com/messaging/webhooks) per project, W&B, PyYAML (for `ar_goal`).

## Example: from idea to Slack

```text
Herdr tab 0:   cd my-project && ../neo_research/ar_mate          # first mate + Slack watcher
You -> mate:   "new idea: does a cosine schedule beat step decay on val AUC? plan it"
Mate:          ar_tree new cosine-lr -> worktree + tab with its own agent, which runs /ar_plan
Slack:         "my-project/cosine-lr: plan ready for review" + Experiment Card
You:           edit the card if needed, tell the mate "approved"
Mate:          idea agent runs /ar_dev through notify_run.py (logs to this project's W&B)
Slack:         run finished + duration, then "experiment done" + Planned vs Actual card + tracking link
You -> mate:   "close it as dead" -> only the summary returns to main; code archived as a tag
```

`ar_mate` puts the mate rules in Claude's system prompt, so it stays the mate through long sessions. It asks before anything irreversible (full runs, closes, merges, pushes) and never edits code itself.

## Skills

| Skill | Use it to |
|---|---|
| `ar_metaplan` | sharpen an idea: prior evidence, theory, decisive design |
| `ar_plan` | write a plan that opens with an editable 20-line Experiment Card |
| `ar_dev` | implement and run it; report opens with Planned vs Actual |
| `ar_tree` | one worktree per idea; closing returns only a summary to main |
| `ar_mate` | first mate coordinating all ideas of a project |
| `ar_goal` | overnight one-change-at-a-time tuning loop with a sealed test |
| `ar_notify` | Slack text message when a run ends |
| `ar_note` | focused technical note |

Claude: `/ar_<name>`, Codex: `$ar_<name>`. Commands and flags: **[SKILLS.md](SKILLS.md)**.

W&B logging is curated by [tracking conventions](skills/references/tracking.md): descriptive run names and groups, curves only along a real x-axis, one-off results as summary values or tables (no one-dot charts).

## What `ar_init` does

- Links `.agents`, `.codex`, `AGENTS.md`, `.claude/commands`, `.claude/CLAUDE.md` to this checkout; `.claude/` stays a real folder; Claude's local settings live in `__board__/claude/`.
- Creates `__board__/PROJECT.md` and `__board__/project.env` if missing; hides links and `project.env` from git via `.git/info/exclude`.
- On an older setup: re-links anything that came from neo_research, keeps project-only skills/commands, moves custom `AGENTS.md`/`CLAUDE.md` text into `PROJECT.md`, never touches other `__board__/` content, backs up every replaced file to `__board__/notes/local/ar_init-backup/`. `--dry-run` previews; `--untrack` untracks old committed links.
- Idea worktrees get the same links and use the main checkout's `project.env`, so each project's notifications and runs stay in its own channel and workspace.

Linked projects follow this checkout live; keep it on a stable branch and develop neo_research in a separate clone or worktree. Machine-wide rules (e.g. GPU claims) go in `~/.config/ar/host.md`, installed from `hosts/` when recognized.

## Layout and tests

```text
ar_init, ar_mate   setup and first-mate launchers
skills/<name>/     SKILL.md + scripts        adapters/claude/   slash-command wrappers
hosts/             machine rule templates    tests/             tooling tests (not linked)
```

```bash
python -m unittest discover -s tests && python -m unittest discover -s skills/ar_dev/tests
```
