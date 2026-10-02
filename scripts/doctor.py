#!/usr/bin/env python3
"""Check local skill prerequisites without installing or compiling anything."""

import argparse
import importlib
import json
import re
import shutil
import sys

from install import SKILLS


def pdf_probe():
    check = {"name": "pymupdf", "status": "missing", "reason": None,
             "version": None, "module_path": None, "detail": "", "next_action": None}
    install_hint = 'Use the reported Python executable with: -m pip install "PyMuPDF>=1.24.10,<2"'
    try:
        module = importlib.import_module("pymupdf")
    except ModuleNotFoundError as exc:
        if exc.name == "pymupdf":
            check.update(reason="missing_module", detail="PyMuPDF is not installed in this Python", next_action=install_hint)
        else:
            check.update(status="broken", reason="import_failed", detail=f"PyMuPDF import failed: {exc}",
                         next_action="Inspect the missing dependency in this Python environment before reinstalling")
    except (ImportError, OSError) as exc:
        check.update(status="broken", reason="import_failed", detail=f"PyMuPDF import failed: {exc}",
                     next_action="Inspect the import/DLL error and the reported Python environment")
    else:
        check["module_path"] = str(module.__file__) if getattr(module, "__file__", None) else None
        if not all(hasattr(module, attr) for attr in ("open", "Document", "VersionBind")):
            check.update(status="broken", reason="wrong_module", detail="Imported pymupdf does not expose the expected PyMuPDF API",
                         next_action="Check the module path for a shadowing local file or unrelated package")
        else:
            check["version"] = str(module.VersionBind)
            version = re.match(r"^(\d+)\.(\d+)\.(\d+)", check["version"])
            if not version:
                check.update(status="unsupported", reason="unknown_version", detail=f"Cannot verify PyMuPDF version {check['version']!r}",
                             next_action=install_hint)
            elif not (1, 24, 10) <= tuple(map(int, version.groups())) < (2, 0, 0):
                check.update(status="unsupported", reason="unsupported_version", detail=f"PyMuPDF {check['version']} is outside the helper's supported range >=1.24.10,<2",
                             next_action=install_hint)
            else:
                check.update(status="available", detail=f"PyMuPDF {check['version']} imports successfully")
    return check


def pdf_available():
    return pdf_probe()["status"] == "available"


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
        check = pdf_probe()
        check["required"] = "pdf2tex" in selected
        checks.append(check)
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
        "schema": 1, "skills": list(selected), "engine": engine, "backend": backend,
        "python": {"executable": sys.executable, "version": sys.version.split()[0]},
        "local_prerequisites_met": not any(c["required"] and c["status"] != "available" for c in checks),
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
        print("Local prerequisites: " + ("met" if report["local_prerequisites_met"] else "not met"))
        print(f"Python {report['python']['version']}: {report['python']['executable']}")
        for check in report["checks"]:
            requirement = "required" if check["required"] else "advisory"
            print(f"[{check['status']}] {check['name']} ({requirement}): {check['detail']}")
            if check.get("module_path"):
                print(f"  Module: {check['module_path']}")
            if check.get("next_action"):
                print(f"  Next: {check['next_action']}")
        print("No documents were compiled or edited, and no packages were installed.")
    return 0 if report["local_prerequisites_met"] else 1


if __name__ == "__main__":
    sys.exit(main())
