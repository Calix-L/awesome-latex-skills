"""Compile in isolated directories; never treat a produced log/PDF as success."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

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
