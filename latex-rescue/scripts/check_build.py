#!/usr/bin/env python3
"""Build a conventional TeX project into a new directory and retain evidence."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ENGINES = ("pdflatex", "xelatex", "lualatex")
BACKENDS = ("bibtex", "biber")


def diagnostics(text):
    """Recognize common engine diagnostics; retain full logs for everything else."""
    findings = []
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        severity = None
        if stripped.startswith("!") or re.search(r"\.(?:tex|sty|cls|ltx):\d+: ", line):
            severity = "error"
        elif re.match(r"(?:LaTeX|Package .+|Class .+) Warning:", stripped):
            severity = "warning"
        elif re.match(r"(?:Over|Under)full \\[hv]box", stripped):
            severity = "layout"
        if severity:
            findings.append({"severity": severity, "log_line": number, "message": stripped})
    return findings


def build(source, output, engine="pdflatex", backend=None, passes=None, timeout=60):
    source = Path(source).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".tex":
        raise ValueError("Source must be an existing .tex root document")
    if any(char in source.name for char in '\n\r"{}%#\\'):
        raise ValueError("Root filename contains unsupported TeX command-line characters")
    if engine not in ENGINES or backend not in (None, *BACKENDS):
        raise ValueError("Unsupported engine or bibliography backend")
    passes = (3 if backend else 2) if passes is None else passes
    if not isinstance(passes, int) or not 1 <= passes <= 5 or (backend and passes < 2):
        raise ValueError("Use 1–5 engine passes; a bibliography build needs at least 2")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Timeout must be a finite positive number of seconds")
    if output.exists():
        raise ValueError("Output directory must be new; existing build artifacts cannot be reused")
    executables = {}
    for tool in (engine, backend):
        if tool:
            executable = shutil.which(tool)
            if not executable:
                raise ValueError(f"Required tool is not on PATH: {tool}")
            executables[tool] = executable
    # mkdir is the reservation: do not replace a directory created after preflight.
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": 1, "source": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "engine": engine, "backend": backend, "requested_passes": passes,
        "output": str(output), "steps": [], "status": "failed", "pdf": None,
        "diagnostics": [], "failure": None,
    }
    environment = os.environ.copy()
    for variable in ("TEXINPUTS", "BIBINPUTS", "BSTINPUTS"):
        environment[variable] = str(source.parent) + os.pathsep + environment.get(variable, "")

    def run(command, cwd, name, native_log):
        capture = output / f"{name}.txt"
        step = {"command": command, "cwd": str(cwd), "exit_code": None,
                "timed_out": False, "transcript": capture.name, "log": None}
        report["steps"].append(step)
        # A failed later pass must not inherit the preceding pass's native log.
        if native_log.exists():
            native_log.unlink()
        # A disk transcript avoids buffering long compiler output in memory.
        with capture.open("wb") as stream:
            try:
                result = subprocess.run(command, cwd=cwd, env=environment,
                                        stdin=subprocess.DEVNULL, stdout=stream,
                                        stderr=subprocess.STDOUT, timeout=timeout)
                step["exit_code"] = result.returncode
            except subprocess.TimeoutExpired:
                step["timed_out"] = True
                report["failure"] = f"{name} exceeded {timeout:g} seconds"
            except OSError as exc:
                report["failure"] = f"{name} could not launch: {exc}"
        if native_log.is_file():
            saved = output / f"{name}{native_log.suffix}"
            shutil.copyfile(native_log, saved)
            step["log"] = saved.name
        if step["exit_code"] != 0:
            report["failure"] = report["failure"] or f"{name} exited with {step['exit_code']}"
            return False
        return True

    try:
        for number in range(1, passes + 1):
            # Quotes are interpreted by TeX's filename scanner, not a shell.
            filename = f'"./{source.name}"' if " " in source.name else f"./{source.name}"
            command = [executables[engine], "-no-shell-escape", "-interaction=nonstopmode",
                       "-halt-on-error", "-file-line-error", "-recorder", "-jobname=document",
                       f"-output-directory={output}", filename]
            if not run(command, source.parent, f"engine-{number:02}", output / "document.log"):
                break
            if number == 1 and backend:
                control = output / ("document.aux" if backend == "bibtex" else "document.bcf")
                if not control.is_file():
                    report["failure"] = f"Requested {backend}, but {control.name} was not generated"
                    break
                if backend == "bibtex":
                    command, cwd = [executables[backend], "document"], output
                else:
                    command = [executables[backend], f"--input-directory={output}",
                               f"--output-directory={output}", "document"]
                    cwd = source.parent
                if not run(command, cwd, "bibliography", output / "document.blg"):
                    break
        if report["steps"]:
            last_engine = next(step for step in reversed(report["steps"]) if step["command"][0] == executables[engine])
            log = output / (last_engine["log"] or last_engine["transcript"])
            report["diagnostics"] = diagnostics(log.read_text(encoding="utf-8", errors="replace"))
        pdf = output / "document.pdf"
        valid_pdf = False
        if pdf.is_file():
            with pdf.open("rb") as stream:
                valid_pdf = stream.read(5) == b"%PDF-"
        if not report["failure"]:
            if any(item["severity"] == "error" for item in report["diagnostics"]):
                report["failure"] = "Final engine log contains TeX errors"
            elif not valid_pdf:
                report["failure"] = "Engine did not produce a PDF with a valid header"
            else:
                report["status"], report["pdf"] = "success", pdf.name
    except KeyboardInterrupt:
        report["failure"] = "Build interrupted; compilation is unverified"
        raise
    finally:
        (output / "build-report.json").write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Actual root document; relative assets resolve from its directory")
    parser.add_argument("--output", type=Path, required=True, help="New directory for PDF, logs, and JSON evidence")
    parser.add_argument("--engine", choices=ENGINES, default="pdflatex")
    parser.add_argument("--backend", choices=BACKENDS, help="Explicit bibliography backend; omitted means none")
    parser.add_argument("--passes", type=int, help="1–5 engine passes; default 2, or 3 with a backend")
    parser.add_argument("--timeout", type=float, default=60, help="Seconds per engine/backend process (default 60)")
    args = parser.parse_args(argv)
    try:
        report = build(args.source, args.output, args.engine, args.backend, args.passes, args.timeout)
    except (OSError, ValueError) as exc:
        print(f"Build check: {exc}", file=sys.stderr)
        return 2
    print(f"Build {report['status']}: {report['output']}")
    if report["failure"]:
        print(report["failure"], file=sys.stderr)
    print("Evidence: build-report.json; inspect final diagnostics and the PDF separately.")
    return 0 if report["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
