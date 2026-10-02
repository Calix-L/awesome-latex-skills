#!/usr/bin/env python3
"""Validate bundled skill metadata, YAML, and local resource links."""

import argparse
from html.parser import HTMLParser
import math
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

import yaml
from markdown_it import MarkdownIt

from install import REPO, SKILLS, RECEIPT


MARKDOWN = MarkdownIt("commonmark").enable(["table", "strikethrough"])


def srcset_urls(value):
    # Consume URLs before descriptors; commas inside data URLs belong to the URL.
    while value.strip(" ,\t\r\n"):
        value = value.lstrip(" ,\t\r\n")
        match = re.match(r"\S+", value)
        url = match[0]
        value = value[match.end():]
        yield url.rstrip(",")
        if not url.endswith(","):
            value = value.partition(",")[2]


class HTMLResources(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.ids.update(value for key, value in attributes if value and (key == "id" or (tag == "a" and key == "name")))
        self.links.extend(attrs[key] for key in ("href", "src") if attrs.get(key))
        if attrs.get("srcset"):
            self.links.extend(srcset_urls(attrs["srcset"]))

    handle_startendtag = handle_starttag


def inline_tokens(tokens):
    for token in tokens:
        yield token
        if token.children:
            yield from inline_tokens(token.children)


def document_resources(text):
    tokens = MARKDOWN.parse(text)
    html = HTMLResources()
    links, code_paths = [], []
    for token in inline_tokens(tokens):
        if token.type in ("html_inline", "html_block"):
            html.feed(token.content)
        if token.type == "link_open":
            links.append(token.attrGet("href"))
        elif token.type == "image":
            links.append(token.attrGet("src"))
        elif token.type == "code_inline" and token.content.startswith(("references/", "scripts/", "assets/")):
            code_paths.append(token.content)
    return tokens, set(links + html.links), code_paths, html.ids


def heading_ids(text):
    """GFM-style IDs for ordinary headings, including Chinese and duplicates."""
    tokens, _, _, explicit_ids = document_resources(text)
    ids, generated = set(explicit_ids), set()
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        heading = "".join(child.content if child.type in ("text", "code_inline", "image") else " " if child.type in ("softbreak", "hardbreak") else ""
                          for child in tokens[index + 1].children or []).strip().lower()
        slug = "".join(c for c in heading if c in " -_" or unicodedata.category(c)[0] in "LN").replace(" ", "-")
        count, candidate = 0, slug
        while candidate in generated:
            count += 1
            candidate = f"{slug}-{count}"
        generated.add(candidate)
        ids.add(candidate)
    return ids


def validate_document(document, repo, bundle=None):
    """Check local Markdown/HTML links and navigation without network requests."""
    document, repo = Path(document), Path(repo).resolve()
    try:
        _, links, code_paths, _ = document_resources(document.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        return [f"{document.name}: cannot read UTF-8 document: {exc}"]
    errors = []
    for raw in sorted(links):
        try:
            parsed = urlsplit(raw)
        except ValueError:
            errors.append(f"{document.name}: invalid link {raw}")
            continue
        if parsed.scheme or parsed.netloc:
            continue
        target = (document.parent / unquote(parsed.path)).resolve() if parsed.path else document.resolve()
        if not target.is_relative_to(repo) or not target.exists():
            errors.append(f"{document.name}: missing or external local link {raw}")
        elif bundle and not target.is_relative_to(bundle.resolve()):
            errors.append(f"{document.name}: resource outside this skill bundle {raw}; selected installs must be self-contained")
        elif parsed.fragment and target.suffix.lower() == ".md":
            try:
                if unquote(parsed.fragment) not in heading_ids(target.read_text(encoding="utf-8")):
                    errors.append(f"{document.name}: missing heading anchor {raw}")
            except (OSError, UnicodeError) as exc:
                errors.append(f"{document.name}: cannot read link target {raw}: {exc}")
    if bundle:
        for raw in sorted(set(code_paths)):
            if any(char in raw for char in "*<>{}"):
                continue
            target = (bundle / raw).resolve()
            if not target.is_relative_to(bundle.resolve()) or not target.exists():
                errors.append(f"{document.name}: missing or external local resource {raw}")
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
        try:
            text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{name}: cannot read SKILL.md: {exc}")
            continue
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
            except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
                errors.append(f"{name}/agents/{filename}: {exc}")
        # Check actual resource paths, including links from supporting references.
        for document in folder.rglob("*.md"):
            errors.extend(validate_document(document, repo, bundle=folder))
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
            viewbox = [float(part) for part in re.split(r"[\s,]+", root.get("viewBox", "").strip()) if part]
            if root.tag != "{http://www.w3.org/2000/svg}svg" or len(viewbox) != 4 or not all(math.isfinite(v) for v in viewbox) or any(v <= 0 for v in viewbox[2:]):
                errors.append(f"{asset.name}: expected an SVG root with viewBox")
        except (OSError, ET.ParseError, UnicodeError, ValueError) as exc:
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
