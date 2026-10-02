#!/usr/bin/env python3
"""Install skill bundles with Python's standard library (Python 3.10+)."""

import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile

SKILLS = ("latex-rescue", "latex-polish", "latex-fmt", "paper-read", "pdf2tex")
REPO = Path(__file__).resolve().parents[1]


def default_destination(agent):
    if agent == "codex":
        return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills"
    return Path.home() / ".claude" / "skills"


def bundle_files(folder):
    """Only skip transient Python artifacts; preserve all skill resources."""
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError(f"Not a regular skill directory: {folder}")
    files = {}
    for path in folder.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not supported in skill bundles: {path}")
        relative = path.relative_to(folder)
        if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.is_file():
            files[relative] = path.read_bytes()
    if Path("SKILL.md") not in files:
        raise ValueError(f"Missing SKILL.md: {folder}")
    return files


def install(repo, destination, skills, dry_run=False):
    """Preflight every bundle before writing; never overwrite existing skills."""
    repo = Path(repo).resolve()
    destination = Path(destination).expanduser().resolve()
    if destination.is_relative_to(repo):
        raise ValueError("Installation destination must be outside the source repository")
    if destination.exists() and not destination.is_dir():
        raise ValueError(f"Destination is not a directory: {destination}")
    plan = []
    for name in dict.fromkeys(skills):
        if name not in SKILLS:
            raise ValueError(f"Unknown skill: {name}")
        source = repo / name
        files = bundle_files(source)
        target = destination / name
        if target.is_symlink():
            raise ValueError(f"Refusing symlink destination: {target}")
        if target.exists():
            if not target.is_dir() or bundle_files(target) != files:
                raise ValueError(f"Existing skill differs: {target}. Back it up and move it away, or choose --dest.")
            plan.append((name, files, "unchanged"))
        else:
            plan.append((name, files, "install"))
    if dry_run or all(action == "unchanged" for _, _, action in plan):
        return [(name, action) for name, _, action in plan]
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".latex-skills-", dir=destination) as temporary:
        staged = Path(temporary)
        # Stage the complete batch so a read/copy error cannot leave a partial skill.
        for name, files, action in plan:
            if action == "unchanged":
                continue
            for relative, data in files.items():
                path = staged / name / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        published = []
        try:
            for name, _, action in plan:
                if action == "install":
                    target = destination / name
                    if target.exists() or target.is_symlink():
                        raise ValueError(f"Destination appeared during installation: {target}")
                    (staged / name).rename(target)
                    published.append(name)
        except (OSError, ValueError):
            for name in reversed(published):
                (destination / name).rename(staged / name)
            raise
    return [(name, action) for name, _, action in plan]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=("claude", "codex"), default="claude")
    parser.add_argument("--dest", type=Path, help="Custom skills directory")
    parser.add_argument("--skill", choices=SKILLS, action="append", help="Install one skill; repeat to select several")
    parser.add_argument("--dry-run", action="store_true", help="Validate and show actions without writing")
    args = parser.parse_args(argv)
    destination = args.dest or default_destination(args.agent)
    try:
        result = install(REPO, destination, args.skill or SKILLS, args.dry_run)
    except (OSError, ValueError) as exc:
        print(f"Installation failed: {exc}", file=sys.stderr)
        return 1
    print(f"Destination: {destination.expanduser().resolve()}")
    for name, action in result:
        print(f"{'Would ' if args.dry_run else ''}{action}: {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
