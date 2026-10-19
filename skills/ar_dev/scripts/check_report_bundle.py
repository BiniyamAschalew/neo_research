#!/usr/bin/env python3
"""Check a new experiment's Git bundle; optionally inventory and export it.

Uses only the standard library and Git. Does not stage files or touch local/
outputs. See the project artifact policy or the shared references/artifact-policy.md.
"""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def allowed(path):
    parts = path.parts
    if len(parts) == 1:
        return path.suffix == ".md" or path.name in {
            "metadata.json", "config.json", "requirements.txt", "artifacts.csv"
        }
    if parts[0] == "code":
        return len(parts) >= 2 and path.suffix == ".py" and not any(p.startswith(".") or p == "__pycache__" for p in parts)
    if parts[0] == "fixtures":
        return len(parts) >= 2 and (path.suffix in {".json", ".csv", ".npy", ".npz", ".parquet"} or path.name.endswith(".csv.gz"))
    if len(parts) != 2:
        return False
    if parts[0] == "figures":
        return path.suffix in {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".csv"} or path.name.endswith(".csv.gz")
    if parts[0] == "tables":
        return path.name.endswith((".csv", ".csv.gz"))
    return parts[0] == "code" and path.suffix == ".py"


def manifest_text(report, paths):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["path", "bytes", "sha256"])
    for path in paths:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        writer.writerow([path.relative_to(report).as_posix(), path.stat().st_size,
                         digest.hexdigest()])
    return stream.getvalue()


def check(args):
    report = args.report.resolve(strict=True)
    root = Path(git(report, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if report.parent != root / "__board__" / "reports":
        raise ValueError("Expected __board__/reports/<experiment-id>, not a legacy flat report")
    if args.max_file_mib <= 0 or args.max_total_mib <= 0 or args.max_fixture_mib <= 0:
        raise ValueError("Size budgets must be positive")
    destination = args.export.resolve() if args.export else None
    if destination and (destination.exists() or destination.is_relative_to(root)):
        raise ValueError("Export needs a new path outside the repository")

    # Includes tracked files even when ignored, so a force-added raw artifact is
    # detected. Untracked local/ files never enter the inventory or export.
    entries = git(root, "ls-files", "-z", "--cached", "--others",
                  "--exclude-standard", "--", report.relative_to(root).as_posix())
    paths = sorted({root / name.decode() for name in entries.split(b"\0") if name})
    for path in paths:
        relative = path.relative_to(report)
        if not allowed(relative):
            raise ValueError(f"Unexpected published artifact: {relative}")
        if any(p.is_symlink() for p in (path, *path.parents) if p != root):
            raise ValueError(f"Published artifacts must be regular files: {relative}")
        if not path.is_file():
            raise ValueError(f"Published artifact missing from disk: {relative}")

    names = {p.relative_to(report).as_posix() for p in paths}
    report_file = args.report_file or f"{report.name}.md"
    if Path(report_file).name != report_file or not report_file.endswith(".md"):
        raise ValueError("report-file must be a Markdown filename within the report directory")
    required = {report_file, "metadata.json", "requirements.txt", "code/plot.py"}
    missing = required - names
    if missing:
        raise ValueError(f"Missing publication files: {', '.join(sorted(missing))}")
    if not any(name.startswith("figures/") and Path(name).suffix in {".png", ".jpg", ".jpeg", ".svg", ".pdf"} for name in names):
        raise ValueError("No published figures/ images")
    if not any(name.startswith(("tables/", "figures/")) and name.endswith((".csv", ".csv.gz")) for name in names):
        raise ValueError("No published backing CSV files")
    metadata = json.loads((report / "metadata.json").read_text())
    if not isinstance(metadata, dict) or metadata.get("experiment_id") != report.name:
        raise ValueError("metadata.json experiment_id must match the report directory")
    if not isinstance(metadata.get("created_utc"), str) or not metadata["created_utc"]:
        raise ValueError("metadata.json needs a created_utc string")
    for key in ("protocol", "provenance", "reproduction"):
        if not isinstance(metadata.get(key), dict) or not metadata[key]:
            raise ValueError(f"metadata.json needs a nonempty {key} object")

    fixture_paths = [p for p in paths if p.relative_to(report).parts[0] == "fixtures"]
    if fixture_paths:
        fixture_root = report / "fixtures"
        fixture_manifest = fixture_root / "manifest.json"
        if fixture_manifest not in fixture_paths:
            raise ValueError("fixtures/ needs manifest.json")
        fixture = json.loads(fixture_manifest.read_text())
        if not fixture.get("source") or not fixture.get("rows"):
            raise ValueError("Fixture manifest needs source and row-selection provenance")
        declared = {}
        for entry in fixture.get("files", []):
            relative = Path(entry["path"])
            if relative.is_absolute() or ".." in relative.parts or entry["path"] in declared:
                raise ValueError("Invalid or duplicate fixture path")
            path = fixture_root / relative
            declared[entry["path"]] = path
            if path not in fixture_paths or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError(f"Missing or changed fixture: {relative}")
        expected_fixtures = set(fixture_paths) - {fixture_manifest}
        if set(declared.values()) != expected_fixtures:
            raise ValueError("Fixture manifest must list every published fixture file")
        if sum(p.stat().st_size for p in fixture_paths) > args.max_fixture_mib * 1024 * 1024:
            raise ValueError("Fixture bytes exceed the fixture budget")

    manifest = report / "artifacts.csv"
    paths = [p for p in paths if p != manifest]
    sizes = [(p.relative_to(report).as_posix(), p.stat().st_size) for p in paths]
    # Check sizes before hashing so accidental huge tracked blobs fail quickly.
    mib = 1024 * 1024
    for name, size in sizes:
        if size > args.max_file_mib * mib:
            raise ValueError(f"{name}: {size / mib:.2f} MiB exceeds file budget")
    if sum(size for _, size in sizes) > args.max_total_mib * mib:
        raise ValueError("Published files exceed the total bundle budget")
    content = manifest_text(report, paths)
    manifest_size = len(content.encode())
    total = sum(size for _, size in sizes) + manifest_size
    if manifest_size > args.max_file_mib * mib or total > args.max_total_mib * mib:
        raise ValueError("Published files plus manifest exceed the size budget")
    if args.write_manifest:
        manifest.write_text(content)
    elif not manifest.is_file() or manifest.read_text() != content:
        raise ValueError("artifacts.csv is missing or stale; run with --write-manifest")

    if destination:
        destination.mkdir(parents=True)
        for path in [*paths, manifest]:
            target = destination / path.relative_to(report)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    print(f"PASS: {len(paths) + 1} published files, {total / mib:.3f} MiB "
          f"(budget {args.max_total_mib:g} MiB); local outputs excluded")
    if destination:
        print(f"Exported to {destination}; run the report's plotting command there")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--report-file", help="Report Markdown filename when different from the directory name")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--export", type=Path)
    parser.add_argument("--max-file-mib", type=float, default=5)
    parser.add_argument("--max-total-mib", type=float, default=20)
    parser.add_argument("--max-fixture-mib", type=float, default=2)
    args = parser.parse_args()
    try:
        check(args)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
