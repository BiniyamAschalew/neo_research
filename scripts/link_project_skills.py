#!/usr/bin/env python3
"""Link project AutoResearch entrypoints to this checkout; preview by default."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile


SKILLS = ("ar_plan", "ar_dev", "ar_metaplan", "ar_tree", "ar_mate", "ar_goal", "ar_notify")


def destinations(projects, canonical):
    """Resolve parent aliases without following the entrypoint being replaced."""
    sources = {
        **{f".agents/skills/{name}": canonical / "skills" / name for name in SKILLS},
        ".agents/skills/references": canonical / "skills/references",
        **{f".claude/commands/{name}.md": canonical / "adapters/claude" / f"{name}.md" for name in SKILLS},
    }
    for source in sources.values():
        if not source.exists():
            raise ValueError(f"Missing canonical source: {source}")
    seen = set()
    for project in projects:
        project = Path(project).resolve(strict=True)
        if not project.is_dir():
            raise ValueError(f"Not a project directory: {project}")
        for relative, source in sources.items():
            requested = project / relative
            destination = requested.parent.resolve() / requested.name
            if destination in seen:
                continue
            seen.add(destination)
            if destination == source or destination in source.parents:
                raise ValueError(f"Link would replace its canonical source: {destination}")
            if destination.is_symlink() and destination.resolve() == source.resolve():
                continue
            yield destination, source


def install(projects, canonical=None, apply=False):
    """Back up replaced entries, then install relative links with rollback on error."""
    canonical = Path(canonical or Path(__file__).resolve().parents[1]).resolve(strict=True)
    changes = list(destinations(projects, canonical))
    result = {"apply": apply, "backup": None, "changes": []}
    for destination, source in changes:
        result["changes"].append({
            "destination": str(destination),
            "target": os.path.relpath(source, destination.parent),
            "backup": None,
        })
    if not apply or not changes:
        return result

    backup_root = canonical / "__board__/notes/local/skill-links"
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-")
    backup = Path(tempfile.mkdtemp(prefix=stamp, dir=backup_root))
    result["backup"] = str(backup)
    manifest = backup / "manifest.json"
    completed = []
    try:
        for index, ((destination, source), record) in enumerate(zip(changes, result["changes"])):
            destination.parent.mkdir(parents=True, exist_ok=True)
            saved = backup / f"{index:03d}-{destination.name}"
            if os.path.lexists(destination):
                record["backup"] = str(saved)
            manifest.write_text(json.dumps(result, indent=2) + "\n")
            if record["backup"]:
                shutil.move(str(destination), str(saved))
            completed.append(record)
            destination.symlink_to(record["target"], target_is_directory=source.is_dir())
        result["status"] = "installed"
    except Exception:
        for record in reversed(completed):
            destination = Path(record["destination"])
            if destination.is_symlink():
                destination.unlink()
            if record["backup"]:
                shutil.move(record["backup"], str(destination))
        result["status"] = "rolled_back"
        manifest.write_text(json.dumps(result, indent=2) + "\n")
        raise
    manifest.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("projects", nargs="+", type=Path)
    parser.add_argument("--apply", action="store_true", help="Apply links after backing up originals")
    args = parser.parse_args()
    try:
        result = install(args.projects, apply=args.apply)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Link installation failed: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
