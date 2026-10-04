#!/usr/bin/env python3
"""Verify the complete multi-file English/Chinese manuscript and review bundle."""
import argparse
import json
from pathlib import Path
import shutil
import sys

from project_doctor import inspect_project
from project_report import write_inspection_html
from project_support import ROOT, write_new_json
from review_project import review, snapshot
from verify_artifacts import verify_review
from run_examples import load_helper


def run_paper(output, allow_unverified=False, language="en"):
    if language not in {"en", "zh"}:
        raise ValueError("Review language must be en or zh")
    output = Path(output).expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("Full-paper evidence requires a new output directory")
    tools = {name: shutil.which(name) for name in ("pdflatex", "xelatex", "bibtex")}
    if not all(tools.values()) and not allow_unverified:
        raise ValueError("Full-paper native checks need pdfLaTeX, XeLaTeX and BibTeX; use --allow-unverified explicitly for source review only")
    import pymupdf
    build = load_helper("full_paper_build", "latex-rescue/scripts/check_build.py").build
    fixture = ROOT / "examples/full-paper"
    before, after = output / "before", output / "after"
    original = {side: snapshot(fixture / side) for side in ("before", "after")}
    output.mkdir(parents=True)
    for side in ("before", "after"):
        shutil.copytree(fixture / side, output / side)
    result = {"schema": 1, "kind": "maintainer_full_paper", "status": "verified" if all(tools.values()) else "partial",
              "tools": tools, "builds": {}, "interpretation": "A complete synthetic manuscript project, not a published research paper or measured agent improvement."}
    try:
        for side in ("before", "after"):
            inspection = inspect_project(output / side, "main.tex", "pdflatex", "bibtex")
            write_new_json(output / f"inspection-{side}.json", inspection)
            write_inspection_html(output / f"inspection-{side}.html", inspection, language, json_path=output / f"inspection-{side}.json")
        before_report = after_report = None
        if tools["pdflatex"] and tools["bibtex"]:
            before_result = build(before / "main.tex", output / "build-before", "pdflatex", "bibtex", 3)
            after_result = build(after / "main.tex", output / "build-after", "pdflatex", "bibtex", 3, require_resolved=True)
            before_report, after_report = output / "build-before/build-report.json", output / "build-after/build-report.json"
            result["builds"].update(before=before_result["status"], after=after_result["status"])
            if before_result["status"] != "failed" or after_result["status"] != "success":
                raise ValueError(f"Unexpected full-paper build results: before={before_result['failure']}, after={after_result['failure']}")
            log = (output / "build-after/main.log").read_text(encoding="utf-8", errors="replace")
            if "Overfull \\hbox" in log:
                raise ValueError("Candidate manuscript still has horizontal overflow")
            with pymupdf.open(output / "build-after/main.pdf") as document:
                text = "\n".join(page.get_text() for page in document)
                for value in ("76.10", "78.20", "0.30", "0.40", "0.5", "UNCERTAIN"):
                    if value not in text:
                        raise ValueError(f"Compiled manuscript lost supplied evidence: {value}")
                result["english_pages"] = len(document)
        else:
            result["builds"].update(before="unverified", after="unverified")
        if tools["xelatex"] and tools["bibtex"]:
            chinese = build(after / "main-cn.tex", output / "build-chinese", "xelatex", "bibtex", 3, require_resolved=True)
            result["builds"]["chinese"] = chinese["status"]
            if chinese["status"] != "success":
                raise ValueError(f"Chinese companion failed: {chinese['failure']}")
            with pymupdf.open(output / "build-chinese/main-cn.pdf") as document:
                text = "\n".join(page.get_text() for page in document)
                if "自制样例" not in text or "76.10" not in text:
                    raise ValueError("Compiled Chinese companion lost its supplied text")
                previews = output / "chinese-pages"
                previews.mkdir()
                for index, page in enumerate(document):
                    page.get_pixmap(dpi=120, alpha=False).save(previews / f"page-{index + 1:02}.png")
                result["chinese_pages"] = len(document)
        else:
            result["builds"]["chinese"] = "unverified"
        result["review"] = review(before, after, output / "review", before_report, after_report, fixture / "decisions.md", language)
        result["review_integrity"] = verify_review(output / "review")
        if result["review_integrity"]["status"] != "verified":
            raise ValueError("Generated full-paper review did not pass offline integrity checks")
        if result["review"]["content_flags"]:
            raise ValueError("Unexpected protected number/key/math changes in the candidate")
        result["sources_unchanged"] = all(original[side] == snapshot(fixture / side) == snapshot(output / side) for side in ("before", "after"))
        if not result["sources_unchanged"]:
            raise ValueError("Source manuscript files changed during verification")
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        result.update(status="failed", error=str(exc))
    write_new_json(output / "verification.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-unverified", action="store_true")
    parser.add_argument("--language", choices=("en", "zh"), default="en", help="Inspection and review interface language")
    args = parser.parse_args(argv)
    try:
        result = run_paper(args.output, args.allow_unverified, args.language)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 1 if result["status"] == "failed" else 0
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        print(json.dumps({"schema": 1, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
