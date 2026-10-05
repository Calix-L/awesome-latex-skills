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
from project_support import ROOT, read_json, sha256, write_new_json


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
        exported = cwd / "exported-example"
        copied = json.loads(run([command, "--json", "examples", "export", "--case", "full-paper", "--output", exported, "--language", "zh"]))["result"]
        receipt = json.loads((exported / "example.json").read_text(encoding="utf-8"))
        if copied["status"] != "exported-not-run" or receipt["candidate"] != "case/after/main.tex":
            raise ValueError("Installed example export lost initial-copy status or candidate selection")
        if "可编辑的论文案例" not in (exported / "report.html").read_text(encoding="utf-8"):
            raise ValueError("Installed example export lost Chinese offline guide")
        for row in receipt["source_files"]:
            if sha256(exported / row["file"]) != sha256(ROOT / row["source"]):
                raise ValueError("Installed example export differs from the release source")
        if not (exported / "case/after/.als.json").is_file():
            raise ValueError("Installed example export omitted hidden project configuration")
        run([command, "verify", "example", exported])
        relocated = cwd / "relocated-example"
        exported.rename(relocated)
        checked = json.loads(run([command, "--json", "verify", "example", relocated]))["result"]
        if checked["status"] != "verified" or checked["case"] != "full-paper":
            raise ValueError("Installed example verification depended on the initial export directory")
        (relocated / "case/after/main.tex").write_text("Changed after copying", encoding="utf-8")
        damaged = json.loads(run([command, "--json", "verify", "example", relocated], expected=(1,)))["result"]
        if damaged["status"] != "failed" or not any(item["code"] == "changed-file" for item in damaged["findings"]):
            raise ValueError("Installed example verifier missed a changed source")
        pdf_copy = json.loads(run([command, "--json", "examples", "export", "--case", "pdf2tex", "--output", cwd / "pdf-example"]))["result"]
        if pdf_copy["status"] != "exported-not-run" or not (cwd / "pdf-example/case/input.pdf").is_file():
            raise ValueError("Installed PDF example export required optional tools or lost its PDF")
        run([command, "verify", "example", cwd / "pdf-example"])
        main = cwd / "paper/main.tex"
        main.parent.mkdir()
        main.write_text("% \\begin{verbatim}\n\\documentclass{article}\n"
                        "\\begin{document}Example\\\\input{absent} \\verb 1\\input{absent}1\\end{document}\n"
                        "% \\end{verbatim}\n", encoding="utf-8")
        run([command, "project", "init", main.parent, "--main", "main.tex"])
        configured_source_hash = sha256(main)
        configured_hash = sha256(main.parent / ".als.json")
        doctor = json.loads(run([command, "--json", "doctor", "--project", main.parent,
                                 "--skill", "latex-rescue", "--language", "zh"], expected=(0, 1)))["result"]
        if (doctor["engine"] != "pdflatex" or doctor["backend"] is not None
                or doctor["project"]["main"] != "main.tex" or doctor["project"]["root_selection"] != "configuration"
                or doctor["project"]["configuration_sha256"] != configured_hash
                or doctor["project"]["observed_files"] == []):
            raise ValueError("Installed project doctor lost configuration or source evidence")
        human_doctor = run([command, "doctor", "--project", main.parent, "--skill", "latex-rescue", "--language", "zh"], expected=(0, 1))
        if "综合状态" not in human_doctor or "未编译或修改文档" not in human_doctor:
            raise ValueError("Installed doctor lost Chinese operator guidance")
        if sha256(main) != configured_source_hash or sha256(main.parent / ".als.json") != configured_hash:
            raise ValueError("Installed doctor changed its project")
        invalid_doctor = json.loads(run([command, "--json", "doctor", "--project", cwd / "missing-project"], expected=(2,)))
        if "error" not in invalid_doctor["result"] or (cwd / "missing-project").exists():
            raise ValueError("Installed doctor did not retain a read-only project error")
        help_report = json.loads(run([command, "--json", "build", "--project", cwd / "missing-project", "--help"]))
        if (help_report["invocation"] is not None or "--project" not in help_report["stdout"]
                or "--watch-input" not in help_report["stdout"] or help_report["evidence"]):
            raise ValueError("Installed build help incorrectly required a project or attempted execution")
        rejected = json.loads(run([command, "--json", "build", "--project", main.parent,
                                   "--out=" + str(cwd / "unused-build"), "--engine=invalid"], expected=(2,)))
        if rejected["invocation"] is not None or (cwd / "unused-build").exists() or rejected["result"] is not None:
            raise ValueError("Installed argument preflight ran a build or retained unrelated evidence")
        rejected_watch = json.loads(run([command, "--json", "build", "--project", main.parent,
                                         "--output", cwd / "invalid-watch-build", "--watch-input=../escape.bib"], expected=(2,)))
        if (rejected_watch["invocation"] is None or rejected_watch["result"] is not None
                or rejected_watch["evidence"] or (cwd / "invalid-watch-build").exists()
                or "portable path" not in rejected_watch["stderr"]):
            raise ValueError("Installed watched-input validation depended on native tools or wrote partial output")
        standalone = cwd / "standalone-invalid-watch"
        run([python, cwd / "skills/latex-rescue/scripts/check_build.py", main,
             "--output", standalone, "--watch-input=../escape.bib"], expected=(2,))
        if standalone.exists():
            raise ValueError("Installed standalone skill created output for an invalid watch selector")
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
        (bib_project / "main.tex").write_text(r"\documentclass{article}\parencites(see)(together)[{nested ] note}]{brace,paren}[p. 2]{percent,comment-active}\textcite{fake-braced}\autocite{fake-quoted}\Parencite{fake-string}\bibliography{refs}", encoding="utf-8")
        bib_report = json.loads(run([command, "--json", "project", "check", bib_project, "--backend", "bibtex",
                                     "--bundle", cwd / "bibliography-inspection", "--html-language", "zh"], expected=(0, 1)))["result"]
        if ({item["key"] for item in bib_report["bibliography_entries"]} != {"brace", "paren", "percent", "comment-active"}
                or sum(item["code"] == "unknown-citation" for item in bib_report["diagnostics"]) != 3
                or "参考文献字面条目头" not in (cwd / "bibliography-inspection/report.html").read_text(encoding="utf-8")):
            raise ValueError("Installed bibliography header inventory confused literal values with entries")
        if not any(item["file"] == "refs.bib" and item["sha256"] == sha256(bib_project / "refs.bib") for item in bib_report["observed_files"]):
            raise ValueError("Installed bibliography inventory was not bound to parsed database bytes")
        if ([item["key"] for item in bib_report["citation_inventory"]] != ["brace", "paren", "percent", "comment-active", "fake-braced", "fake-quoted", "fake-string"]
                or [item["group"] for item in bib_report["citation_inventory"][:4]] != [1, 1, 2, 2]
                or any(item["code"] == "citation-unverified" for item in bib_report["diagnostics"])
                or "带源码位置的文献引用" not in (cwd / "bibliography-inspection/report.html").read_text(encoding="utf-8")):
            raise ValueError("Installed citation inventory lost common commands or later multicite groups")
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
        math_original, math_candidate = cwd / "math-original", cwd / "math-candidate"
        for folder, operator in ((math_original, "+"), (math_candidate, "-")):
            folder.mkdir()
            (folder / "main.tex").write_text(r"\documentclass{article}\begin{document}" +
                                             rf"\begin{{equation}}x{operator}y\end{{equation}}" +
                                             r"\end{document}", encoding="utf-8")
        math_output = cwd / "math-review"
        math_result = json.loads(run([command, "--json", "review", "--before", math_original, "--after", math_candidate,
                                      "--output", math_output, "--language", "zh"]))["result"]
        math_report = read_json(math_output / "review.json")
        if (math_result["content_flags"] != 1 or math_result["source_scan_issues"] != 0
                or set(math_report["content_audit"][0]) != {"file", "requires_review", "math_environments"}
                or math_report["math_environment_inventory"]["after"][0]["content"] != "x-y"
                or "带源码位置的公式环境" not in (math_output / "report.html").read_text(encoding="utf-8")):
            raise ValueError("Installed formula review missed an operator-only change")
        run([command, "verify", "review", math_output])
        cite_before, cite_after = cwd / "citation-original", cwd / "citation-candidate"
        for folder, key in ((cite_before, "old"), (cite_after, "new")):
            folder.mkdir()
            (folder / "main.tex").write_text(r"\documentclass{article}\parencites{same}{" + key + "}", encoding="utf-8")
        cite_output = cwd / "citation-review"
        cite_result = json.loads(run([command, "--json", "review", "--before", cite_before, "--after", cite_after,
                                      "--output", cite_output, "--language", "zh"]))["result"]
        cite_report = read_json(cite_output / "review.json")
        if (cite_result["content_flags"] != 1 or cite_result["source_scan_issues"] != 0
                or set(cite_report["content_audit"][0]) != {"file", "requires_review", "reference_keys"}
                or cite_report["citation_inventory"]["after"][1]["key"] != "new"
                or "带源码位置的文献引用" not in (cite_output / "report.html").read_text(encoding="utf-8")):
            raise ValueError("Installed citation review missed a second-group key-only change")
        run([command, "verify", "review", cite_output])
        ref_project = cwd / "reference-paper"
        ref_project.mkdir()
        (ref_project / "main.tex").write_text("\\documentclass{article}\n\\label{a,b}\\ref{a,b}\n\\input{two}\n\\crefrange{start}{missing}\\hyperref[start]{See section}", encoding="utf-8")
        (ref_project / "two.tex").write_text("\\label{start}\n\\label{a,b}", encoding="utf-8")
        ref_report = json.loads(run([command, "--json", "project", "check", ref_project,
                                     "--bundle", cwd / "reference-inspection", "--html-language", "zh"], expected=(0, 1)))["result"]
        duplicate = [r for r in ref_report["diagnostics"] if r["code"] == "duplicate-label"]
        if (len(duplicate) != 1 or duplicate[0]["file"] != "two.tex" or duplicate[0]["line"] != 2
                or [r["key"] for r in ref_report["reference_inventory"]] != ["a,b", "start", "missing", "start"]
                or [r["resolution"] for r in ref_report["reference_inventory"]] != ["ambiguous", "defined", "missing", "defined"]
                or "标签定义与交叉引用" not in (cwd / "reference-inspection/report.html").read_text(encoding="utf-8")):
            raise ValueError("Installed cross-reference inspection lost duplicate locations, comma keys or range endpoints")
        run([command, "verify", "inspection", cwd / "reference-inspection"])
        ref_before, ref_after = cwd / "reference-original", cwd / "reference-candidate"
        for folder, values in ((ref_before, "{a}{b}"), (ref_after, "{b}{a}")):
            folder.mkdir()
            (folder / "main.tex").write_text(r"\documentclass{article}\crefrange" + values, encoding="utf-8")
        ref_output = cwd / "reference-review"
        ref_result = json.loads(run([command, "--json", "review", "--before", ref_before, "--after", ref_after,
                                     "--output", ref_output, "--language", "zh"]))["result"]
        ref_record = read_json(ref_output / "review.json")
        if (ref_result["content_flags"] != 1 or ref_result["source_scan_issues"] != 0
                or set(ref_record["content_audit"][0]) != {"file", "requires_review", "reference_keys"}
                or ref_record["reference_inventory"]["after"][1]["key"] != "a"
                or "标签定义与交叉引用" not in (ref_output / "report.html").read_text(encoding="utf-8")):
            raise ValueError("Installed source review missed reversed range endpoints")
        run([command, "verify", "review", ref_output])
        manual = cwd / "manual-paper"
        manual.mkdir()
        (manual / "main.tex").write_text("\\documentclass{article}\n\\cite{a,b,missing}\\input{references}", encoding="utf-8")
        (manual / "references.tex").write_text("\\bibitem[Author(2020)]{a} Synthetic entry.\n\\bibitem{b} Other.\n\\bibitem{a} Duplicate.", encoding="utf-8")
        manual_output = cwd / "manual-inspection"
        manual_report = json.loads(run([command, "--json", "project", "check", manual, "--bundle", manual_output,
                                        "--html-language", "zh"], expected=(0, 1)))["result"]
        duplicate = [r for r in manual_report["diagnostics"] if r["code"] == "duplicate-bibitem-key"]
        unknown = [r for r in manual_report["diagnostics"] if r["code"] == "unknown-citation"]
        if (len(duplicate) != 1 or (duplicate[0]["file"], duplicate[0]["line"]) != ("references.tex", 3)
                or "references.tex:1" not in duplicate[0]["message"] or len(unknown) != 1
                or not unknown[0]["message"].endswith(" missing") or manual_report["backend"] is not None
                or [r["key"] for r in manual_report["bibitem_inventory"]] != ["a", "b", "a"]
                or "手写参考文献条目" not in (manual_output / "report.html").read_text(encoding="utf-8")):
            raise ValueError("Installed manual bibliography inspection lost keys or duplicate/unknown locations")
        run([command, "verify", "inspection", manual_output])
        manual_before, manual_after = cwd / "manual-original", cwd / "manual-candidate"
        for folder, key in ((manual_before, "old"), (manual_after, "new")):
            folder.mkdir()
            (folder / "main.tex").write_text(r"\documentclass{article}\bibitem[Author]{" + key + "} Synthetic entry.", encoding="utf-8")
        manual_review = cwd / "manual-review"
        manual_result = json.loads(run([command, "--json", "review", "--before", manual_before, "--after", manual_after,
                                         "--output", manual_review, "--language", "zh"]))["result"]
        manual_record = read_json(manual_review / "review.json")
        if (manual_result["content_flags"] != 1 or manual_result["source_scan_issues"] != 0
                or set(manual_record["content_audit"][0]) != {"file", "requires_review", "reference_keys"}
                or manual_record["bibitem_inventory"]["after"][0]["key"] != "new"
                or "手写参考文献条目" not in (manual_review / "report.html").read_text(encoding="utf-8")):
            raise ValueError("Installed review missed a manual bibliography definition-only edit")
        run([command, "verify", "review", manual_review])
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
