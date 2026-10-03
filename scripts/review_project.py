#!/usr/bin/env python3
"""Create an offline source/build/PDF review bundle without changing projects."""
import argparse
from collections import Counter
import difflib
import html
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

from project_doctor import commands, inventory, mask_tex
from project_support import read_json, safe_path, sha256, write_new_json


def snapshot(root):
    files = inventory(root, assets=True)
    return {name: {"sha256": sha256(path), "bytes": path.stat().st_size} for name, path in sorted(files.items())}


def content_tokens(text):
    masked = mask_tex(text)
    numbers = Counter(re.findall(r"(?<![\w])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", masked))
    keys = Counter((command["name"], key.strip()) for command in commands(text)
                   if command["name"] == "label" or command["name"].startswith("cite") or command["name"] in {"ref", "eqref", "cref", "Cref", "pageref", "autoref"}
                   for key in command["value"].split(","))
    math = Counter(re.findall(r"(?<!\\)\$([^$]*)(?<!\\)\$|\\\((.*?)\\\)|\\\[(.*?)\\\]", masked, flags=re.S))
    return numbers, keys, math


def attach_build(path, project, side, bundle):
    if path is None:
        return {"status": "unverified", "reason": "No actual build report supplied", "pages": []}
    path = Path(path).resolve()
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
    if sha256(safe_path(project, relative)) != report.get("source_sha256"):
        raise ValueError(f"{side} build source fingerprint differs from current input")
    for item in report.get("local_inputs", []):
        # Recorder hashes refer to paths relative to the root source's directory.
        name = item.get("path")
        observations = item.get("observations", [])
        if not isinstance(name, str) or not isinstance(observations, list) or not observations or any(not isinstance(row, dict) or not isinstance(row.get("sha256"), str) or row.get("error") for row in observations):
            raise ValueError("Build input evidence needs literal paths and SHA-256 hashes")
        actual = safe_path(source.parent, name)
        if any(sha256(actual) != row["sha256"] for row in observations):
            raise ValueError(f"{side} recorded input changed: {name}")
    evidence = bundle / "evidence" / side
    evidence.mkdir(parents=True)
    shutil.copyfile(path, evidence / "build-report.json")
    copied = set()
    for step in report.get("steps", []):
        for field in ("transcript", "log", "recorder"):
            name = step.get(field)
            if name and name not in copied:
                original = safe_path(path.parent, name)
                if original.is_file():
                    target = safe_path(evidence, name)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(original, target)
                    copied.add(name)
    result = {"status": report["status"], "source": relative, "source_sha256": report["source_sha256"],
              "evidence": f"evidence/{side}/build-report.json", "engine": report.get("engine"), "backend": report.get("backend"),
              "failure": report.get("failure"), "unresolved_references": report.get("unresolved_references"),
              "diagnostics": report.get("diagnostics", []), "pages": []}
    # A failed build's PDF is not presented as a successful comparison.
    if report["status"] == "success":
        tracking = report.get("input_tracking", {})
        if not isinstance(tracking, dict) or report.get("source_unchanged") is not True or tracking.get("changed"):
            raise ValueError("Successful build evidence did not retain stable source inputs")
        pdf = safe_path(path.parent, report.get("pdf"))
        if not pdf.is_file():
            raise ValueError("Successful report lacks its actual PDF")
        with pdf.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                raise ValueError("Successful report lacks a PDF header")
        if report.get("pdf_sha256") and sha256(pdf) != report["pdf_sha256"]:
            raise ValueError("Build PDF changed after evidence was recorded")
        result["pdf_binding"] = "fingerprint-matched" if report.get("pdf_sha256") else "unverified-legacy-report"
        import pymupdf
        shutil.copyfile(pdf, evidence / "document.pdf")
        result["pdf"] = f"evidence/{side}/document.pdf"
        result["pdf_sha256"] = sha256(pdf)
        with pymupdf.open(pdf) as document:
            if len(document) > 100:
                raise ValueError("Review previews are limited to 100 pages per side")
            pages = evidence / "pages"
            pages.mkdir()
            for number, page in enumerate(document):
                if page.rect.width * page.rect.height * (120 / 72) ** 2 > 20_000_000:
                    raise ValueError("PDF page preview exceeds 20 million pixels")
                filename = f"page-{number + 1:04}.png"
                page.get_pixmap(dpi=120, colorspace=pymupdf.csRGB, alpha=False).save(pages / filename)
                result["pages"].append(f"evidence/{side}/pages/{filename}")
    return result


