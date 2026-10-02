"""Portable build behavior; real engine/backend integration is in test_compile."""
import importlib.util
import hashlib
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
        self.source = self.project / "document.tex"
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
            self.jobname = next(arg.split("=", 1)[1] for arg in command if arg.startswith("-jobname="))
            (self.output / f"{self.jobname}.log").write_text("LaTeX Warning: Reference `missing' undefined.\n", encoding="utf-8")
            (self.output / f"{self.jobname}.pdf").write_bytes(b"%PDF-1.5\nfixture")
            (self.output / f"{self.jobname}.aux").write_text("aux", encoding="utf-8")
            (self.output / f"{self.jobname}.bcf").write_text("bcf", encoding="utf-8")
        else:
            (self.output / f"{self.jobname}.blg").write_text("Bibliography log", encoding="utf-8")
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
            self.assertTrue((self.output / "logs/engine-01.txt").is_file())

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
                self.assertTrue((self.output / "logs/bibliography.blg").is_file())
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

    def test_failed_backend_diagnostics_are_taken_from_the_backend_not_prior_engine(self):
        for backend, message in (("bibtex", "I couldn't open database file missing.bib\n"),
                                 ("biber", "[12] Utils.pm:399> ERROR - Cannot find 'missing.bib'!\n")):
            with self.subTest(backend=backend):
                self.output = self.project / f"failed-{backend}"
                self.calls.clear()
                def fail(command, **kwargs):
                    result = self.engine(command, **kwargs)
                    if Path(command[0]).name == backend:
                        (self.output / "document.blg").write_text(message, encoding="utf-8")
                        return subprocess.CompletedProcess(command, 2)
                    return result
                report = self.run_build(fail, backend=backend)
                self.assertEqual(report["failed_step"], "bibliography")
                self.assertEqual(report["diagnostic_step"], "bibliography")
                self.assertEqual(report["diagnostics"][0]["severity"], "error")
                self.assertIn("missing.bib", report["diagnostics"][0]["message"])
                self.assertEqual(report["diagnostics"][0]["log_line"], 1)
                self.assertTrue(report["source_unchanged"])
                self.assertEqual(len(report["steps"]), 2)

    def test_backend_warnings_and_zero_exit_errors_are_not_lost(self):
        for message, expected in (("Warning--I didn't find a database entry for missing\n", "success"),
                                  ("I was expecting an equals sign---line 3 of file refs.bib\n", "failed")):
            with self.subTest(message=message):
                self.output = self.project / expected
                self.calls.clear()
                def runner(command, **kwargs):
                    result = self.engine(command, **kwargs)
                    if Path(command[0]).name == "bibtex":
                        (self.output / "document.blg").write_text(message, encoding="utf-8")
                    return result
                report = self.run_build(runner, backend="bibtex")
                self.assertEqual(report["status"], expected)
                self.assertTrue(report["steps"][1]["diagnostics"])

    def test_backend_transcript_is_used_when_native_log_is_missing(self):
        def runner(command, **kwargs):
            if Path(command[0]).name == "bibtex":
                kwargs["stdout"].write(b"I couldn't open auxiliary file document.aux\n")
                return subprocess.CompletedProcess(command, 1)
            return self.engine(command, **kwargs)
        report = self.run_build(runner, backend="bibtex")
        self.assertIsNone(report["steps"][-1]["log"])
        self.assertEqual(report["diagnostic_step"], "bibliography")
        self.assertIn("auxiliary file", report["diagnostics"][0]["message"])

    def test_recorder_retains_local_inputs_with_spaces_and_excludes_generated_and_external_files(self):
        part = self.project / "parts/chapter one.tex"
        part.parent.mkdir()
        part.write_text("chapter", encoding="utf-8")
        unused = self.project / "unused.tex"
        unused.write_text("unused", encoding="utf-8")
        outside = self.project.parent / "external.sty"
        outside.write_text("external", encoding="utf-8")
        def runner(command, **kwargs):
            result = self.engine(command, **kwargs)
            (self.output / "document.fls").write_text(
                f"PWD {self.project}\nINPUT ./document.tex\nINPUT parts/chapter one.tex\n"
                f"INPUT {part}\nINPUT {outside}\nINPUT {self.output / 'document.aux'}\n"
                f"OUTPUT {self.output / 'document.aux'}\n", encoding="utf-8")
            return result
        report = self.run_build(runner)
        self.assertEqual(report["status"], "success")
        self.assertEqual([item["path"] for item in report["local_inputs"]], ["document.tex", "parts/chapter one.tex"])
        item = report["local_inputs"][1]
        self.assertEqual([observation["step"] for observation in item["observations"]], ["engine-01", "engine-02", "final"])
        self.assertEqual(item["observations"][0]["sha256"], hashlib.sha256(part.read_bytes()).hexdigest())
        self.assertEqual(report["input_tracking"]["recorder_steps"], ["engine-01", "engine-02"])
        for step in report["steps"]:
            self.assertTrue((self.output / step["recorder"]).is_file())

    def test_changed_included_file_fails_without_reverting_the_edit(self):
        part = self.project / "part.tex"
        part.write_text("original", encoding="utf-8")
        def runner(command, **kwargs):
            if self.calls:
                part.write_text("new author edit", encoding="utf-8")
            result = self.engine(command, **kwargs)
            (self.output / "document.fls").write_text(f"PWD {self.project}\nINPUT part.tex\n", encoding="utf-8")
            return result
        report = self.run_build(runner)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["input_tracking"]["changed"], ["part.tex"])
        self.assertIn("local inputs changed", report["failure"])
        self.assertTrue(report["source_unchanged"])
        self.assertEqual(part.read_text(), "new author edit")
        self.assertIsNone(report["pdf"])

    def test_missing_recorded_input_is_reported_and_stale_recorder_is_not_reused(self):
        def runner(command, **kwargs):
            result = self.engine(command, **kwargs)
            if len(self.calls) == 1:
                (self.output / "document.fls").write_text(f"PWD {self.project}\nINPUT removed.tex\n", encoding="utf-8")
            return result
        report = self.run_build(runner)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["input_tracking"]["recorder_steps"], ["engine-01"])
        self.assertIsNone(report["steps"][-1]["recorder"])
        self.assertEqual(report["input_tracking"]["unreadable"], ["removed.tex"])
        self.assertIsNotNone(report["local_inputs"][0]["observations"][0]["error"])

    def test_failed_initial_fingerprint_does_not_create_an_empty_output(self):
        with patch.object(check_build, "fingerprint", side_effect=OSError("source unreadable")):
            with self.assertRaisesRegex(OSError, "source unreadable"):
                self.run_build()
        self.assertFalse(self.output.exists())

    def test_cli_identifies_the_failure_evidence_and_first_error(self):
        def runner(command, **kwargs):
            result = self.engine(command, **kwargs)
            (self.output / "document.log").write_text("./document.tex:7: Undefined control sequence.\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 1)
        stderr = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(stderr), patch.object(check_build.subprocess, "run", side_effect=runner):
            status = check_build.main([str(self.source), "--output", str(self.output)])
        self.assertEqual(status, 1)
        self.assertIn("Failed step: engine-01", stderr.getvalue())
        self.assertIn("logs/engine-01.log:1:", stderr.getvalue())
        self.assertIn("Undefined control sequence", stderr.getvalue())

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
        self.assertIn("Partial", (self.output / "logs/engine-02.txt").read_text())
        self.assertTrue((self.output / "logs/engine-01.log").is_file())

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

    def test_root_basename_and_explicit_jobname_are_preserved(self):
        self.source = self.project / "paper with spaces.tex"
        self.source.write_text("source", encoding="utf-8")
        for jobname in (None, "submission-final", "engine-01", "bibliography"):
            with self.subTest(jobname=jobname):
                self.output = self.project / str(jobname)
                report = self.run_build(jobname=jobname)
                expected = jobname or "paper with spaces"
                self.assertEqual(report["jobname"], expected)
                self.assertEqual(report["pdf"], f"{expected}.pdf")
                self.assertTrue((self.output / report["pdf"]).is_file())

    def test_bibtex_receives_a_single_unquoted_jobname_argument(self):
        report = self.run_build(backend="bibtex", jobname="paper with spaces")
        self.assertEqual(report["status"], "success")
        command, _ = self.calls[1]
        self.assertEqual(command, ["/tools/bibtex", "paper with spaces"])

    def test_later_zero_exit_cannot_reuse_an_earlier_pass_pdf(self):
        def runner(command, **kwargs):
            if not self.calls:
                return self.engine(command, **kwargs)
            (self.output / "document.log").write_text("No PDF produced by this pass.")
            return subprocess.CompletedProcess(command, 0)
        report = self.run_build(runner)
        self.assertEqual(report["status"], "failed")
        self.assertIsNone(report["pdf"])
        self.assertIn("did not produce", report["failure"])

    def test_invalid_jobname_and_convergence_limit_create_nothing(self):
        for options in ({"jobname": "../outside"}, {"jobname": ""}, {"jobname": "bad\nname"},
                        {"jobname": "bad%name"}, {"until_stable": True, "passes": 1}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.run_build(**options)
        self.assertFalse(self.output.exists())

    def test_nested_include_directories_are_prepared_without_copying_source(self):
        chapter = self.project / "sections/nested/part.tex"
        chapter.parent.mkdir(parents=True)
        chapter.write_text("chapter content", encoding="utf-8")
        report = self.run_build()
        self.assertEqual(report["status"], "success")
        self.assertTrue((self.output / "sections/nested").is_dir())
        self.assertFalse((self.output / "sections/nested/part.tex").exists())
        self.assertEqual(chapter.read_text(), "chapter content")

    def test_convergence_stops_when_auxiliary_files_settle(self):
        report = self.run_build(until_stable=True)
        self.assertEqual(report["status"], "success")
        self.assertTrue(report["auxiliary_stable"])
        self.assertEqual(len(report["steps"]), 2)
        self.assertTrue(report["unresolved_references"])

    def test_unsettled_auxiliary_or_rerun_requests_fail_at_limit(self):
        for mode in ("changing", "rerun"):
            with self.subTest(mode=mode):
                self.output = self.project / mode
                self.calls.clear()
                def runner(command, **kwargs):
                    result = self.engine(command, **kwargs)
                    if mode == "changing":
                        (self.output / "document.aux").write_text(str(len(self.calls)))
                    else:
                        (self.output / "document.log").write_text("LaTeX Warning: Label(s) may have changed. Rerun to get cross-references right.\n")
                    return result
                report = self.run_build(runner, until_stable=True, passes=3)
                self.assertEqual(report["status"], "failed")
                self.assertEqual(len(report["steps"]), 3)
                self.assertIn("pass limit", report["failure"])

    def test_strict_references_fail_even_with_successful_pdf(self):
        report = self.run_build(require_resolved=True)
        self.assertEqual(report["status"], "failed")
        self.assertIn("unresolved", report["failure"])
        self.assertIsNone(report["pdf"])
        self.assertTrue((self.output / "document.pdf").is_file())

    def test_root_changed_during_build_is_reported_without_reverting_user_edit(self):
        def edit(command, **kwargs):
            self.source.write_text("editor saved new content", encoding="utf-8")
            return self.engine(command, **kwargs)
        report = self.run_build(edit)
        self.assertEqual(report["status"], "failed")
        self.assertFalse(report["source_unchanged"])
        self.assertIn("source changed", report["failure"])
        self.assertEqual(self.source.read_text(), "editor saved new content")

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
