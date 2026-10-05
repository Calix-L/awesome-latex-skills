"""Bounded, portable file inventories for offline delivery verification."""
import os
from pathlib import Path, PurePosixPath
import re

from project_support import safe_path, write_new_json
from bounded_io import MAX_FILE_BYTES, MAX_TOTAL_BYTES, MAX_METADATA_BYTES, fingerprint

MAX_FILES = 20_000
HASH = re.compile(r"[0-9a-f]{64}\Z")


def portable_name(root, name):
    path = safe_path(root, name)
    if PurePosixPath(name).as_posix() != name or name.endswith("/"):
        raise ValueError(f"Noncanonical portable filename: {name!r}")
    return path


def validate_files(root, rows):
    if not isinstance(rows, list) or not rows or len(rows) > MAX_FILES:
        raise ValueError("File inventory must be a nonempty bounded list")
    found = {}
    names = set()
    total = 0
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError("File inventory needs structured rows")
        name = item.get("file")
        portable_name(root, name)
        if name.casefold() in names:
            raise ValueError(f"Duplicate or case-colliding inventory path: {name}")
        digest, size = item.get("sha256"), item.get("bytes")
        if not isinstance(digest, str) or HASH.fullmatch(digest) is None:
            raise ValueError(f"Invalid SHA-256 fingerprint: {name}")
        if type(size) is not int or not 0 <= size <= MAX_FILE_BYTES:
            raise ValueError(f"Invalid or oversized byte count: {name}")
        total += size
        if total > MAX_TOTAL_BYTES:
            raise ValueError("File inventory exceeds the total byte limit")
        names.add(name.casefold())
        found[name] = item
    return found


def regular_files(root):
    """Never descend into symlinks; include hidden files and arbitrary extensions."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("Artifact root must be a directory")
    found = {}
    total = 0
    folded = set()
    def walk_error(error):
        raise error
    for directory, children, files in os.walk(root, followlinks=False, onerror=walk_error):
        for child in children:
            safe_path(root, (Path(directory) / child).relative_to(root).as_posix())
        for name in sorted(files):
            relative = (Path(directory) / name).relative_to(root).as_posix()
            path = portable_name(root, relative)
            if not path.is_file():
                raise ValueError(f"Artifact is not a regular file: {relative}")
            if relative.casefold() in folded:
                raise ValueError(f"Case-colliding artifact paths: {relative}")
            size = path.stat().st_size
            total += size
            if size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES or len(found) >= MAX_FILES:
                raise ValueError("Artifact inventory exceeds file/byte limits")
            found[relative] = path
            folded.add(relative.casefold())
    return found


def file_inventory(root, exclude=()):
    rows = [{"file": name, **fingerprint(path, MAX_FILE_BYTES)}
            for name, path in sorted(regular_files(root).items()) if name not in exclude]
    if sum(item["bytes"] for item in rows) > MAX_TOTAL_BYTES:
        raise ValueError("Artifact inventory exceeds the total byte limit")
    return rows


def seal_bundle(root, kind):
    """Seal only the new staged bundle; existing manifests are never replaced."""
    root = Path(root).resolve()
    manifest = {"schema": 1, "kind": kind, "files": file_inventory(root),
                "interpretation": "Byte integrity relative to this manifest; producer authenticity and scientific fidelity are not verified."}
    if any(item["file"] == "integrity.json" for item in manifest["files"]):
        raise ValueError("Bundle integrity manifest already exists")
    write_new_json(root / "integrity.json", manifest)
    return manifest


def seal_review(root):
    return seal_bundle(root, "project_review_integrity")


def seal_inspection(root):
    return seal_bundle(root, "project_inspection_integrity")
