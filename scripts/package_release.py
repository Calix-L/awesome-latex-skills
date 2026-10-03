#!/usr/bin/env python3
"""Create deterministic source/bundle ZIPs and SHA-256 manifests in a new directory."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import zipfile

from install import SKILLS, bundle_files
from project_support import ROOT, sha256, version, write_new_json

SOURCE_ROOTS = (*SKILLS, "scripts", "assets", "docs", "examples", "evaluation", "maintenance", "tests", ".github")
SOURCE_FILES = ("VERSION", "LICENSE", "README.md", "README_CN.md", "CHANGELOG.md", "CONTRIBUTING.md", "requirements-dev.txt", ".gitignore", ".gitattributes")


def archive(path, files):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            output.writestr(info, content)


def package(output, root=ROOT):
    root, output = Path(root).resolve(), Path(output).expanduser().absolute()
    current = version(root)
    if not re.fullmatch(r"\d+\.\d+\.\d+", current):
        raise ValueError("VERSION must contain a semantic version")
    if output.exists() or output.is_symlink():
        raise ValueError("Release output must be a new directory")
    bundles = {}
    for skill in SKILLS:
        files = bundle_files(root / skill)
        match = re.search(r'(?m)^  version: "([0-9.]+)"$', "\n".join(files[Path("SKILL.md")].decode("utf-8").splitlines()))
        if not match or match[1] != current:
            raise ValueError(f"Bundle/version mismatch: {skill}")
        bundles[skill] = {f"{skill}/{path.as_posix()}": content for path, content in files.items()}
    for filename in SOURCE_FILES:
        if (root / filename).is_symlink() or not (root / filename).is_file():
            raise ValueError(f"Missing regular source file: {filename}")
    sources = {filename: (root / filename).read_bytes() for filename in SOURCE_FILES}
    for files in bundles.values():
        files["LICENSE"] = sources["LICENSE"]
    for folder in SOURCE_ROOTS:
        directory = root / folder
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"Missing regular source directory: {folder}")
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Symlink in release source: {path}")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}:
                sources[path.relative_to(root).as_posix()] = path.read_bytes()
    # Refuse placement within an archived tree so staging cannot become an input.
    if any(output.resolve().is_relative_to(root / folder) for folder in SOURCE_ROOTS):
        raise ValueError("Release output cannot be inside an archived source directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".release-", dir=output.parent) as temporary:
        stage = Path(temporary) / "release"
        stage.mkdir()
        names = {f"awesome-latex-skills-{current}.zip": sources,
                 **{f"{skill}-{current}.zip": files for skill, files in bundles.items()}}
        for filename, files in names.items():
            archive(stage / filename, files)
        manifest = {"schema": 1, "version": current, "archives": [
            {"file": filename, "sha256": sha256(stage / filename), "bytes": (stage / filename).stat().st_size,
             "entries": len(names[filename])} for filename in sorted(names)],
            "source_files": {filename: hashlib.sha256(content).hexdigest() for filename, content in sorted(sources.items())},
            "interpretation": "Checksums establish file integrity, not authenticity; verify the release/tag and CI separately"}
        write_new_json(stage / "release-manifest.json", manifest)
        (stage / "SHA256SUMS").write_text("".join(f"{item['sha256']}  {item['file']}\n" for item in manifest["archives"])
                                          + f"{sha256(stage / 'release-manifest.json')}  release-manifest.json\n", encoding="utf-8")
        if output.exists() or output.is_symlink():
            raise ValueError("Release output appeared while packaging")
        stage.rename(output)
    return {"schema": 1, "version": current, "output": str(output), "archives": manifest["archives"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = package(args.output)
        print(json.dumps(result, ensure_ascii=True, indent=2) if args.json else f"Packaged {len(result['archives'])} archives in {result['output']}")
        return 0
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"schema": 1, "error": str(exc)}) if args.json else f"Release: {exc}", file=sys.stdout if args.json else sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
