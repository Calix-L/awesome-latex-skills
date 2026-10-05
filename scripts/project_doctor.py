#!/usr/bin/env python3
"""Inspect literal LaTeX project dependencies without editing or compiling them."""
import argparse
from bisect import bisect_right
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

from project_support import parse_json, safe_path, sha256, write_new_json
from tex_lexer import TOKEN, lex_tex, mask_tex
from bib_lexer import ASCII_FOLD, scan_bibliography
from citation_lexer import CITATION_NAMES, citation_candidate, citation_arguments

ENGINES = ("pdflatex", "xelatex", "lualatex")
BACKENDS = (None, "bibtex", "biber")
GENERATED = {".git", "work", "dist", "build", ".als-runs", "__pycache__", "evaluation-runs", ".venv", "venv", "node_modules"}
SOURCE_SUFFIXES = {".tex", ".bib", ".cls", ".sty", ".bst"}
ASSET_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg"}
MAX_FILES = 5000
MAX_SOURCE_BYTES = 2_000_000


COMMAND = re.compile(r"\\(?P<name>documentclass|usepackage|RequirePackageWithOptions|RequirePackage|LoadClassWithOptions|LoadClass|input|includeonly|includegraphics|include|graphicspath|DeclareGraphicsExtensions|bibliography|addbibresource|bibliographystyle|label|ref|eqref|pageref|autoref|[cC]ref|cite[a-zA-Z]*|nocite)(?![a-zA-Z@])\*?\s*(?P<options>(?:\[[^\]]*\]\s*)*)")
ARGUMENT = re.compile(r"\{(?P<value>[^{}]*)\}")
GRAPHICS_ARGUMENT = re.compile(r"\{(?P<value>(?:\{[^{}]*\}\s*)*)\}")


def commands(text):
    masked = mask_tex(text)
    newlines = [match.start() for match in re.finditer("\n", masked)]
    consumed = 0
    for token in TOKEN.finditer(masked):
        if token.start() < consumed:
            continue
        name = token[0][1:]
        if citation_candidate(name):
            offset = token.end()
            starred = masked[offset:offset + 1] == "*"
            offset += int(starred)
            values, consumed, issue = (citation_arguments(masked, offset, name) if name in CITATION_NAMES
                                       else ([], offset, "Custom or special citation syntax is unsupported"))
            line = bisect_right(newlines, token.start()) + 1
            for index, value in enumerate(values, 1):
                yield {"name": name, "value": value, "options": "", "supported": True,
                       "line": line, "citation_group": index, "starred": starred}
            if issue:
                yield {"name": name, "value": "", "options": "", "supported": False,
                       "line": line, "citation_issue": issue}
            continue
        if name == "citetext":
            continue  # Its prose is not a key; nested citation tokens remain visible.
        match = COMMAND.match(masked, token.start())
        if match is None:
            continue
        argument = (GRAPHICS_ARGUMENT if match["name"] == "graphicspath" else ARGUMENT).match(masked, match.end())
        value = argument["value"] if argument else None
        if value is None and match["name"] == "input":
            bare = re.match(r'"[^"\n]+"|[^\s{}%]+', masked[match.end():])
            value = bare[0] if bare else None
        supported = value is not None
        if not supported:
            value = re.match(r"[^\r\n]{0,160}", masked[match.end():match.end() + 160])[0]
        yield {"name": match["name"], "value": value.strip(), "options": match["options"], "supported": supported,
               "line": bisect_right(newlines, match.start()) + 1}


def inventory(root, assets=False):
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("Project root must be a directory")
    suffixes = SOURCE_SUFFIXES | (ASSET_SUFFIXES if assets else set())
    found = {}
    def walk_error(error):
        raise error
    for directory, children, filenames in os.walk(root, topdown=True, followlinks=False, onerror=walk_error):
        children[:] = sorted(name for name in children if name not in GENERATED)
        for child in children:
            safe_path(root, (Path(directory) / child).relative_to(root).as_posix())
        for filename in sorted(filenames):
            path = Path(directory) / filename
            relative = path.relative_to(root)
            if (path.suffix.lower() in suffixes or assets and relative.as_posix() == ".als.json") and (path.is_file() or path.is_symlink()):
                checked = safe_path(root, relative.as_posix())
                if checked.stat().st_size > MAX_SOURCE_BYTES and checked.suffix.lower() in SOURCE_SUFFIXES:
                    raise ValueError(f"Source exceeds {MAX_SOURCE_BYTES} bytes: {relative}")
                found[relative.as_posix()] = checked
                if len(found) > MAX_FILES:
                    raise ValueError(f"Project inventory exceeds {MAX_FILES} files")
    return found


