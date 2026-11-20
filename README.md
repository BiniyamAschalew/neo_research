# neo_research

Shared research workflows for Claude Code and Codex. One checkout of this repo serves all your projects: skills are linked into each project, while each project keeps its own research board (`__board__/`) with plans, reports, notes and idea summaries.

## Quick start

```bash
git clone git@github.com:BiniyamAschalew/neo_research.git
cd neo_research
./ar_init ../my-project        # the only setup step
```

Then open `claude` (or `codex`) in `../my-project` and run e.g. `/ar_plan "test X against baseline Y"`.

`./ar_init --dry-run ../my-project` previews; rerunning is safe. Run it once per project on each machine.

**Requirements**: git, Python 3.8+, Claude Code and/or Codex CLI. Optional: [Herdr](https://herdr.dev) (one tab per idea), a Slack Incoming Webhook (run notifications), PyYAML (`ar_goal` configs).

## Skills

| Skill | Use it to |
|---|---|
| `ar_metaplan` | sharpen an idea: prior evidence, theory, decisive experiment design |
| `ar_plan` | write a plan that opens with an editable 20-line **Experiment Card** |
| `ar_dev` | implement and run the plan; report opens with the card as Planned vs Actual |
| `ar_tree` | give each idea its own worktree; closing returns only a summary to main |
| `ar_mate` | one "first mate" agent that coordinates all ideas in a project |
| `ar_goal` | overnight one-change-at-a-time improvement loop with a sealed test |
| `ar_notify` | Slack text message whenever an experiment run ends |
| `ar_note` | write a focused technical note |

Claude uses `/ar_<name>`, Codex `$ar_<name>`. Commands, flags and the typical flow: **[SKILLS.md](SKILLS.md)**.

## What `ar_init` sets up

```text
my-project/
  .agents            -> neo_research/.agents          shared skills
  .codex             -> neo_research/.codex
  AGENTS.md          -> neo_research/AGENTS.md        shared instructions
  .claude/           real folder (stays per project)
    commands         -> neo_research/.claude/commands
    CLAUDE.md        -> neo_research/.claude/CLAUDE.md
    settings.local.json -> ../__board__/claude/settings.local.json
  __board__/         this project's research state
    PROJECT.md       fill in once: env, data paths, conventions
```

- Rerun it on an already set-up project to upgrade it. Anything that came from neo_research (old links, copied shared skills or commands, old copies of `AGENTS.md`) is replaced by a link; project-only skills and commands stay beside the shared ones; custom text in `AGENTS.md`/`CLAUDE.md` moves into `__board__/PROJECT.md`; Claude's local settings move to `__board__/claude/`. `__board__/` content (status, plans, reports, notes) is never touched. Every replaced real file is backed up to `__board__/notes/local/ar_init-backup/<time>/`.
- If an older setup committed agent files to git, `--untrack` removes them from the index (files stay on disk); commit afterwards.
- Links are absolute and machine-specific, so they are hidden via `.git/info/exclude` and never committed.
- New or updated skills here reach every linked project immediately. Keep the linked checkout on a stable branch and develop neo_research in a separate clone or worktree.

## Per-project and per-machine settings

| File | Scope | Purpose |
|---|---|---|
| `my-project/__board__/PROJECT.md` | project | env, data, conventions that override shared defaults |
| `~/.config/ar/host.md` | machine | e.g. GPU claim rules; `ar_init` installs one from `hosts/` when it recognizes the machine |
| `neo_research/secrets/slack.env` | machine | `SLACK_WEBHOOK_URL=...` (gitignored; copy `secrets/slack.env.example`) |

## Repository layout

```text
ar_init               project setup command
skills/<name>/        skill definitions (SKILL.md) and their scripts
adapters/claude/      thin Claude slash-command wrappers that load the skills
skills/references/    shared execution and artifact-publication conventions
hosts/                machine rule templates for ~/.config/ar/host.md
tests/                tests for the tooling itself (never linked into projects)
```

To add a skill: create `skills/<name>/SKILL.md`, link it from `.agents/skills/<name>`, add `adapters/claude/<name>.md` and link it from `.claude/commands/<name>.md`. Linked projects see it at once.

## Tests

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s skills/ar_dev/tests -v
```
