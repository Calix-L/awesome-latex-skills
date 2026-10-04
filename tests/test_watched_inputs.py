"""Explicit local input guards without inferring which bibliography files ran."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_build as build_fixtures
check_build, REPO = build_fixtures.check_build, build_fixtures.REPO
sys.path.insert(0, str(REPO / "scripts"))
import als
import review_project
from project_support import sha256


class WatchedBuildTests(unittest.TestCase):
    setUp = build_fixtures.BuildTests.setUp
    engine = build_fixtures.BuildTests.engine
    run_build = build_fixtures.BuildTests.run_build

    def resource(self, name="refs.bib", text="@article{x, title={Original}}"):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_explicit_file_is_fingerprinted_without_any_engine_recorder(self):
        self.resource()
        report = self.run_build(watch_inputs=["refs.bib"])
        self.assertEqual(report["status"], "success")
        self.assertEqual(report["input_tracking"]["watched_inputs"], ["refs.bib"])
        self.assertEqual(report["input_tracking"]["recorder_steps"], [])
        item = report["local_inputs"][0]
        self.assertEqual([o["step"] for o in item["observations"]], ["preflight", "engine-01", "engine-02", "final"])
        self.assertTrue(all(o["sha256"] == sha256(self.project / "refs.bib") for o in item["observations"]))

    def test_backend_steps_also_observe_watched_resources(self):
        self.resource("data/文献库.bib")
        self.resource("styles/local.bst", "style")
        for backend in check_build.BACKENDS:
            with self.subTest(backend=backend):
                self.output = self.project / backend
                self.calls.clear()
                report = self.run_build(backend=backend, watch_inputs=["data/文献库.bib", "styles/local.bst"])
                self.assertEqual(report["status"], "success")
                for row in report["local_inputs"]:
                    self.assertEqual([o["step"] for o in row["observations"]],
                                     ["preflight", "engine-01", "bibliography", "engine-02", "engine-03", "final"])

    def test_edit_before_first_engine_observation_is_caught(self):
        path = self.resource()
        def runner(command, **kwargs):
            path.write_text("Author edit", encoding="utf-8")
            return self.engine(command, **kwargs)
        report = self.run_build(runner, watch_inputs=["refs.bib"])
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["input_tracking"]["changed"], ["refs.bib"])
        self.assertIsNone(report["pdf"])
        self.assertEqual(path.read_text(), "Author edit")

    def test_edit_during_backend_cannot_pass_as_stable_input(self):
        path = self.resource()
        def runner(command, **kwargs):
            result = self.engine(command, **kwargs)
            if Path(command[0]).name == "bibtex":
                path.write_text("Changed during bibliography", encoding="utf-8")
            return result
        report = self.run_build(runner, backend="bibtex", watch_inputs=["refs.bib"])
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["input_tracking"]["changed"], ["refs.bib"])
        self.assertTrue(report["source_unchanged"])

    def test_final_observation_catches_late_edit(self):
        path = self.resource()
        original = check_build.auxiliary_hashes
        def edit(output):
            if len(self.calls) == 2:
                path.write_text("Late edit", encoding="utf-8")
            return original(output)
        with patch.object(check_build, "auxiliary_hashes", side_effect=edit):
            report = self.run_build(watch_inputs=["refs.bib"])
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["input_tracking"]["changed"], ["refs.bib"])
        self.assertEqual(report["local_inputs"][0]["observations"][-1]["step"], "final")

    def test_removed_watched_file_is_retained_as_unreadable_evidence(self):
        path = self.resource()
        def runner(command, **kwargs):
            result = self.engine(command, **kwargs)
            if path.exists():
                path.unlink()
            return result
        report = self.run_build(runner, watch_inputs=["refs.bib"])
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["input_tracking"]["unreadable"], ["refs.bib"])
        self.assertTrue(report["local_inputs"][0]["observations"][-1]["error"])
        self.assertEqual(json.loads((self.output / "build-report.json").read_text()), report)

    def test_unselected_file_edits_are_outside_explicit_guard(self):
        path = self.resource()
        def runner(command, **kwargs):
            path.write_text("Changed unused resource", encoding="utf-8")
            return self.engine(command, **kwargs)
        report = self.run_build(runner)
        self.assertEqual(report["status"], "success")
        self.assertEqual(report["input_tracking"]["watched_inputs"], [])
        self.assertEqual(report["local_inputs"], [])

    def test_missing_or_directory_selection_creates_no_output_or_process(self):
        for value in ("missing.bib", "folder"):
            (self.project / "folder").mkdir(exist_ok=True)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "regular file"):
                self.run_build(watch_inputs=[value])
        self.assertFalse(self.output.exists())
        self.assertFalse(self.calls)

    def test_absolute_traversing_and_nonportable_paths_are_refused(self):
        self.resource()
        for value in ("../refs.bib", "/refs.bib", "C:/refs.bib", "\\refs.bib", "a//refs.bib", "./refs.bib", "a/../refs.bib",
                      "a\\refs.bib", "a:refs.bib", "", "a\nb", "a\x00b", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_build(watch_inputs=[value])
        self.assertFalse(self.output.exists())
        self.assertFalse(self.calls)

    def test_symlink_selection_is_refused_without_touching_target(self):
        resource = self.resource()
        link = self.project / "linked.bib"
        try:
            link.symlink_to(resource)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation unavailable")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.run_build(watch_inputs=["linked.bib"])
        self.assertEqual(resource.read_text(), "@article{x, title={Original}}")
        self.assertFalse(self.output.exists())

    def test_symlink_replacement_after_preflight_is_unreadable(self):
        path = self.resource()
        other = self.resource("other.bib")
        trial = self.project / "trial.bib"
        try:
            trial.symlink_to(other)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation unavailable")
        trial.unlink()
        def runner(command, **kwargs):
            result = self.engine(command, **kwargs)
            if not path.is_symlink():
                path.unlink()
                path.symlink_to(other)
            return result
        report = self.run_build(runner, watch_inputs=["refs.bib"])
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["input_tracking"]["unreadable"], ["refs.bib"])

    def test_duplicate_selection_and_recorder_overlap_have_one_observation_per_step(self):
        self.resource()
        def runner(command, **kwargs):
            result = self.engine(command, **kwargs)
            (self.output / "document.fls").write_text(f"PWD {self.project}\nINPUT refs.bib\n", encoding="utf-8")
            return result
        report = self.run_build(runner, watch_inputs=["refs.bib", "refs.bib"])
        self.assertEqual(len(report["local_inputs"]), 1)
        self.assertEqual(report["input_tracking"]["watched_inputs"], ["refs.bib"])
        self.assertEqual(len(report["local_inputs"][0]["observations"]), 4)

    def test_file_identity_overlap_respects_platform_case_rules(self):
        self.resource()
        if os.name != "nt":
            self.resource("REFS.BIB", "Separate case-sensitive input")
        def runner(command, **kwargs):
            result = self.engine(command, **kwargs)
            (self.output / "document.fls").write_text(f"PWD {self.project}\nINPUT refs.bib\n", encoding="utf-8")
            return result
        report = self.run_build(runner, watch_inputs=["REFS.BIB"])
        self.assertEqual(len(report["local_inputs"]), 1 if os.name == "nt" else 2)
        selected = next(row for row in report["local_inputs"] if row["path"] in report["input_tracking"]["watched_inputs"])
        self.assertEqual([o["step"] for o in selected["observations"]], ["preflight", "engine-01", "engine-02", "final"])

    def test_selection_count_and_initial_size_bounds_fail_before_output(self):
        self.resource(text="123456")
        for values in ("refs.bib", ["refs.bib"] * 129):
            with self.assertRaisesRegex(ValueError, "at most"):
                self.run_build(watch_inputs=values)
        with patch.object(check_build, "MAX_WATCH_BYTES", 5):
            with self.assertRaisesRegex(ValueError, "exceeds"):
                self.run_build(watch_inputs=["refs.bib"])
        self.resource("other.bib", "123456")
        with patch.object(check_build, "MAX_WATCH_TOTAL", 10):
            with self.assertRaisesRegex(ValueError, "total bytes"):
                self.run_build(watch_inputs=["refs.bib", "other.bib"])
        self.assertFalse(self.output.exists())

    def test_actual_read_bound_catches_growth_after_size_preflight(self):
        path = self.resource(text="1234")
        original = check_build.fingerprint
        def grow(target, max_bytes=None):
            if target == path:
                path.write_bytes(b"123456")
            return original(target, max_bytes)
        with patch.object(check_build, "MAX_WATCH_BYTES", 5), patch.object(check_build, "fingerprint", side_effect=grow):
            with self.assertRaisesRegex(ValueError, "exceeds"):
                self.run_build(watch_inputs=["refs.bib"])
        self.assertFalse(self.output.exists())

    def test_growth_after_engine_is_unreadable_and_cannot_succeed(self):
        path = self.resource(text="1234")
        def runner(command, **kwargs):
            result = self.engine(command, **kwargs)
            path.write_bytes(b"123456")
            return result
        with patch.object(check_build, "MAX_WATCH_BYTES", 5):
            report = self.run_build(runner, watch_inputs=["refs.bib"])
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["input_tracking"]["unreadable"], ["refs.bib"])

    def test_failed_process_still_records_selected_file_fingerprint(self):
        self.resource()
        def runner(command, **kwargs):
            self.engine(command, **kwargs)
            return subprocess.CompletedProcess(command, 1)
        report = self.run_build(runner, watch_inputs=["refs.bib"])
        self.assertEqual(report["failed_step"], "engine-01")
        self.assertEqual([o["step"] for o in report["local_inputs"][0]["observations"]], ["preflight", "engine-01", "final"])

    def test_timeout_retains_watch_observation_and_native_failure(self):
        self.resource()
        def runner(command, **kwargs):
            raise subprocess.TimeoutExpired(command, 0.1)
        report = self.run_build(runner, watch_inputs=["refs.bib"], timeout=0.1)
        self.assertTrue(report["steps"][0]["timed_out"])
        self.assertEqual(report["local_inputs"][0]["observations"][1]["step"], "engine-01")

    def test_selector_failure_is_independent_of_missing_tools(self):
        with patch.object(check_build.shutil, "which", return_value=None):
            with self.assertRaisesRegex(ValueError, "portable path"):
                self.run_build(watch_inputs=["../refs.bib"])
        self.assertFalse(self.output.exists())

    def test_cli_normalization_preserves_repeat_unicode_and_option_like_values(self):
        self.resource("文献库.bib")
        self.resource("--refs.bib")
        prepared, parsed = als.build_arguments([str(self.source), "--output", str(self.output),
                                                "--watch-input=文献库.bib", "--watch-input=--refs.bib"])
        self.assertEqual(parsed.watch_input, ["文献库.bib", "--refs.bib"])
        self.assertIn("--watch-input=文献库.bib", prepared)
        self.assertIn("--watch-input=--refs.bib", prepared)

    def test_configured_build_selector_is_relative_to_selected_main_directory(self):
        from project_doctor import initialize
        source = self.resource("nested/main.tex", r"\documentclass{article}")
        initialize(self.project, "nested/main.tex")
        prepared, options = als.build_arguments(["--project", str(self.project), "--output", str(self.output), "--watch-input", "refs.bib"])
        self.assertEqual(options.source.resolve(), source)
        self.assertIn("--watch-input=refs.bib", prepared)

    def test_help_does_not_read_watch_inputs_or_create_output(self):
        output = io.StringIO()
        with redirect_stdout(output), patch.object(check_build, "prepare_watched", side_effect=AssertionError("must not read")):
            with self.assertRaises(SystemExit) as result:
                check_build.main(["--watch-input=missing.bib", "--help"])
        self.assertEqual(result.exception.code, 0)
        self.assertIn("--watch-input", output.getvalue())
        self.assertFalse(self.output.exists())


class WatchedReviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="watched-review-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "review"
        for side in ("before", "after"):
            folder = self.root / side
            folder.mkdir()
            (folder / "main.tex").write_text(r"\documentclass{article}Text", encoding="utf-8")
        self.resource = self.root / "after/文献 &.bib"
        self.resource.write_text("@article{x,title={Original}}", encoding="utf-8")
        self.build = self.root / "build"
        (self.build / "logs").mkdir(parents=True)
        (self.build / "logs/engine.txt").write_text("Synthetic failed build evidence", encoding="utf-8")
        self.data = {"schema": 3, "status": "failed", "source": str(self.root / "after/main.tex"),
                     "source_sha256": sha256(self.root / "after/main.tex"),
                     "steps": [{"transcript": "logs/engine.txt"}],
                     "local_inputs": [{"path": self.resource.name, "observations": [
                         {"step": "preflight", "sha256": sha256(self.resource), "error": None},
                         {"step": "final", "sha256": sha256(self.resource), "error": None}]}],
                     "input_tracking": {"watched_inputs": [self.resource.name], "changed": [], "unreadable": []}}

    def run_review(self):
        path = self.build / "build-report.json"
        path.write_text(json.dumps(self.data), encoding="utf-8")
        return review_project.review(self.root / "before", self.root / "after", self.output,
                                     after_build=path, language="zh")

    def test_selected_inputs_are_bound_retained_and_escaped_in_offline_review(self):
        from verify_artifacts import verify_review
        self.run_review()
        data = json.loads((self.output / "review.json").read_text(encoding="utf-8"))
        self.assertEqual(data["builds"]["after"]["watched_inputs"], [self.resource.name])
        self.assertIn("显式监测的输入文件", (self.output / "report.html").read_text(encoding="utf-8"))
        self.assertIn("文献 &amp;.bib", (self.output / "report.html").read_text(encoding="utf-8"))
        self.assertEqual(verify_review(self.output)["status"], "verified")
        retained = json.loads((self.output / "evidence/after/build-report.json").read_text(encoding="utf-8"))
        self.assertEqual(retained, self.data)

    def test_later_bibliography_edit_rejects_stale_build_report(self):
        self.resource.write_text("@article{x,title={Edited after build}}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "recorded input changed"):
            self.run_review()
        self.assertFalse(self.output.exists())

    def test_watch_metadata_needs_matching_input_observations(self):
        self.data["input_tracking"]["watched_inputs"] = ["missing.bib"]
        with self.assertRaisesRegex(ValueError, "starting fingerprint"):
            self.run_review()
        self.assertFalse(self.output.exists())

    def test_watch_metadata_cannot_claim_starting_hash_from_final_only(self):
        self.data["local_inputs"][0]["observations"] = self.data["local_inputs"][0]["observations"][1:]
        with self.assertRaisesRegex(ValueError, "starting fingerprint"):
            self.run_review()
        self.assertFalse(self.output.exists())

    def test_malformed_watch_metadata_returns_value_errors(self):
        for value in (True, "refs.bib", [None], [self.resource.name, self.resource.name], [{}]):
            self.data["input_tracking"]["watched_inputs"] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "unique literal"):
                self.run_review()
        self.assertFalse(self.output.exists())

    def test_malformed_starting_observation_is_not_interpreted(self):
        self.data["local_inputs"][0]["observations"] = ["bad"]
        with self.assertRaisesRegex(ValueError, "starting fingerprint"):
            self.run_review()
        self.assertFalse(self.output.exists())

    def test_malformed_tracking_object_is_refused(self):
        self.data["input_tracking"] = []
        with self.assertRaisesRegex(ValueError, "tracking must be an object"):
            self.run_review()
        self.assertFalse(self.output.exists())

    def test_legacy_build_without_selection_field_remains_compatible(self):
        self.data["input_tracking"].pop("watched_inputs")
        self.run_review()
        data = json.loads((self.output / "review.json").read_text(encoding="utf-8"))
        self.assertEqual(data["builds"]["after"]["watched_inputs"], [])
