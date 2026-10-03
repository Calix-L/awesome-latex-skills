#!/usr/bin/env python3
"""Inspect literal LaTeX project dependencies without editing or compiling them."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import sys

from project_support import read_json, safe_path, sha256, write_new_json

ENGINES = ("pdflatex", "xelatex", "lualatex")
BACKENDS = (None, "bibtex", "biber")
GENERATED = {".git", "work", "dist", "build", ".als-runs", "__pycache__", "evaluation-runs"}
SOURCE_SUFFIXES = {".tex", ".bib", ".cls", ".sty", ".bst"}
ASSET_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg"}
MAX_FILES = 5000
MAX_SOURCE_BYTES = 2_000_000


def mask_tex(text):
    """Keep offsets/lines; ignore ordinary comments and common verbatim forms."""
    def blank(match):
        return re.sub(r"[^\n]", " ", match.group())
    text = re.sub(r"\\begin\{(verbatim\*?|lstlisting|minted)\}.*?\\end\{\1\}", blank, text, flags=re.S)
    text = re.sub(r"\\verb\*?([^\w\s]).*?\1", blank, text)
    lines = []
    for line in text.splitlines(keepends=True):
        for position, char in enumerate(line):
            if char == "%":
                backslashes = len(line[:position]) - len(line[:position].rstrip("\\"))
                if backslashes % 2 == 0:
                    line = line[:position] + re.sub(r"[^\n]", " ", line[position:])
                    break
        lines.append(line)
    return "".join(lines)


COMMAND = re.compile(r"\\(?P<name>documentclass|usepackage|RequirePackage|input|include|includegraphics|bibliography|addbibresource|bibliographystyle|label|ref|eqref|pageref|autoref|[cC]ref|cite[a-zA-Z]*|nocite)\*?\s*(?P<options>(?:\[[^\]\n]*\]\s*)*)\{(?P<value>[^{}\n]*)\}")


def commands(text):
    masked = mask_tex(text)
    for match in COMMAND.finditer(masked):
        yield {"name": match["name"], "value": match["value"].strip(), "options": match["options"],
               "line": masked.count("\n", 0, match.start()) + 1}


def inventory(root, assets=False):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("Project root must be a directory")
    suffixes = SOURCE_SUFFIXES | (ASSET_SUFFIXES if assets else set())
    found = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in GENERATED for part in relative.parts):
            continue
        if (path.suffix.lower() in suffixes or assets and relative.as_posix() == ".als.json") and (path.is_file() or path.is_symlink()):
            checked = safe_path(root, relative.as_posix())
            if checked.stat().st_size > MAX_SOURCE_BYTES and checked.suffix.lower() in SOURCE_SUFFIXES:
                raise ValueError(f"Source exceeds {MAX_SOURCE_BYTES} bytes: {relative}")
            found[relative.as_posix()] = checked
            if len(found) > MAX_FILES:
                raise ValueError(f"Project inventory exceeds {MAX_FILES} files")
    return found


def load_config(root, filename=".als.json"):
    root = Path(root).resolve()
    config = read_json(safe_path(root, filename))
    if config.get("schema") != 1 or set(config) - {"schema", "main", "engine", "backend", "passes"}:
        raise ValueError("Expected schema-1 project config with main/engine/backend/passes only")
    if not safe_path(root, config.get("main")).is_file():
        raise ValueError("Configured main file is missing")
    if config.get("engine") not in ENGINES or config.get("backend") not in BACKENDS:
        raise ValueError("Invalid configured engine/backend")
    if type(config.get("passes", 2)) is not int or not 1 <= config.get("passes", 2) <= 5:
        raise ValueError("Configured passes must be 1–5")
    return config


def initialize(root, main, engine="pdflatex", backend=None, passes=2):
    root = Path(root).resolve()
    if not root.is_dir() or not safe_path(root, main).is_file():
        raise ValueError("Supply an existing project root and main source")
    if engine not in ENGINES or backend not in BACKENDS or type(passes) is not int or not 1 <= passes <= 5:
        raise ValueError("Invalid engine/backend/pass settings")
    config = {"schema": 1, "main": main, "engine": engine, "backend": backend, "passes": passes}
    write_new_json(root / ".als.json", config)
    return {"schema": 1, "config": str(root / ".als.json"), "settings": config}


def inspect_project(root, main=None, engine=None, backend=None):
    root = Path(root).resolve()
    files = inventory(root)
    texts = {name: path.read_text(encoding="utf-8") for name, path in files.items() if path.suffix.lower() == ".tex"}
    roots = [name for name, text in texts.items() if any(c["name"] == "documentclass" for c in commands(text))]
    if (root / ".als.json").exists():
        config = load_config(root)
        main = main or config["main"]
        engine = engine or config["engine"]
        backend = backend if backend is not None else config.get("backend")
    if engine is not None and engine not in ENGINES or backend not in BACKENDS:
        raise ValueError("Invalid engine/backend")
    main = main or (roots[0] if len(roots) == 1 else None)
    result = {"schema": 1, "kind": "project_inspection", "root": str(root), "main": main,
              "root_candidates": sorted(roots), "engine": engine, "backend": backend,
              "inputs": [], "dependencies": [], "diagnostics": [], "status": "ready",
              "limitations": ["Static literal references only: macro expansion, conditionals, class/package internals and external search paths are not evaluated.",
                              "A clean inspection is not a compilation or scientific-content review."]}
    def diagnostic(code, severity, file, line, message, next_step):
        result["diagnostics"].append({"code": code, "severity": severity, "file": file, "line": line,
                                      "message": message, "next_step": next_step})
    if main is None:
        diagnostic("root-selection", "error", None, None, "No unique document root", "Choose --main from root_candidates or create .als.json with project init")
        result["status"] = "blocked"
        return result
    source = safe_path(root, main)
    if main not in texts or not source.is_file():
        raise ValueError("Selected main must be an existing UTF-8 .tex file inside the project")
    visited, bibliography, packages, labels, references, citations = set(), set(), set(), Counter(), [], []
    working_prefix = Path(main).parent
    graphics_paths = [""]
    queue = [main]
    while queue:
        filename = queue.pop(0)
        if filename in visited:
            continue
        visited.add(filename)
        if len(visited) > MAX_FILES:
            raise ValueError("Dependency graph exceeds the supported file limit")
        path = safe_path(root, filename)
        if path.stat().st_size > MAX_SOURCE_BYTES:
            raise ValueError(f"Source exceeds the supported size limit: {filename}")
        text = texts[filename] if filename in texts else path.read_text(encoding="utf-8")
        result["inputs"].append({"file": filename, "sha256": sha256(path)})
        # graphicspath is limited to literal, project-root-relative directories.
        for match in re.finditer(r"\\graphicspath\s*\{((?:\{[^{}]*\}\s*)+)\}", mask_tex(text)):
            graphics_paths.extend(re.findall(r"\{([^{}]*)\}", match[1]))
        for command in commands(text):
            name, value, line = command["name"], command["value"], command["line"]
            if "\\" in value or "#" in value:
                diagnostic("dynamic-reference", "unverified", filename, line, f"Dynamic {name} argument: {value}", "Inspect macro expansion in the actual build")
                continue
            if name in {"documentclass", "usepackage", "RequirePackage"}:
                extension = ".cls" if name == "documentclass" else ".sty"
                if name != "documentclass":
                    packages.update(part.strip() for part in value.split(","))
                for package in (part.strip() for part in value.split(",")):
                    local_name = (working_prefix / (package + extension)).as_posix()
                    try:
                        local = safe_path(root, local_name)
                    except ValueError as exc:
                        diagnostic("external-package", "unverified", filename, line, str(exc), "Review this package lookup explicitly")
                        continue
                    if "/" in package or local.is_file():
                        exists = local.is_file()
                        result["dependencies"].append({"from": filename, "line": line, "command": name, "requested": package,
                                                       "file": local_name if exists else None, "exists": exists})
                        if exists:
                            queue.append(local_name)
                        else:
                            diagnostic("missing-local-package", "error", filename, line, f"Local class/package not found: {package}", f"Supply its actual {extension} file")
                if "biblatex" in {part.strip() for part in value.split(",")}:
                    specified = re.search(r"backend\s*=\s*(biber|bibtex)", command["options"])
                    if specified and backend and specified[1] != backend:
                        diagnostic("backend-mismatch", "error", filename, line, "Configured bibliography backend differs from explicit biblatex options", "Use the project's actual backend")
                continue
            if name == "label":
                labels[value] += 1
                continue
            if name in {"ref", "eqref", "pageref", "autoref", "cref", "Cref"}:
                references.extend((key.strip(), filename, line) for key in value.split(","))
                continue
            if name.startswith("cite") or name == "nocite":
                citations.extend((key.strip(), filename, line) for key in value.split(",") if key.strip() != "*")
                continue
            if name not in {"input", "include", "includegraphics", "bibliography", "addbibresource"}:
                continue
            for raw in value.split(",") if name == "bibliography" else [value]:
                raw = raw.strip()
                suffixes = [".tex"] if name in {"input", "include"} else [".bib"]
                bases = [""]
                if name == "includegraphics":
                    suffixes = [".pdf", ".png", ".jpg", ".jpeg", ".eps"]
                    bases = graphics_paths
                candidates = []
                try:
                    for base in bases:
                        relative = (working_prefix / base / raw).as_posix()
                        target = safe_path(root, relative)
                        candidates.extend([target] if target.suffix else [safe_path(root, relative + extension) for extension in suffixes])
                except ValueError as exc:
                    diagnostic("external-or-dynamic-path", "unverified", filename, line, str(exc), "Review this path explicitly; the inspector does not read outside the project")
                    continue
                existing = next((target for target in candidates if target.is_file()), None)
                dependency = {"from": filename, "line": line, "command": name, "requested": raw,
                              "file": existing.relative_to(root).as_posix() if existing else None, "exists": existing is not None}
                result["dependencies"].append(dependency)
                if existing is None:
                    diagnostic("missing-input", "error", filename, line, f"Literal {name} target not found: {raw}", "Supply the referenced file or correct its path; conditional/external lookup may need manual review")
                elif name in {"input", "include"}:
                    queue.append(existing.relative_to(root).as_posix())
                elif name in {"bibliography", "addbibresource"}:
                    bibliography.add(existing.relative_to(root).as_posix())
                else:
                    result["inputs"].append({"file": existing.relative_to(root).as_posix(), "sha256": sha256(existing)})
    known_keys = set()
    for filename in sorted(bibliography):
        path = safe_path(root, filename)
        known_keys.update(re.findall(r"@(?!(?:comment|string|preamble)\b)[a-zA-Z]+\s*\{\s*([^,\s]+)\s*,", path.read_text(encoding="utf-8"), flags=re.I))
        result["inputs"].append({"file": filename, "sha256": sha256(path)})
    for key, filename, line in references:
        if key not in labels:
            diagnostic("unknown-label", "warning", filename, line, f"No literal label definition found for {key}", "Retain the key and ask for its intended target; inspect generated definitions")
    for key, filename, line in citations:
        if key not in known_keys:
            diagnostic("unknown-citation", "warning", filename, line, f"No parsed bibliography entry found for {key}", "Supply the actual entry; do not invent a source")
    for key, count in labels.items():
        if count > 1:
            diagnostic("duplicate-label", "warning", main, None, f"Literal label {key} appears {count} times", "Check active definitions in the actual build")
    if "fontspec" in packages and engine == "pdflatex":
        diagnostic("engine-mismatch", "error", main, None, "fontspec requires XeLaTeX or LuaLaTeX", "Select the engine actually supported by the project")
    if {"natbib", "biblatex"}.issubset(packages):
        diagnostic("bibliography-conflict", "error", main, None, "Both natbib and biblatex are explicitly loaded", "Review the actual template's bibliography setup")
    if engine is None:
        diagnostic("engine-unverified", "unverified", main, None, "No engine has been selected", "Record the actual engine with project init or --engine")
    elif shutil.which(engine) is None:
        diagnostic("missing-engine", "error", main, None, f"{engine} is not on PATH", "Use an existing TeX installation or supply its PATH")
    if backend and shutil.which(backend) is None:
        diagnostic("missing-backend", "error", main, None, f"{backend} is not on PATH", "Supply the actual bibliography tool on PATH")
    result["packages"] = sorted(packages)
    result["status"] = "blocked" if any(item["severity"] == "error" for item in result["diagnostics"]) else "needs-review" if result["diagnostics"] else "ready"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    commands_parser = parser.add_subparsers(dest="command", required=True)
    init = commands_parser.add_parser("init")
    init.add_argument("root", type=Path)
    init.add_argument("--main", required=True)
    init.add_argument("--engine", choices=ENGINES, default="pdflatex")
    init.add_argument("--backend", choices=BACKENDS[1:])
    init.add_argument("--passes", type=int, default=2)
    check = commands_parser.add_parser("check")
    check.add_argument("root", type=Path)
    check.add_argument("--main")
    check.add_argument("--engine", choices=ENGINES)
    check.add_argument("--backend", choices=BACKENDS[1:])
    check.add_argument("--output", type=Path, help="Optional new JSON file")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = initialize(args.root, args.main, args.engine, args.backend, args.passes)
        else:
            result = inspect_project(args.root, args.main, args.engine, args.backend)
            if args.output:
                write_new_json(args.output, result)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 1 if result.get("status") == "blocked" else 0
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        print(json.dumps({"schema": 1, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
