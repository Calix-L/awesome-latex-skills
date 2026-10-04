#!/usr/bin/env python3
"""Install a wheel in a fresh environment and verify commands outside the checkout."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv
import zipfile

from install import SKILLS, bundle_files
from project_support import ROOT, sha256, write_new_json


def check_distribution(wheel, output):
    wheel = Path(wheel).resolve()
    output = Path(output).expanduser().absolute()
    if not wheel.is_file() or wheel.suffix != ".whl" or output.exists() or output.is_symlink():
        raise ValueError("Supply a wheel and a new verification directory")
    output = output.resolve()
    with zipfile.ZipFile(wheel) as archive:
        required = {"awesome_latex_skills/data/VERSION", "awesome_latex_skills/data/scripts/als.py",
                    "awesome_latex_skills/data/evaluation/cases.json", "awesome_latex_skills/data/examples/pdf2tex/input.pdf"}
        if not required.issubset(archive.namelist()) or archive.testzip():
            raise ValueError("Wheel resources are incomplete/corrupt")
        for name in archive.namelist():
            if "__pycache__" in name or ".git/" in name or "/work/" in name:
                raise ValueError(f"Generated/private files entered the wheel: {name}")
    output.mkdir(parents=True)
    environment = output / "environment"
    venv.EnvBuilder(with_pip=True).create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    command = environment / ("Scripts/als.exe" if os.name == "nt" else "bin/als")
    cwd = output / "outside-checkout"
    cwd.mkdir()
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("PYTHONPATH", None)
    steps = []
    def run(args, expected=(0,)):
        result = subprocess.run([str(item) for item in args], cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)
        steps.append({"arguments": [str(item) for item in args], "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode not in expected:
            raise ValueError(f"Distribution command failed: {result.stderr or result.stdout}")
        return result.stdout
    try:
        run([python, "-m", "pip", "install", "--no-deps", wheel])
        version = run([command, "--version"]).strip()
        metadata = json.loads(run([python, "-I", "-m", "awesome_latex_skills", "--json", "--version"]))
        if metadata["result"]["version"] != version:
            raise ValueError("Console and module entry points disagree")
        report = json.loads(run([command, "--json", "doctor", "--skill", "paper-read"]))
        if Path(report["result"]["python"]["executable"]).resolve() != python.resolve():
            raise ValueError("CLI used a different Python environment")
        run([command, "install", "--dest", cwd / "skills"])
        for skill in SKILLS:
            if bundle_files(cwd / "skills" / skill) != bundle_files(ROOT / skill):
                raise ValueError(f"Installed skill differs from release resources: {skill}")
        run([command, "evaluate", "validate"])
        # Synthetic local process; no provider call or model-quality measurement.
        run([command, "benchmark", "prepare", "--case", "polish-scope", "--trials", "1", "--output", cwd / "batch"])
        spec = cwd / "synthetic-runner.json"
        write_new_json(spec, {"schema": 1, "command": [str(python), "-I", "-c", "print('Synthetic package smoke test; no model called')"],
                              "agent": "synthetic-package-control", "model": "no-model", "model_version": "no-model",
                              "session_id": "synthetic-package-baseline", "settings": {"purpose": "packaging control only"}})
        task = cwd / "batch/tasks/polish-scope-01-baseline"
        run([command, "benchmark", "run", "--task", task, "--spec", spec])
        run([command, "benchmark", "review-template", "--task", task, "--output", cwd / "review-template.json"])
        summary = json.loads(run([command, "--json", "benchmark", "report", "--batch", cwd / "batch", "--output", cwd / "batch-report"]))["result"]
        if summary["scheduled_runs"] != 2 or summary["conditions"]["baseline"]["statuses"] != {"completed": 1} or summary["comparable_pairs"]:
            raise ValueError("Installed benchmark did not retain the expected synthetic control and missing pair")
        main = cwd / "paper/main.tex"
        main.parent.mkdir()
        main.write_text("% \\begin{verbatim}\n\\documentclass{article}\n"
                        "\\begin{document}Example\\\\input{absent} \\verb 1\\input{absent}1\\end{document}\n"
                        "% \\end{verbatim}\n", encoding="utf-8")
        run([command, "project", "init", main.parent, "--main", "main.tex"])
        help_report = json.loads(run([command, "--json", "build", "--project", cwd / "missing-project", "--help"]))
        if help_report["invocation"] is not None or "--project" not in help_report["stdout"] or help_report["evidence"]:
            raise ValueError("Installed build help incorrectly required a project or attempted execution")
        rejected = json.loads(run([command, "--json", "build", "--project", main.parent,
                                   "--out=" + str(cwd / "unused-build"), "--engine=invalid"], expected=(2,)))
        if rejected["invocation"] is not None or (cwd / "unused-build").exists() or rejected["result"] is not None:
            raise ValueError("Installed argument preflight ran a build or retained unrelated evidence")
        if not (main.parent / ".als.json").is_file():
            raise ValueError("Installed CLI did not initialize the selected project")
        inspection = json.loads(run([command, "--json", "project", "check", main.parent,
                                     "--output", cwd / "inspection.json", "--html", cwd / "inspection.html",
                                     "--html-language", "zh"], expected=(0, 1)))["result"]
        if (inspection["main"] != "main.tex" or inspection["root_selection"] != "configuration"
                or any(item["code"] != "missing-engine" for item in inspection["diagnostics"])
                or "LaTeX 项目检查" not in (cwd / "inspection.html").read_text(encoding="utf-8")):
            raise ValueError("Installed project inspection/report resources failed first-use checks")
        if ({item["file"] for item in inspection["observed_files"]} != {".als.json", "main.tex"}
                or inspection["dependencies"]):
            raise ValueError("Installed scanner mistook comment/verbatim/control-symbol examples for dependencies")
        sealed = json.loads(run([command, "--json", "project", "check", main.parent,
                                 "--bundle", cwd / "sealed-inspection", "--html-language", "zh"], expected=(0, 1)))["result"]
        if sealed["status"] != inspection["status"] or sealed["observed_files"] != inspection["observed_files"]:
            raise ValueError("Installed sealed inspection disagreed with the separate reports")
        transferred = cwd / "transferred-inspection"
        (cwd / "sealed-inspection").rename(transferred)
        main.parent.rename(cwd / "paper-moved")
        checked = json.loads(run([command, "--json", "verify", "inspection", transferred]))["result"]
        if checked["status"] != "verified" or checked["files_checked"] != 2:
            raise ValueError("Installed inspection verifier required original project/report paths")
        # Restore only for the subsequent before/after review smoke test.
        (cwd / "paper-moved").rename(main.parent)
        (transferred / "report.html").write_text("Changed after delivery", encoding="utf-8")
        damaged = json.loads(run([command, "--json", "verify", "inspection", transferred], expected=(1,)))["result"]
        if damaged["status"] != "failed" or not any(item["code"] == "changed-file" for item in damaged["findings"]):
            raise ValueError("Installed verifier missed a changed inspection page")
        bib_project = cwd / "bibliography-paper"
        bib_project.mkdir()
        shutil.copyfile(ROOT / "tests/fixtures/bibliography/headers.bib", bib_project / "refs.bib")
        (bib_project / "main.tex").write_text(r"\documentclass{article}\cite{brace,paren,percent,comment-active,fake-braced,fake-quoted,fake-string}\bibliography{refs}", encoding="utf-8")
        bib_report = json.loads(run([command, "--json", "project", "check", bib_project, "--backend", "bibtex",
                                     "--bundle", cwd / "bibliography-inspection", "--html-language", "zh"], expected=(0, 1)))["result"]
        if ({item["key"] for item in bib_report["bibliography_entries"]} != {"brace", "paren", "percent", "comment-active"}
                or sum(item["code"] == "unknown-citation" for item in bib_report["diagnostics"]) != 3
                or "参考文献字面条目头" not in (cwd / "bibliography-inspection/report.html").read_text(encoding="utf-8")):
            raise ValueError("Installed bibliography header inventory confused literal values with entries")
        if not any(item["file"] == "refs.bib" and item["sha256"] == sha256(bib_project / "refs.bib") for item in bib_report["observed_files"]):
            raise ValueError("Installed bibliography inventory was not bound to parsed database bytes")
        run([command, "verify", "inspection", cwd / "bibliography-inspection"])
        candidate = cwd / "candidate"
        candidate.mkdir()
        (candidate / "main.tex").write_text("\\documentclass{article}\n\\begin{document}Example 42\\end{document}\nTODO: confirm value\n", encoding="utf-8")
        reviewed = json.loads(run([command, "--json", "review", "--before", main.parent, "--after", candidate,
                                   "--output", cwd / "source-review", "--language", "zh"]))["result"]
        if (reviewed["builds"] != {"before": "unverified", "after": "unverified"}
                or reviewed["content_flags"] != 1 or reviewed["open_decisions"] != 1
                or "论文修改审阅" not in (cwd / "source-review/report.html").read_text(encoding="utf-8")):
            raise ValueError("Installed offline source review failed first-use checks")
        integrity = json.loads(run([command, "--json", "verify", "review", cwd / "source-review"]))["result"]
        if integrity["status"] != "verified" or integrity["files_checked"] != 3:
            raise ValueError("Installed offline artifact verifier failed first-use checks")
        (cwd / "source-review/changes.diff").write_text("Changed after delivery", encoding="utf-8")
        failed = json.loads(run([command, "--json", "verify", "review", cwd / "source-review"], expected=(1,)))["result"]
        if failed["status"] != "failed" or not any(item["code"] == "changed-file" for item in failed["findings"]):
            raise ValueError("Installed verifier missed a changed source diff")
        result = {"schema": 1, "status": "verified", "version": version, "wheel_sha256": sha256(wheel), "steps": steps}
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        result = {"schema": 1, "status": "failed", "error": str(exc), "steps": steps}
    write_new_json(output / "verification.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = check_distribution(args.wheel, args.output)
        print(json.dumps({key: value for key, value in result.items() if key != "steps"}, ensure_ascii=True))
        return 0 if result["status"] == "verified" else 1
    except (OSError, ValueError) as exc:
        print(f"Distribution: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
