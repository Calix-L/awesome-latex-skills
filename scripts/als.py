#!/usr/bin/env python3
"""One entry point for installation, evidence, evaluation and maintenance."""
import json
import os
from pathlib import Path
import subprocess
import sys

from project_support import ROOT, read_json, version

COMMANDS = {
    "install": "scripts/install.py", "doctor": "scripts/doctor.py",
    "build": "latex-rescue/scripts/check_build.py", "extract": "pdf2tex/scripts/extract_pdf.py",
    "validate": "scripts/validate_repo.py", "evaluate": "scripts/evaluate.py",
    "examples": "scripts/run_examples.py", "sources": "scripts/audit_sources.py",
    "release": "scripts/package_release.py",
    "project": "scripts/project_doctor.py", "review": "scripts/review_project.py",
    "paper": "scripts/run_paper_example.py",
    "benchmark": "scripts/evaluate_batch.py",
}
STRUCTURED = {"doctor", "evaluate", "examples", "sources", "release", "project", "review", "paper", "benchmark"}


def configured_build(args):
    args = list(args)
    project = None
    remaining = []
    while args:
        item = args.pop(0)
        if item == "--project" or item.startswith("--project="):
            if project is not None:
                raise ValueError("Specify --project only once")
            if item == "--project":
                if not args:
                    raise ValueError("--project requires a directory")
                project = args.pop(0)
            else:
                project = item.split("=", 1)[1]
        else:
            remaining.append(item)
    if project is None:
        return remaining
    from project_doctor import load_config
    root = Path(project).expanduser().resolve()
    config = load_config(root)
    remaining.insert(0, str(root / config["main"]))
    for field in ("engine", "backend", "passes"):
        if config.get(field) is not None and not any(item == f"--{field}" or item.startswith(f"--{field}=") for item in remaining):
            remaining.extend([f"--{field}", str(config[field])])
    return remaining


def output_argument(args):
    for index, value in enumerate(args):
        if value == "--output" and index + 1 < len(args):
            return Path(args[index + 1]).expanduser().absolute()
        if value.startswith("--output="):
            return Path(value.split("=", 1)[1]).expanduser().absolute()
    return None


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    machine = bool(args and args[0] == "--json")
    if machine:
        args.pop(0)
    if not args or args[0] in {"-h", "--help"}:
        print("Usage: python scripts/als.py [--json] COMMAND [options]\n"
              "Commands: " + ", ".join(COMMANDS) + "\n"
              "Use COMMAND --help for details. Exit codes are preserved. --json precedes COMMAND.")
        return 0
    command = args.pop(0)
    report = {"schema": 1, "version": version(), "command": command, "status": "failed",
              "exit_code": 2, "result": None, "evidence": [], "stdout": "", "stderr": ""}
    if command == "--version":
        report.update(status="success", exit_code=0, result={"version": version()})
    elif command not in COMMANDS:
        report["stderr"] = f"Unknown command {command!r}; use --help"
    else:
        destination = output_argument(args)
        existing = destination is not None and (destination.exists() or destination.is_symlink())
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        try:
            if command == "build":
                args = configured_build(args)
            child_args = (["--json"] if machine and command in STRUCTURED else []) + args
            child = subprocess.run([sys.executable, str(ROOT / COMMANDS[command]), *child_args],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
            report.update(exit_code=child.returncode, status="success" if child.returncode == 0 else "failed",
                          stdout=child.stdout, stderr=child.stderr)
            if machine and command in STRUCTURED and child.stdout.strip():
                try:
                    report["result"] = json.loads(child.stdout)
                except ValueError:
                    # --help and native startup messages remain captured evidence.
                    pass
            filename = {"build": "build-report.json", "extract": "layout.json"}.get(command)
            if filename and destination is not None and not existing:
                evidence = destination / filename
                if evidence.is_file() and not evidence.is_symlink():
                    report["result"] = read_json(evidence)
                    report["evidence"].append(str(evidence))
        except KeyboardInterrupt:
            report.update(exit_code=130, stderr="Command interrupted; inspect any retained native evidence")
        except (OSError, ValueError) as exc:
            report.update(exit_code=2, status="failed", stderr=str(exc))
    if machine:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        if report["stdout"]:
            print(report["stdout"], end="")
        if report["stderr"]:
            print(report["stderr"], file=sys.stderr, end="\n" if not report["stderr"].endswith("\n") else "")
        if command == "--version":
            print(version())
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
