#!/usr/bin/env python3
"""Create an offline source/build/PDF review bundle without changing projects."""
import argparse
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

from project_doctor import commands, inventory, mask_tex, read_source, GENERATED, SOURCE_SUFFIXES, ASSET_SUFFIXES
from tex_lexer import lex_tex
from project_support import read_json, safe_path, sha256, write_new_json
from review_report import review_html
from artifact_integrity import seal_review


def snapshot(root):
    files = inventory(root, assets=True)
    return {name: {"sha256": sha256(path), "bytes": path.stat().st_size} for name, path in sorted(files.items())}


def content_tokens(text):
    masked = mask_tex(text)
    numbers = Counter(re.findall(r"(?<![\w])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", masked))
    keys = Counter((command["name"], key.strip()) for command in commands(text)
                   if command["supported"] and (command["name"] == "label" or command["name"].startswith("cite") or command["name"] in {"nocite", "ref", "eqref", "cref", "Cref", "pageref", "autoref"})
                   for key in command["value"].split(","))
    math = Counter(simple_math(masked))
    return numbers, keys, math


def simple_math(text):
    """Literal delimited math only; escaped delimiters retain their source meaning."""
    delimiter = re.compile(r"\$\$?|\\[()\[\]]")
    opened = None
    pairs = {"$": "$", "$$": "$$", r"\(": r"\)", r"\[": r"\]"}
    offset = 0
    while (match := delimiter.search(text, offset)) is not None:
        position = match.start()
        offset = match.end()
        slashes = 0
        cursor = position - 1
        while cursor >= 0 and text[cursor] == "\\":
            slashes += 1
            cursor -= 1
        if slashes % 2:
            # In \$$x$, only the first dollar is escaped; the second opens math.
            if match.group() == "$$":
                offset = position + 1
            continue
        token = match.group()
        if opened is None:
            if token in pairs:
                opened = (token, match.end())
        elif token == pairs[opened[0]]:
            yield (opened[0], text[opened[1]:position])
            opened = None


