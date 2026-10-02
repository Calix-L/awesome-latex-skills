#!/usr/bin/env python3
"""Validate bundled skill metadata, YAML, and local resource links."""

import argparse
from pathlib import Path
import re
import sys

import yaml

from install import REPO, SKILLS


def validate(repo):
    repo = Path(repo).resolve()
    errors = []
    versions = set()
    for name in SKILLS:
        folder = repo / name
        source = folder / "SKILL.md"
        if not source.is_file():
            errors.append(f"{name}: missing SKILL.md")
            continue
        text = source.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
        try:
            meta = yaml.safe_load(match[1]) if match else None
            if not isinstance(meta, dict):
                raise ValueError("missing or invalid YAML frontmatter")
            if meta.get("name") != name:
                errors.append(f"{name}: frontmatter name must match folder")
            if not isinstance(meta.get("description"), str) or not meta["description"].strip():
                errors.append(f"{name}: description must be a nonempty string")
            extra = meta.keys() - {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
            if extra:
                errors.append(f"{name}: unsupported frontmatter keys: {sorted(extra)}")
            metadata = meta.get("metadata", {})
            if not isinstance(metadata, dict):
                raise ValueError("metadata must be a mapping")
            version = metadata.get("version")
            if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
                errors.append(f"{name}: metadata.version must be a quoted semantic version")
            else:
                versions.add(version)
        except (yaml.YAMLError, ValueError) as exc:
            errors.append(f"{name}: {exc}")
        for filename in ("config.yaml", "openai.yaml"):
            config = folder / "agents" / filename
            try:
                data = yaml.safe_load(config.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("must contain a mapping")
                if filename == "config.yaml" and data.get("skill_file") != f"{name}/SKILL.md":
                    errors.append(f"{name}: config.yaml skill_file does not match bundle")
                if filename == "openai.yaml":
                    interface = data.get("interface", {})
                    if not isinstance(interface, dict):
                        raise ValueError("interface must be a mapping")
                    short = interface.get("short_description", "")
                    if not isinstance(short, str) or not 25 <= len(short) <= 64:
                        errors.append(f"{name}: short_description must be 25–64 characters")
            except (OSError, yaml.YAMLError, ValueError) as exc:
                errors.append(f"{name}/agents/{filename}: {exc}")
        # Check actual resource paths, including links from supporting references.
        for document in folder.rglob("*.md"):
            content = document.read_text(encoding="utf-8")
            paths = re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", content)
            paths += re.findall(r"`((?:references|scripts|assets)/[^`\n]+)`", content)
            for raw in set(paths):
                if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", raw) or raw.startswith("#"):
                    continue
                local = raw.split("#", 1)[0]
                if not local or any(char in local for char in "*<>{}"):
                    continue
                base = folder if raw.startswith(("references/", "scripts/", "assets/")) else document.parent
                target = (base / local).resolve()
                if not target.is_relative_to(repo) or not target.exists():
                    errors.append(f"{document.relative_to(repo)}: missing or external local resource {raw}")
    if len(versions) > 1:
        errors.append(f"Skill versions differ: {sorted(versions)}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO)
    args = parser.parse_args()
    errors = validate(args.root)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print(f"Validated {len(SKILLS)} skill bundles, metadata, YAML, and resource links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
