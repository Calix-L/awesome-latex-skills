#!/usr/bin/env python3
"""Install skill bundles with Python's standard library (Python 3.10+)."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

SKILLS = ("latex-rescue", "latex-polish", "latex-fmt", "paper-read", "pdf2tex")
REPO = Path(__file__).resolve().parents[1]
RECEIPT = ".awesome-latex-skills-install.json"


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
        if relative == Path(RECEIPT):
            continue
        if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.is_file():
            files[relative] = path.read_bytes()
    if Path("SKILL.md") not in files:
        raise ValueError(f"Missing SKILL.md: {folder}")
    return files


def fingerprints(files):
    return {str(path.as_posix()): hashlib.sha256(data).hexdigest() for path, data in files.items()}


def snapshot(folder):
    files = bundle_files(folder)
    receipt = folder / RECEIPT
    if receipt.exists():
        files[Path(RECEIPT)] = receipt.read_bytes()
    return files


def managed(folder, name, files):
    try:
        data = json.loads((folder / RECEIPT).read_text(encoding="utf-8"))
        return (isinstance(data, dict) and data.get("schema") == 1
                and data.get("skill") == name and data.get("files") == fingerprints(files))
    except (OSError, ValueError, UnicodeError):
        return False


def install(repo, destination, skills, dry_run=False, update=False):
    """Stage a whole batch; update only bundles matching their install receipt."""
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
        if (source / RECEIPT).exists():
            raise ValueError(f"Reserved installation receipt in source bundle: {source}")
        files = bundle_files(source)
        target = destination / name
        if repo.is_relative_to(target.resolve()) or target.resolve().is_relative_to(repo):
            raise ValueError("Installation target must not overlap the source repository")
        if target.is_symlink():
            raise ValueError(f"Refusing symlink destination: {target}")
        if target.exists():
            existing = bundle_files(target) if target.is_dir() else None
            if existing == files:
                action = "adopt" if update and not managed(target, name, existing) else "unchanged"
            elif update and existing is not None and managed(target, name, existing):
                action = "update"
            else:
                raise ValueError(f"Existing skill differs: {target}. Unmanaged or locally edited bundles cannot be updated; back it up and move it away, or choose --dest.")
            plan.append((name, files, action, snapshot(target)))
        else:
            plan.append((name, files, "install", None))
    if dry_run or all(action == "unchanged" for _, _, action, _ in plan):
        return [(name, action) for name, _, action, _ in plan]
    destination.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix=".latex-skills-", dir=destination))
    cleanup = True
    journal = []
    try:
        # Stage the complete batch so a read/copy error cannot leave a partial skill.
        for name, files, action, _ in plan:
            if action == "unchanged":
                continue
            for relative, data in files.items():
                path = staged / "new" / name / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            receipt = {"schema": 1, "skill": name, "files": fingerprints(files)}
            (staged / "new" / name / RECEIPT).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        (staged / "old").mkdir()
        try:
            for name, _, action, previous in plan:
                if action == "unchanged":
                    continue
                target, backup = destination / name, staged / "old" / name
                if previous is None:
                    if target.exists() or target.is_symlink():
                        raise ValueError(f"Destination appeared during installation: {target}")
                else:
                    if target.is_symlink() or not target.is_dir() or snapshot(target) != previous:
                        raise ValueError(f"Destination changed during installation: {target}")
                journal.append(name)
                if previous is not None:
                    target.rename(backup)
                (staged / "new" / name).rename(target)
        except BaseException:
            # Preserve backups even if rollback itself is interrupted.
            cleanup = False
            failures = []
            for name in reversed(journal):
                try:
                    if not (staged / "new" / name).exists():
                        (destination / name).rename(staged / "new" / name)
                    if (staged / "old" / name).exists():
                        (staged / "old" / name).rename(destination / name)
                except OSError as exc:
                    failures.append(str(exc))
            if failures:
                raise RuntimeError(f"Rollback needs manual recovery; preserved files at {staged}: {'; '.join(failures)}")
            cleanup = True
            raise
    finally:
        if cleanup:
            shutil.rmtree(staged)
    return [(name, action) for name, _, action, _ in plan]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=("claude", "codex"), default="claude")
    parser.add_argument("--dest", type=Path, help="Custom skills directory")
    parser.add_argument("--skill", choices=SKILLS, action="append", help="Install one skill; repeat to select several")
    parser.add_argument("--dry-run", action="store_true", help="Validate and show actions without writing")
    parser.add_argument("--update", action="store_true", help="Update managed bundles only when no local files changed")
    args = parser.parse_args(argv)
    destination = args.dest or default_destination(args.agent)
    try:
        result = install(REPO, destination, args.skill or SKILLS, args.dry_run, args.update)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Installation failed: {exc}", file=sys.stderr)
        return 1
    print(f"Destination: {destination.expanduser().resolve()}")
    for name, action in result:
        print(f"{'Would ' if args.dry_run else ''}{action}: {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
