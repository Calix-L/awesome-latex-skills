import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doctor import diagnose, main, pdf_available


class DoctorTests(unittest.TestCase):
    @patch("doctor.shutil.which", return_value=None)
    def test_rescue_reports_missing_compiler_as_required(self, probe):
        report = diagnose(["latex-rescue"], "xelatex")
        self.assertFalse(report["local_prerequisites_met"])
        self.assertEqual(report["engine"], "xelatex")
        self.assertTrue(any(c["name"] == "xelatex" and c["required"] for c in report["checks"]))

    @patch("doctor.shutil.which", side_effect=lambda tool: "/bin/pdflatex" if tool == "pdflatex" else None)
    def test_missing_optional_latexmk_does_not_block(self, probe):
        self.assertTrue(diagnose(["latex-rescue"])["local_prerequisites_met"])

    @patch("doctor.shutil.which", return_value=None)
    def test_text_polishing_can_work_without_compiler(self, probe):
        report = diagnose(["latex-polish"])
        self.assertTrue(report["local_prerequisites_met"])
        self.assertTrue(any(c["name"] == "pdflatex" and c["status"] == "missing" for c in report["checks"]))

    @patch("doctor.pdf_available", return_value=False)
    @patch("doctor.shutil.which", return_value=None)
    def test_pdf_reconstruction_requires_extraction_library(self, tools, pdf):
        self.assertFalse(diagnose(["pdf2tex"])["local_prerequisites_met"])

    @patch("doctor.pdf_available", return_value=False)
    def test_pasted_paper_reading_does_not_require_pdf_library(self, pdf):
        self.assertTrue(diagnose(["paper-read"])["local_prerequisites_met"])

    @patch("doctor.shutil.which", return_value=None)
    def test_explicit_backend_is_required(self, probe):
        self.assertFalse(diagnose(["latex-polish"], backend="biber")["local_prerequisites_met"])

    @patch("doctor.shutil.which", return_value="/bin/tool")
    def test_formatting_still_requires_manual_rule_verification(self, probe):
        report = diagnose(["latex-fmt"])
        self.assertTrue(report["local_prerequisites_met"])
        self.assertTrue(any(c["status"] == "manual" for c in report["checks"]))

    @patch("doctor.importlib.import_module", side_effect=ImportError("missing"))
    def test_missing_or_broken_pdf_imports_are_reported(self, probe):
        self.assertFalse(pdf_available())

    @patch("doctor.importlib.import_module", return_value=object())
    def test_unrelated_fitz_module_is_not_accepted(self, probe):
        self.assertFalse(pdf_available())

    @patch("doctor.shutil.which", return_value=None)
    def test_json_report_and_exit_status_agree(self, probe):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            status = main(["--skill", "latex-rescue", "--json"])
        report = json.loads(output.getvalue())
        self.assertEqual(status, 1)
        self.assertFalse(report["local_prerequisites_met"])

    def test_invalid_probe_inputs_are_rejected(self):
        for args in (([],), (["unknown"],), (["latex-rescue"], "fake"), (["latex-rescue"], "pdflatex", "fake")):
            with self.subTest(args=args), self.assertRaises(ValueError):
                diagnose(*args)
