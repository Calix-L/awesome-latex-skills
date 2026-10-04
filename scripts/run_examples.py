#!/usr/bin/env python3
"""Run the five worked examples and retain actual build/extraction evidence."""
import argparse
import difflib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

from evaluate import score
from install import SKILLS
from project_support import ROOT, read_json, safe_path, sha256, write_new_json


def load_helper(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def catalog(root=ROOT, document=None):
    root = Path(root).resolve()
    document = read_json(root / "examples/index.json") if document is None else document
    if document.get("schema") != 1 or not isinstance(document.get("examples"), list) or len(document["examples"]) != 5:
        raise ValueError("Expected five schema-1 worked examples")
    identifiers, skills = set(), set()
    for item in document["examples"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"] or item["id"] in identifiers:
            raise ValueError("Example ids must be nonempty and unique")
        safe_path(root, item["id"])
        if "/" in item["id"] or item.get("skill") not in SKILLS or item["skill"] in skills:
            raise ValueError("Expected one portable example id per skill")
        identifiers.add(item["id"])
        skills.add(item["skill"])
        directory = safe_path(root, item["directory"])
        for name in (item["input"], item["candidate"], "report.md"):
            if not safe_path(directory, name).is_file():
                raise ValueError(f"Missing example artifact: {item['id']}/{name}")
    return document["examples"]


def run_examples(output, engine="pdflatex", allow_unverified=False):
    examples = catalog()
    native = shutil.which(engine)
    # Extraction is required even in explicit portable mode.
    import pymupdf
    if native is None and not allow_unverified:
        raise ValueError(f"{engine} is missing; use --allow-unverified for extraction/literal checks only")
    output = Path(output).expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("Worked examples require a new output directory")
    build = load_helper("example_build", "latex-rescue/scripts/check_build.py").build
    extract = load_helper("example_extract", "pdf2tex/scripts/extract_pdf.py").extract
    output.mkdir(parents=True)
    result = {"schema": 1, "kind": "maintainer_examples", "engine": engine,
              "status": "verified" if native else "partial", "examples": [],
              "interpretation": "Maintainer-authored synthetic cases. Native checks and literal checks do not establish agent improvement or scientific fidelity."}
    for example in examples:
        item = {"id": example["id"], "skill": example["skill"], "status": "verified" if native else "partial",
                "builds": {}, "extraction": None, "human_review": "required"}
        result["examples"].append(item)
        folder = safe_path(output, example["id"])
        folder.mkdir()
        source = safe_path(ROOT, example["directory"])
        names = (example["input"], example["candidate"], "report.md")
        hashes = {name: sha256(source / name) for name in names}
        for name in names:
            shutil.copyfile(source / name, folder / name)
        item["source_sha256"] = hashes
        try:
            audit = score(example["case_id"], folder, kind="maintainer_candidate")
            write_new_json(folder / "invariants.json", audit)
            item["automatic"] = audit["automatic"]
            if audit["automatic"]["passed"] != audit["automatic"]["total"]:
                raise ValueError("Candidate failed a protected literal invariant")
            if example["input"].endswith(".tex"):
                before = (folder / example["input"]).read_text(encoding="utf-8").splitlines(keepends=True)
                after = (folder / example["candidate"]).read_text(encoding="utf-8").splitlines(keepends=True)
                (folder / "changes.diff").write_text("".join(difflib.unified_diff(before, after, fromfile="input.tex", tofile="output.tex")), encoding="utf-8")
            if example["skill"] == "pdf2tex":
                extracted = extract(folder / example["input"], folder / "extraction", None, True, True, 120, True)
                item["extraction"] = {"pages": len(extracted["pages"]), "source_sha256": extracted["source_sha256"],
                                      "evidence": "extraction/layout.json", "review": "extraction/report.html"}
                if len(extracted["pages"]) != 2 or sha256(folder / example["input"]) != extracted["source_sha256"]:
                    raise ValueError("PDF extraction did not cover the recorded two-page input")
            tex_names = [name for name in names if name.endswith(".tex")]
            if native:
                for name in tex_names:
                    report = build(folder / name, folder / f"build-{Path(name).stem}", engine=engine)
                    expected = "failed" if example["skill"] == "latex-rescue" and name == example["input"] else "success"
                    item["builds"][name] = {"status": report["status"], "expected": expected,
                                           "evidence": f"build-{Path(name).stem}/build-report.json"}
                    if report["status"] != expected:
                        raise ValueError(f"Unexpected native build status for {name}: {report['failure']}")
                    if report["status"] == "success":
                        pdf = folder / f"build-{Path(name).stem}" / report["pdf"]
                        with pymupdf.open(pdf) as document:
                            previews = folder / f"preview-{Path(name).stem}"
                            previews.mkdir()
                            for number, page in enumerate(document):
                                page.get_pixmap(dpi=120, alpha=False).save(previews / f"page-{number + 1:02}.png")
                if example["skill"] == "latex-rescue":
                    strict = build(folder / example["candidate"], folder / "strict-references", engine=engine, require_resolved=True)
                    if strict["status"] != "failed" or not strict["unresolved_references"]:
                        raise ValueError("Unknown keys must remain explicitly unresolved in the strict check")
                    item["strict_references"] = {"status": strict["status"], "expected": "failed", "evidence": "strict-references/build-report.json"}
                if example["skill"] == "latex-fmt":
                    logs = [(folder / f"build-{Path(name).stem}" / f"{Path(name).stem}.log").read_text(encoding="utf-8", errors="replace") for name in tex_names]
                    if "Overfull \\hbox" not in logs[0] or "Overfull \\hbox" in logs[1]:
                        raise ValueError("The layout case must expose and resolve the local-width overflow")
                    item["overflow"] = {"input": True, "candidate": False}
            else:
                item["builds"] = {name: {"status": "unverified", "reason": f"{engine} missing"} for name in tex_names}
            item["inputs_unchanged"] = hashes == {name: sha256(folder / name) for name in names} == {name: sha256(source / name) for name in names}
            if not item["inputs_unchanged"]:
                raise ValueError("An example artifact changed during verification")
            if not tex_names:
                item["status"] = "verified"  # reading artifact invariants; human review stays required
        except (OSError, ValueError, RuntimeError) as exc:
            item.update(status="failed", error=str(exc))
            result["status"] = "failed"
        write_new_json(folder / "verification.json", item)
    write_new_json(output / "verification.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    from export_examples import EXPORT_CASES
    export = commands.add_parser("export", help="Copy a synthetic case with an offline guide and source fingerprints; no build or extraction")
    export.add_argument("--case", choices=EXPORT_CASES, default="full-paper")
    export.add_argument("--output", type=Path, required=True, help="New directory outside bundled source resources")
    export.add_argument("--language", choices=("en", "zh"), default="en")
    run = commands.add_parser("run")
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--engine", choices=("pdflatex", "xelatex", "lualatex"), default="pdflatex")
    run.add_argument("--allow-unverified", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            result = {"schema": 1, "examples": catalog(), "export_cases": list(EXPORT_CASES)}
        elif args.command == "export":
            from export_examples import export_example
            result = export_example(args.case, args.output, args.language)
        else:
            result = run_examples(args.output, args.engine, args.allow_unverified)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 1 if result.get("status") == "failed" else 0
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        print(json.dumps({"schema": 1, "error": str(exc)}) if args.json else f"Examples: {exc}", file=sys.stdout if args.json else sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