def read_source(path):
    """Bound the bytes actually read, including files that grow after inventory."""
    with Path(path).open("rb") as source:
        content = source.read(MAX_SOURCE_BYTES + 1)
    if len(content) > MAX_SOURCE_BYTES:
        raise ValueError(f"Source exceeds the supported size limit: {Path(path).name}")
    return content


def parse_config(root, content, observations=None):
    config = parse_json(content.decode("utf-8"))
    root = Path(root).expanduser().resolve()
    if config.get("schema") != 1 or set(config) - {"schema", "main", "engine", "backend", "passes"}:
        raise ValueError("Expected schema-1 project config with main/engine/backend/passes only")
    validate_main(root, config.get("main"), observations)
    if config.get("engine") not in ENGINES or config.get("backend") not in BACKENDS:
        raise ValueError("Invalid configured engine/backend")
    if type(config.get("passes", 2)) is not int or not 1 <= config.get("passes", 2) <= 5:
        raise ValueError("Configured passes must be 1–5")
    return config


def load_config(root, filename=".als.json"):
    root = Path(root).expanduser().resolve()
    return parse_config(root, read_source(safe_path(root, filename)))


def validate_main(root, main, observations=None):
    source = safe_path(root, main)
    if (not source.is_file() or source.suffix.lower() != ".tex"
            or any(part in GENERATED for part in Path(main).parts)):
        raise ValueError("Main must be an existing .tex source outside reserved generated directories")
    if source.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError("Main source exceeds the supported size limit")
    content = read_source(source)
    content.decode("utf-8-sig")
    if observations is not None:
        observations[main] = hashlib.sha256(content).hexdigest()
    return source


def initialize(root, main, engine="pdflatex", backend=None, passes=2):
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("Supply an existing project root")
    validate_main(root, main)
    if engine not in ENGINES or backend not in BACKENDS or type(passes) is not int or not 1 <= passes <= 5:
        raise ValueError("Invalid engine/backend/pass settings")
    config = {"schema": 1, "main": main, "engine": engine, "backend": backend, "passes": passes}
    write_new_json(root / ".als.json", config)
    return {"schema": 1, "config": str(root / ".als.json"), "settings": config}


