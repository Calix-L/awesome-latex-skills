"""Behavior checks for blind preparation, attribution, evidence and release integrity."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_sources
import evaluate
import package_release
import run_examples
from project_support import ROOT, read_json, safe_path, sha256, write_new_json


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def cli(self, *args):
        process = subprocess.run([sys.executable, str(ROOT / "scripts/als.py"), "--json", *args],
                                 cwd=self.folder, capture_output=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        return process, json.loads(process.stdout)

    def candidate(self, case_id):
        for example in run_examples.catalog():
            if example["case_id"] == case_id:
                return ROOT / example["directory"]
        return ROOT / "evaluation/reference-artifacts" / case_id

    def prepared_score(self, mode):
        destination = self.folder / mode
        evaluate.prepare("polish-scope", mode, destination)
        for name in ("output.tex", "report.md"):
            shutil.copyfile(self.candidate("polish-scope") / name, destination / "submission" / name)
        record = read_json(destination / "run.json")
        record.update(agent="unit-test-agent", model="test-model", model_version="fixture-version",
                      settings={"tools": "none", "temperature": 0}, trial="fixture-01", session_id=mode)
        (destination / "run.json").write_text(json.dumps(record), encoding="utf-8")
        return evaluate.score("polish-scope", destination / "submission", destination / "run.json")

    def test_cli_unknown_command_is_structured_failure(self):
        process, report = self.cli("not-a-command")
        self.assertEqual(process.returncode, 2)
        self.assertEqual(report["exit_code"], 2)
        self.assertEqual(report["status"], "failed")
        self.assertIn("Unknown", report["stderr"])

    def test_cli_dispatches_from_other_working_directory(self):
        process, report = self.cli("evaluate", "validate")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(report["result"]["cases"], 10)
        process, report = self.cli("doctor")
        self.assertIn(process.returncode, (0, 1))
        self.assertEqual(Path(report["result"]["python"]["executable"]), Path(sys.executable))

    def test_cli_never_attaches_existing_build_evidence(self):
        destination = self.folder / "old"
        destination.mkdir()
        write_new_json(destination / "build-report.json", {"status": "success", "fake": True})
        process, report = self.cli("build", str(ROOT / "examples/fmt/output.tex"), "--output", str(destination))
        self.assertNotEqual(process.returncode, 0)
        self.assertIsNone(report["result"])
        self.assertEqual(report["evidence"], [])
        self.assertTrue(read_json(destination / "build-report.json")["fake"])

    def test_catalog_and_all_ten_maintainer_candidates(self):
        cases = evaluate.cases()
        self.assertEqual(len(cases), 10)
        self.assertEqual(len({item["skill"] for item in cases.values()}), 5)
        for identifier in cases:
            with self.subTest(identifier=identifier):
                report = evaluate.score(identifier, self.candidate(identifier), kind="maintainer_candidate")
                self.assertEqual(report["automatic"]["passed"], report["automatic"]["total"], report)
                self.assertIsNone(report["human"]["score"])

    def test_prepared_tasks_are_blind_and_inputs_identical(self):
        for mode in ("baseline", "with-skill"):
            evaluate.prepare("rescue-errors", mode, self.folder / mode)
            self.assertEqual(list((self.folder / mode / "submission").iterdir()), [])
            self.assertFalse((self.folder / mode / "cases.json").exists())
            self.assertFalse((self.folder / mode / "reference-artifacts").exists())
        self.assertEqual((self.folder / "baseline/TASK.md").read_bytes(), (self.folder / "with-skill/TASK.md").read_bytes())
        self.assertEqual((self.folder / "baseline/inputs/input.tex").read_bytes(), (self.folder / "with-skill/inputs/input.tex").read_bytes())
        self.assertFalse((self.folder / "baseline/context").exists())
        self.assertTrue((self.folder / "with-skill/context/latex-rescue/scripts/check_build.py").is_file())
        self.assertFalse((self.folder / "with-skill/context/latex-polish").exists())

    def test_prepare_refuses_existing_destination(self):
        self.folder.joinpath("existing").mkdir()
        with self.assertRaisesRegex(ValueError, "new output"):
            evaluate.prepare("polish-scope", "baseline", self.folder / "existing")

    def test_protected_value_negative_control_fails(self):
        shutil.copytree(self.candidate("polish-scope"), self.folder / "submission")
        path = self.folder / "submission/output.tex"
        path.write_text(path.read_text(encoding="utf-8").replace("84.0", "94.0"), encoding="utf-8")
        report = evaluate.score("polish-scope", path.parent, kind="negative_control")
        self.assertLess(report["automatic"]["passed"], report["automatic"]["total"])

    def test_missing_artifact_fails_absence_checks(self):
        report = evaluate.score("polish-scope", self.folder)
        self.assertEqual(report["automatic"]["passed"], 0)

    def test_changed_prepared_input_and_context_are_rejected(self):
        for mode, relative in (("baseline", "inputs/input.tex"), ("with-skill", "context/latex-polish/SKILL.md")):
            self.prepared_score(mode)
            path = self.folder / mode / relative
            with path.open("a", encoding="utf-8") as stream:
                stream.write("changed")
            with self.assertRaises(ValueError):
                evaluate.score("polish-scope", self.folder / mode / "submission", self.folder / mode / "run.json")

    def test_comparison_requires_attribution_and_distinct_sessions(self):
        baseline, treatment = self.prepared_score("baseline"), self.prepared_score("with-skill")
        report = evaluate.compare(baseline, treatment)
        self.assertTrue(report["comparable"])
        self.assertEqual(report["automatic_delta"], 0)
        self.assertIsNone(report["human_delta"])
        self.assertEqual(report["quality_review"], "unverified")
        treatment["run"]["session_id"] = "baseline"
        self.assertFalse(evaluate.compare(baseline, treatment)["comparable"])

    def test_comparison_rejects_changed_settings_and_maintainer_scores(self):
        baseline, treatment = self.prepared_score("baseline"), self.prepared_score("with-skill")
        treatment["run"]["settings"]["temperature"] = 1
        self.assertFalse(evaluate.compare(baseline, treatment)["comparable"])
        candidate = evaluate.score("polish-scope", self.candidate("polish-scope"), kind="maintainer_candidate")
        self.assertFalse(evaluate.compare(candidate, candidate)["comparable"])

    def test_human_review_requires_real_line_excerpt(self):
        case = evaluate.cases()["polish-scope"]
        submission = self.candidate("polish-scope")
        excerpt = (submission / "output.tex").read_text(encoding="utf-8").splitlines()[0]
        review = {"reviewer": "test reviewer", "criteria": {item["id"]: {
            "score": 1, "reason": "Fixture checking evidence validation only", "evidence": "output.tex:1", "excerpt": excerpt} for item in case["review"]}}
        report = evaluate.review_scores(case, submission, review)
        self.assertEqual(report["score"], 4)
        review["criteria"]["meaning"]["excerpt"] = "not on the line"
        with self.assertRaisesRegex(ValueError, "excerpt"):
            evaluate.review_scores(case, submission, review)

    def test_malformed_catalog_and_nonobject_reports_fail_cleanly(self):
        for document in ({"schema": 1, "cases": ["bad"]}, {"schema": 1, "cases": [{"id": "bad", "skill": "latex-rescue", "prompt": "task", "inputs": "bad", "checks": [{}], "review": [{}]}]}):
            path = self.folder / f"catalog-{len(list(self.folder.iterdir()))}.json"
            write_new_json(path, document)
            with self.assertRaises(ValueError):
                evaluate.cases(path)
        with self.assertRaises(ValueError):
            evaluate.compare({"run": []}, {})

    def test_json_duplicate_nonfinite_and_nonobject_rejected(self):
        for content in ('{"key":1,"key":2}', '{"key":NaN}', '[]'):
            path = self.folder / "bad.json"
            path.write_text(content, encoding="utf-8")
            with self.assertRaises(ValueError):
                read_json(path)

    def test_paths_and_existing_report_are_protected(self):
        for value in ("../escape", "/absolute", "C:/outside", "a\\b", "./local"):
            with self.assertRaises(ValueError):
                safe_path(self.folder, value)
        path = self.folder / "score.json"
        write_new_json(path, {"original": True})
        with self.assertRaises(FileExistsError):
            write_new_json(path, {"original": False})
        self.assertTrue(read_json(path)["original"])

    def test_source_review_date_and_verification_semantics(self):
        data = read_json(ROOT / "maintenance/sources.json")
        data["sources"] = data["sources"][:1]
        data["sources"][0]["checked_on"] = "2026-10-04"
        data["sources"][0]["review_after_days"] = 30
        path = self.folder / "sources.json"
        write_new_json(path, data)
        self.assertEqual(audit_sources.audit(path, as_of="2026-10-04")["sources"][0]["status"], "current")
        self.assertEqual(audit_sources.audit(path, as_of="2026-11-03")["sources"][0]["status"], "due")
        with self.assertRaisesRegex(ValueError, "Future"):
            audit_sources.audit(path, as_of="2026-10-03")
        data["sources"][0]["verification"] = "entrypoint-only"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(audit_sources.audit(path, as_of="2026-10-04")["sources"][0]["status"], "entrypoint-only")

    def test_release_is_deterministic_and_checksums_match(self):
        first, second = self.folder / "release-a", self.folder / "release-b"
        package_release.package(first)
        package_release.package(second)
        self.assertEqual({p.name: sha256(p) for p in first.iterdir()}, {p.name: sha256(p) for p in second.iterdir()})
        manifest = read_json(first / "release-manifest.json")
        self.assertEqual(len(manifest["archives"]), 6)
        for item in manifest["archives"]:
            self.assertEqual(item["sha256"], sha256(first / item["file"]))
            with zipfile.ZipFile(first / item["file"]) as archive:
                self.assertEqual(archive.testzip(), None)
                for name in archive.namelist():
                    self.assertNotIn("__pycache__", name)
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), manifest["source_files"][name])
        with self.assertRaisesRegex(ValueError, "new directory"):
            package_release.package(first)

    def test_example_missing_engine_and_portable_evidence(self):
        with patch.object(run_examples.shutil, "which", return_value=None):
            with self.assertRaisesRegex(ValueError, "missing"):
                run_examples.run_examples(self.folder / "strict")
            self.assertFalse((self.folder / "strict").exists())
            report = run_examples.run_examples(self.folder / "portable", allow_unverified=True)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(len(report["examples"]), 5)
        self.assertTrue(all(item["inputs_unchanged"] for item in report["examples"]))
        pdf_case = next(item for item in report["examples"] if item["skill"] == "pdf2tex")
        self.assertEqual(pdf_case["extraction"]["pages"], 2)
        self.assertEqual(pdf_case["builds"]["output.tex"]["status"], "unverified")
        self.assertTrue((self.folder / "portable/pdf2tex/extraction/pages/page-0002.png").is_file())


if __name__ == "__main__":
    unittest.main()
