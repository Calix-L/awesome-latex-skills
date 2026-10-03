"""Shared validation for project reports; no network or third-party dependencies."""
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    def invalid_constant(value):
        raise ValueError(f"Nonfinite JSON value: {value}")
    result = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_keys,
                        parse_constant=invalid_constant)
    if not isinstance(result, dict):
        raise ValueError("JSON document must contain an object")
    return result


def safe_path(root, value):
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value or ":" in value:
        raise ValueError(f"Invalid portable path: {value!r}")
    parts = PurePosixPath(value).parts
    if PurePosixPath(value).is_absolute() or PureWindowsPath(value).drive or any(p in {"..", "."} for p in value.split("/")):
        raise ValueError(f"Path must stay inside its root: {value}")
    root = Path(root).resolve()
    target = root.joinpath(*parts)
    if not target.resolve().is_relative_to(root) or any(root.joinpath(*parts[:i]).is_symlink() for i in range(1, len(parts) + 1)):
        raise ValueError(f"Symlink or escaping path: {value}")
    return target


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_new_json(path, value):
    content = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output:
        output.write(content)


def version(root=ROOT):
    return (Path(root) / "VERSION").read_text(encoding="utf-8").strip()
