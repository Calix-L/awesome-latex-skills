#!/usr/bin/env python3
"""Build a conventional TeX project into a new directory and retain evidence."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import subprocess
import sys

ENGINES = ("pdflatex", "xelatex", "lualatex")
BACKENDS = ("bibtex", "biber")
MAX_BIBTEX_AUX_FILES = 128
MAX_BIBTEX_AUX_BYTES = 2_000_000
AUX_COMMAND = re.compile(r"^\\(bibdata|bibstyle|@input)\{([^{}\\\r\n]*)\}[ \t]*(?=\r?$)", re.MULTILINE)
AUXILIARY_SUFFIXES = {".aux", ".toc", ".lof", ".lot", ".out", ".bcf", ".bbl", ".nav", ".snm"}
MAX_WATCH_FILES = 128
MAX_WATCH_BYTES = 64 * 1024 * 1024
MAX_WATCH_TOTAL = 256 * 1024 * 1024


def fingerprint(path, max_bytes=None):
    digest, size = hashlib.sha256(), 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
            if max_bytes is not None and size > max_bytes:
                raise ValueError(f"Watched input exceeds {max_bytes} bytes: {path.name}")
    return {"sha256": digest.hexdigest(), "size": size}


def prepare_bibtex_inputs(source, output, jobname):
    """Stage only explicit ./ or ../ database/style names, preserving AUX bytes.

    BibTeX runs in the output directory for child AUX lookup and output isolation.
    Its explicitly relative database/style names bypass BIBINPUTS/BSTINPUTS, so
    copies with stable output-local aliases bind their source-directory meaning.
    """
    texts = {}
    pending = [output / f"{jobname}.aux"]
    while pending:
        path = pending.pop()
        if path in texts:
            continue
        if len(texts) >= MAX_BIBTEX_AUX_FILES:
            raise ValueError("BibTeX auxiliary inventory exceeds 128 files")
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BIBTEX_AUX_BYTES:
            raise ValueError("BibTeX AUX must be a bounded regular file")
        with path.open("rb") as stream:
            data = stream.read(MAX_BIBTEX_AUX_BYTES + 1)
        if len(data) > MAX_BIBTEX_AUX_BYTES:
            raise ValueError("BibTeX AUX exceeds the actual-read limit")
        texts[path] = data
        for match in AUX_COMMAND.finditer(data.decode("utf-8", "surrogateescape")):
            if match[1] == "@input":
                child = (output / match[2]).resolve()
                if child.is_relative_to(output) and child.is_file():
                    pending.append(child)
    needed = any(name.strip().startswith(("./", "../"))
                 for data in texts.values() for match in AUX_COMMAND.finditer(data.decode("utf-8", "surrogateescape"))
                 if match[1] in {"bibdata", "bibstyle"} for name in match[2].split(","))
    if not needed:
        return jobname, []
    stage = output / "bibtex-inputs"
    stage.mkdir(exist_ok=False)
    rows, resources, total = [], {}, 0
    def resource(name, suffix):
        nonlocal total
        original = source.parent / (name if name.endswith(suffix) else name + suffix)
        if original.is_symlink() or not original.is_file():
            raise ValueError(f"Explicit relative BibTeX input is not a regular file: {name}")
        original = original.resolve()
        key = (original, suffix)
        if key in resources:
            return resources[key]
        expected = fingerprint(original, MAX_WATCH_BYTES)
        total += expected["size"]
        if len(resources) >= MAX_WATCH_FILES or total > MAX_WATCH_TOTAL:
            raise ValueError("Prepared BibTeX inputs exceed file/total byte limits")
        target = stage / f"resource-{len(resources) + 1:04}{suffix}"
        digest, size = hashlib.sha256(), 0
        with original.open("rb") as stream, target.open("xb") as copied:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                size += len(chunk)
                if size > MAX_WATCH_BYTES:
                    raise ValueError("Prepared BibTeX input exceeds the actual-read limit")
                digest.update(chunk)
                copied.write(chunk)
        if {"sha256": digest.hexdigest(), "size": size} != expected or fingerprint(original, MAX_WATCH_BYTES) != expected:
            raise ValueError(f"BibTeX input changed during preparation: {name}")
        relative = target.relative_to(output).as_posix()
        rows.append({"file": relative, "sha256": expected["sha256"], "bytes": size,
                     "kind": "bibliography" if suffix == ".bib" else "style", "original": str(original)})
        resources[key] = "./" + relative.removesuffix(suffix)
        return resources[key]
    for path, data in sorted(texts.items()):
        def replace(match):
            command, value = match[1], match[2]
            if command == "@input":
                child = (output / value).resolve()
                if child not in texts or not child.is_relative_to(output):
                    raise ValueError(f"BibTeX child AUX is missing or outside the output: {value}")
                value = "./" + (stage / child.relative_to(output)).relative_to(output).as_posix()
            else:
                suffix = ".bib" if command == "bibdata" else ".bst"
                value = ",".join(resource(name.strip(), suffix) if name.strip().startswith(("./", "../")) else name
                                 for name in value.split(","))
            return f"\\{command}{{{value}}}"
        rendered = AUX_COMMAND.sub(replace, data.decode("utf-8", "surrogateescape")).encode("utf-8", "surrogateescape")
        target = stage / path.relative_to(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(rendered)
        rows.append({"file": target.relative_to(output).as_posix(), "sha256": hashlib.sha256(rendered).hexdigest(),
                     "bytes": len(rendered), "kind": "auxiliary", "original_auxiliary": path.relative_to(output).as_posix(),
                     "original_sha256": hashlib.sha256(data).hexdigest()})
    return (stage / jobname).relative_to(output).as_posix(), rows


def check_prepared_inputs(output, rows):
    for item in rows:
        if fingerprint(output / item["file"], MAX_WATCH_BYTES)["sha256"] != item["sha256"]:
            raise ValueError(f"Prepared BibTeX input changed: {item['file']}")
        if item.get("original") and fingerprint(Path(item["original"]), MAX_WATCH_BYTES)["sha256"] != item["sha256"]:
            raise ValueError(f"Prepared BibTeX source changed: {item['original']}")


def watched_path(project, value):
    """An explicit portable local filename, revalidated at every observation."""
    if (not isinstance(value, str) or not value or any(c in value for c in "\\:\x00\r\n")
            or PureWindowsPath(value).drive or Path(value).is_absolute()
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise ValueError("Watched input must be a portable path relative to the root source directory")
    project = Path(project).resolve()
    parts = value.split("/")
    path = project.joinpath(*parts)
    if any(project.joinpath(*parts[:i]).is_symlink() for i in range(1, len(parts) + 1)) or not path.resolve().is_relative_to(project):
        raise ValueError(f"Watched input is a symlink or escapes its project: {value}")
    if not path.is_file():
        raise ValueError(f"Watched input must be an existing regular file: {value}")
    return path.resolve()


def prepare_watched(project, output, values):
    if values is None:
        return {}
    if not isinstance(values, (list, tuple)) or len(values) > MAX_WATCH_FILES:
        raise ValueError(f"Select at most {MAX_WATCH_FILES} watched inputs")
    watched, seen, total = {}, set(), 0
    for value in values:
        path = watched_path(project, value)
        if path.is_relative_to(output):
            raise ValueError("Watched input cannot be inside build output")
        if path in seen:
            continue
        seen.add(path)
        if path.stat().st_size > MAX_WATCH_BYTES:
            raise ValueError(f"Watched input exceeds {MAX_WATCH_BYTES} bytes: {value}")
        digest = fingerprint(path, MAX_WATCH_BYTES)
        total += digest["size"]
        if total > MAX_WATCH_TOTAL:
            raise ValueError(f"Watched inputs exceed {MAX_WATCH_TOTAL} total bytes")
        watched[path.relative_to(project).as_posix()] = digest
    return watched


def recorder_inputs(text, cwd, project, output):
    """Resolve FLS paths, excluding generated outputs and external resources."""
    inputs, outputs = set(), set()
    directory = cwd
    for line in text.splitlines():
        kind, separator, value = line.partition(" ")
        if not separator or not value or kind not in {"PWD", "INPUT", "OUTPUT"}:
            continue
        path = (directory / value).resolve()
        if kind == "PWD":
            directory = path
        elif kind == "INPUT":
            inputs.add(path)
        else:
            outputs.add(path)
    return sorted(path for path in inputs - outputs
                  if path.is_relative_to(project) and not path.is_relative_to(output))


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


def diagnostics(text, tool=None):
    """Recognize common engine diagnostics; retain full logs for everything else."""
    findings = []
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        severity = None
        if tool == "biber":
            if re.search(r"(?:^|\s)ERROR - ", stripped):
                severity = "error"
            elif re.search(r"(?:^|\s)WARN - ", stripped):
                severity = "warning"
        elif tool == "bibtex":
            if stripped.startswith("Warning--"):
                severity = "warning"
            elif re.match(r"I couldn't open |I found no |I was expecting |Repeated entry|Illegal, |Unbalanced braces", stripped) or re.search(r"---line \d+ of file ", stripped):
                severity = "error"
        elif stripped.startswith("!") or re.search(r"\.(?:tex|sty|cls|ltx):\d+: ", line):
            severity = "error"
        elif re.match(r"(?:LaTeX|Package .+|Class .+) Warning:", stripped):
            severity = "warning"
        elif re.match(r"(?:Over|Under)full \\[hv]box", stripped):
            severity = "layout"
        if severity:
            findings.append({"severity": severity, "log_line": number, "message": stripped})
    return findings


def build(source, output, engine="pdflatex", backend=None, passes=None, timeout=60,
          jobname=None, until_stable=False, require_resolved=False, watch_inputs=None):
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
    source_sha256 = fingerprint(source)["sha256"]
    watched = prepare_watched(source.parent, output, watch_inputs)
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
        "schema": 3, "source": str(source), "jobname": jobname,
        "source_sha256": source_sha256,
        "engine": engine, "backend": backend, "requested_passes": passes,
        "output": str(output), "steps": [], "status": "failed", "pdf": None,
        "diagnostics": [], "failure": None,
        "until_stable": until_stable, "require_resolved": require_resolved,
        "auxiliary_stable": None, "rerun_requested": False, "unresolved_references": False,
        "source_unchanged": None,
        "failed_step": None, "diagnostic_step": None,
        "local_inputs": [], "input_tracking": {"recorder_steps": [], "watched_inputs": list(watched),
                                              "changed": [], "unreadable": []},
    }
    observed_inputs = {name: {"path": name, "observations": [{"step": "preflight", **digest, "error": None}]}
                       for name, digest in watched.items()}
    watch_lookup = {source.parent / name: name for name in watched}

    def observe(path, name):
        relative = watch_lookup.get(path, path.relative_to(source.parent).as_posix())
        item = observed_inputs.setdefault(relative, {"path": relative, "observations": []})
        observation = {"step": name, "sha256": None, "size": None, "error": None}
        try:
            resolved = path.resolve()
            if not resolved.is_relative_to(source.parent) or resolved.is_relative_to(output):
                raise ValueError("Recorded path now resolves outside the local input scope")
            if relative in watched:
                resolved = watched_path(source.parent, relative)
                observation.update(fingerprint(resolved, MAX_WATCH_BYTES))
            else:
                observation.update(fingerprint(resolved))
        except (OSError, ValueError) as exc:
            observation["error"] = str(exc)
            if relative not in report["input_tracking"]["unreadable"]:
                report["input_tracking"]["unreadable"].append(relative)
        item["observations"].append(observation)
        hashes = {entry["sha256"] for entry in item["observations"] if entry["sha256"] is not None}
        if len(hashes) > 1 and relative not in report["input_tracking"]["changed"]:
            report["input_tracking"]["changed"].append(relative)
    environment = os.environ.copy()
    for variable in ("TEXINPUTS", "BIBINPUTS", "BSTINPUTS"):
        environment[variable] = str(source.parent) + os.pathsep + environment.get(variable, "")

    def run(command, cwd, name, native_log, recorder=None, prepared_inputs=None):
        evidence = output / "logs"
        evidence.mkdir(exist_ok=True)
        capture = evidence / f"{name}.txt"
        step = {"command": command, "cwd": str(cwd), "exit_code": None,
                "name": name, "tool": engine if name.startswith("engine-") else backend,
                "timed_out": False, "transcript": capture.relative_to(output).as_posix(), "log": None,
                "recorder": None, "diagnostics": []}
        if prepared_inputs:
            step["prepared_inputs"] = prepared_inputs
        report["steps"].append(step)
        # A failed later pass must not inherit the preceding pass's native log.
        if native_log.exists():
            native_log.unlink()
        if recorder and recorder.exists():
            recorder.unlink()
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
        diagnostic_file = output / (step["log"] or step["transcript"])
        step["diagnostics"] = diagnostics(diagnostic_file.read_text(encoding="utf-8", errors="replace"), step["tool"])
        if recorder and recorder.is_file():
            saved_recorder = evidence / f"{name}.fls"
            shutil.copyfile(recorder, saved_recorder)
            step["recorder"] = saved_recorder.relative_to(output).as_posix()
            report["input_tracking"]["recorder_steps"].append(name)
            for path in recorder_inputs(saved_recorder.read_text(encoding="utf-8", errors="replace"), cwd, source.parent, output):
                if path in watch_lookup:
                    continue  # Explicit selection supplies one observation per step below.
                observe(path, name)
        for relative in watched:
            observe(source.parent / relative, name)
        if step["exit_code"] != 0:
            report["failed_step"] = name
            report["failure"] = report["failure"] or f"{name} exited with {step['exit_code']}"
            return False
        if any(item["severity"] == "error" for item in step["diagnostics"]):
            report["failed_step"] = name
            report["failure"] = f"{name} log contains recognized errors"
            return False
        return True

    try:
        prepared_inputs = []
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
            if not run(command, source.parent, f"engine-{number:02}", output / f"{jobname}.log", output / f"{jobname}.fls"):
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
                    auxiliary_name, prepared_inputs = prepare_bibtex_inputs(source, output, jobname)
                    command, cwd = [executables[backend], auxiliary_name], output
                else:
                    command = [executables[backend], f"--input-directory={output}",
                               f"--output-directory={output}", jobname]
                    cwd = source.parent
                if not run(command, cwd, "bibliography", output / f"{jobname}.blg", prepared_inputs=prepared_inputs):
                    break
                check_prepared_inputs(output, prepared_inputs)
            if until_stable and report["auxiliary_stable"] and not report["rerun_requested"]:
                break
        if report["steps"]:
            last_engine = next(step for step in reversed(report["steps"]) if step["name"].startswith("engine-"))
            selected_step = next((step for step in report["steps"] if step["name"] == report["failed_step"]), last_engine)
            report["diagnostic_step"] = selected_step["name"]
            report["diagnostics"] = selected_step["diagnostics"]
            log = output / (last_engine["log"] or last_engine["transcript"])
            final_text = log.read_text(encoding="utf-8", errors="replace")
            report.update(log_state(final_text))
        check_prepared_inputs(output, prepared_inputs)
        for relative in sorted(observed_inputs):
            observe(source.parent / relative, "final")
        report["local_inputs"] = [observed_inputs[key] for key in sorted(observed_inputs)]
        report["source_unchanged"] = fingerprint(source)["sha256"] == report["source_sha256"]
        pdf = output / f"{jobname}.pdf"
        valid_pdf = False
        if pdf.is_file():
            with pdf.open("rb") as stream:
                valid_pdf = stream.read(5) == b"%PDF-"
        report["pdf_sha256"] = fingerprint(pdf)["sha256"] if valid_pdf else None
        if not report["failure"]:
            if any(item["severity"] == "error" for item in report["diagnostics"]):
                report["failure"] = "Final engine log contains TeX errors"
            elif not report["source_unchanged"]:
                report["failure"] = "Root source changed during the build; output cannot be verified against its starting hash"
            elif report["input_tracking"]["changed"]:
                report["failure"] = "Recorded local inputs changed between observations: " + ", ".join(report["input_tracking"]["changed"])
            elif report["input_tracking"]["unreadable"]:
                report["failure"] = "Recorded local inputs could not be fingerprinted: " + ", ".join(report["input_tracking"]["unreadable"])
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
        report["local_inputs"] = [observed_inputs[key] for key in sorted(observed_inputs)]
        (output / "build-report.json").write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return report


def argument_parser(source_optional=False, **kwargs):
    """Shared CLI grammar; creating a parser does not probe or run TeX."""
    parser = argparse.ArgumentParser(description=__doc__, **kwargs)
    parser.add_argument("source", type=Path, nargs="?" if source_optional else None,
                        help="Actual root document; relative assets resolve from its directory")
    parser.add_argument("--output", type=Path, required=True, help="New directory for PDF, logs, and JSON evidence")
    parser.add_argument("--engine", choices=ENGINES, default="pdflatex")
    parser.add_argument("--backend", choices=BACKENDS, help="Explicit bibliography backend; omitted means none")
    parser.add_argument("--passes", type=int, help="1–5 engine passes; default 2, 3 with a backend, or maximum 5 with --until-stable")
    parser.add_argument("--timeout", type=float, default=60, help="Seconds per engine/backend process (default 60)")
    parser.add_argument("--jobname", help="Output basename; default: root filename without .tex")
    parser.add_argument("--until-stable", action="store_true", help="Stop on settled auxiliary files and rerun requests; default maximum 5 passes")
    parser.add_argument("--require-resolved", action="store_true", help="Fail if final references/citations or rerun requests remain")
    parser.add_argument("--watch-input", action="append", default=[], metavar="RELATIVE_FILE",
                        help="Repeat to fingerprint explicit local inputs before/after native steps; relative to the root source directory, not the shell cwd")
    return parser


def main(argv=None):
    parser = argument_parser()
    args = parser.parse_args(argv)
    try:
        report = build(args.source, args.output, args.engine, args.backend, args.passes, args.timeout,
                       args.jobname, args.until_stable, args.require_resolved, args.watch_input)
    except (OSError, ValueError) as exc:
        print(f"Build check: {exc}", file=sys.stderr)
        return 2
    print(f"Build {report['status']}: {report['output']}")
    if report["failure"]:
        print(report["failure"], file=sys.stderr)
        if report["failed_step"]:
            step = next(item for item in report["steps"] if item["name"] == report["failed_step"])
            print(f"Failed step: {step['name']}; evidence: {step['log'] or step['transcript']}", file=sys.stderr)
        errors = [item for item in report["diagnostics"] if item["severity"] == "error"]
        if errors:
            step = next(item for item in report["steps"] if item["name"] == report["diagnostic_step"])
            print(f"First recognized error: {step['log'] or step['transcript']}:{errors[0]['log_line']}: {errors[0]['message']}", file=sys.stderr)
    print("Evidence: build-report.json; inspect final diagnostics and the PDF separately.")
    return 0 if report["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
