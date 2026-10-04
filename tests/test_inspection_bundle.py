"""Failure-safe publication and portable checks of static inspection deliveries."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import inspection_bundle as exporter
import project_doctor
import project_report
from project_support import read_json
import verify_artifacts as verifier


class InspectionBundleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.project = self.root / "paper"
        self.project.mkdir()
        self.source = self.project / "main.tex"
        self.source.write_text("\\documentclass{article}\n\\input{part}\n", encoding="utf-8")
        (self.project / "part.tex").write_text("Supplied text 42\n", encoding="utf-8")
        self.output = self.root / "inspection #1"

    def export(self, **kwargs):
        return exporter.export_inspection(self.project, self.output, **kwargs)

    def assert_unpublished(self):
        self.assertFalse(self.output.exists())
        self.assertEqual(sorted(path.name for path in self.root.iterdir()), ["paper"])

    def cli(self, *arguments):
        cli = Path(__file__).resolve().parents[1] / "scripts/als.py"
        result = subprocess.run([sys.executable, str(cli), "--json", *map(str, arguments)],
                                capture_output=True, text=True, encoding="utf-8")
        return result.returncode, json.loads(result.stdout)

    def test_chinese_export_binds_files_and_preserves_sources(self):
        original = {path.name: path.read_bytes() for path in self.project.iterdir()}
        result = self.export(language="zh")
        self.assertEqual(result["status"], "needs-review")
        self.assertEqual(read_json(self.output / "inspection.json"), result)
        self.assertEqual({path.name for path in self.output.iterdir()}, {"inspection.json", "report.html", "integrity.json"})
        page = (self.output / "report.html").read_text(encoding="utf-8")
        self.assertIn("LaTeX 项目检查", page)
        self.assertIn('href="inspection.json"', page)
        self.assertIn('href="integrity.json"', page)
        self.assertNotIn("<script", page)
        self.assertEqual(verifier.verify_inspection(self.output)["files_checked"], 2)
        self.assertEqual(original, {path.name: path.read_bytes() for path in self.project.iterdir()})

    def test_moved_bundle_verifies_without_original_manuscript_or_export_paths(self):
        self.export()
        transferred = self.root / "received"
        shutil.copytree(self.output, transferred)
        self.project.rename(self.root / "paper-renamed")
        self.output.rename(self.root / "old-export")
        before = {path.name: path.read_bytes() for path in transferred.iterdir()}
        result = verifier.verify_inspection(transferred)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["target_kind"], "inspection")
        self.assertEqual(result["authentication"], "not verified")
        self.assertEqual(before, {path.name: path.read_bytes() for path in transferred.iterdir()})

    def test_blocked_cli_still_exports_a_verifiable_diagnostic_bundle(self):
        self.source.write_text("\\documentclass{article}\\input{missing}", encoding="utf-8")
        code, envelope = self.cli("project", "check", self.project, "--bundle", self.output)
        self.assertEqual(code, 1)
        self.assertEqual(envelope["result"]["status"], "blocked")
        self.assertEqual(read_json(self.output / "inspection.json")["status"], "blocked")
        code, check = self.cli("verify", "inspection", self.output)
        self.assertEqual(code, 0)
        self.assertEqual(check["result"]["status"], "verified")

    def test_ambiguous_roots_keep_complete_observations(self):
        (self.project / "other.tex").write_text("\\documentclass{article}", encoding="utf-8")
        result = self.export()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual({item["file"] for item in result["observed_files"]}, {"main.tex", "part.tex", "other.tex"})
        self.assertEqual(verifier.verify_inspection(self.output)["status"], "verified")

    def test_preflight_refuses_existing_and_internal_destinations_before_inspection(self):
        existing = self.root / "existing"
        existing.mkdir()
        (existing / "keep").write_bytes(b"retained")
        for output in (existing, self.source, self.project / "generated/report", self.project):
            with self.subTest(output=output), patch.object(exporter, "inspect_project", side_effect=AssertionError("No input reads")):
                with self.assertRaises(ValueError):
                    exporter.export_inspection(self.project, output)
        self.assertEqual((existing / "keep").read_bytes(), b"retained")
        self.assertFalse((self.project / "generated").exists())

    def test_mixed_output_modes_are_refused_without_creating_files(self):
        json_path = self.root / "separate.json"
        for option in ("--output", "--html"):
            code, result = self.cli("project", "check", self.project, "--bundle", self.output, option, json_path)
            self.assertEqual(code, 2)
            self.assertIn("--bundle", result["result"]["error"])
            self.assert_unpublished()

    def test_render_failure_leaves_no_published_directory(self):
        with patch.object(project_report, "inspection_html", side_effect=ValueError("Render failed")):
            with self.assertRaisesRegex(ValueError, "Render failed"):
                self.export()
        self.assert_unpublished()

    def test_html_write_failure_cleans_staged_json(self):
        original_open = Path.open
        def fail_html(path, mode="r", *args, **kwargs):
            if path.name == "report.html" and mode == "x":
                raise OSError("Full filesystem")
            return original_open(path, mode, *args, **kwargs)
        with patch.object(Path, "open", fail_html):
            with self.assertRaisesRegex(OSError, "Full filesystem"):
                self.export()
        self.assert_unpublished()

    def test_manifest_failure_cleans_staged_reports(self):
        with patch.object(exporter, "seal_inspection", side_effect=OSError("Cannot seal")):
            with self.assertRaisesRegex(OSError, "Cannot seal"):
                self.export()
        self.assert_unpublished()

    def test_publication_failure_cleans_complete_stage(self):
        with patch.object(Path, "rename", side_effect=OSError("Cannot publish")):
            with self.assertRaisesRegex(OSError, "Cannot publish"):
                self.export()
        self.assert_unpublished()

    def test_late_destination_collision_preserves_other_writer_files(self):
        seal = exporter.seal_inspection
        def occupy(stage):
            result = seal(stage)
            self.output.mkdir()
            (self.output / "keep").write_bytes(b"Other writer")
            return result
        with patch.object(exporter, "seal_inspection", side_effect=occupy):
            with self.assertRaisesRegex(ValueError, "appeared"):
                self.export()
        self.assertEqual({path.name for path in self.output.iterdir()}, {"keep"})
        self.assertEqual((self.output / "keep").read_bytes(), b"Other writer")
        self.assertFalse(list(self.root.glob(".inspection-*")))

    def test_source_change_during_render_prevents_publication(self):
        render = project_report.inspection_html
        def mutate(*args, **kwargs):
            page = render(*args, **kwargs)
            self.source.write_text("Changed manuscript", encoding="utf-8")
            return page
        with patch.object(project_report, "inspection_html", side_effect=mutate):
            with self.assertRaisesRegex(ValueError, "changed before inspection publication: main.tex"):
                self.export()
        self.assert_unpublished()

    def test_source_change_during_sealing_prevents_publication(self):
        seal = exporter.seal_inspection
        def mutate(stage):
            result = seal(stage)
            self.source.write_text("Changed while sealing", encoding="utf-8")
            return result
        with patch.object(exporter, "seal_inspection", side_effect=mutate):
            with self.assertRaisesRegex(ValueError, "changed before inspection publication"):
                self.export()
        self.assert_unpublished()

    def test_corrupt_missing_and_extra_files_fail_portable_checks(self):
        self.export()
        for change, code in (("changed", "changed-file"), ("missing", "missing-file"), ("extra", "unexpected-file")):
            with self.subTest(change=change):
                target = self.root / change
                shutil.copytree(self.output, target)
                if change == "changed":
                    (target / "inspection.json").write_bytes(b"corrupt")
                elif change == "missing":
                    (target / "report.html").unlink()
                else:
                    (target / "notes.txt").write_bytes(b"extra")
                result = verifier.verify_inspection(target)
                self.assertEqual(result["status"], "failed")
                self.assertIn(code, {item["code"] for item in result["findings"]})

    def test_wrong_manifest_kind_incomplete_and_unsafe_inventories_are_refused(self):
        self.export()
        manifest = read_json(self.output / "integrity.json")
        variants = [dict(manifest, schema=True), dict(manifest, kind="project_review_integrity"), dict(manifest, files=manifest["files"][:1]),
                    dict(manifest, files=manifest["files"] * 2),
                    dict(manifest, files=[dict(manifest["files"][0], file="../outside")])]
        for variant in variants:
            with self.subTest(variant=variant):
                (self.output / "integrity.json").write_text(json.dumps(variant), encoding="utf-8")
                with self.assertRaises(ValueError):
                    verifier.verify_inspection(self.output)

    def test_manifest_change_during_verification_is_reported(self):
        self.export()
        check = verifier.check_files
        def mutate(*args, **kwargs):
            check(*args, **kwargs)
            with (self.output / "integrity.json").open("a", encoding="utf-8") as stream:
                stream.write("\n")
        with patch.object(verifier, "check_files", side_effect=mutate):
            result = verifier.verify_inspection(self.output)
        self.assertEqual(result["status"], "failed")
        self.assertIn("changed-manifest", {item["code"] for item in result["findings"]})

    def test_legacy_pair_prepares_html_before_publishing_json(self):
        with contextlib.redirect_stdout(io.StringIO()), patch.object(project_report, "inspection_html", side_effect=ValueError("Render failed")):
            code = project_doctor.main(["check", str(self.project), "--output", str(self.root / "new.json"), "--html", str(self.root / "new.html")])
        self.assertEqual(code, 2)
        self.assert_unpublished()

    def test_legacy_pair_refuses_parent_child_paths_before_writing(self):
        with contextlib.redirect_stdout(io.StringIO()):
            code = project_doctor.main(["check", str(self.project), "--output", str(self.root / "new.json"),
                                        "--html", str(self.root / "new.json/nested.html")])
        self.assertEqual(code, 2)
        self.assert_unpublished()

    def test_json_serialization_error_precedes_any_export_files(self):
        record = project_doctor.inspect_project(self.project)
        record["extra"] = float("nan")
        with self.assertRaises(ValueError):
            project_report.write_inspection_reports(self.root / "new.json", self.root / "new.html", record)
        self.assert_unpublished()

    def test_invalid_language_is_rejected_before_inspection(self):
        with patch.object(exporter, "inspect_project", side_effect=AssertionError("No input reads")):
            with self.assertRaises(ValueError):
                self.export(language="invalid")
        self.assert_unpublished()

    def test_malformed_manifest_has_cli_precondition_exit(self):
        self.export()
        (self.output / "integrity.json").write_text('{"schema":1,"schema":1}', encoding="utf-8")
        code, result = self.cli("verify", "inspection", self.output)
        self.assertEqual(code, 2)
        self.assertIn("error", result["result"])
