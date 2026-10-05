"""Shared validation for project reports; no network or third-party dependencies."""
import json
import math
from pathlib import Path, PurePosixPath, PureWindowsPath
from bounded_io import MAX_METADATA_BYTES, fingerprint, read_bytes

ROOT = Path(__file__).resolve().parents[1]


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(text):
    def invalid_constant(value):
        raise ValueError(f"Nonfinite JSON value: {value}")
    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError(f"Nonfinite JSON value: {value}")
        return result
    result = json.loads(text, object_pairs_hook=unique_keys,
                        parse_constant=invalid_constant, parse_float=finite_float)
    if not isinstance(result, dict):
        raise ValueError("JSON document must contain an object")
    return result


def read_json(path):
    return parse_json(read_bytes(path, MAX_METADATA_BYTES).decode("utf-8"))


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
    return fingerprint(path)["sha256"]


def write_new_json(path, value):
    content = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if len(content.encode("utf-8")) > MAX_METADATA_BYTES:
        raise ValueError(f"JSON output exceeds the {MAX_METADATA_BYTES}-byte size limit")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output:
        output.write(content)


def version(root=ROOT):
    return (Path(root) / "VERSION").read_text(encoding="utf-8").strip()