def render(bundle, report, diffs):
    esc = lambda value: html.escape(str(value), quote=True)
    content = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
               '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\' data:; style-src \'unsafe-inline\'">',
               '<title>Manuscript change review</title><style>',
               'body{margin:0;background:#f4f3ed;color:#263027;font:16px/1.65 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:36px 24px}h1{font-size:38px;line-height:1.2}h2{margin-top:38px}small{color:#586555}section,details{background:#fffefa;border:1px solid #d5dacd;border-radius:12px;padding:20px;margin:16px 0}pre{overflow:auto;font:13px/1.5 ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere}a{color:#326041}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}.pair img{width:100%;border:1px solid #ddd}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:9px;border-bottom:1px solid #ddd}summary{cursor:pointer;font-weight:600}.pill{border:1px solid #bac5b3;border-radius:20px;padding:3px 12px} @media(max-width:700px){.pair{grid-template-columns:1fr}h1{font-size:28px}} @media(prefers-color-scheme:dark){body{background:#171c18;color:#e0e7da}section,details{background:#212a22;border-color:#40523f}a{color:#b2d9a6}small{color:#b6c2b0}}',
               '</style></head><body><main><small>MANUSCRIPT TOOLKIT / REVIEWABLE CHANGES</small><h1>Manuscript change review</h1>',
               '<p><span class="pill">Human content review required</span></p><p>Actual source snapshots, supplied build evidence and page previews. Literal preservation checks do not certify scientific fidelity.</p>',
               '<p><a href="review.json">JSON evidence</a> · <a href="changes.diff">Source diff</a></p><h2>Build evidence</h2><div class="pair">']
    for side in ("before", "after"):
        build = report["builds"][side]
        content.append(f'<section><h3>{side.title()}: {esc(build["status"])}</h3>')
        if build.get("evidence"):
            content.append(f'<a href="{esc(build["evidence"])}">Build report &amp; retained logs</a>')
        if build.get("pdf"):
            content.append(f' · <a href="{esc(build["pdf"])}">PDF</a>')
        if build.get("pdf_binding") == "unverified-legacy-report":
            content.append('<p>Legacy report: the original build did not record a PDF fingerprint. The current PDF is retained, but its identity at build time is unverified.</p>')
        content.append(f'<pre>{esc(build.get("failure") or build.get("reason") or "Inspect warnings and the PDF separately.")}</pre></section>')
    content.append('</div><h2>Content audit and author decisions</h2><p>Changed numbers, citation keys and simple math are review signals, not judgments of correctness.</p><pre>')
    content.append(esc(json.dumps(report["content_audit"], ensure_ascii=False, indent=2)) + '</pre>')
    content.append('<pre>' + esc(json.dumps(report["author_decisions"], ensure_ascii=False, indent=2)) + '</pre>')
    if report["notes"]:
        content.append('<section><h3>Supplied notes</h3><pre>' + esc(report["notes"]) + '</pre></section>')
    content.append('<h2>Source changes</h2>')
    for name, diff in diffs.items():
        content.append(f'<details><summary>{esc(name)}</summary><pre>{esc(diff)}</pre></details>')
    content.append('<h2>PDF pages</h2>')
    before, after = report["builds"]["before"]["pages"], report["builds"]["after"]["pages"]
    for index in range(max(len(before), len(after))):
        content.append(f'<section><h3>Page {index + 1}</h3><div class="pair">')
        for label, pages in (("Before", before), ("After", after)):
            content.append(f'<div><h4>{label}</h4>')
            content.append(f'<img loading="lazy" src="{esc(pages[index])}" alt="{label} page {index + 1}">' if index < len(pages) else '<p>No supplied verified page.</p>')
            content.append('</div>')
        content.append('</div></section>')
    content.append('<p><small>Page numbers align by index only. Pagination changes need manual comparison. Keep this folder together for offline use.</small></p></main></body></html>')
    (bundle / "report.html").write_text("".join(content), encoding="utf-8")


def review(before, after, output, before_build=None, after_build=None, notes=None):
    before, after = Path(before).resolve(), Path(after).resolve()
    output = Path(output).expanduser().absolute()
    if before == after:
        raise ValueError("Before and after must be distinct project directories")
    if output.exists() or output.is_symlink() or any(output.resolve().is_relative_to(root) for root in (before, after)):
        raise ValueError("Review output must be new and outside both project trees")
    original, candidate = snapshot(before), snapshot(after)
    notes_text = Path(notes).read_text(encoding="utf-8") if notes else None
    report = {"schema": 1, "kind": "project_review", "before": {"root": str(before), "files": original},
              "after": {"root": str(after), "files": candidate}, "builds": {}, "changes": [],
              "content_audit": [], "author_decisions": [], "notes": notes_text,
              "interpretation": "Build success, literal invariants and scientific fidelity are distinct. No AI quality score or venue compliance is inferred."}
    diffs = {}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".review-", dir=output.parent) as temporary:
        bundle = Path(temporary) / "review"
        bundle.mkdir()
        for name in sorted(set(original) | set(candidate)):
            if original.get(name) == candidate.get(name):
                continue
            kind = "added" if name not in original else "removed" if name not in candidate else "modified"
            report["changes"].append({"file": name, "kind": kind})
            if Path(name).suffix.lower() not in {".tex", ".bib", ".sty", ".cls", ".bst", ".json"}:
                continue
            old = safe_path(before, name).read_text(encoding="utf-8") if name in original else ""
            new = safe_path(after, name).read_text(encoding="utf-8") if name in candidate else ""
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
            if Path(name).suffix == ".tex":
                for number, line in enumerate(safe_path(after, name).read_text(encoding="utf-8").splitlines(), 1):
                    if "[UNCERTAIN" in line or re.search(r"\bTODO\b", line):
                        report["author_decisions"].append({"file": name, "line": number, "excerpt": line.strip(), "status": "open"})
        report["builds"]["before"] = attach_build(before_build, before, "before", bundle)
        report["builds"]["after"] = attach_build(after_build, after, "after", bundle)
        (bundle / "changes.diff").write_text("".join(diffs.values()), encoding="utf-8")
        if original != snapshot(before) or candidate != snapshot(after):
            raise ValueError("Project inputs changed during review preparation")
        write_new_json(bundle / "review.json", report)
        render(bundle, report, diffs)
        if output.exists() or output.is_symlink():
            raise ValueError("Review output appeared during publication")
        bundle.rename(output)
    return {"schema": 1, "status": "ready-for-review", "output": str(output), "report": str(output / "report.html"),
            "changed_files": len(report["changes"]), "content_flags": len(report["content_audit"]),
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
    args = parser.parse_args(argv)
    try:
        result = review(args.before, args.after, args.output, args.before_build, args.after_build, args.notes)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, UnicodeError, ImportError, RuntimeError) as exc:
        print(json.dumps({"schema": 1, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
