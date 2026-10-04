"""Synthetic child-process controls; never model performance measurements."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import benchmark_runner
import evaluate_batch
from evaluate import score
from project_support import read_json, write_new_json


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.batch = self.root / "batch"
        evaluate_batch.prepare_batch(self.batch, trials=1, case_ids=["polish-scope"])
        self.task = self.batch / "tasks/polish-scope-01-baseline"
        self.spec = self.root / "spec.json"

    def specification(self, code, session="synthetic-baseline"):
        program = self.root / (session + ".py")
        program.write_text(code, encoding="utf-8")
        document = {"schema": 1, "command": [sys.executable, "-I", str(program)],
                    "agent": "synthetic-test-process", "model": "no-model",
                    "model_version": "no-model", "session_id": session,
                    "settings": {"purpose": "regression control only"}}
        self.spec.write_text(json.dumps(document), encoding="utf-8")
        return self.spec

    def test_subset_schedule_is_complete_and_legacy_catalog_still_works(self):
        self.assertEqual(len(read_json(self.batch / "batch.json")["runs"]), 2)
        result = evaluate_batch.report_batch(self.batch, self.root / "subset-report")
        self.assertEqual(result["scheduled_runs"], 2)
        self.assertIsNone(result["conditions"]["baseline"]["tokens"])
        self.assertEqual(result["conditions"]["baseline"]["token_measured_runs"], 0)
        legacy = self.root / "legacy"
        evaluate_batch.prepare_batch(legacy, trials=1)
        catalog = read_json(legacy / "batch.json")
        del catalog["case_ids"]
        (legacy / "batch.json").write_text(json.dumps(catalog), encoding="utf-8")
        self.assertEqual(evaluate_batch.report_batch(legacy, self.root / "legacy-report")["scheduled_runs"], 20)
        for selection in ([], ["unknown"], ["polish-scope", "polish-scope"]):
            with self.assertRaises(ValueError):
                evaluate_batch.prepare_batch(self.root / "invalid", case_ids=selection)
        self.assertFalse((self.root / "invalid").exists())

    def test_command_gets_identical_prompt_and_only_prepared_working_directory(self):
        spec = self.specification("from pathlib import Path\nimport sys\n"
                                  "prompt = sys.stdin.buffer.read()\n"
                                  "assert prompt == Path('TASK.md').read_bytes()\n"
                                  "assert not Path('context').exists()\n"
                                  "Path('submission/report.md').write_text('Synthetic output', encoding='utf-8')\n"
                                  "sys.stdout.buffer.write(b'raw-output\\xff')\n")
        result = benchmark_runner.run_task(self.task, spec)
        self.assertEqual(result["status"], "completed")
        self.assertIsNone(result["integrity_error"])
        self.assertGreaterEqual(result["elapsed_seconds"], 0)
        evidence = evaluate_batch.execution_evidence(self.task)
        self.assertEqual(evidence["exit_code"], 0)
        self.assertEqual(set(evidence["submission_sha256"]), {"report.md"})
        self.assertIsNone(evidence["tokens"])
        self.assertIsNone(evidence["cost"])
        self.assertIn(b"raw-output\xff", (self.task / evidence["transcript"]).read_bytes())
        before = (self.task / "run.json").read_bytes()
        with self.assertRaises(ValueError):
            benchmark_runner.run_task(self.task, spec)
        self.assertEqual((self.task / "run.json").read_bytes(), before)

    def test_failed_command_is_retained_and_not_reported_as_success(self):
        result = benchmark_runner.run_task(self.task, self.specification("import sys\nprint('synthetic failure')\nsys.exit(7)\n"))
        self.assertEqual((result["status"], result["exit_code"]), ("failed", 7))
        evaluate_batch.report_batch(self.batch, self.root / "report")
        report = read_json(self.root / "report/report.json")
        failed = next(item for item in report["runs"] if item["mode"] == "baseline")
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["score"]["automatic"]["passed"], 0)
        self.assertEqual(report["conditions"]["baseline"]["elapsed_measured_runs"], 1)
        self.assertIn("| polish-scope | 1 | baseline | failed |", (self.root / "report/report.md").read_text(encoding="utf-8"))

    def test_timeout_and_startup_failure_retain_transcript(self):
        result = benchmark_runner.run_task(self.task, self.specification("import time\nprint('started', flush=True)\ntime.sleep(10)\n"), timeout=0.7)
        self.assertEqual(result["status"], "timeout")
        self.assertIn(b"status=timeout", (self.task / "runner/transcript.log").read_bytes())
        other = self.batch / "tasks/polish-scope-01-with-skill"
        document = read_json(self.spec)
        document["command"] = [str(self.root / "missing-executable")]
        document["session_id"] = "synthetic-startup-failure"
        self.spec.write_text(json.dumps(document), encoding="utf-8")
        result = benchmark_runner.run_task(other, self.spec)
        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["exit_code"])
        self.assertTrue(read_json(other / "execution.json")["error"])
        self.assertFalse((other / ".execution.lock").exists())

    def test_record_transcript_and_complete_submission_are_bound_to_execution(self):
        benchmark_runner.run_task(self.task, self.specification("from pathlib import Path\nPath('submission/report.md').write_text('fixture')\n"))
        for relative in ("run.json", "runner/transcript.log", "submission/report.md"):
            path = self.task / relative
            original = path.read_bytes()
            path.write_bytes(original + (b" " if relative == "run.json" else b"changed"))
            with self.assertRaises(ValueError):
                evaluate_batch.execution_evidence(self.task)
            path.write_bytes(original)
        added = self.task / "submission/extra.txt"
        added.write_text("unrecorded", encoding="utf-8")
        with self.assertRaises(ValueError):
            evaluate_batch.execution_evidence(self.task)
        evaluate_batch.report_batch(self.batch, self.root / "tampered-report")
        bad = next(item for item in read_json(self.root / "tampered-report/report.json")["runs"] if item["mode"] == "baseline")
        self.assertEqual(bad["status"], "invalid-evidence")
        self.assertEqual(bad["unverified_execution_record"]["status"], "completed")

    def test_command_changing_prepared_inputs_is_retained_but_rejected(self):
        spec = self.specification("from pathlib import Path\np = next(Path('inputs').rglob('*.tex'))\np.write_text('changed')\n")
        result = benchmark_runner.run_task(self.task, spec)
        self.assertEqual(result["status"], "completed")
        self.assertIn("inputs", result["integrity_error"].lower())
        with self.assertRaises(ValueError):
            evaluate_batch.execution_evidence(self.task)

    def test_failed_exit_cannot_be_relabelled_completed(self):
        benchmark_runner.run_task(self.task, self.specification("import sys\nsys.exit(7)\n"))
        evidence = read_json(self.task / "execution.json")
        evidence["status"] = "completed"
        (self.task / "execution.json").write_text(json.dumps(evidence), encoding="utf-8")
        with self.assertRaises(ValueError):
            evaluate_batch.execution_evidence(self.task)

    def test_missing_attribution_and_active_locks_do_not_mutate_task(self):
        self.specification("print('fixture')\n")
        document = read_json(self.spec)
        document["model_version"] = None
        self.spec.write_text(json.dumps(document), encoding="utf-8")
        before = (self.task / "run.json").read_bytes()
        with self.assertRaises(ValueError):
            benchmark_runner.run_task(self.task, self.spec)
        self.assertFalse((self.task / "runner").exists())
        self.specification("print('fixture')\n")
        (self.task / ".execution.lock").mkdir()
        with self.assertRaises(FileExistsError):
            benchmark_runner.run_task(self.task, self.spec)
        self.assertEqual((self.task / "run.json").read_bytes(), before)

    def test_empty_review_template_is_outside_task_and_cannot_score_as_human_review(self):
        destination = self.root / "review.json"
        result = benchmark_runner.review_template(self.task, destination)
        self.assertEqual(result["status"], "unfilled")
        template = read_json(destination)
        self.assertEqual(len(template["criteria"]), 4)
        self.assertTrue(all(item["score"] is None for item in template["criteria"].values()))
        with self.assertRaises(ValueError):
            score("polish-scope", self.task / "submission", self.task / "run.json", destination)
        with self.assertRaises(ValueError):
            benchmark_runner.review_template(self.task, self.task / "rubric.json")

    def test_build_tool_failure_does_not_discard_valid_pair(self):
        for mode in ("baseline", "with-skill"):
            task = self.batch / f"tasks/polish-scope-01-{mode}"
            spec = self.specification("print('synthetic process')\n", session="synthetic-" + mode)
            benchmark_runner.run_task(task, spec)
        with patch.object(evaluate_batch, "compile_submission", side_effect=RuntimeError("test tool failure")):
            result = evaluate_batch.report_batch(self.batch, self.root / "tool-report")
        self.assertEqual(result["comparable_pairs"], 1)
        runs = read_json(self.root / "tool-report/report.json")["runs"]
        self.assertTrue(all(item["status"] == "completed" for item in runs))
        self.assertTrue(all(item["compilation"]["status"] == "unverified" for item in runs))

    def test_cli_preserves_failed_runner_outcome_in_json_envelope(self):
        spec = self.specification("import sys\nsys.exit(9)\n")
        cli = Path(__file__).resolve().parents[1] / "scripts/als.py"
        result = subprocess.run([sys.executable, str(cli), "--json", "benchmark", "run", "--task", str(self.task), "--spec", str(spec)],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 1, result.stderr)
        envelope = json.loads(result.stdout)
        self.assertEqual(envelope["result"]["exit_code"], 9)
        self.assertEqual(envelope["result"]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
