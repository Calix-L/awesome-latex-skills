#!/usr/bin/env python3
"""Validate bundled skill metadata, YAML, and local resource links."""

import argparse
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

import yaml

from install import REPO, SKILLS, RECEIPT


def without_fences(text):
    return re.sub(r"(?m)^(`{3,}|~{3,})[^\n]*\n.*?^\1[^\n]*(?:\n|$)", "", text, flags=re.S)


def heading_ids(text):
    """GFM-style IDs for ordinary headings, including Chinese and duplicates."""
    ids = set(re.findall(r'<a\s+(?:id|name)=[\"\']([^\"\']+)', text))
    counts = {}
    for heading in re.findall(r"(?m)^#{1,6}\s+(.+?)(?:\s+#+)?$", without_fences(text)):
        heading = re.sub(r"<[^>]+>", "", heading).strip().lower()
        slug = "".join(c for c in heading if c in " -_" or unicodedata.category(c)[0] in "LN").replace(" ", "-")
        count = counts.get(slug, 0)
        candidate = f"{slug}-{count}" if count else slug
        while candidate in ids:
            count += 1
            candidate = f"{slug}-{count}"
        counts[slug] = count + 1
        ids.add(candidate)
    return ids


def validate_document(document, repo):
    """Check local Markdown/HTML links and navigation without network requests."""
    document, repo = Path(document), Path(repo).resolve()
    text = without_fences(document.read_text(encoding="utf-8"))
    links = re.findall(r"!?\[[^\]]*\]\(([^\s)]+)\)", text)
    links += re.findall(r'(?:href|src|srcset)=[\"\']([^\"\']+)', text)
    errors = []
    for raw in set(links):
        parsed = urlsplit(raw)
        if parsed.scheme or parsed.netloc:
            continue
        target = (document.parent / unquote(parsed.path)).resolve() if parsed.path else document.resolve()
        if not target.is_relative_to(repo) or not target.is_file():
            errors.append(f"{document.name}: missing or external local link {raw}")
        elif parsed.fragment and target.suffix == ".md":
            if unquote(parsed.fragment) not in heading_ids(target.read_text(encoding="utf-8")):
                errors.append(f"{document.name}: missing heading anchor {raw}")
    return errors


def validate(repo):
    repo = Path(repo).resolve()
    errors = []
    versions = set()
    for name in SKILLS:
        folder = repo / name
        if (folder / RECEIPT).exists():
            errors.append(f"{name}: installation receipts belong in installed copies, not source bundles")
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
            errors.extend(validate_document(document, repo))
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
                elif not target.is_relative_to(folder):
                    errors.append(f"{document.relative_to(repo)}: resource outside this skill bundle {raw}; selected installs must be self-contained")
    if len(versions) > 1:
        errors.append(f"Skill versions differ: {sorted(versions)}")
    for document in repo.rglob("*.md"):
        relative = document.relative_to(repo)
        if relative.parts[0] in SKILLS or ".git" in relative.parts:
            continue
        errors.extend(validate_document(document, repo))
    for asset in (repo / "assets").glob("*.svg"):
        try:
            root = ET.fromstring(asset.read_text(encoding="utf-8"))
            if root.tag != "{http://www.w3.org/2000/svg}svg" or not root.get("viewBox"):
                errors.append(f"{asset.name}: expected an SVG root with viewBox")
        except (ET.ParseError, UnicodeError) as exc:
            errors.append(f"{asset.name}: malformed SVG: {exc}")
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
    print(f"Validated {len(SKILLS)} bundles, metadata, resources, README links/anchors, and SVG assets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
