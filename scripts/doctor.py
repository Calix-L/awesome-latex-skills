#!/usr/bin/env python3
"""Check local skill prerequisites without installing or compiling anything."""

import argparse
import importlib
import json
import shutil
import sys

from install import SKILLS


def pdf_available():
    for name in ("pymupdf", "fitz"):
        try:
            module = importlib.import_module(name)
            if all(hasattr(module, attr) for attr in ("open", "Document", "VersionBind")):
                return True
        except (ImportError, OSError):
            continue
    return False


def diagnose(skills, engine="pdflatex", backend=None):
    selected = tuple(dict.fromkeys(skills))
    if not selected or any(name not in SKILLS for name in selected):
        raise ValueError("Select one or more known skills")
    if engine not in ("pdflatex", "xelatex", "lualatex"):
        raise ValueError("Unsupported TeX engine")
    if backend not in (None, "bibtex", "biber"):
        raise ValueError("Unsupported bibliography backend")
    checks = [{
        "name": "python", "status": "available" if sys.version_info >= (3, 10) else "missing",
        "required": True, "detail": f"{sys.version_info.major}.{sys.version_info.minor}; Python 3.10+ required",
    }]
    needs_compile = bool(set(selected) & {"latex-rescue", "latex-fmt"})
    if set(selected) & {"latex-rescue", "latex-fmt", "latex-polish", "pdf2tex"}:
        path = shutil.which(engine)
        checks.append({
            "name": engine, "status": "available" if path else "missing", "required": needs_compile,
            "detail": path or "Not found on PATH; local compilation cannot be verified",
        })
        latexmk = shutil.which("latexmk")
        checks.append({
            "name": "latexmk", "status": "available" if latexmk else "missing", "required": False,
            "detail": latexmk or "Optional build helper; manual engine/backend passes remain possible",
        })
    if backend:
        path = shutil.which(backend)
        checks.append({
            "name": backend, "status": "available" if path else "missing", "required": True,
            "detail": path or "Not found on PATH; requested bibliography build cannot run",
        })
    if set(selected) & {"pdf2tex", "paper-read"}:
        present = pdf_available()
        checks.append({
            "name": "pymupdf", "status": "available" if present else "missing", "required": "pdf2tex" in selected,
            "detail": "PyMuPDF imports successfully" if present else "For local PDF extraction: python -m pip install pymupdf",
        })
    if "latex-fmt" in selected:
        checks.append({
            "name": "official-template", "status": "manual", "required": False,
            "detail": "Supply the official kit and verify venue/year/track/stage; this probe cannot certify compliance",
        })
    if "pdf2tex" in selected:
        checks.append({
            "name": "scanned-pdf", "status": "manual", "required": False,
            "detail": "Scanned PDFs need a separate OCR workflow; extraction does not recover exact source",
        })
    return {
        "skills": list(selected), "engine": engine, "backend": backend,
        "local_prerequisites_met": not any(c["required"] and c["status"] == "missing" for c in checks),
        "checks": checks,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", choices=SKILLS, action="append", help="Repeat to select skills; default: all")
    parser.add_argument("--engine", choices=("pdflatex", "xelatex", "lualatex"), default="pdflatex", help="Choose the project's actual engine")
    parser.add_argument("--backend", choices=("bibtex", "biber"), help="Check the project's selected bibliography backend")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable report")
    args = parser.parse_args(argv)
    report = diagnose(args.skill or SKILLS, args.engine, args.backend)
    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print("Local prerequisites: " + ("met" if report["local_prerequisites_met"] else "missing"))
        for check in report["checks"]:
            requirement = "required" if check["required"] else "advisory"
            print(f"[{check['status']}] {check['name']} ({requirement}): {check['detail']}")
        print("No documents were compiled or edited, and no packages were installed.")
    return 0 if report["local_prerequisites_met"] else 1


if __name__ == "__main__":
    sys.exit(main())
