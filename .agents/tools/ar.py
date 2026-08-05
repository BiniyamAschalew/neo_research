#!/usr/bin/env python3
"""Minimal deterministic board helper for Addis Research."""

from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


KINDS = {"idea": "I", "experiment": "E", "review": "R"}
STATES = {"running", "failed", "done", "accepted"}

STATUS = """# Project Status

**Last Updated**: initialized
**Current Phase**: setup

## Active

None.

## Next

- Define or select a research idea.

## Blockers

None.
"""

RECORD = """# Research Record

## Thesis

Not set.

## Literature Synthesis

None yet.

## Ideas

None yet.

## Experiments

None yet.

## Claims

None yet.

## Failed And Mixed Results

None yet.

## Open Questions

None yet.
"""

CONFIG = """models:
  think1: { model: gpt-5.6-sol, effort: xhigh }
  think2: { model: opus, effort: high }
  dev1:   { model: gpt-5.5, effort: high }

routing:
  lit: think1
  plan: think1
  critique: [think1, think2]
  dev: dev1
  result: think1
  record: think1
  loop: think1

settings:
  loop_size: 3
  max_review_rounds: 2
  save_token: false
  artifact_budget: { figures: 3, tables: 3 }
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def board(root: str | Path) -> Path:
    return Path(root).expanduser().resolve() / "__board__"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    atomic_write(path, content)
    return True


def initialize(root: str | Path) -> list[str]:
    target = board(root)
    target.mkdir(parents=True, exist_ok=True)
    templates = {
        "STATUS.md": STATUS,
        "record.md": RECORD,
        "registry.jsonl": "",
        "config.yaml": CONFIG,
    }
    return [name for name, content in templates.items() if write_if_missing(target / name, content)]


@contextmanager
def locked_registry(root: str | Path) -> Iterator[Any]:
    initialize(root)
    path = board(root) / "registry.jsonl"
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield handle
        finally:
            handle.flush()
            os.fsync(handle.fileno())
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def read_events(handle: Any) -> list[dict[str, Any]]:
    handle.seek(0)
    events = []
    for line in handle:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def parse_scalar(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def parse_fields(values: list[str]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Field must be key=value: {value}")
        key, raw = value.split("=", 1)
        if not key or key in {"ts", "event", "id"}:
            raise ValueError(f"Invalid field: {key}")
        fields[key] = parse_scalar(raw)
    return fields


def append_locked(handle: Any, event: dict[str, Any]) -> None:
    handle.seek(0, os.SEEK_END)
    handle.write(json.dumps(event, sort_keys=True) + "\n")


def allocate(root: str | Path, kind: str, fields: dict[str, Any]) -> str:
    prefix = KINDS[kind]
    target = board(root)
    with locked_registry(root) as handle:
        ids = {
            str(event.get("id"))
            for event in read_events(handle)
            if isinstance(event.get("id"), str)
        }
        if prefix == "E" and (target / "runs").exists():
            ids.update(path.name for path in (target / "runs").iterdir() if path.is_dir())
        numbers = [
            int(match.group(1))
            for value in ids
            if (match := re.fullmatch(rf"{prefix}(\d+)", value))
        ]
        identifier = f"{prefix}{max(numbers, default=0) + 1:03d}"
        if prefix == "E":
            (target / "runs" / identifier).mkdir(parents=True, exist_ok=False)
        append_locked(
            handle,
            {"ts": now(), "event": f"{kind}.allocated", "id": identifier, **fields},
        )
    return identifier


def append_event(root: str | Path, name: str, identifier: str, fields: dict[str, Any]) -> dict[str, Any]:
    event = {"ts": now(), "event": name, "id": identifier, **fields}
    with locked_registry(root) as handle:
        append_locked(handle, event)
    return event


def set_state(root: str | Path, identifier: str, status: str, fields: dict[str, Any]) -> dict[str, Any]:
    if not re.fullmatch(r"E\d+", identifier):
        raise ValueError("State IDs must look like E001")
    if status not in STATES:
        raise ValueError(f"Unknown state: {status}")
    run = board(root) / "runs" / identifier
    run.mkdir(parents=True, exist_ok=True)
    path = run / "state.json"
    current: dict[str, Any] = {}
    if path.exists():
        current = json.loads(path.read_text(encoding="utf-8"))
    state = {
        **current,
        "experiment_id": identifier,
        "status": status,
        "updated_at": now(),
        **fields,
    }
    atomic_write(path, json.dumps(state, indent=2, sort_keys=True) + "\n")
    append_event(root, f"experiment.{status}", identifier, fields)
    return state


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
        return digest.hexdigest()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(str(child.relative_to(path)).encode())
        digest.update(child.read_bytes())
    return digest.hexdigest()


def hash_paths(root: str | Path, paths: list[str]) -> dict[str, str | None]:
    base = Path(root).expanduser().resolve()
    output: dict[str, str | None] = {}
    for raw in paths:
        path = Path(raw).expanduser()
        path = path if path.is_absolute() else base / path
        output[raw] = file_hash(path) if path.exists() else None
    return output


def flatten(value: Any) -> Iterator[Any]:
    if isinstance(value, dict):
        for item in value.values():
            yield from flatten(item)
    elif isinstance(value, list):
        for item in value:
            yield from flatten(item)
    else:
        yield value


def values_in(path: Path) -> list[Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return list(flatten(json.loads(path.read_text(encoding="utf-8"))))
    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return [cell for row in csv.reader(handle) for cell in row]
    text = path.read_text(encoding="utf-8", errors="replace")
    return [text, *re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text)]


def same_value(candidate: Any, expected: str) -> bool:
    if str(candidate).strip() == expected.strip():
        return True
    try:
        left, right = float(candidate), float(expected)
    except (TypeError, ValueError):
        return False
    return abs(left - right) <= max(1e-12, abs(right) * 1e-9)


def check_evidence(root: str | Path, source: str, value: str, claim_id: str) -> dict[str, Any]:
    base = Path(root).expanduser().resolve()
    path = Path(source).expanduser()
    path = path if path.is_absolute() else base / path
    if not path.exists():
        status = "path_missing"
    elif not path.is_file():
        status = "unparseable"
    else:
        try:
            status = "verified" if any(same_value(item, value) for item in values_in(path)) else "value_not_found"
        except (OSError, UnicodeError, csv.Error, json.JSONDecodeError):
            status = "unparseable"
    return {"id": claim_id, "value": value, "source": source, "status": status}


def resume_state(root: str | Path, idea: str | None) -> dict[str, Any]:
    target = board(root)
    if not target.exists():
        return {"board": "missing", "idea_id": idea, "runs": [], "loop": None}
    initialize(root)
    runs = []
    run_root = target / "runs"
    if run_root.exists():
        for path in sorted(run_root.glob("E*/state.json")):
            try:
                state = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if state.get("status") != "accepted":
                runs.append(state)
    events = []
    with (target / "registry.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(event.get("event", "")).startswith("loop.") and (
                idea is None or event.get("id") == idea or event.get("idea_id") == idea
            ):
                events.append(event)
    return {"board": str(target), "idea_id": idea, "runs": runs, "loop": events[-1] if events else None}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("root")

    alloc = commands.add_parser("allocate")
    alloc.add_argument("root")
    alloc.add_argument("kind", choices=KINDS)
    alloc.add_argument("--field", action="append", default=[])

    event = commands.add_parser("event")
    event.add_argument("root")
    event.add_argument("name")
    event.add_argument("--id", required=True)
    event.add_argument("--field", action="append", default=[])

    state = commands.add_parser("state")
    state.add_argument("root")
    state.add_argument("id")
    state.add_argument("status", choices=sorted(STATES))
    state.add_argument("--field", action="append", default=[])

    hashing = commands.add_parser("hash")
    hashing.add_argument("root")
    hashing.add_argument("paths", nargs="+")

    evidence = commands.add_parser("evidence")
    evidence.add_argument("root")
    evidence.add_argument("source")
    evidence.add_argument("value")
    evidence.add_argument("--id", default="claim")

    resume = commands.add_parser("resume")
    resume.add_argument("root")
    resume.add_argument("--idea")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "init":
            print(json.dumps({"board": str(board(args.root)), "created": initialize(args.root)}))
        elif args.command == "allocate":
            print(allocate(args.root, args.kind, parse_fields(args.field)))
        elif args.command == "event":
            print(json.dumps(append_event(args.root, args.name, args.id, parse_fields(args.field))))
        elif args.command == "state":
            print(json.dumps(set_state(args.root, args.id, args.status, parse_fields(args.field))))
        elif args.command == "hash":
            print(json.dumps(hash_paths(args.root, args.paths), sort_keys=True))
        elif args.command == "evidence":
            result = check_evidence(args.root, args.source, args.value, args.id)
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] == "verified" else 1
        elif args.command == "resume":
            print(json.dumps(resume_state(args.root, args.idea), indent=2, sort_keys=True))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