def inspect_project(root, main=None, engine=None, backend=None):
    root = Path(root).expanduser().resolve()
    files = inventory(root)
    observed, texts = {}, {}
    def source_text(name):
        if name not in texts:
            path = safe_path(root, name)
            if path.stat().st_size > MAX_SOURCE_BYTES:
                raise ValueError(f"Source exceeds the supported size limit: {name}")
            content = read_source(path)
            texts[name] = content.decode("utf-8-sig")
            observed[name] = hashlib.sha256(content).hexdigest()
        return texts[name]
    selection = "explicit" if main else "automatic"
    if (root / ".als.json").exists():
        content = read_source(safe_path(root, ".als.json"))
        observed[".als.json"] = hashlib.sha256(content).hexdigest()
        config = parse_config(root, content, observed)
        if main is None:
            selection = "configuration"
        main = main or config["main"]
        engine = engine or config["engine"]
        backend = backend if backend is not None else config.get("backend")
    if engine is not None and engine not in ENGINES or backend not in BACKENDS:
        raise ValueError("Invalid engine/backend")
    if main is None:
        for name, path in files.items():
            if path.suffix.lower() == ".tex":
                source_text(name)
    else:
        validate_main(root, main)
        source_text(main)
    roots = [name for name, text in texts.items() if any(c["name"] == "documentclass" for c in commands(text))]
    main = main or (roots[0] if len(roots) == 1 else None)
    result = {"schema": 1, "kind": "project_inspection", "root": str(root), "main": main,
              "root_candidates": sorted(roots), "engine": engine, "backend": backend,
              "root_selection": selection,
              "root_candidate_scope": "all-project-tex" if selection == "automatic" else "selected-main-only",
              "configuration_sha256": observed.get(".als.json"),
              "inputs": [], "observed_files": [], "dependencies": [], "bibliography_entries": [], "citation_inventory": [], "diagnostics": [], "status": "ready",
              "limitations": ["Static literal references only: macro expansion, grouping, conditionals, system class/package internals and external search paths are not evaluated.",
                              "Literal scanning assumes ordinary category codes; custom verbatim environments and package escape/termination options are not evaluated.",
                              "Default graphics extension order is a common PDF-engine subset; explicit DeclareGraphicsExtensions is honored, but driver/conversion rules are not evaluated.",
                              "Bibliography headers only: field grammar, string expansion, aliases, inheritance, crossref/xdata and backend/style acceptance are not validated. Citation keys are compared exactly.",
                              "Common literal citation commands only; notes are not keys. Custom/special citation syntax, commands inside notes, macro-generated keys and manual bibitem definitions are not evaluated.",
                              "A clean inspection is not a compilation or scientific-content review."]}
    def diagnostic(code, severity, file, line, message, next_step):
        result["diagnostics"].append({"code": code, "severity": severity, "file": file, "line": line,
                                      "message": message, "next_step": next_step})
    def finalize_observations():
        for filename, expected in sorted(observed.items()):
            path = safe_path(root, filename)
            actual = (hashlib.sha256(read_source(path)).hexdigest()
                      if path.suffix.lower() in SOURCE_SUFFIXES or filename == ".als.json" else sha256(path))
            if actual != expected:
                raise ValueError(f"Project input changed during inspection: {filename}")
        result["observed_files"] = [{"file": name, "sha256": digest} for name, digest in sorted(observed.items())]

    # Automatic selection examines all TeX files, including malformed candidates.
    # Explicit/configured selection examines only reachable sources below.
    lex_checked = set()
    if selection == "automatic":
        for filename, text in texts.items():
            lex_checked.add(filename)
            for item in lex_tex(text)[1]:
                diagnostic(item["code"], "unverified", filename, item["line"], item["message"],
                           "Check the literal region in the actual build; later contents may be masked")
    if main is None:
        diagnostic("root-selection", "error", None, None, "No unique document root", "Choose --main from root_candidates or create .als.json with project init")
        result["status"] = "blocked"
        finalize_observations()
        return result
    source = validate_main(root, main)
    if main not in texts or not source.is_file():
        raise ValueError("Selected main must be an existing UTF-8 .tex file inside the project")
    visited, active, bibliography, packages, labels, references, citations = set(), [], {}, set(), Counter(), [], []
    working_prefix = Path(main).parent
    graphics_paths = [""]
    graphics_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".eps"]
    include_only = None
    def remember(name):
        if name not in observed:
            observed[name] = sha256(safe_path(root, name))
        if not any(item["file"] == name for item in result["inputs"]):
            result["inputs"].append({"file": name, "sha256": observed[name]})

    def scan(filename, origin=None, loader=None):
        nonlocal graphics_paths, graphics_extensions, include_only
        if filename in visited and loader in {"usepackage", "RequirePackage", "RequirePackageWithOptions"}:
            return  # LaTeX package loaders do not execute an already loaded package twice.
        if filename in active:
            diagnostic("dependency-cycle", "error", origin[0], origin[1], "Literal dependency cycle: " + " -> ".join(active + [filename]), "Remove the recursive input/class/package dependency")
            return
        if filename in visited:
            diagnostic("repeated-source", "unverified", origin[0], origin[1], f"Source referenced more than once: {filename}", "Inspect repeated execution in the build; static contents are scanned once")
            return
        if len(active) >= 100:
            raise ValueError("Literal dependency nesting exceeds 100 files")
        active.append(filename)
        visited.add(filename)
        if len(visited) > MAX_FILES:
            raise ValueError("Dependency graph exceeds the supported file limit")
        text = source_text(filename)
        remember(filename)
        if filename not in lex_checked:
            lex_checked.add(filename)
            for item in lex_tex(text)[1]:
                diagnostic(item["code"], "unverified", filename, item["line"], item["message"],
                           "Check the literal region in the actual build; later contents may be masked")
        for command in commands(text):
            name, value, line = command["name"], command["value"], command["line"]
            if "citation_issue" in command:
                diagnostic("citation-unverified", "unverified", filename, line, command["citation_issue"] + f": {name}", "Check the actual citation command with its package/backend; the key inventory may be incomplete")
                continue
            if not command["supported"] or "\\" in value or "#" in value:
                diagnostic("dynamic-reference", "unverified", filename, line, f"Dynamic {name} argument: {value}", "Inspect macro expansion in the actual build")
                if name == "graphicspath":
                    graphics_paths = None
                elif name == "DeclareGraphicsExtensions":
                    graphics_extensions = None
                elif name == "includeonly":
                    include_only = None
                continue
            if name == "graphicspath":
                graphics_paths = [""] + re.findall(r"\{([^{}]*)\}", value)
                continue
            if name == "DeclareGraphicsExtensions":
                extensions = [part.strip() for part in value.split(",") if part.strip()]
                if not extensions or any(not re.fullmatch(r"\.[a-zA-Z0-9]+", part) for part in extensions):
                    diagnostic("graphics-extensions", "unverified", filename, line, "Unsupported graphics extension declaration", "Review the actual driver/extension setup")
                    graphics_extensions = None
                else:
                    graphics_extensions = extensions
                continue
            if name == "includeonly":
                include_only = {part.strip() for part in value.split(",") if part.strip()}
                continue
            if name in {"documentclass", "LoadClass", "LoadClassWithOptions", "usepackage", "RequirePackage", "RequirePackageWithOptions", "bibliographystyle"}:
                extension = ".cls" if name in {"documentclass", "LoadClass", "LoadClassWithOptions"} else ".bst" if name == "bibliographystyle" else ".sty"
                if extension == ".sty":
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
                            if extension == ".bst":
                                remember(local_name)
                            else:
                                scan(local_name, (filename, line), name)
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
            if name in CITATION_NAMES:
                for key in value.split(","):
                    key = key.strip()
                    result["citation_inventory"].append({"file": filename, "line": line, "command": name,
                                                         "key": key, "group": command["citation_group"], "starred": command["starred"]})
                    if name != "nocite" or key != "*":
                        citations.append((key, filename, line))
                continue
            if name not in {"input", "include", "includegraphics", "bibliography", "addbibresource"}:
                continue
            for raw in value.split(",") if name == "bibliography" else [value]:
                raw = raw.strip()
                if len(raw) >= 2 and raw.startswith('"') and raw.endswith('"'):
                    raw = raw[1:-1]
                if name == "include" and include_only is not None and raw not in include_only:
                    result["dependencies"].append({"from": filename, "line": line, "command": name, "requested": raw,
                                                   "file": None, "exists": None, "skipped": True, "reason": "Excluded by literal includeonly"})
                    continue
                suffixes = [".tex"] if name in {"input", "include"} else [".bib"]
                bases = [""]
                if name == "includegraphics":
                    if graphics_paths is None or (not Path(raw).suffix and graphics_extensions is None):
                        diagnostic("graphics-search-unverified", "unverified", filename, line, "Graphics search was changed by an unsupported declaration", "Resolve paths/extensions in the actual build")
                        continue
                    suffixes = graphics_extensions
                    bases = graphics_paths
                candidates = []
                try:
                    # Extensions precede search directories, as in the graphics package.
                    for extension in ([""] if Path(raw).suffix else suffixes):
                        for base in bases:
                            relative = (working_prefix / base / (raw + extension)).as_posix()
                            candidates.append(safe_path(root, relative))
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
                    scan(existing.relative_to(root).as_posix(), (filename, line))
                elif name in {"bibliography", "addbibresource"}:
                    bibliography.setdefault(existing.relative_to(root).as_posix(), None)
                else:
                    remember(existing.relative_to(root).as_posix())
        active.pop()
    scan(main)
    known_keys = set()
    key_origins = {}
    for filename in bibliography:
        entries, issues = scan_bibliography(source_text(filename), backend)
        for item in issues:
            diagnostic(item["code"], "unverified", filename, item["line"], item["message"], "Inspect this region with the selected native bibliography backend; no source is repaired or invented")
        for entry in entries:
            result["bibliography_entries"].append({"file": filename, **entry})
            known_keys.add(entry["key"])
            folded = entry["key"].translate(ASCII_FOLD) if backend == "bibtex" else entry["key"]
            previous = key_origins.get(folded)
            if previous:
                diagnostic("duplicate-bib-key", "warning", filename, entry["line"],
                           f"Repeated bibliography key {entry['key']}; first header at {previous['file']}:{previous['line']}",
                           "Choose the intended entry and check backend handling; do not silently merge references")
            else:
                key_origins[folded] = {"file": filename, **entry}
        remember(filename)
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
    finalize_observations()
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
    check.add_argument("--html", type=Path, help="Optional new offline HTML report (.html/.htm)")
    check.add_argument("--html-language", choices=("en", "zh"), default="en")
    check.add_argument("--bundle", type=Path, help="New portable JSON/HTML/integrity directory outside the project; exclusive with --output/--html")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = initialize(args.root, args.main, args.engine, args.backend, args.passes)
        else:
            if args.bundle and (args.output or args.html):
                raise ValueError("Use --bundle alone or separate --output/--html files")
            args.output = args.output.expanduser().absolute() if args.output else None
            args.html = args.html.expanduser().absolute() if args.html else None
            destinations = [path for path in (args.output, args.html) if path is not None]
            if len({path.resolve() for path in destinations}) != len(destinations) or any(path.exists() or path.is_symlink() for path in destinations):
                raise ValueError("Each report needs a distinct new file")
            if args.html and args.html.suffix.lower() not in {".html", ".htm"}:
                raise ValueError("HTML report needs a .html or .htm filename")
            if args.bundle:
                from inspection_bundle import export_inspection
                result = export_inspection(args.root, args.bundle, args.main, args.engine, args.backend, args.html_language)
            else:
                result = inspect_project(args.root, args.main, args.engine, args.backend)
                if args.html:
                    result["html"] = str(args.html)
                from project_report import write_inspection_reports
                write_inspection_reports(args.output, args.html, result, args.html_language)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 1 if result.get("status") == "blocked" else 0
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        print(json.dumps({"schema": 1, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
