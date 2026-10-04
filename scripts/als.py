#!/usr/bin/env python3
"""One entry point for installation, evidence, evaluation and maintenance."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
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
    "verify": "scripts/verify_artifacts.py",
}
STRUCTURED = {"doctor", "evaluate", "examples", "sources", "release", "project", "review", "paper", "benchmark", "verify"}


class HelperArgumentExit(Exception):
    def __init__(self, code, stdout, stderr):
        self.code, self.stdout, self.stderr = code, stdout, stderr


def helper_parser(command, **kwargs):
    """Use the helper's exact grammar without running its operational code."""
    spec = importlib.util.spec_from_file_location(f"als_{command}_arguments", ROOT / COMMANDS[command])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.argument_parser(prog=f"als {command}", **kwargs)


def build_arguments(args):
    parser = helper_parser("build", source_optional=True)
    parser.add_argument("--project", type=Path, action="append", help="Project directory with .als.json; omit the source argument")
    parser.set_defaults(engine=None, backend=None, passes=None)
    options = parser.parse_args(args)
    if options.project is not None:
        if len(options.project) != 1:
            raise ValueError("Specify --project only once")
        if options.source is not None:
            raise ValueError("Use either a source file or --project, not both")
        from project_doctor import load_config
        root = options.project[0].expanduser().resolve()
        config = load_config(root)
        options.source = root / config["main"]
        for field in ("engine", "backend", "passes"):
            if getattr(options, field) is None:
                setattr(options, field, config.get(field))
    elif options.source is None:
        raise ValueError("Build requires a source file or --project")
    options.source = options.source.expanduser().absolute()
    options.output = options.output.expanduser().absolute()
    remaining = [str(options.source)]
    for field in ("output", "engine", "backend", "passes", "timeout", "jobname"):
        value = getattr(options, field)
        if value is not None:
            flag = f"--{field.replace('_', '-')}"
            remaining.extend([f"{flag}={value}"] if str(value).startswith("-") else [flag, str(value)])
    for field in ("until_stable", "require_resolved"):
        if getattr(options, field):
            remaining.append(f"--{field.replace('_', '-')}")
    return remaining, options


def configured_build(args):
    """Compatibility entry point for callers preparing project builds."""
    return build_arguments(args)[0]


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    machine = bool(args and args[0] == "--json")
    if machine:
        args.pop(0)
    if not args or args[0] in {"-h", "--help"}:
        print("Usage: als [--json] COMMAND [options]\n"
              "From source: python scripts/als.py [--json] COMMAND [options]\n"
              "Commands: " + ", ".join(COMMANDS) + "\n"
              "Use COMMAND --help for details. Exit codes are preserved. --json precedes COMMAND.")
        return 0
    command = args.pop(0)
    report = {"schema": 1, "version": version(), "command": command, "status": "failed",
              "exit_code": 2, "result": None, "evidence": [], "invocation": None, "stdout": "", "stderr": ""}
    if command == "--version":
        report.update(status="success", exit_code=0, result={"version": version()})
    elif command not in COMMANDS:
        report["stderr"] = f"Unknown command {command!r}; use --help"
    else:
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        try:
            destination, existing = None, False
            if command in {"build", "extract"}:
                captured_out, captured_err = io.StringIO(), io.StringIO()
                try:
                    with redirect_stdout(captured_out), redirect_stderr(captured_err):
                        if command == "build":
                            args, options = build_arguments(args)
                        else:
                            options = helper_parser(command).parse_args(args)
                except SystemExit as exc:
                    raise HelperArgumentExit(exc.code, captured_out.getvalue(), captured_err.getvalue()) from None
                destination = options.output.expanduser().absolute()
                existing = destination.exists() or destination.is_symlink()
            child_args = (["--json"] if machine and command in STRUCTURED else []) + args
            report["invocation"] = {"python": sys.executable, "helper": COMMANDS[command],
                                    "arguments": child_args, "cwd": str(Path.cwd())}
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
        except HelperArgumentExit as exc:
            report.update(exit_code=exc.code, status="success" if exc.code == 0 else "failed",
                          stdout=exc.stdout, stderr=exc.stderr)
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
