# Shared AutoResearch workflows

Edit workflow definitions under `skills/`. Project Codex skills link to those
directories; Claude commands link to the thin adapters under `adapters/claude/`,
which read the same definitions. `ar_plan`, `ar_dev` and `ar_metaplan` share
supporting references; the artifact helper lives with `ar_dev`.

## Ideas, first mate, goal loop and Slack (`tree` branch)

- `ar_tree`: one git worktree and Herdr tab per idea (`../<project>.ideas/<slug>`, branch `idea/<slug>`). Closing an idea commits only `__board__/ideas/<slug>.md` (approach, main results, why it failed, when to retry) to main, tags the code as `archive/<slug>`, and moves raw results to `~/ar_archive/`. `bury` does the same for old experiments already on main.
- `ar_mate`: the first mate in Herdr tab 0; `mate_status.py` shows every idea's agent state, phase, latest result and GPU use.
- `ar_goal`: `goal.py` runs an overnight hill-climb in an idea worktree, one component change per iteration, kept only when validation beats the best by more than measured noise; sealed test once at the end.
- Plans start with a 20-line Experiment Card (Flow, Compare, Decide, Edit me) that the human edits before `ar_dev`; reports start with the same card as Planned vs Actual.
- `ar_notify`: Slack text notifications. `notify_run.py -- python run.py` posts automatically when any run ends (status, duration, report card or output tail); `slack_notify.py --report` sends a report's card with text tables. Copy `secrets/slack.env.example` to `secrets/slack.env` (gitignored) and paste an Incoming Webhook URL.

## Set up a project: `ar_init`

From this checkout:

```bash
./ar_init ../your-project            # safe: links, __board__/, PROJECT.md; never overwrites real files
./ar_init ../your-project --dry-run  # preview
./ar_init ../your-project --replace  # move conflicting real files to __board__/notes/local/ar_init-backup/ first
```

It links `.agents`, `.codex`, `AGENTS.md`, `.claude/commands` and `.claude/CLAUDE.md` to this checkout (absolute links, ignored through `.git/info/exclude`), keeps `.claude/` itself a real per-project folder, links `.claude/settings.local.json` to `__board__/claude/` so Claude's per-project state stays with the project, and creates `__board__/PROJECT.md` for project specifics. Machine rules (for example the GPU persist.py claim) live in `~/.config/ar/host.md`; `ar_init` installs the matching file from `hosts/` when it detects the machine. New skills added here appear in every project immediately; `ar_tree new` repeats the links in each idea worktree. Rerunning is idempotent and re-points stale links.

## Install or refresh project links (legacy per-skill installer)

Keep this checkout alongside your projects on each machine. From this checkout:

```bash
python scripts/link_project_skills.py . ../your-project
python scripts/link_project_skills.py --apply . ../your-project
```

The first command previews changes. Applying preserves replaced files and
directories under ignored `__board__/notes/local/skill-links/`, then creates
relative links. Existing correct links are skipped, shared parent directories
are handled once, and an installation error rolls back changed entrypoints.
The JSON manifest records original destinations and backup locations.

Relative links survive relocation when the relative checkout layout is preserved.
A project clone needs this shared checkout at the linked location; rerun the
installer for another layout. Existing Claude/Codex sessions may need to reload
to discover added commands or refresh instructions already loaded in context.

## What stays local

The active project remains the research/code root. Its AGENTS.md, Claude
instructions, artifact policy and selected plan determine project-specific
requirements and existing runner/report conventions. New defaults provide
`At a Glance` summaries followed by `======`, semantic code organization,
config-selected full/tiny execution with actual-data fixtures, explicit device
and weight prerequisites, and curated reproducible scientific publications.

The installer changes only the linked workflows (`ar_plan`, `ar_dev`, `ar_metaplan`, `ar_tree`, `ar_mate`, `ar_goal`, `ar_notify`) and their shared references.
It leaves other skills, notifications, project data, results and local policies
in place. It does not stage, commit or push. Project ignore rules must allow the
adapter links; fixture/data publication rules remain project configuration.

## Verify the shared tooling

No test-only dependencies are required:

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s skills/ar_dev/tests -v
```
