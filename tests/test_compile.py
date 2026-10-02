"""Compile in isolated directories; never treat a produced log/PDF as success."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from test_build import check_build

FIXTURES = Path(__file__).resolve().parent / "fixtures"
PDFLATEX = shutil.which("pdflatex")


class CompilationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PDFLATEX:
            if os.environ.get("LATEX_SKILLS_REQUIRE_TEX") == "1":
                raise RuntimeError("pdflatex is required for this run but was not found")
            raise unittest.SkipTest("pdflatex unavailable; real compilation runs in CI")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="latex-skills-tests-")
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        (self.work / "asset.tex").write_text(
            r"\documentclass{article}\pagestyle{empty}\begin{document}Fixture figure\end{document}",
            encoding="utf-8",
        )
        result = self.compile("asset.tex")
        self.assertEqual(result.returncode, 0, result.stdout[-4000:])
        for name in ("example.pdf", "plot.pdf"):
            shutil.copyfile(self.work / "asset.pdf", self.work / name)

    def compile(self, filename):
        return subprocess.run(
            [PDFLATEX, "-no-shell-escape", "-interaction=nonstopmode", "-file-line-error", filename],
            cwd=self.work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", timeout=60,
        )

    def copy_fixture(self, name):
        shutil.copyfile(FIXTURES / "errors" / name, self.work / name)

    def test_broken_fixture_has_real_compilation_failure(self):
        self.copy_fixture("broken_paper.tex")
        result = self.compile("broken_paper.tex")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Undefined control sequence", result.stdout)

    def test_corrected_fixture_builds_pdf_without_tex_errors(self):
        self.copy_fixture("expected_fixed.tex")
        for _ in range(2):
            result = self.compile("expected_fixed.tex")
            self.assertEqual(result.returncode, 0, result.stdout[-6000:])
        pdf = self.work / "expected_fixed.pdf"
        self.assertTrue(pdf.read_bytes().startswith(b"%PDF-"))
        log = (self.work / "expected_fixed.log").read_text(encoding="utf-8", errors="replace")
        self.assertIsNone(re.search(r"(?m)^!|^.*\.tex:\d+:.*(?:Error|Undefined control sequence)", log))

    def test_valid_reference_resolves_and_unknown_keys_stay_flagged(self):
        self.copy_fixture("expected_fixed.tex")
        for _ in range(2):
            result = self.compile("expected_fixed.tex")
            self.assertEqual(result.returncode, 0, result.stdout[-6000:])
        log = (self.work / "expected_fixed.log").read_text(encoding="utf-8", errors="replace")
        self.assertNotRegex(log, r"Reference [`']fig:results'")
        self.assertRegex(log, r"Reference [`']sec:missing'.*undefined")
        self.assertRegex(log, r"Citation [`']undefined2024'.*undefined")

    def test_bundled_build_helper_uses_fresh_output_and_retains_warnings(self):
        self.copy_fixture("expected_fixed.tex")
        report = check_build.build(self.work / "expected_fixed.tex", self.work / "fresh build")
        self.assertEqual(report["status"], "success", report)
        self.assertTrue(any("undefined" in d["message"] for d in report["diagnostics"]))
        self.assertFalse((self.work / "expected_fixed.pdf").exists())
        self.assertEqual(len(report["steps"]), 2)

    def test_bundled_build_helper_does_not_accept_stale_source_pdf(self):
        self.copy_fixture("broken_paper.tex")
        (self.work / "broken_paper.pdf").write_bytes(b"%PDF-stale")
        report = check_build.build(self.work / "broken_paper.tex", self.work / "failed build")
        self.assertEqual(report["status"], "failed", report)
        self.assertTrue(report["diagnostics"])
        self.assertIsNone(report["pdf"])
        self.assertEqual((self.work / "broken_paper.pdf").read_bytes(), b"%PDF-stale")

    def test_bundled_build_helper_resolves_bibtex_and_paths_with_spaces(self):
        source = self.work / "paper name.tex"
        source.write_text(r"\documentclass{article}\begin{document}"
                          r"\input{section}\bibliographystyle{plain}\bibliography{refs}\end{document}", encoding="utf-8")
        (self.work / "section.tex").write_text(r"A result~\cite{demo}.\label{sec:one} See~\ref{sec:one}.", encoding="utf-8")
        (self.work / "refs.bib").write_text("@article{demo, author={A. Author}, title={Test}, journal={Example}, year={2020}}", encoding="utf-8")
        report = check_build.build(source, self.work / "bibliography build", backend="bibtex")
        self.assertEqual(report["status"], "success", report)
        self.assertEqual(len(report["steps"]), 4)
        self.assertFalse(any("undefined" in d["message"] for d in report["diagnostics"]), report)
        self.assertTrue((self.work / "bibliography build/document.bbl").is_file())

    def test_bundled_build_helper_resolves_biber_with_project_local_bibliography(self):
        if not shutil.which("biber"):
            if os.environ.get("LATEX_SKILLS_REQUIRE_TEX") == "1":
                self.fail("biber is required for the real backend CI case")
            self.skipTest("biber unavailable")
        source = self.work / "biber paper.tex"
        source.write_text(r"\documentclass{article}\usepackage[backend=biber]{biblatex}"
                          r"\addbibresource{refs.bib}\begin{document}"
                          r"A result~\cite{demo}.\printbibliography\end{document}", encoding="utf-8")
        (self.work / "refs.bib").write_text("@article{demo, author={A. Author}, title={Test}, journal={Example}, year={2020}}", encoding="utf-8")
        report = check_build.build(source, self.work / "biber build", backend="biber")
        self.assertEqual(report["status"], "success", report)
        self.assertFalse(any("undefined" in d["message"] for d in report["diagnostics"]), report)
        self.assertTrue((self.work / "biber build/document.bbl").is_file())
