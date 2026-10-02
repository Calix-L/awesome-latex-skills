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
AUXILIARY_SUFFIXES = {".aux", ".toc", ".lof", ".lot", ".out", ".bcf", ".bbl", ".nav", ".snm"}


def log_state(text):
    normalized = " ".join(text.split())
    return {
        "rerun_requested": bool(re.search(r"Rerun to get|Label\(s\) may have changed|Please (?:\(re\))?run (?:Biber|LaTeX)|Rerun LaTeX", normalized, re.I)),
        "unresolved_references": bool(re.search(r"(?:Reference|Citation) .{0,500}? undefined|There were undefined (?:references|citations)", normalized, re.I)),
    }


def auxiliary_hashes(output):
    return {path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in output.rglob("*") if path.is_file() and path.suffix in AUXILIARY_SUFFIXES}


def prepare_include_directories(project, output):
    """Mirror local TeX file directories so nested include auxiliary files can open."""
    for path in project.rglob("*.tex"):
        relative = path.relative_to(project)
        if ".git" in relative.parts or path.resolve().is_relative_to(output):
            continue
        if path.is_file() and path.resolve().is_relative_to(project):
            (output / relative.parent).mkdir(parents=True, exist_ok=True)


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


def build(source, output, engine="pdflatex", backend=None, passes=None, timeout=60,
          jobname=None, until_stable=False, require_resolved=False):
    source = Path(source).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".tex":
        raise ValueError("Source must be an existing .tex root document")
    if any(char in source.name for char in '\n\r"{}%#\\'):
        raise ValueError("Root filename contains unsupported TeX command-line characters")
    if engine not in ENGINES or backend not in (None, *BACKENDS):
        raise ValueError("Unsupported engine or bibliography backend")
    jobname = source.stem if jobname is None else jobname
    if not isinstance(jobname, str) or not jobname.strip() or jobname in (".", "..") or any(char in jobname for char in '\n\r"{}%#\\/'):
        raise ValueError("Job name must be a nonempty filename without TeX control characters or path separators")
    passes = (5 if until_stable else 3 if backend else 2) if passes is None else passes
    if not isinstance(passes, int) or not 1 <= passes <= 5 or (backend and passes < 2):
        raise ValueError("Use 1–5 engine passes; a bibliography build needs at least 2")
    if until_stable and passes < 2:
        raise ValueError("Convergence checking needs at least 2 engine passes")
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
        "schema": 2, "source": str(source), "jobname": jobname,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "engine": engine, "backend": backend, "requested_passes": passes,
        "output": str(output), "steps": [], "status": "failed", "pdf": None,
        "diagnostics": [], "failure": None,
        "until_stable": until_stable, "require_resolved": require_resolved,
        "auxiliary_stable": None, "rerun_requested": False, "unresolved_references": False,
        "source_unchanged": None,
    }
    environment = os.environ.copy()
    for variable in ("TEXINPUTS", "BIBINPUTS", "BSTINPUTS"):
        environment[variable] = str(source.parent) + os.pathsep + environment.get(variable, "")

    def run(command, cwd, name, native_log):
        evidence = output / "logs"
        evidence.mkdir(exist_ok=True)
        capture = evidence / f"{name}.txt"
        step = {"command": command, "cwd": str(cwd), "exit_code": None,
                "timed_out": False, "transcript": capture.relative_to(output).as_posix(), "log": None}
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
            saved = evidence / f"{name}{native_log.suffix}"
            shutil.copyfile(native_log, saved)
            step["log"] = saved.relative_to(output).as_posix()
        if step["exit_code"] != 0:
            report["failure"] = report["failure"] or f"{name} exited with {step['exit_code']}"
            return False
        return True

    try:
        prepare_include_directories(source.parent, output)
        previous_auxiliary = None
        for number in range(1, passes + 1):
            # Each successful pass must produce its own PDF, not inherit an earlier one.
            prior_pdf = output / f"{jobname}.pdf"
            if prior_pdf.exists():
                prior_pdf.unlink()
            # Quotes are interpreted by TeX's filename scanner, not a shell.
            filename = f'"./{source.name}"' if " " in source.name else f"./{source.name}"
            command = [executables[engine], "-no-shell-escape", "-interaction=nonstopmode",
                       "-halt-on-error", "-file-line-error", "-recorder", f"-jobname={jobname}",
                       f"-output-directory={output}", filename]
            if not run(command, source.parent, f"engine-{number:02}", output / f"{jobname}.log"):
                break
            current_auxiliary = auxiliary_hashes(output)
            report["auxiliary_stable"] = bool(current_auxiliary) and current_auxiliary == previous_auxiliary if previous_auxiliary is not None else None
            previous_auxiliary = current_auxiliary
            report.update(log_state((output / f"{jobname}.log").read_text(encoding="utf-8", errors="replace")
                                    if (output / f"{jobname}.log").is_file() else ""))
            if number == 1 and backend:
                control = output / f"{jobname}{'.aux' if backend == 'bibtex' else '.bcf'}"
                if not control.is_file():
                    report["failure"] = f"Requested {backend}, but {control.name} was not generated"
                    break
                if backend == "bibtex":
                    # subprocess already supplies one argument; BibTeX takes it literally.
                    command, cwd = [executables[backend], jobname], output
                else:
                    command = [executables[backend], f"--input-directory={output}",
                               f"--output-directory={output}", jobname]
                    cwd = source.parent
                if not run(command, cwd, "bibliography", output / f"{jobname}.blg"):
                    break
            if until_stable and report["auxiliary_stable"] and not report["rerun_requested"]:
                break
        if report["steps"]:
            last_engine = next(step for step in reversed(report["steps"]) if step["command"][0] == executables[engine])
            log = output / (last_engine["log"] or last_engine["transcript"])
            final_text = log.read_text(encoding="utf-8", errors="replace")
            report["diagnostics"] = diagnostics(final_text)
            report.update(log_state(final_text))
        pdf = output / f"{jobname}.pdf"
        valid_pdf = False
        if pdf.is_file():
            with pdf.open("rb") as stream:
                valid_pdf = stream.read(5) == b"%PDF-"
        if not report["failure"]:
            report["source_unchanged"] = hashlib.sha256(source.read_bytes()).hexdigest() == report["source_sha256"]
            if any(item["severity"] == "error" for item in report["diagnostics"]):
                report["failure"] = "Final engine log contains TeX errors"
            elif not report["source_unchanged"]:
                report["failure"] = "Root source changed during the build; output cannot be verified against its starting hash"
            elif not valid_pdf:
                report["failure"] = "Engine did not produce a PDF with a valid header"
            elif until_stable and (not report["auxiliary_stable"] or report["rerun_requested"]):
                report["failure"] = "Auxiliary files or rerun requests did not settle within the engine-pass limit"
            elif require_resolved and (report["unresolved_references"] or report["rerun_requested"]):
                report["failure"] = "Final log contains unresolved references/citations or rerun requests"
            else:
                report["status"], report["pdf"] = "success", pdf.name
    except KeyboardInterrupt:
        report["failure"] = "Build interrupted; compilation is unverified"
        raise
    except (OSError, ValueError) as exc:
        report["failure"] = f"Build evidence could not be completed: {exc}"
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
    parser.add_argument("--passes", type=int, help="1–5 engine passes; default 2, 3 with a backend, or maximum 5 with --until-stable")
    parser.add_argument("--timeout", type=float, default=60, help="Seconds per engine/backend process (default 60)")
    parser.add_argument("--jobname", help="Output basename; default: root filename without .tex")
    parser.add_argument("--until-stable", action="store_true", help="Stop on settled auxiliary files and rerun requests; default maximum 5 passes")
    parser.add_argument("--require-resolved", action="store_true", help="Fail if final references/citations or rerun requests remain")
    args = parser.parse_args(argv)
    try:
        report = build(args.source, args.output, args.engine, args.backend, args.passes, args.timeout,
                       args.jobname, args.until_stable, args.require_resolved)
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
