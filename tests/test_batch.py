"""Regression controls for repeated-run accounting, not measurements of a model."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import evaluate_batch
from project_support import read_json, write_new_json
from evaluate import cases


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def record_fixture(self, task, session, status="failed"):
        # Deliberately synthetic attribution/measurements for validation tests only.
        record = read_json(task / "run.json")
        record.update(agent="unit-fixture", model="unit-fixture", model_version="unit-fixture",
                      session_id=session, settings={"tools": "unit-fixture"})
        (task / "run.json").write_text(json.dumps(record), encoding="utf-8")
        (task / "transcript.txt").write_text("Synthetic failure transcript for regression testing", encoding="utf-8")
        write_new_json(task / "execution.json", {"schema": 1, "status": status, "transcript": "transcript.txt",
                                                "elapsed_seconds": 1.5, "tokens": None, "cost": None})

    def test_three_trials_prepare_sixty_blind_tasks(self):
        first, second = self.root / "first", self.root / "second"
        result = evaluate_batch.prepare_batch(first)
        evaluate_batch.prepare_batch(second)
        self.assertEqual(result["status"], "prepared-not-run")
        self.assertEqual(result["runs"], 60)
        self.assertEqual(read_json(first / "batch.json"), read_json(second / "batch.json"))
        for row in read_json(first / "batch.json")["runs"]:
            task = first / row["directory"]
            self.assertEqual((task / "context").exists(), row["mode"] == "with-skill")
            self.assertIsNone(read_json(task / "run.json")["model"])
            self.assertFalse((task / "reference").exists())
            self.assertEqual(list((task / "submission").iterdir()), [])
        with self.assertRaises(ValueError):
            evaluate_batch.prepare_batch(first)

    def test_unexecuted_runs_do_not_become_zero_cost_or_success(self):
        batch = self.root / "batch"
        evaluate_batch.prepare_batch(batch, trials=1)
        report = evaluate_batch.report_batch(batch, self.root / "report")
        self.assertEqual(report["comparable_pairs"], 0)
        for mode in report["conditions"].values():
            self.assertEqual(mode["statuses"], {"not-run": 10})
            self.assertIsNone(mode["measured_elapsed_seconds"])
            self.assertIsNone(mode["cost_by_currency"])

    def test_failures_remain_scored_and_missing_human_review_stays_null(self):
        batch, output = self.root / "batch", self.root / "report"
        evaluate_batch.prepare_batch(batch, trials=1)
        for mode in ("baseline", "with-skill"):
            self.record_fixture(batch / f"tasks/polish-scope-01-{mode}", mode)
        evaluate_batch.report_batch(batch, output)
        report = read_json(output / "report.json")
        failed = [item for item in report["runs"] if item["status"] == "failed"]
        self.assertEqual(len(failed), 2)
        self.assertTrue(all(item["score"]["automatic"]["passed"] == 0 for item in failed))
        self.assertTrue(all(item["score"]["human"]["score"] is None for item in failed))
        self.assertEqual(report["comparable_pairs"], 1)
        self.assertIsNone(next(item for item in report["pairs"] if item["comparable"])["human_delta"])

    def test_reused_sessions_across_trials_are_rejected(self):
        batch, output = self.root / "batch", self.root / "report"
        evaluate_batch.prepare_batch(batch, trials=2)
        for trial in (1, 2):
            for mode in ("baseline", "with-skill"):
                task = batch / f"tasks/polish-scope-{trial:02}-{mode}"
                self.record_fixture(task, mode)
                # Synthetic rubric records exercise rejection after both reviews exist.
                excerpt = "Synthetic unit-test review evidence"
                (task / "submission/report.md").write_text(excerpt, encoding="utf-8")
                write_new_json(task / "human-review.json", {"reviewer": "synthetic unit control", "criteria": {
                    item["id"]: {"score": 2, "reason": "Synthetic regression control, not model/human performance data",
                                 "evidence": "report.md:1", "excerpt": excerpt}
                    for item in cases()["polish-scope"]["review"]}})
        evaluate_batch.report_batch(batch, output)
        report = read_json(output / "report.json")
        self.assertEqual(report["comparable_pairs"], 0)
        affected = [item for item in report["pairs"] if item["case_id"] == "polish-scope"]
        self.assertTrue(all("reused" in " ".join(item["reasons"]) for item in affected))
        self.assertTrue(all(item["quality_review"] == "unverified" and item["human_delta"] is None for item in affected))

    def test_batch_traversal_and_missing_coverage_are_refused_before_output(self):
        batch = self.root / "batch"
        evaluate_batch.prepare_batch(batch, trials=1)
        catalog = read_json(batch / "batch.json")
        catalog["runs"][0]["id"] = "../escape"
        (batch / "batch.json").write_text(json.dumps(catalog), encoding="utf-8")
        with self.assertRaises(ValueError):
            evaluate_batch.report_batch(batch, self.root / "report")
        self.assertFalse((self.root / "report").exists())
        catalog["runs"].pop()
        (batch / "batch.json").write_text(json.dumps(catalog), encoding="utf-8")
        with self.assertRaises(ValueError):
            evaluate_batch.report_batch(batch, self.root / "report")

    def test_measurements_require_raw_transcript_and_finite_numbers(self):
        task = self.root / "task"
        task.mkdir()
        (task / "raw.txt").write_text("Actual test fixture transcript", encoding="utf-8")
        record = {"schema": 1, "status": "completed", "elapsed_seconds": 2, "transcript": "raw.txt",
                  "tokens": {"input": 5, "output": 3}, "cost": {"amount": 0.01, "currency": "USD", "source": "test-fixture"}}
        (task / "execution.json").write_text(json.dumps(record), encoding="utf-8")
        self.assertEqual(evaluate_batch.execution_evidence(task)["cost"]["amount"], 0.01)
        for field, value in (("elapsed_seconds", True), ("elapsed_seconds", 10 ** 400), ("transcript", "../external"), ("tokens", {"input": True, "output": 2}),
                             ("cost", {"amount": -1, "currency": "USD", "source": "fixture"})):
            altered = dict(record, **{field: value})
            (task / "execution.json").write_text(json.dumps(altered), encoding="utf-8")
            with self.assertRaises(ValueError):
                evaluate_batch.execution_evidence(task)


if __name__ == "__main__":
    unittest.main()
