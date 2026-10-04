"""Editable copies keep initial-byte evidence and stay independent of installation paths."""
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import export_examples as exporter
from project_support import ROOT, read_json, sha256
from verify_artifacts import verify_example


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.extend(value for name, value in attrs if name == "href")


class ExampleExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name).resolve()
        self.root = self.work / "bundled sources"
        self.root.mkdir()
        for name in ("VERSION", "LICENSE"):
            shutil.copyfile(ROOT / name, self.root / name)
        shutil.copytree(ROOT / "examples", self.root / "examples", ignore=shutil.ignore_patterns("__pycache__"))
        self.output = self.work / "editable case"

    def export(self, case="full-paper", language="en"):
        return exporter.export_example(case, self.output, language, self.root)

    def no_publication(self):
        self.assertFalse(self.output.exists())
        self.assertFalse(any(p.name.startswith(".example-") for p in self.work.iterdir()))

    def reseal(self):
        manifest = read_json(self.output / "integrity.json")
        for row in manifest["files"]:
            path = self.output / row["file"]
            if path.is_file():
                row.update(sha256=sha256(path), bytes=path.stat().st_size)
        (self.output / "integrity.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_all_six_cases_preserve_copied_bytes_and_live_offline_links(self):
        for case in exporter.EXPORT_CASES:
            with self.subTest(case=case):
                output = self.work / case
                result = exporter.export_example(case, output, "zh", self.root)
                self.assertEqual(result["status"], "exported-not-run")
                self.assertEqual(verify_example(output)["status"], "verified")
                receipt = read_json(output / "example.json")
                self.assertEqual(receipt["origin"], "synthetic-maintainer-authored")
                for row in receipt["source_files"]:
                    self.assertEqual((output / row["file"]).read_bytes(), (self.root / row["source"]).read_bytes())
                    self.assertEqual(sha256(output / row["file"]), row["sha256"])
                self.assertEqual(result["files_copied"], len(receipt["source_files"]))
                page = (output / "report.html").read_text(encoding="utf-8")
                parser = LinkParser()
                parser.feed(page)
                for link in parser.links:
                    if not urlsplit(link).scheme:
                        self.assertTrue((output / unquote(link)).is_file(), link)
                for text in ("可编辑的论文案例", "不能用作盲评", "prefers-color-scheme", "Content-Security-Policy"):
                    self.assertIn(text, page)

    def test_full_paper_retains_hidden_configuration_and_local_assets(self):
        self.export()
        receipt = read_json(self.output / "example.json")
        for name in ("after/.als.json", "after/main-cn.tex", "after/styles/example.sty", "before/figures/panel.svg"):
            self.assertTrue((self.output / "case" / name).is_file())
        self.assertEqual(receipt["candidate"], "case/after/main.tex")
        self.assertIn("als build --project case/after", (self.output / "README.md").read_text(encoding="utf-8"))

    def test_copy_does_not_execute_scripts_or_require_optional_libraries(self):
        script = ROOT / "scripts/als.py"
        result = subprocess.run([sys.executable, "-S", str(script), "--json", "examples", "export", "--case", "pdf2tex", "--output", str(self.output)],
                                cwd=self.work, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        envelope = json.loads(result.stdout)
        self.assertEqual(envelope["result"]["status"], "exported-not-run")
        self.assertEqual(list((self.output / "case").glob("build*")), [])
        self.assertTrue((self.output / "case/generate_input.py").is_file())
        self.assertEqual(verify_example(self.output)["status"], "verified")

    def test_moved_export_verifies_after_original_resources_are_removed(self):
        self.export()
        self.root.rename(self.work / "resources moved away")
        relocated = self.work / "relocated"
        self.output.rename(relocated)
        checked = verify_example(relocated)
        self.assertEqual(checked["status"], "verified")
        self.assertEqual(checked["case"], "full-paper")

    def test_export_never_changes_source_files(self):
        before = {p.relative_to(self.root).as_posix(): sha256(p) for p in self.root.rglob("*") if p.is_file()}
        self.export("pdf2tex")
        after = {p.relative_to(self.root).as_posix(): sha256(p) for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_existing_or_internal_output_is_refused(self):
        self.output.mkdir()
        (self.output / "keep.txt").write_text("Keep", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.export()
        self.assertEqual((self.output / "keep.txt").read_text(encoding="utf-8"), "Keep")
        for output in (self.root / "exported", self.root / "examples/full-paper/exported"):
            with self.subTest(output=output), self.assertRaises(ValueError):
                exporter.export_example("full-paper", output, root=self.root)
            self.assertFalse(output.exists())

    def test_invalid_case_or_language_creates_nothing(self):
        for case, language in (("unknown", "en"), ("full-paper", "unknown")):
            with self.subTest(case=case), self.assertRaises(ValueError):
                self.export(case, language)
            self.no_publication()

    def test_missing_required_local_source_creates_nothing(self):
        (self.root / "examples/full-paper/after/.als.json").unlink()
        with self.assertRaises(ValueError):
            self.export()
        self.no_publication()

    def test_missing_catalog_case_reports_value_error(self):
        path = self.root / "examples/index.json"
        catalog = read_json(path)
        catalog["examples"][0]["id"] = "renamed"
        path.write_text(json.dumps(catalog), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "absent"):
            self.export("rescue")
        self.no_publication()

    def test_file_count_and_byte_limits_fail_before_publication(self):
        for limit, value in (("MAX_COPY_FILES", 1), ("MAX_COPY_BYTES", 1), ("MAX_COPY_TOTAL", 1)):
            with self.subTest(limit=limit), patch.object(exporter, limit, value), self.assertRaises(ValueError):
                self.export()
            self.no_publication()

    def test_symlink_source_is_refused_without_following_it(self):
        target = self.work / "private.txt"
        target.write_text("Private", encoding="utf-8")
        link = self.root / "examples/full-paper/link.txt"
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("Creating symlinks is unavailable")
        with self.assertRaises(ValueError):
            self.export()
        self.no_publication()

    def test_render_failure_creates_no_destination(self):
        with patch.object(exporter, "example_html", side_effect=ValueError("render")), self.assertRaises(ValueError):
            self.export()
        self.no_publication()

    def test_sealing_failure_cleans_stage(self):
        with patch.object(exporter, "seal_bundle", side_effect=OSError("seal")), self.assertRaises(OSError):
            self.export()
        self.no_publication()

    def test_copy_write_failure_removes_partial_stage(self):
        write = Path.write_bytes
        def failing(path, content):
            if path.name == "references.bib":
                raise OSError("write failed")
            return write(path, content)
        with patch.object(Path, "write_bytes", autospec=True, side_effect=failing), self.assertRaises(OSError):
            self.export()
        self.no_publication()

    def test_source_change_during_rendering_is_refused(self):
        render = exporter.example_html
        def changing(report, language):
            (self.root / "examples/full-paper/after/main.tex").write_text("Changed", encoding="utf-8")
            return render(report, language)
        with patch.object(exporter, "example_html", side_effect=changing), self.assertRaisesRegex(ValueError, "source changed"):
            self.export()
        self.no_publication()

    def test_added_source_during_rendering_is_refused(self):
        render = exporter.example_html
        def adding(report, language):
            (self.root / "examples/full-paper/extra.tex").write_text("Extra", encoding="utf-8")
            return render(report, language)
        with patch.object(exporter, "example_html", side_effect=adding), self.assertRaisesRegex(ValueError, "inventory changed"):
            self.export()
        self.no_publication()

    def test_version_change_after_parsing_is_refused(self):
        prepare = exporter.case_spec
        def changing(*args):
            (self.root / "VERSION").write_text("9.0.0\n", encoding="utf-8")
            return prepare(*args)
        with patch.object(exporter, "case_spec", side_effect=changing), self.assertRaisesRegex(ValueError, "VERSION"):
            self.export()
        self.no_publication()

    def test_catalog_change_after_parsing_is_refused(self):
        prepare = exporter.case_spec
        def changing(*args):
            result = prepare(*args)
            path = self.root / "examples/index.json"
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            return result
        with patch.object(exporter, "case_spec", side_effect=changing), self.assertRaisesRegex(ValueError, "index.json"):
            self.export("polish")
        self.no_publication()

    def test_staged_guide_change_after_sealing_is_refused(self):
        seal = exporter.seal_bundle
        def changing(root, kind):
            result = seal(root, kind)
            (root / "report.html").write_text("Changed", encoding="utf-8")
            return result
        with patch.object(exporter, "seal_bundle", side_effect=changing), self.assertRaisesRegex(ValueError, "verification"):
            self.export()
        self.no_publication()

    def test_destination_created_during_rendering_is_preserved(self):
        render = exporter.example_html
        def occupying(report, language):
            self.output.mkdir()
            (self.output / "keep.txt").write_text("Owned", encoding="utf-8")
            return render(report, language)
        with patch.object(exporter, "example_html", side_effect=occupying), self.assertRaisesRegex(ValueError, "appeared"):
            self.export()
        self.assertEqual(list(self.output.iterdir()), [self.output / "keep.txt"])
        self.assertFalse(any(p.name.startswith(".example-") for p in self.work.iterdir()))

    def test_source_edit_is_detected_by_offline_verifier(self):
        self.export()
        path = self.output / "case/after/main.tex"
        path.write_text("Changed", encoding="utf-8")
        result = verify_example(self.output)
        self.assertEqual(result["status"], "failed")
        self.assertTrue(any(row["code"] == "changed-file" for row in result["findings"]))

    def test_corrupted_receipt_is_reported_as_changed_bytes_without_parsing(self):
        self.export()
        (self.output / "example.json").write_text("{broken", encoding="utf-8")
        result = verify_example(self.output)
        self.assertEqual(result["status"], "failed")
        self.assertTrue(any(row["code"] == "changed-receipt" for row in result["findings"]))

    def test_added_and_missing_files_are_detected(self):
        self.export()
        (self.output / "added.txt").write_text("Added", encoding="utf-8")
        (self.output / "case/decisions.md").unlink()
        result = verify_example(self.output)
        self.assertEqual(result["status"], "failed")
        self.assertTrue({"unexpected-file", "missing-file"}.issubset({r["code"] for r in result["findings"]}))

    def test_source_receipt_disagreement_survives_manifest_resealing(self):
        self.export()
        path = self.output / "example.json"
        receipt = read_json(path)
        receipt["source_files"][0]["sha256"] = "0" * 64
        path.write_text(json.dumps(receipt), encoding="utf-8")
        self.reseal()
        result = verify_example(self.output)
        self.assertEqual(result["status"], "failed")
        self.assertTrue(any(row["code"] == "source-receipt-mismatch" for row in result["findings"]))

    def test_manifest_kind_boolean_schema_and_coverage_are_refused(self):
        self.export()
        path = self.output / "integrity.json"
        original = read_json(path)
        for change in ({"kind": "project_inspection_integrity"}, {"schema": True}, {"files": original["files"][1:]}):
            with self.subTest(change=change):
                path.write_text(json.dumps({**original, **change}), encoding="utf-8")
                with self.assertRaises(ValueError):
                    verify_example(self.output)

    def test_invalid_source_mapping_or_entry_pointer_is_refused(self):
        self.export()
        path = self.output / "example.json"
        original = read_json(path)
        for field in ("source", "input"):
            receipt = json.loads(json.dumps(original))
            if field == "source":
                receipt["source_files"][0]["source"] = "../private"
            else:
                receipt["input"] = "../private"
            path.write_text(json.dumps(receipt), encoding="utf-8")
            self.reseal()
            with self.subTest(field=field), self.assertRaises(ValueError):
                verify_example(self.output)

    def test_html_escapes_source_labels_and_url_characters(self):
        self.export("rescue")
        receipt = read_json(self.output / "example.json")
        receipt["skill"] = '<script>alert("x")</script>'
        receipt["input"] = "case/a#b%20<name>.tex"
        page = exporter.example_html(receipt, "en")
        self.assertNotIn('<script>', page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("case/a%23b%2520%3Cname%3E.tex", page)

    def test_cli_help_and_catalog_discovery_need_no_optional_dependencies(self):
        result = subprocess.run([sys.executable, "-S", str(ROOT / "scripts/als.py"), "--json", "examples", "export", "--output", str(self.output), "--help"],
                                cwd=self.work, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--case", json.loads(result.stdout)["stdout"])
        listed = subprocess.run([sys.executable, "-S", str(ROOT / "scripts/als.py"), "--json", "examples", "list"],
                                cwd=self.work, capture_output=True, text=True, timeout=30)
        self.assertEqual(listed.returncode, 0, listed.stderr)
        catalog = json.loads(listed.stdout)["result"]
        self.assertEqual(len(catalog["examples"]), 5)
        self.assertEqual(set(catalog["export_cases"]), set(exporter.EXPORT_CASES))
        self.no_publication()


if __name__ == "__main__":
    unittest.main()
