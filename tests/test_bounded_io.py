"""Real files and synthetic streams exercise bounded evidence handling."""
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bounded_io as tool
import project_support
import project_doctor
import review_project
import inspection_bundle
import artifact_integrity
import verify_artifacts


class BoundedReads(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source.bin"
        self.source.write_bytes(b"abcdefgh")

    def projects(self):
        for side in ("before", "after"):
            (self.root / side).mkdir()
            (self.root / side / "main.tex").write_text(r"\documentclass{article}", encoding="utf-8")
        return self.root / "before", self.root / "after", self.root / "review"

    def test_exact_limit_and_empty_files_have_matching_byte_counts(self):
        self.assertEqual(tool.read_bytes(self.source, 8), b"abcdefgh")
        self.assertEqual(tool.fingerprint(self.source, 8), {"bytes": 8, "sha256": hashlib.sha256(b"abcdefgh").hexdigest()})
        self.source.write_bytes(b"")
        self.assertEqual(tool.read_bytes(self.source, 0), b"")
        self.assertEqual(tool.fingerprint(self.source, 0)["bytes"], 0)

    def test_oversized_file_is_rejected_before_open_or_target_creation(self):
        target = self.root / "target.bin"
        with patch.object(tool.os, "open", side_effect=AssertionError("Must not open oversized input")):
            for operation in (lambda: tool.read_bytes(self.source, 7), lambda: tool.fingerprint(self.source, 7),
                              lambda: tool.copy_file(self.source, target, 7)):
                with self.assertRaisesRegex(ValueError, "size limit"):
                    operation()
        self.assertFalse(target.exists())

    def test_directory_and_symlink_are_rejected_before_open(self):
        with self.assertRaisesRegex(ValueError, "regular file"):
            tool.fingerprint(self.root)
        link = self.root / "link.bin"
        try:
            link.symlink_to(self.source)
        except OSError:
            self.skipTest("Host cannot create file symlinks")
        with self.assertRaisesRegex(ValueError, "regular file"):
            tool.read_bytes(link, 8)

    def test_fifo_is_rejected_without_blocking_on_posix(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFOs require POSIX")
        fifo = self.root / "pipe.png"
        os.mkfifo(fifo)
        with patch.object(tool.os, "open", side_effect=AssertionError("Must not open FIFO")):
            with self.assertRaisesRegex(ValueError, "regular file"):
                tool.fingerprint(fifo)
        with self.assertRaisesRegex(ValueError, "regular file"):
            project_doctor.inventory(self.root, assets=True)

    def test_actual_stream_growth_is_bounded_independently_of_stat(self):
        @contextmanager
        def synthetic_stream(*unused):
            yield io.BytesIO(b"x" * 9)
        with patch.object(tool, "source_stream", synthetic_stream), patch.object(tool, "CHUNK_BYTES", 3):
            for operation in (lambda: tool.fingerprint(self.source, 8), lambda: tool.read_bytes(self.source, 8),
                              lambda: tool.copy_file(self.source, self.root / "copy", 8)):
                with self.assertRaisesRegex(ValueError, "size limit"):
                    operation()
        self.assertLessEqual((self.root / "copy").stat().st_size, 8)

    def test_same_size_change_during_read_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "changed during reading"):
            with tool.source_stream(self.source, 8) as stream:
                stream.read(2)
                previous = self.source.stat()
                self.source.write_bytes(b"changed!")
                os.utime(self.source, ns=(previous.st_atime_ns, previous.st_mtime_ns + 1_000_000_000))

    def test_replacement_after_open_is_rejected_on_posix(self):
        if os.name == "nt":
            self.skipTest("Windows prevents replacing an open file")
        with self.assertRaisesRegex(ValueError, "changed during reading"):
            with tool.source_stream(self.source, 8):
                replacement = self.root / "replacement"
                replacement.write_bytes(b"abcdefgh")
                replacement.replace(self.source)

    def test_opened_descriptor_identity_is_checked_before_read(self):
        original = tool.os.open
        other = self.root / "other.bin"
        other.write_bytes(b"abcdefgh")
        with patch.object(tool.os, "open", side_effect=lambda unused, flags: original(other, flags)):
            with self.assertRaisesRegex(ValueError, "changed before reading"):
                tool.read_bytes(self.source, 8)

    def test_windows_ctime_semantics_do_not_cause_false_changes(self):
        # Real-file control also runs on Python 3.10-3.13 across native CI hosts.
        self.assertEqual(project_support.sha256(self.source), hashlib.sha256(b"abcdefgh").hexdigest())

    def test_copy_is_fresh_exact_and_never_overwrites_existing_bytes(self):
        target = self.root / "copy.bin"
        copied = tool.copy_file(self.source, target, 8)
        self.assertEqual(copied, tool.fingerprint(target, 8))
        target.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            tool.copy_file(self.source, target, 8)
        self.assertEqual(target.read_bytes(), b"keep")

    def test_shared_hash_limit_is_enforced(self):
        with patch.object(tool, "MAX_FILE_BYTES", 7):
            with self.assertRaisesRegex(ValueError, "size limit"):
                project_support.sha256(self.source)

    def test_json_is_bounded_before_parsing(self):
        self.source.write_bytes(b'{"value":1}')
        with patch.object(project_support, "MAX_METADATA_BYTES", 4), patch.object(project_support, "parse_json", side_effect=AssertionError("No parse")):
            with self.assertRaisesRegex(ValueError, "size limit"):
                project_support.read_json(self.source)

    def test_json_output_limit_counts_utf8_bytes_and_creates_nothing(self):
        target = self.root / "new-parent/report.json"
        with patch.object(project_support, "MAX_METADATA_BYTES", 10):
            with self.assertRaisesRegex(ValueError, "JSON output exceeds"):
                project_support.write_new_json(target, {"note": "中文"})
        self.assertFalse(target.parent.exists())

    def test_project_asset_preflight_limit_runs_before_hashing(self):
        before, after, output = self.projects()
        (after / "figure.png").write_bytes(b"123456789")
        with patch.object(project_doctor, "MAX_FILE_BYTES", 8), patch.object(review_project, "fingerprint", side_effect=AssertionError("No hashing")):
            with self.assertRaisesRegex(ValueError, "size limit"):
                review_project.snapshot(after)
        self.assertFalse(output.exists())

    def test_project_inventory_checks_total_before_hashing(self):
        before, after, output = self.projects()
        for name in ("a.png", "b.png"):
            (after / name).write_bytes(b"12345678")
        with patch.object(project_doctor, "MAX_TOTAL_BYTES", 30), patch.object(review_project, "fingerprint", side_effect=AssertionError("No hashing")):
            with self.assertRaisesRegex(ValueError, "total byte limit"):
                review_project.snapshot(after)

    def test_snapshot_actual_byte_total_is_checked_again(self):
        before, after, output = self.projects()
        with patch.object(review_project, "MAX_TOTAL_BYTES", 1):
            with self.assertRaisesRegex(ValueError, "total byte limit"):
                review_project.snapshot(after)

    def test_notes_limit_prevents_review_publication(self):
        before, after, output = self.projects()
        with patch.object(review_project, "MAX_NOTES_BYTES", 7):
            with self.assertRaisesRegex(ValueError, "size limit"):
                review_project.review(before, after, output, notes=self.source)
        self.assertFalse(output.exists())
        self.assertFalse(list(self.root.glob(".review-*")))

    def test_notes_preserve_bom_unicode_and_are_escaped_in_both_languages(self):
        before, after, unused = self.projects()
        self.source.write_bytes(b"\xef\xbb\xbf" + "中文 <script>".encode("utf-8"))
        for language in ("en", "zh"):
            output = self.root / language
            review_project.review(before, after, output, notes=self.source, language=language)
            self.assertEqual(project_support.read_json(output / "review.json")["notes"], "中文 <script>")
            self.assertIn("中文 &lt;script&gt;", (output / "report.html").read_text(encoding="utf-8"))
            self.assertEqual(verify_artifacts.verify_review(output)["status"], "verified")

    def test_build_metadata_limit_prevents_hashing_parsing_or_publication(self):
        before, after, output = self.projects()
        self.source.write_bytes(b"{" + b" " * 20)
        with patch.object(review_project, "MAX_METADATA_BYTES", 10):
            with self.assertRaisesRegex(ValueError, "size limit"):
                review_project.review(before, after, output, after_build=self.source)
        self.assertFalse(output.exists())
        self.assertFalse(list(self.root.glob(".review-*")))

    def test_growth_before_inspection_publication_uses_source_limit(self):
        project = self.root / "project"
        project.mkdir()
        (project / "main.tex").write_text(r"\documentclass{article}\input{manual.bbl}", encoding="utf-8")
        manual = project / "manual.bbl"
        manual.write_text(r"\bibitem{key} Original", encoding="utf-8")
        original = inspection_bundle.write_inspection_reports
        def grow(*args):
            original(*args)
            manual.write_bytes(b"x" * 100)
        with patch.object(inspection_bundle, "MAX_SOURCE_BYTES", 80), patch.object(inspection_bundle, "write_inspection_reports", side_effect=grow):
            with self.assertRaisesRegex(ValueError, "size limit"):
                inspection_bundle.export_inspection(project, self.root / "inspection", main="main.tex")
        self.assertFalse((self.root / "inspection").exists())
        self.assertFalse(list(self.root.glob(".inspection-*")))

    def test_build_report_hash_binds_the_exact_parsed_bytes(self):
        before, after, output = self.projects()
        source = after / "main.tex"
        self.source.write_text(json.dumps({"schema": 3, "status": "failed", "steps": [], "local_inputs": [],
            "source": str(source), "source_sha256": project_support.sha256(source)}), encoding="utf-8")
        parse = review_project.parse_json
        def mutate_after_parsing(text):
            result = parse(text)
            self.source.write_bytes(self.source.read_bytes() + b" ")
            return result
        with patch.object(review_project, "parse_json", side_effect=mutate_after_parsing):
            with self.assertRaisesRegex(ValueError, "evidence changed during retention"):
                review_project.review(before, after, output, after_build=self.source)
        self.assertFalse(output.exists())

    def test_bundle_inventory_uses_hash_bytes_and_total_limit(self):
        with patch.object(artifact_integrity, "MAX_TOTAL_BYTES", 7):
            with self.assertRaisesRegex(ValueError, "limits"):
                artifact_integrity.file_inventory(self.root)
        self.assertEqual(artifact_integrity.file_inventory(self.root)[0]["bytes"], 8)


if __name__ == "__main__":
    unittest.main()