def retain_file(original, target, bundle, bindings, expected=None, origin_root=None):
    """Bind the copied bytes and recheck originals immediately and at publication."""
    digest = expected or sha256(original)
    if target.exists():
        raise ValueError(f"Retained evidence path collision: {target.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(original, target)
    if sha256(target) != digest or sha256(original) != digest:
        raise ValueError(f"Build evidence changed during retention: {original.name}")
    origin_root = original.parent if origin_root is None else origin_root
    bindings.append((origin_root, original.relative_to(origin_root).as_posix(), target, digest))
    return {"file": target.relative_to(bundle).as_posix(), "sha256": digest, "bytes": target.stat().st_size}


def attach_build(path, project, side, bundle, bindings=None):
    bindings = [] if bindings is None else bindings
    if path is None:
        return {"status": "unverified", "reason": "No actual build report supplied", "pages": []}
    path = Path(path).resolve()
    report_hash = sha256(path)
    report = read_json(path)
    if report.get("schema") != 3 or report.get("status") not in {"success", "failed"}:
        raise ValueError("Expected an actual schema-3 build report")
    if any(not isinstance(report.get(field), list) or any(not isinstance(item, dict) for item in report[field]) for field in ("steps", "local_inputs")):
        raise ValueError("Build report needs structured steps and local input evidence")
    source = Path(report.get("source", "")).resolve()
    project = Path(project).resolve()
    if not source.is_relative_to(project):
        raise ValueError(f"{side} build source is outside its project")
    relative = source.relative_to(project).as_posix()
    source_path = safe_path(project, relative)
    if sha256(source_path) != report.get("source_sha256"):
        raise ValueError(f"{side} build source fingerprint differs from current input")
    bindings.append((project, relative, None, report["source_sha256"]))
    for item in report.get("local_inputs", []):
        # Recorder hashes refer to paths relative to the root source's directory.
        name = item.get("path")
        observations = item.get("observations", [])
        if not isinstance(name, str) or not isinstance(observations, list) or not observations or any(not isinstance(row, dict) or not isinstance(row.get("sha256"), str) or row.get("error") for row in observations):
            raise ValueError("Build input evidence needs literal paths and SHA-256 hashes")
        actual = safe_path(source.parent, name)
        if any(sha256(actual) != row["sha256"] for row in observations):
            raise ValueError(f"{side} recorded input changed: {name}")
        bindings.append((source.parent, name, None, observations[0]["sha256"]))
    evidence = bundle / "evidence" / side
    evidence.mkdir(parents=True)
    retained = [retain_file(path, evidence / "build-report.json", bundle, bindings, report_hash)]
    copied = set()
    for step in report.get("steps", []):
        for field in ("transcript", "log", "recorder"):
            name = step.get(field)
            if name and name not in copied:
                original = safe_path(path.parent, name)
                if not original.is_file():
                    raise ValueError(f"{side} declared build evidence is missing: {name}")
                target = safe_path(evidence, name)
                retained.append(retain_file(original, target, bundle, bindings, origin_root=path.parent))
                copied.add(name)
    result = {"status": report["status"], "source": relative, "source_sha256": report["source_sha256"],
              "evidence": f"evidence/{side}/build-report.json", "engine": report.get("engine"), "backend": report.get("backend"),
              "failure": report.get("failure"), "unresolved_references": report.get("unresolved_references"),
              "diagnostics": report.get("diagnostics", []), "pages": [], "retained_files": retained}
    # A failed build's PDF is not presented as a successful comparison.
    if report["status"] == "success":
        tracking = report.get("input_tracking", {})
        if not isinstance(tracking, dict) or report.get("source_unchanged") is not True or tracking.get("changed") or tracking.get("unreadable"):
            raise ValueError("Successful build evidence did not retain stable source inputs")
        pdf = safe_path(path.parent, report.get("pdf"))
        if not pdf.is_file():
            raise ValueError("Successful report lacks its actual PDF")
        with pdf.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                raise ValueError("Successful report lacks a PDF header")
        pdf_hash = sha256(pdf)
        if report.get("pdf_sha256") and pdf_hash != report["pdf_sha256"]:
            raise ValueError("Build PDF changed after evidence was recorded")
        result["pdf_binding"] = "fingerprint-matched" if report.get("pdf_sha256") else "unverified-legacy-report"
        import pymupdf
        retained.append(retain_file(pdf, evidence / "document.pdf", bundle, bindings, pdf_hash))
        result["pdf"] = f"evidence/{side}/document.pdf"
        result["pdf_sha256"] = sha256(pdf)
        with pymupdf.open(evidence / "document.pdf") as document:
            if len(document) > 100:
                raise ValueError("Review previews are limited to 100 pages per side")
            pages = evidence / "pages"
            pages.mkdir()
            for number, page in enumerate(document):
                if page.rect.width * page.rect.height * (120 / 72) ** 2 > 20_000_000:
                    raise ValueError("PDF page preview exceeds 20 million pixels")
                filename = f"page-{number + 1:04}.png"
                image = pages / filename
                page.get_pixmap(dpi=120, colorspace=pymupdf.csRGB, alpha=False).save(image)
                image_hash = sha256(image)
                retained.append({"file": image.relative_to(bundle).as_posix(), "sha256": image_hash, "bytes": image.stat().st_size})
                bindings.append((pages, filename, None, image_hash))
                result["pages"].append(f"evidence/{side}/pages/{filename}")
    return result


def render(bundle, report, diffs):
    (bundle / "report.html").write_text(review_html(report, diffs, report.get("language", "en")), encoding="utf-8")


def review(before, after, output, before_build=None, after_build=None, notes=None, language="en"):
    if language not in {"en", "zh"}:
        raise ValueError("Review language must be en or zh")
    before, after = Path(before).expanduser().resolve(), Path(after).expanduser().resolve()
    output = Path(output).expanduser().absolute()
    if before == after:
        raise ValueError("Before and after must be distinct project directories")
    if output.exists() or output.is_symlink() or any(output.resolve().is_relative_to(root) for root in (before, after)):
        raise ValueError("Review output must be new and outside both project trees")
    output = output.resolve()
    original, candidate = snapshot(before), snapshot(after)
    notes_text = Path(notes).expanduser().read_text(encoding="utf-8-sig") if notes else None
    report = {"schema": 1, "kind": "project_review", "before": {"root": str(before), "files": original},
              "after": {"root": str(after), "files": candidate}, "builds": {}, "changes": [],
              "content_audit": [], "source_scan_issues": [], "author_decisions": [], "notes": notes_text, "language": language,
              "inventory_scope": {"extensions": sorted(SOURCE_SUFFIXES | ASSET_SUFFIXES), "configuration": ".als.json",
                                  "excluded_directories": sorted(GENERATED), "other_files": "not inspected"},
              "interpretation": "Build success, literal invariants and scientific fidelity are distinct. No AI quality score or venue compliance is inferred."}
    diffs = {}
    bindings = []
    parsed = {}
    def source_text(root, name, files):
        if name not in files:
            return ""
        key = (root, name)
        if key not in parsed:
            data = read_source(safe_path(root, name))
            if hashlib.sha256(data).hexdigest() != files[name]["sha256"]:
                raise ValueError(f"Project inputs changed before parsing: {name}")
            parsed[key] = data.decode("utf-8-sig")
        return parsed[key]
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".review-", dir=output.parent) as temporary:
        bundle = (Path(temporary) / "review").resolve()
        bundle.mkdir()
        for side, root, files in (("before", before, original), ("after", after, candidate)):
            for name in sorted(files):
                if Path(name).suffix.lower() in {".tex", ".cls", ".sty"}:
                    for item in lex_tex(source_text(root, name, files))[1]:
                        report["source_scan_issues"].append({"side": side, "file": name, **item})
        for name in sorted(set(original) | set(candidate)):
            if original.get(name) == candidate.get(name):
                continue
            kind = "added" if name not in original else "removed" if name not in candidate else "modified"
            report["changes"].append({"file": name, "kind": kind})
            if Path(name).suffix.lower() not in {".tex", ".bib", ".sty", ".cls", ".bst", ".json"}:
                continue
            old = source_text(before, name, original)
            new = source_text(after, name, candidate)
            diffs[name] = "".join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True), fromfile=f"before/{name}", tofile=f"after/{name}"))
            if Path(name).suffix.lower() == ".json":
                continue
            prior, later = content_tokens(old), content_tokens(new)
            changes = {}
            for label, a, b in zip(("numbers", "reference_keys", "simple_math"), prior, later):
                if a != b:
                    changes[label] = {"removed": [[str(key), count] for key, count in (a - b).items()],
                                      "added": [[str(key), count] for key, count in (b - a).items()]}
            if changes:
                report["content_audit"].append({"file": name, "requires_review": True, **changes})
        for name in candidate:
            if Path(name).suffix.lower() == ".tex":
                for number, line in enumerate(source_text(after, name, candidate).splitlines(), 1):
                    if "[UNCERTAIN" in line or re.search(r"\bTODO\b", line):
                        report["author_decisions"].append({"file": name, "line": number, "excerpt": line.strip(), "status": "open"})
        report["builds"]["before"] = attach_build(before_build, before, "before", bundle, bindings)
        report["builds"]["after"] = attach_build(after_build, after, "after", bundle, bindings)
        (bundle / "changes.diff").write_text("".join(diffs.values()), encoding="utf-8")
        write_new_json(bundle / "review.json", report)
        render(bundle, report, diffs)
        if original != snapshot(before) or candidate != snapshot(after):
            raise ValueError("Project inputs changed during review preparation")
        for root, name, retained, digest in bindings:
            if sha256(safe_path(root, name)) != digest or retained is not None and sha256(retained) != digest:
                raise ValueError(f"Build evidence changed before review publication: {name}")
        seal_review(bundle)
        if output.exists() or output.is_symlink():
            raise ValueError("Review output appeared during publication")
        bundle.rename(output)
    return {"schema": 1, "status": "ready-for-review", "output": str(output), "report": str(output / "report.html"),
            "integrity": str(output / "integrity.json"),
            "changed_files": len(report["changes"]), "content_flags": len(report["content_audit"]),
            "source_scan_issues": len(report["source_scan_issues"]),
            "open_decisions": len(report["author_decisions"]), "builds": {side: item["status"] for side, item in report["builds"].items()}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--before-build", type=Path)
    parser.add_argument("--after-build", type=Path)
    parser.add_argument("--notes", type=Path)
    parser.add_argument("--language", choices=("en", "zh"), default="en", help="Offline report interface language; source evidence is unchanged")
    args = parser.parse_args(argv)
    try:
        result = review(args.before, args.after, args.output, args.before_build, args.after_build, args.notes, args.language)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, UnicodeError, ImportError, RuntimeError) as exc:
        print(json.dumps({"schema": 1, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
