"""The wrapper must use the helper's effective arguments and fresh evidence."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import als
from project_doctor import initialize
from project_support import ROOT, read_json, write_new_json


class CliArgumentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project = self.root / "paper with spaces"
        self.project.mkdir()
        (self.project / "main.tex").write_text(r"\documentclass{article}\begin{document}Fixture\end{document}", encoding="utf-8")
        initialize(self.project, "main.tex", "xelatex", "bibtex", 3)
        self.pdf = self.root / "source.pdf"
        with pymupdf.open() as doc:
            doc.new_page().insert_text((72, 72), "Real extraction argument fixture")
            doc.save(self.pdf)

    def call(self, *args):
        process = subprocess.run([sys.executable, str(ROOT / "scripts/als.py"), "--json", *map(str, args)],
                                 cwd=self.root, capture_output=True, text=True, encoding="utf-8")
        return process, json.loads(process.stdout)

    def in_process(self, *args, runner=None):
        stdout = io.StringIO()
        with patch.object(als.subprocess, "run", side_effect=runner or AssertionError("Unexpected helper execution")) as mocked:
            with redirect_stdout(stdout):
                code = als.main(["--json", *map(str, args)])
        return code, json.loads(stdout.getvalue()), mocked

    def test_help_does_not_read_project_config_or_launch_a_process(self):
        for args in (("--project", self.root / "missing", "--help"),
                     ("--project", self.project, "-h"), ("--he",)):
            with self.subTest(args=args), patch("project_doctor.load_config", side_effect=AssertionError("Config read during help")):
                code, report, runner = self.in_process("build", *args)
                self.assertEqual(code, 0)
                self.assertIn("--project", report["stdout"])
                self.assertEqual(report["evidence"], [])
                self.assertIsNone(report["result"])
                self.assertIsNone(report["invocation"])
                runner.assert_not_called()

    def test_extract_help_does_not_probe_optional_dependencies(self):
        with patch.dict(sys.modules, {"pymupdf": None}):
            code, report, runner = self.in_process("extract", "--help")
        self.assertEqual(code, 0)
        self.assertIn("--chars", report["stdout"])
        runner.assert_not_called()

    def test_invalid_arguments_are_structured_before_any_process_or_directory(self):
        cases = (("build", "--project", self.project, "--output"),
                 ("build", "--project", self.project, "--output", self.root / "bad", "--engine", "invented"),
                 ("extract", self.pdf, "--output", self.root / "bad", "--dpi", "not-a-number"),
                 ("extract", self.pdf, "--output", self.root / "bad", "--unknown"))
        for args in cases:
            with self.subTest(args=args):
                code, report, runner = self.in_process(*args)
                self.assertEqual(code, 2)
                self.assertEqual(report["status"], "failed")
                self.assertIn("error:", report["stderr"])
                self.assertEqual(report["evidence"], [])
                runner.assert_not_called()
        self.assertFalse((self.root / "bad").exists())

    def test_project_and_source_are_exclusive_and_repeated_projects_are_refused(self):
        for args in (("--project", self.project, str(self.project / "main.tex")),
                     ("--project", self.project, "--project=" + str(self.project)), ()):
            with self.subTest(args=args):
                code, report, runner = self.in_process("build", "--output", self.root / "bad", *args)
                self.assertEqual(code, 2)
                self.assertTrue(report["stderr"])
                runner.assert_not_called()

    def test_configuration_overrides_use_the_same_grammar_and_last_values(self):
        args, options = als.build_arguments(["--project=" + str(self.project), "--out=" + str(self.root / "new"),
                                            "--eng", "pdflatex", "--engine=lualatex", "--pa=4", "--backend=biber"])
        parsed = als.helper_parser("build").parse_args(args)
        self.assertEqual(parsed.engine, "lualatex")
        self.assertEqual(parsed.backend, "biber")
        self.assertEqual(parsed.passes, 4)
        self.assertEqual(parsed.source, self.project / "main.tex")
        self.assertEqual(parsed.output, options.output)

    def test_end_of_options_keeps_option_like_source_names_literal(self):
        args, options = als.build_arguments(["--output", str(self.root / "new"), "--", "--project.tex"])
        self.assertEqual(options.project, None)
        self.assertEqual(options.source.name, "--project.tex")
        parsed = als.helper_parser("build").parse_args(args)
        self.assertEqual(parsed.source, options.source)
        args, options = als.build_arguments(["--project", str(self.project), "--output", str(self.root / "new"), "--"])
        self.assertEqual(als.helper_parser("build").parse_args(args).passes, 3)

    def test_normalization_keeps_negative_values_and_dash_prefixed_output(self):
        args, options = als.build_arguments(["--output=-output", "--timeout=-1", "--jobname=--output", str(self.project / "main.tex")])
        parsed = als.helper_parser("build").parse_args(args)
        self.assertEqual(parsed.timeout, -1)
        self.assertEqual(parsed.jobname, "--output")
        self.assertEqual(parsed.output.name, "-output")
        self.assertEqual(parsed.output, options.output)

    def test_repeated_extract_outputs_attach_only_the_last_real_directory(self):
        old, actual = self.root / "ignored", self.root / "actual"
        old.mkdir()
        write_new_json(old / "layout.json", {"fake": True})
        process, report = self.call("extract", self.pdf, "--output", old, "--output=" + str(actual))
        self.assertEqual(process.returncode, 0, report)
        self.assertEqual(report["evidence"], [str(actual / "layout.json")])
        self.assertEqual(report["result"]["source"], self.pdf.name)
        self.assertEqual(report["result"]["schema_version"], 2)
        self.assertTrue(read_json(old / "layout.json")["fake"])

    def test_abbreviated_extract_output_and_literal_dash_pdf_attach_real_evidence(self):
        pdf = self.root / "--output.pdf"
        pdf.write_bytes(self.pdf.read_bytes())
        output = self.root / "extracted"
        process, report = self.call("extract", "--out=" + str(output), "--", pdf.name)
        self.assertEqual(process.returncode, 0, report)
        self.assertEqual(report["result"]["source"], pdf.name)
        self.assertEqual(report["evidence"], [str(output / "layout.json")])

    def test_last_existing_extract_output_is_never_attached_or_modified(self):
        old = self.root / "existing"
        old.mkdir()
        write_new_json(old / "layout.json", {"fake": True})
        process, report = self.call("extract", self.pdf, "--output", self.root / "unused", "--out=" + str(old))
        self.assertEqual(process.returncode, 1)
        self.assertIsNone(report["result"])
        self.assertEqual(report["evidence"], [])
        self.assertFalse((self.root / "unused").exists())
        self.assertTrue(read_json(old / "layout.json")["fake"])

    def test_build_evidence_uses_effective_output_and_preserves_native_failure(self):
        ignored, actual = self.root / "ignored", self.root / "build"
        ignored.mkdir()
        write_new_json(ignored / "build-report.json", {"fake": True})
        def runner(arguments, **kwargs):
            self.assertIn(str(actual), arguments)
            self.assertNotIn(str(ignored), arguments)
            actual.mkdir()
            write_new_json(actual / "build-report.json", {"schema": 3, "status": "failed", "source": str(self.project / "main.tex")})
            return subprocess.CompletedProcess(arguments, 1, "Retained fixture failure", "Native failure")
        code, report, _ = self.in_process("build", "--project", self.project, "--output", ignored, "--out=" + str(actual), runner=runner)
        self.assertEqual(code, 1)
        self.assertEqual(report["result"]["status"], "failed")
        self.assertEqual(report["evidence"], [str(actual / "build-report.json")])
        self.assertIn(str(actual), report["invocation"]["arguments"])
        self.assertEqual(report["invocation"]["python"], sys.executable)
        self.assertTrue(read_json(ignored / "build-report.json")["fake"])

    def test_existing_effective_build_output_does_not_attach_stale_evidence(self):
        output = self.root / "existing"
        output.mkdir()
        write_new_json(output / "build-report.json", {"fake": True})
        code, report, _ = self.in_process("build", str(self.project / "main.tex"), "--out=" + str(output),
                                          runner=lambda argv, **kwargs: subprocess.CompletedProcess(argv, 2, "", "Existing output"))
        self.assertEqual(code, 2)
        self.assertIsNone(report["result"])
        self.assertEqual(report["evidence"], [])
