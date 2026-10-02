import contextlib
import io
import json
from pathlib import Path
import sys
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doctor import diagnose, main, pdf_available, pdf_probe


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

    @patch("doctor.pdf_probe", return_value={"name": "pymupdf", "status": "missing", "detail": "not installed"})
    @patch("doctor.shutil.which", return_value=None)
    def test_pdf_reconstruction_requires_extraction_library(self, tools, pdf):
        self.assertFalse(diagnose(["pdf2tex"])["local_prerequisites_met"])

    @patch("doctor.pdf_probe", return_value={"name": "pymupdf", "status": "missing", "detail": "not installed"})
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

    def test_pdf_dependency_version_matches_the_bundled_helper(self):
        for version, expected in (("1.24.9", False), ("1.24.10", True), ("1.27.2.3", True), ("2.0.0", False), ("unknown", False)):
            module = SimpleNamespace(open=lambda: None, Document=object, VersionBind=version)
            with self.subTest(version=version), patch("doctor.importlib.import_module", return_value=module):
                self.assertEqual(pdf_available(), expected)

    def test_pdf_probe_distinguishes_absence_from_import_failure(self):
        for error, status, reason in ((ModuleNotFoundError("No module named pymupdf", name="pymupdf"), "missing", "missing_module"),
                                      (ModuleNotFoundError("No module named helper", name="helper"), "broken", "import_failed"),
                                      (OSError("Missing native library"), "broken", "import_failed"),
                                      (ImportError("DLL load failed"), "broken", "import_failed")):
            with self.subTest(error=error), patch("doctor.importlib.import_module", side_effect=error):
                check = pdf_probe()
                self.assertEqual((check["status"], check["reason"]), (status, reason))
                self.assertIsNotNone(check["next_action"])
                if status == "broken":
                    self.assertIn(str(error), check["detail"])

    def test_pdf_probe_reports_module_path_and_version_or_shadowing(self):
        module_path = str(Path.cwd() / "environment with spaces/pymupdf/__init__.py")
        for version, status, reason in (("1.24.9", "unsupported", "unsupported_version"),
                                        ("2.0.0", "unsupported", "unsupported_version"),
                                        ("unknown", "unsupported", "unknown_version"),
                                        ("1.24.10", "available", None)):
            module = SimpleNamespace(open=lambda: None, Document=object, VersionBind=version, __file__=module_path)
            with self.subTest(version=version), patch("doctor.importlib.import_module", return_value=module):
                check = pdf_probe()
                self.assertEqual((check["status"], check["reason"], check["version"]), (status, reason, version))
                self.assertEqual(check["module_path"], module_path)
        with patch("doctor.importlib.import_module", return_value=SimpleNamespace(__file__=module_path)):
            check = pdf_probe()
            self.assertEqual(check["reason"], "wrong_module")
            self.assertIn("shadowing", check["next_action"])

    @patch("doctor.shutil.which", return_value=None)
    def test_broken_or_unsupported_pdf_dependency_blocks_only_required_work(self, tools):
        for module in (object(), SimpleNamespace(open=lambda: None, Document=object, VersionBind="1.24.9")):
            with self.subTest(module=module), patch("doctor.importlib.import_module", return_value=module):
                self.assertFalse(diagnose(["pdf2tex"])["local_prerequisites_met"])
                self.assertTrue(diagnose(["paper-read"])["local_prerequisites_met"])

    def test_json_report_identifies_the_running_python(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            main(["--skill", "paper-read", "--json"])
        report = json.loads(output.getvalue())
        self.assertEqual(report["schema"], 1)
        self.assertEqual(report["python"]["executable"], sys.executable)
        self.assertEqual(report["python"]["version"], sys.version.split()[0])

    def test_cli_without_site_packages_returns_actionable_json_from_another_directory(self):
        script = Path(__file__).resolve().parents[1] / "scripts/doctor.py"
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run([sys.executable, "-S", str(script), "--skill", "pdf2tex", "--json"],
                                    cwd=temporary, capture_output=True, text=True, timeout=30)
            self.assertEqual(list(Path(temporary).iterdir()), [])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        report = json.loads(result.stdout)
        check = next(item for item in report["checks"] if item["name"] == "pymupdf")
        self.assertEqual(check["reason"], "missing_module")
        self.assertIn("reported Python", check["next_action"])

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
