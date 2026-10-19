# Shared AutoResearch workflows

Edit workflow definitions under `skills/`. Project Codex skills link to those
directories; Claude commands link to the thin adapters under `adapters/claude/`,
which read the same definitions. `ar_plan`, `ar_dev` and `ar_metaplan` share
supporting references; the artifact helper lives with `ar_dev`.

## Install or refresh project links

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

The installer changes only these three workflows and their shared references.
It leaves other skills, notifications, project data, results and local policies
in place. It does not stage, commit or push. Project ignore rules must allow the
adapter links; fixture/data publication rules remain project configuration.

## Verify the shared tooling

No test-only dependencies are required:

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s skills/ar_dev/tests -v
```
