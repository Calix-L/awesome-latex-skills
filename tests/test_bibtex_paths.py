"""Prepared BibTeX input aliases and their retained review evidence."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from test_build import check_build, REPO

sys.path.insert(0, str(REPO / "scripts"))
import review_project
from project_support import sha256, read_json
from verify_artifacts import verify_review


class BibTeXPathTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.project = self.root / "project space"
        (self.project / "paper").mkdir(parents=True)
        self.source = self.project / "paper/main.tex"
        self.source.write_text(r"\documentclass{article}", encoding="utf-8")
        (self.project / "refs.bib").write_bytes(b"@misc{a, title={Synthetic}}")
        (self.project / "style.bst").write_bytes(b"% synthetic style")
        self.output = self.root / "build space"
        self.output.mkdir()
        self.aux = self.output / "main.aux"
        self.aux.write_bytes(b"\\bibdata{../refs}\r\n\\bibstyle{../style}\r\n")

    def prepare(self):
        return check_build.prepare_bibtex_inputs(self.source, self.output, "main")

    def test_staged_bbl_is_copied_to_engine_job_without_overwriting(self):
        target, _ = self.prepare()
        bbl = self.output / f"{target}.bbl"
        bbl.write_bytes(b"\\bibitem{a} Synthetic bibliography\r\n")
        check_build.promote_bibtex_output(self.output, target, "main")
        self.assertEqual((self.output / "main.bbl").read_bytes(), bbl.read_bytes())
        with self.assertRaises(FileExistsError):
            check_build.promote_bibtex_output(self.output, target, "main")
        check_build.promote_bibtex_output(self.output, "main", "main")

    def test_staged_bbl_requires_bounded_generated_bytes(self):
        target, _ = self.prepare()
        with self.assertRaisesRegex(ValueError, "regular BBL"):
            check_build.promote_bibtex_output(self.output, target, "main")
        (self.output / f"{target}.bbl").write_bytes(b"oversized synthetic BBL")
        with patch.object(check_build, "MAX_WATCH_BYTES", 4), self.assertRaisesRegex(ValueError, "exceeds"):
            check_build.promote_bibtex_output(self.output, target, "main")
        self.assertFalse((self.output / "main.bbl").exists())

    def test_plain_names_and_unreachable_dot_aux_leave_backend_arguments_unchanged(self):
        self.aux.write_bytes(b"\\bibdata{refs}\n\\bibstyle{plain}\n")
        (self.output / "unused.aux").write_bytes(b"\\bibdata{../absent}\n")
        self.assertEqual(self.prepare(), ("main", []))
        self.assertFalse((self.output / "bibtex-inputs").exists())

    def test_relative_resources_stage_exact_bytes_and_keep_original_aux_unchanged(self):
        original = self.aux.read_bytes()
        argument, rows = self.prepare()
        self.assertEqual(argument, "bibtex-inputs/main")
        self.assertEqual(self.aux.read_bytes(), original)
        self.assertEqual({row["kind"] for row in rows}, {"bibliography", "style", "auxiliary"})
        staged = (self.output / "bibtex-inputs/main.aux").read_bytes()
        self.assertIn(b"./bibtex-inputs/resource-0001", staged)
        self.assertNotIn(b"../refs", staged)
        for row in rows:
            content = (self.output / row["file"]).read_bytes()
            self.assertEqual(hashlib.sha256(content).hexdigest(), row["sha256"])
            self.assertEqual(len(content), row["bytes"])
            if row.get("original"):
                self.assertEqual(Path(row["original"]).read_bytes(), content)

    def test_child_aux_routes_and_crlf_unicode_are_preserved_in_staged_copy(self):
        child = self.output / "chapters/one.aux"
        child.parent.mkdir()
        child.write_bytes(b"\\bibdata{../refs}\r\n")
        raw = "\\@input{./chapters/one.aux}\r\n% 中文原始记录\r\n".encode("utf-8")
        self.aux.write_bytes(raw)
        argument, rows = self.prepare()
        self.assertEqual(self.aux.read_bytes(), raw)
        copied = (self.output / "bibtex-inputs/main.aux").read_bytes()
        self.assertIn(b"\\@input{./bibtex-inputs/chapters/one.aux}", copied)
        self.assertIn("% 中文原始记录\r\n".encode("utf-8"), copied)
        self.assertEqual(len([row for row in rows if row["kind"] == "auxiliary"]), 2)

    def test_same_resolved_resource_uses_one_alias(self):
        self.aux.write_bytes(b"\\bibdata{../refs,./../refs.bib}\n")
        argument, rows = self.prepare()
        self.assertEqual(len([row for row in rows if row["kind"] == "bibliography"]), 1)
        aliases = (self.output / "bibtex-inputs/main.aux").read_text().split("{", 1)[1].split("}", 1)[0].split(",")
        self.assertEqual(aliases[0], aliases[1])

    def test_comments_and_non_command_text_do_not_trigger_staging(self):
        self.aux.write_bytes(b"% \\bibdata{../absent}\nText \\bibstyle{../absent}\n")
        self.assertEqual(self.prepare(), ("main", []))

    def test_missing_relative_resource_is_refused_with_its_literal_name(self):
        self.aux.write_bytes(b"\\bibdata{../absent}\n")
        with self.assertRaisesRegex(ValueError, "relative BibTeX input.*absent"):
            self.prepare()

    def test_aux_file_count_and_byte_limits_are_checked(self):
        with patch.object(check_build, "MAX_BIBTEX_AUX_BYTES", 4):
            with self.assertRaisesRegex(ValueError, "bounded regular"):
                self.prepare()
        (self.output / "child.aux").write_bytes(b"\\bibdata{../refs}\n")
        self.aux.write_bytes(b"\\@input{child.aux}\n")
        with patch.object(check_build, "MAX_BIBTEX_AUX_FILES", 1):
            with self.assertRaisesRegex(ValueError, "inventory exceeds"):
                self.prepare()

    def test_resource_byte_limits_apply_before_copying(self):
        with patch.object(check_build, "MAX_WATCH_BYTES", 4):
            with self.assertRaisesRegex(ValueError, "exceeds"):
                self.prepare()
        self.assertFalse(list((self.output / "bibtex-inputs").glob("*.bib")))

    def test_stage_collision_never_overwrites_existing_bytes(self):
        stage = self.output / "bibtex-inputs"
        stage.mkdir()
        (stage / "keep").write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual((stage / "keep").read_bytes(), b"keep")

    def test_changed_copies_and_originals_are_detected(self):
        argument, rows = self.prepare()
        resource = next(row for row in rows if row["kind"] == "bibliography")
        copied = self.output / resource["file"]
        raw = copied.read_bytes()
        copied.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "input changed"):
            check_build.check_prepared_inputs(self.output, rows)
        copied.write_bytes(raw)
        Path(resource["original"]).write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "source changed"):
            check_build.check_prepared_inputs(self.output, rows)

    def review_record(self, rows):
        record = self.output / "build-report.json"
        record.write_text(json.dumps({"schema": 3, "status": "failed", "source": str(self.source),
            "source_sha256": sha256(self.source), "steps": [{"prepared_inputs": rows}], "local_inputs": []}), encoding="utf-8")
        before = self.root / "before"
        before.mkdir()
        (before / "main.tex").write_text(r"\documentclass{article}", encoding="utf-8")
        return before, record

    def test_review_retains_prepared_aux_and_resources_with_sealed_hashes(self):
        argument, rows = self.prepare()
        before, record = self.review_record(rows)
        output = self.root / "review"
        review_project.review(before, self.project, output, after_build=record, language="zh")
        self.assertEqual(verify_review(output)["status"], "verified")
        retained = read_json(output / "review.json")["builds"]["after"]["retained_files"]
        for row in rows:
            name = "evidence/after/" + row["file"]
            self.assertTrue(any(item["file"] == name and item["sha256"] == row["sha256"] for item in retained))

    def test_review_refuses_changed_prepared_resource_without_publication(self):
        argument, rows = self.prepare()
        before, record = self.review_record(rows)
        (self.output / rows[0]["file"]).write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "evidence differs"):
            review_project.review(before, self.project, self.root / "review", after_build=record)
        self.assertFalse((self.root / "review").exists())

    def test_review_refuses_changed_or_external_original_without_publication(self):
        argument, rows = self.prepare()
        before, record = self.review_record(rows)
        Path(rows[0]["original"]).write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "original changed"):
            review_project.review(before, self.project, self.root / "review", after_build=record)
        external = self.root / "outside.bib"
        external.write_bytes((self.output / rows[0]["file"]).read_bytes())
        rows[0]["original"] = str(external)
        data = read_json(record)
        data["steps"] = [{"prepared_inputs": rows}]
        record.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "outside its project"):
            review_project.review(before, self.project, self.root / "review", after_build=record)
        self.assertFalse((self.root / "review").exists())


if __name__ == "__main__":
    unittest.main()
