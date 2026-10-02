"""Portable build behavior; real engine/backend integration is in test_compile."""
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout

REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_build", REPO / "latex-rescue/scripts/check_build.py")
check_build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_build)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "project with spaces"
        self.project.mkdir()
        self.project = self.project.resolve()
        self.source = self.project / "paper name.tex"
        self.source.write_text("Author's source", encoding="utf-8")
        self.output = self.project / "new build"
        self.calls = []
        self.which = patch.object(check_build.shutil, "which", side_effect=lambda name: f"/tools/{name}")
        self.which.start()
        self.addCleanup(self.which.stop)

    def engine(self, command, **kwargs):
        self.calls.append((command, kwargs))
        kwargs["stdout"].write(b"Compiler transcript\n")
        if Path(command[0]).name in check_build.ENGINES:
            (self.output / "document.log").write_text("LaTeX Warning: Reference `missing' undefined.\n", encoding="utf-8")
            (self.output / "document.pdf").write_bytes(b"%PDF-1.5\nfixture")
            (self.output / "document.aux").write_text("aux", encoding="utf-8")
            (self.output / "document.bcf").write_text("bcf", encoding="utf-8")
        else:
            (self.output / "document.blg").write_text("Bibliography log", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    def run_build(self, runner=None, **kwargs):
        with patch.object(check_build.subprocess, "run", side_effect=runner or self.engine):
            return check_build.build(self.source, self.output, **kwargs)

    def test_new_pdf_with_warnings_preserves_source_and_records_each_pass(self):
        report = self.run_build()
        self.assertEqual(report["status"], "success")
        self.assertEqual(len(report["steps"]), 2)
        self.assertEqual(report["diagnostics"][0]["severity"], "warning")
        self.assertEqual(json.loads((self.output / "build-report.json").read_text()), report)
        self.assertEqual(self.source.read_text(), "Author's source")
        for command, kwargs in self.calls:
            self.assertIn("-no-shell-escape", command)
            self.assertEqual(kwargs["cwd"], self.project)
            self.assertNotIn("shell", kwargs)
            self.assertTrue((self.output / "engine-01.txt").is_file())

    def test_error_exit_with_pdf_still_fails_and_stops_passes(self):
        def fail(command, **kwargs):
            self.engine(command, **kwargs)
            (self.output / "document.log").write_text("./paper.tex:3: Missing $ inserted.\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 1)
        report = self.run_build(fail)
        self.assertEqual(report["status"], "failed")
        self.assertIsNone(report["pdf"])
        self.assertEqual(len(report["steps"]), 1)
        self.assertEqual(report["diagnostics"][0]["severity"], "error")

    def test_zero_exit_without_pdf_or_with_error_log_does_not_pass(self):
        for mode in ("missing", "invalid", "error"):
            with self.subTest(mode=mode):
                self.output = self.project / mode
                def runner(command, **kwargs):
                    result = self.engine(command, **kwargs)
                    if mode == "missing":
                        (self.output / "document.pdf").unlink()
                    elif mode == "invalid":
                        (self.output / "document.pdf").write_bytes(b"not a pdf")
                    else:
                        (self.output / "document.log").write_text("! Undefined control sequence.\n")
                    return result
                self.assertEqual(self.run_build(runner)["status"], "failed")

    def test_existing_output_is_not_reused_even_when_it_contains_a_pdf(self):
        self.output.mkdir()
        pdf = self.output / "document.pdf"
        pdf.write_bytes(b"%PDF-stale")
        with self.assertRaisesRegex(ValueError, "must be new"):
            self.run_build()
        self.assertEqual(pdf.read_bytes(), b"%PDF-stale")
        self.assertEqual(self.calls, [])

    def test_missing_tool_fails_before_output_creation(self):
        with patch.object(check_build.shutil, "which", return_value=None):
            with self.assertRaisesRegex(ValueError, "PATH"):
                self.run_build()
        self.assertFalse(self.output.exists())

    def test_bibliography_sequence_and_project_search_paths(self):
        for backend in check_build.BACKENDS:
            with self.subTest(backend=backend):
                self.output = self.project / backend
                self.calls.clear()
                report = self.run_build(backend=backend)
                self.assertEqual(report["status"], "success")
                self.assertEqual([Path(c[0][0]).name for c in self.calls], ["pdflatex", backend, "pdflatex", "pdflatex"])
                self.assertTrue((self.output / "bibliography.blg").is_file())
                for _, kwargs in self.calls:
                    self.assertTrue(kwargs["env"]["BIBINPUTS"].startswith(str(self.project)))
                backend_command, options = self.calls[1]
                if backend == "bibtex":
                    self.assertEqual(options["cwd"], self.output)
                else:
                    self.assertIn(f"--output-directory={self.output}", backend_command)

    def test_absent_control_file_stops_before_backend(self):
        def no_control(command, **kwargs):
            result = self.engine(command, **kwargs)
            (self.output / "document.bcf").unlink()
            return result
        report = self.run_build(no_control, backend="biber")
        self.assertIn("not generated", report["failure"])
        self.assertEqual(len(self.calls), 1)

    def test_backend_failure_stops_before_further_engine_passes(self):
        def fail_backend(command, **kwargs):
            result = self.engine(command, **kwargs)
            return subprocess.CompletedProcess(command, 2) if Path(command[0]).name == "bibtex" else result
        report = self.run_build(fail_backend, backend="bibtex")
        self.assertEqual(len(report["steps"]), 2)
        self.assertIn("exited with 2", report["failure"])
        self.assertIsNone(report["pdf"])

    def test_timeout_retains_transcript_without_reusing_prior_log(self):
        def timeout(command, **kwargs):
            if not self.calls:
                return self.engine(command, **kwargs)
            kwargs["stdout"].write(b"Partial second pass\n")
            raise subprocess.TimeoutExpired(command, 0.1)
        report = self.run_build(timeout, timeout=0.1)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(report["steps"][-1]["timed_out"])
        self.assertIsNone(report["steps"][-1]["log"])
        self.assertEqual(report["diagnostics"], [])
        self.assertIn("Partial", (self.output / "engine-02.txt").read_text())
        self.assertTrue((self.output / "engine-01.log").is_file())

    def test_launch_failure_and_interrupt_retain_report(self):
        for failure in (OSError("launch denied"), KeyboardInterrupt()):
            with self.subTest(failure=type(failure).__name__):
                self.output = self.project / type(failure).__name__
                if isinstance(failure, KeyboardInterrupt):
                    with self.assertRaises(KeyboardInterrupt):
                        self.run_build(lambda *a, **kw: (_ for _ in ()).throw(failure))
                else:
                    self.assertEqual(self.run_build(lambda *a, **kw: (_ for _ in ()).throw(failure))["status"], "failed")
                report = json.loads((self.output / "build-report.json").read_text())
                self.assertTrue(report["failure"])

    def test_invalid_options_write_nothing(self):
        for options in ({"passes": 0}, {"passes": 6}, {"passes": 1, "backend": "bibtex"},
                        {"timeout": 0}, {"timeout": float("nan")}, {"engine": "unknown"}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.run_build(**options)
        self.assertFalse(self.output.exists())

    def test_engine_selection_is_explicit(self):
        for engine in check_build.ENGINES:
            with self.subTest(engine=engine):
                self.output = self.project / engine
                self.calls.clear()
                report = self.run_build(engine=engine, passes=1)
                self.assertEqual(report["status"], "success")
                self.assertEqual(report["engine"], engine)
                self.assertEqual(Path(self.calls[0][0][0]).name, engine)

    def test_cli_exit_codes_and_installed_help(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            with patch.object(check_build.subprocess, "run", side_effect=self.engine):
                self.assertEqual(check_build.main([str(self.source), "--output", str(self.output)]), 0)
            self.assertEqual(check_build.main([str(self.source), "--output", str(self.output)]), 2)
            self.output = self.project / "cli failure"
            with patch.object(check_build.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)):
                self.assertEqual(check_build.main([str(self.source), "--output", str(self.output)]), 1)
        sys.path.insert(0, str(REPO / "scripts"))
        from install import install
        installed = self.project / "skills"
        install(REPO, installed, ["latex-rescue"])
        result = subprocess.run([sys.executable, str(installed / "latex-rescue/scripts/check_build.py"), "--help"],
                                cwd=self.project, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--backend", result.stdout)


if __name__ == "__main__":
    unittest.main()
