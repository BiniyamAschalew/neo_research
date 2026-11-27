"""Allocate stable project-wide research idea IDs."""

import argparse
import fcntl
from pathlib import Path
import re
import shutil
import subprocess


def preserve(root, tree, slug):
    """Copy the idea and linked portable board evidence before its worktree is removed."""
    root, tree = Path(root).resolve(), Path(tree).resolve()
    docs = list((tree / "__board__/ideas").glob(f"I[0-9]*-{slug}/idea.md"))
    files, pending, scanned = set(), list(docs), set()
    for doc in docs:
        files.update(p for p in doc.parent.rglob("*") if p.is_file())
    while pending:
        doc = pending.pop()
        if doc in scanned:
            continue
        scanned.add(doc)
        for link in re.findall(r"\]\(([^)]+)\)", doc.read_text()):
            path = (doc.parent / link.split("#", 1)[0]).resolve()
            if not path.is_relative_to(tree / "__board__") or not path.is_file():
                continue
            relative = path.relative_to(tree)
            if "local" in relative.parts or relative.name == "project.env":
                continue
            files.add(path)
            if path.suffix == ".md":
                pending.append(path)
    for source in files:
        relative = source.relative_to(tree)
        target = root / relative
        if target.exists() and "ideas" not in relative.parts and target.read_bytes() != source.read_bytes():
            raise ValueError(f"Conflicting evidence: {relative}; use an idea-specific report/plan name.")
    for source in files:
        target = root / source.relative_to(tree)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return [str(p.relative_to(tree)) for p in sorted(files)]


def create(root, slug, question):
    root = Path(root).resolve()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", slug):
        raise ValueError("Use a short lowercase hyphenated slug.")
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()
    main = Path(git("worktree", "list", "--porcelain").splitlines()[0].split(" ", 1)[1])
    common = (root / git("rev-parse", "--git-common-dir")).resolve()
    with (common / "ar_idea.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        folders = list((main / "__board__/ideas").glob("I[0-9]*-*"))
        existing = [p for p in folders if p.name.split("-", 1)[1] == slug]
        if existing:
            folder = existing[0]
        else:
            counter = common / "ar_idea.next"
            number = max(int(counter.read_text()) if counter.exists() else 1,
                         max((int(p.name.split("-", 1)[0][1:]) for p in folders), default=0) + 1)
            counter.write_text(str(number + 1))
            folder = main / "__board__/ideas" / f"I{number:03d}-{slug}"
            folder.mkdir(parents=True)
            idea_id = folder.name.split("-", 1)[0]
            (folder / "idea.md").write_text(
                f"# {idea_id}: {slug}\n\n**ID**: {idea_id}\n**Status**: needs refinement\n"
                f"**Question**: {question}\n\n## Hypothesis\n\nTo refine.\n\n## Rationale\n\nNot yet verified.\n"
                "\n## Literature\n\nNot yet reviewed.\n\n## Reference evaluation\n\nNot yet selected.\n"
                "\n## Evidence\n\n| Plan / Report | Hypothesis | Key result | Takeaway |\n|---|---|---|---|\n"
                "\n## Current position\n\nLiterature and theoretical refinement required before planning.\n")
        relative = folder.relative_to(main)
        target = root / relative
        if root != main and not target.exists():
            shutil.copytree(folder, target)
        return target / "idea.md"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug")
    parser.add_argument("--question", required=True)
    args = parser.parse_args()
    print(create(Path.cwd(), args.slug, args.question))
