#!/usr/bin/env python3
"""Check local skill prerequisites without installing or compiling anything."""

import argparse
import importlib
import json
from pathlib import Path
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
    if engine not in (None, "pdflatex", "xelatex", "lualatex"):
        raise ValueError("Unsupported TeX engine")
    if backend not in (None, "bibtex", "biber"):
        raise ValueError("Unsupported bibliography backend")
    checks = [{
        "name": "python", "status": "available" if sys.version_info >= (3, 10) else "missing",
        "required": True, "detail": f"{sys.version_info.major}.{sys.version_info.minor}; Python 3.10+ required",
    }]
    needs_compile = bool(set(selected) & {"latex-rescue", "latex-fmt"})
    if set(selected) & {"latex-rescue", "latex-fmt", "latex-polish", "pdf2tex"}:
        if engine is None:
            checks.append({"name": "engine-selection", "status": "manual", "required": needs_compile,
                           "detail": "No engine selected; no compiler was guessed or probed",
                           "next_action": "Select --engine or save the actual engine with project init"})
        else:
            path = shutil.which(engine)
            checks.append({
                "name": engine, "status": "available" if path else "missing", "required": needs_compile,
                "detail": path or "Not found on PATH; local compilation cannot be verified",
                "next_action": None if path else "Use an existing TeX installation and expose this engine on PATH",
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
            "next_action": None if path else "Expose the project's actual bibliography backend on PATH",
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


def diagnose_project(root, skills, main=None, engine=None, backend=None):
    """Read the selected project; preserve unresolved settings and inspection evidence."""
    from project_doctor import inspect_project
    project = inspect_project(root, main, engine, backend)
    report = diagnose(skills, project["engine"], project["backend"])
    if project["backend"] is None and any(item["command"] in {"bibliography", "addbibresource"} for item in project["dependencies"]):
        report["checks"].append({"name": "backend-selection", "status": "manual",
                                 "required": bool(set(report["skills"]) & {"latex-rescue", "latex-fmt"}),
                                 "detail": "Literal bibliography resources found, but no backend selected",
                                 "next_action": "Select --backend bibtex or --backend biber from the actual project setup"})
        report["local_prerequisites_met"] = not any(c["required"] and c["status"] != "available" for c in report["checks"])
    report["project"] = project
    if not report["local_prerequisites_met"] or project["status"] == "blocked":
        report["status"] = "blocked"
    elif project["status"] == "needs-review" or any(c["status"] == "manual" for c in report["checks"]):
        report["status"] = "needs-review"
    else:
        report["status"] = "ready"
    return report


def next_action_zh(check):
    """Translate actionable probe guidance; retain native import details verbatim."""
    name, reason = check["name"], check.get("reason")
    if name == "pymupdf":
        if reason == "wrong_module":
            return "检查模块路径，排除本地同名文件或错误的包。"
        if reason == "import_failed":
            return "在报告所列的 Python 环境中检查导入错误、依赖或 DLL。"
        return '使用报告所列的 Python 执行：-m pip install "PyMuPDF>=1.24.10,<2"'
    if name == "engine-selection":
        return "用 --engine 选择实际引擎，或用 project init 保存项目设置。"
    if name == "backend-selection":
        return "根据实际项目设置选择 --backend bibtex 或 --backend biber。"
    if name in {"pdflatex", "xelatex", "lualatex"}:
        return "使用已有的 TeX 安装，并将所选引擎加入 PATH。"
    if name in {"bibtex", "biber"}:
        return "将项目实际使用的参考文献后端加入 PATH。"
    return check.get("next_action", "")


def print_report(report, language="en"):
    zh = language == "zh"
    states = {"available": "可用", "missing": "缺失", "broken": "导入失败", "unsupported": "版本不支持",
              "manual": "需人工确认", "ready": "检查通过", "blocked": "受阻", "needs-review": "需审查"}
    print(("本地依赖：" if zh else "Local prerequisites: ") +
          (("满足" if zh else "met") if report["local_prerequisites_met"] else ("未满足" if zh else "not met")))
    print(f"Python {report['python']['version']}: {report['python']['executable']}")
    for check in report["checks"]:
        requirement = ("必需" if zh else "required") if check["required"] else ("建议" if zh else "advisory")
        print(f"[{states.get(check['status'], check['status']) if zh else check['status']}] {check['name']} ({requirement}): {check['detail']}")
        if check.get("module_path"):
            print(f"  {'模块' if zh else 'Module'}: {check['module_path']}")
        if check.get("next_action"):
            print(f"  {'下一步' if zh else 'Next'}: {next_action_zh(check) if zh else check['next_action']}")
    if "project" in report:
        project = report["project"]
        print(f"{'综合状态' if zh else 'Combined status'}: {states[report['status']] if zh else report['status']}")
        print(f"{'项目' if zh else 'Project'}: {project['root']}")
        unset = "未选择" if zh else "unselected"
        print(f"{'主文件 / 引擎 / 后端' if zh else 'Main / engine / backend'}: "
              f"{project['main'] or unset} / {project['engine'] or unset} / {project['backend'] or unset}")
        if project["root_candidates"]:
            print(f"{'候选主文件' if zh else 'Root candidates'}: {', '.join(project['root_candidates'])}")
        for item in project["diagnostics"]:
            location = item["file"] or "project"
            if item["line"] is not None:
                location += f":{item['line']}"
            print(f"[{item['severity']}] {location} ({item['code']}): {item['message']}")
            print(f"  {'下一步' if zh else 'Next'}: {item['next_step']}")
    print("未编译或修改文档，也未安装依赖。检查通过不等于编译成功或内容正确。" if zh else
          "No documents were compiled or edited, and no packages were installed. Passing checks do not establish compilation or content correctness.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", choices=SKILLS, action="append", help="Repeat to select skills; default: all")
    parser.add_argument("--project", type=Path, help="Read project configuration and inspect reachable sources without compiling or writing")
    parser.add_argument("--main", help="Select a project-relative main .tex file; requires --project")
    parser.add_argument("--engine", choices=("pdflatex", "xelatex", "lualatex"), help="Override project engine; default without --project: pdflatex")
    parser.add_argument("--backend", choices=("bibtex", "biber"), help="Check the project's selected bibliography backend")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable report")
    parser.add_argument("--language", choices=("en", "zh"), default="en", help="Human output language; JSON and native diagnostics retain their original text")
    args = parser.parse_args(argv)
    try:
        if args.main is not None and args.project is None:
            raise ValueError("--main requires --project")
        report = (diagnose_project(args.project, args.skill or SKILLS, args.main, args.engine, args.backend)
                  if args.project is not None else diagnose(args.skill or SKILLS, args.engine or "pdflatex", args.backend))
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        if args.json:
            print(json.dumps({"schema": 1, "error": str(exc)}, ensure_ascii=True))
        else:
            print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print_report(report, args.language)
    return 1 if not report["local_prerequisites_met"] or report.get("status") == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main())
