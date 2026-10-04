"""Compile in isolated directories; never treat a produced log/PDF as success."""
import os
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from test_build import check_build, REPO

sys.path.insert(0, str(REPO / "scripts"))
from project_doctor import inspect_project

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

    def assert_build_success(self, report):
        if report["status"] == "success":
            return
        evidence = [json.dumps(report, indent=2)]
        for step in report["steps"]:
            transcript = Path(report["output"]) / step["transcript"]
            if transcript.is_file():
                evidence.append(f"{step['transcript']}:\n" + transcript.read_text(encoding="utf-8", errors="replace")[-4000:])
        self.fail("\n\n".join(evidence))

    def test_broken_fixture_has_real_compilation_failure(self):
        self.copy_fixture("broken_paper.tex")
        result = self.compile("broken_paper.tex")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Undefined control sequence", result.stdout)

    def test_project_inspector_matches_native_class_input_and_graphics_selection(self):
        import pymupdf
        project = self.work / "project"
        for directory in ("styles", "chapters", "a", "b"):
            (project / directory).mkdir(parents=True, exist_ok=True)
        (project / "main.tex").write_text(
            r"\documentclass{styles/top}\input settings.tex" + "\n" +
            r"\includeonly{chapters/one}\begin{document}\include{chapters/one}\include{chapters/missing}"
            r"See~\ref{sec:one}.\includegraphics[width=1cm]{figure}\end{document}", encoding="utf-8")
        (project / "styles/top.cls").write_text(r"\ProvidesClass{styles/top}\LoadClass{styles/base}", encoding="utf-8")
        (project / "styles/base.cls").write_text(r"\ProvidesClass{styles/base}\LoadClass{article}\RequirePackage{graphicx}", encoding="utf-8")
        (project / "settings.tex").write_text(r"\graphicspath{{a/}{b/}}\DeclareGraphicsExtensions{.png,.pdf}", encoding="utf-8")
        (project / "chapters/one.tex").write_text(r"\section{One}\label{sec:one}Supplied fixture.", encoding="utf-8")
        with pymupdf.open(self.work / "plot.pdf") as document:
            document[0].get_pixmap().save(project / "a/figure.png")
        shutil.copyfile(self.work / "plot.pdf", project / "b/figure.pdf")
        inspection = inspect_project(project, "main.tex", "pdflatex")
        self.assertEqual(inspection["status"], "ready", inspection)
        self.assertTrue(next(item for item in inspection["dependencies"] if item["requested"] == "chapters/missing")["skipped"])
        self.assertEqual(next(item["file"] for item in inspection["dependencies"] if item["command"] == "includegraphics"), "a/figure.png")
        report = check_build.build(project / "main.tex", self.work / "project build", require_resolved=True)
        self.assert_build_success(report)
        observed = {item["path"] for item in report["local_inputs"]}
        self.assertTrue({item["file"] for item in inspection["inputs"]}.issubset(observed), (inspection, report))
        self.assertNotIn("b/figure.pdf", observed)
        self.assertNotIn("chapters/missing.tex", observed)

    def test_project_inspector_does_not_apply_a_later_graphics_path_retroactively(self):
        project = self.work / "late-path"
        (project / "figures").mkdir(parents=True)
        shutil.copyfile(self.work / "plot.pdf", project / "figures/figure.pdf")
        source = project / "main.tex"
        source.write_text(r"\documentclass{article}\usepackage{graphicx}\begin{document}"
                          r"\includegraphics{figure}\graphicspath{{figures/}}\end{document}", encoding="utf-8")
        inspection = inspect_project(project, "main.tex", "pdflatex")
        self.assertEqual(inspection["status"], "blocked")
        self.assertFalse(inspection["dependencies"][0]["exists"])
        report = check_build.build(source, self.work / "late-path build")
        self.assertEqual(report["status"], "failed", report)

    def test_literal_scanner_agrees_with_native_comments_verbs_and_control_symbols(self):
        project = self.work / "literal scanner"
        project.mkdir()
        source = project / "main.tex"
        source.write_text(
            "\\documentclass{article}\n% \\begin{verbatim}\n"
            "\\begin{document}\n\\input{live}\n% \\end{verbatim}\n"
            "Example\\\\input{absent}\n"
            "\\verb|\\input{absent} 99|\n"
            "\\verb* 1\\input{absent}1\n"
            "\\verb *\\input{absent}*\n"
            "\\verb a\\input{hidden}a\n"
            "\\verb%\\input{absent}%\n"
            "\\begin{verbatim}\n\\input{absent}\n\\end{verbatim}\n"
            "\\end{document}\n", encoding="utf-8")
        (project / "live.tex").write_text("Actual input.", encoding="utf-8")
        inspection = inspect_project(project, "main.tex", "pdflatex")
        self.assertEqual(inspection["status"], "ready", inspection)
        self.assertEqual([item["requested"] for item in inspection["dependencies"]], ["live"])
        report = check_build.build(source, self.work / "literal scanner build", require_resolved=True)
        self.assert_build_success(report)
        self.assertEqual({item["path"] for item in report["local_inputs"]}, {"main.tex", "live.tex"})

    def test_unfinished_inline_verb_is_unverified_and_fails_native_compilation(self):
        project = self.work / "unfinished literal"
        project.mkdir()
        source = project / "main.tex"
        source.write_text("\\documentclass{article}\n\\begin{document}\n\\verb|unfinished\n\\end{document}\n", encoding="utf-8")
        inspection = inspect_project(project, "main.tex", "pdflatex")
        self.assertEqual(inspection["status"], "needs-review")
        self.assertEqual([(item["code"], item["line"]) for item in inspection["diagnostics"]], [("unterminated-verb", 3)])
        report = check_build.build(source, self.work / "unfinished literal build")
        self.assertEqual(report["status"], "failed", report)

    def test_unified_cli_uses_effective_output_for_literal_source_and_configured_builds(self):
        from project_doctor import initialize
        project = self.work / "CLI project with spaces"
        project.mkdir()
        source = project / "--submission.tex"
        source.write_text(r"\documentclass{article}\begin{document}Actual CLI fixture\end{document}", encoding="utf-8")
        original = source.read_bytes()
        initialize(project, source.name, passes=2)
        for mode in ("source", "configuration"):
            with self.subTest(mode=mode):
                ignored, output = self.work / f"{mode} ignored", self.work / f"{mode} actual"
                ignored.mkdir()
                (ignored / "build-report.json").write_text('{"fake":true}', encoding="utf-8")
                args = ["--out=" + str(ignored), "--output", str(output), "--require-resolved"]
                args += ["--", source.name] if mode == "source" else ["--project=" + str(project), "--"]
                result = subprocess.run([sys.executable, str(REPO / "scripts/als.py"), "--json", "build", *args],
                                        cwd=project, capture_output=True, text=True, encoding="utf-8", timeout=60)
                evidence = json.loads(result.stdout)
                self.assertEqual(result.returncode, 0, evidence)
                self.assertEqual(evidence["result"]["status"], "success")
                self.assertEqual(evidence["result"]["source"], str(source))
                self.assertEqual(evidence["evidence"], [str(output / "build-report.json")])
                self.assertEqual(evidence["invocation"]["cwd"], str(project))
                self.assertIn(str(output), evidence["invocation"]["arguments"])
                self.assertTrue(json.loads((ignored / "build-report.json").read_text())["fake"])
                self.assertEqual(source.read_bytes(), original)
                self.assertFalse((project / "--submission.pdf").exists())

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
        self.assert_build_success(report)
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
        self.assert_build_success(report)
        self.assertEqual(len(report["steps"]), 4)
        self.assertFalse(any("undefined" in d["message"] for d in report["diagnostics"]), report)
        self.assertTrue((self.work / "bibliography build/paper name.bbl").is_file())

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
        self.assert_build_success(report)
        self.assertFalse(any("undefined" in d["message"] for d in report["diagnostics"]), report)
        self.assertTrue((self.work / "biber build/biber paper.bbl").is_file())

    def test_nested_includes_and_root_jobname_build_without_source_artifacts(self):
        source = self.work / "submission.tex"
        source.write_text(r"\documentclass{article}\begin{document}"
                          r"\input{\jobname-content}\include{chapters/one}"
                          r"See section~\ref{sec:one}.\end{document}", encoding="utf-8")
        (self.work / "submission-content.tex").write_text("Main content.", encoding="utf-8")
        (self.work / "chapters").mkdir()
        (self.work / "chapters/one.tex").write_text(r"\section{One}\label{sec:one}Chapter content.", encoding="utf-8")
        report = check_build.build(source, self.work / "nested build", until_stable=True, require_resolved=True)
        self.assert_build_success(report)
        self.assertEqual(report["pdf"], "submission.pdf")
        self.assertTrue(report["auxiliary_stable"])
        self.assertTrue((self.work / "nested build/chapters/one.aux").is_file())
        self.assertFalse((self.work / "chapters/one.aux").exists())
        self.assertFalse((self.work / "submission.aux").exists())
        self.assertEqual({item["path"] for item in report["local_inputs"]},
                         {"submission.tex", "submission-content.tex", "chapters/one.tex"})
        self.assertTrue(all(step["recorder"] for step in report["steps"]))

    def test_real_recorder_captures_local_style_and_graphics_without_unused_files(self):
        source = self.work / "manifest.tex"
        source.write_text(r"\documentclass{article}\usepackage{graphicx}\usepackage{localsettings}"
                          r"\begin{document}\input{part}\includegraphics[width=1cm]{plot.pdf}\end{document}", encoding="utf-8")
        (self.work / "localsettings.sty").write_text(r"\ProvidesPackage{localsettings}\newcommand{\localword}{Local}", encoding="utf-8")
        (self.work / "part.tex").write_text(r"\localword{} content.", encoding="utf-8")
        report = check_build.build(source, self.work / "manifest build")
        self.assert_build_success(report)
        self.assertEqual({item["path"] for item in report["local_inputs"]},
                         {"manifest.tex", "localsettings.sty", "part.tex", "plot.pdf"})
        self.assertEqual(report["input_tracking"]["changed"], [])
        self.assertEqual(report["input_tracking"]["unreadable"], [])
        for item in report["local_inputs"]:
            self.assertEqual(item["observations"][-1]["sha256"], check_build.fingerprint(self.work / item["path"])["sha256"])

    def test_missing_database_reports_real_bibtex_and_biber_failure_diagnostics(self):
        for backend in check_build.BACKENDS:
            with self.subTest(backend=backend):
                if not shutil.which(backend):
                    if os.environ.get("LATEX_SKILLS_REQUIRE_TEX") == "1":
                        self.fail(f"{backend} is required for backend failure coverage")
                    continue
                source = self.work / f"missing-{backend}.tex"
                if backend == "bibtex":
                    content = (r"\documentclass{article}\begin{document}A citation~\cite{demo}."
                               r"\bibliographystyle{plain}\bibliography{nonexistent-latexskills}\end{document}")
                else:
                    content = (r"\documentclass{article}\usepackage[backend=biber]{biblatex}"
                               r"\addbibresource{nonexistent-latexskills.bib}\begin{document}"
                               r"A citation~\cite{demo}.\printbibliography\end{document}")
                source.write_text(content, encoding="utf-8")
                report = check_build.build(source, self.work / f"missing {backend} build", backend=backend)
                self.assertEqual(report["status"], "failed", report)
                self.assertEqual(report["failed_step"], "bibliography", report)
                self.assertEqual(report["diagnostic_step"], "bibliography")
                self.assertTrue(any(item["severity"] == "error" and "nonexistent-latexskills" in item["message"]
                                    for item in report["diagnostics"]), report)
                self.assertEqual(len(report["steps"]), 2)
                self.assertIsNone(report["pdf"])

    def test_installed_build_helper_compiles_without_repository_or_site_packages(self):
        sys.path.insert(0, str(REPO / "scripts"))
        from install import install
        destination = self.work / "installed skills"
        install(REPO, destination, ["latex-rescue"])
        source = self.work / "standalone.tex"
        source.write_text(r"\documentclass{article}\begin{document}Standalone build.\end{document}", encoding="utf-8")
        output = self.work / "installed build"
        result = subprocess.run([sys.executable, "-I", "-S", str(destination / "latex-rescue/scripts/check_build.py"),
                                 str(source), "--output", str(output)], cwd=self.work.parent,
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads((output / "build-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "success")
        self.assertEqual({item["path"] for item in report["local_inputs"]}, {"standalone.tex"})

    def test_strict_check_rejects_real_unresolved_reference(self):
        source = self.work / "strict.tex"
        source.write_text(r"\documentclass{article}\begin{document}See~\ref{author:missing}.\end{document}", encoding="utf-8")
        report = check_build.build(source, self.work / "strict build", require_resolved=True)
        self.assertEqual(report["status"], "failed", report)
        self.assertTrue(report["unresolved_references"])
        self.assertTrue((self.work / "strict build/strict.pdf").is_file())

    def test_unicode_engines_compile_fontspec_with_bounded_settling(self):
        source = self.work / "unicode.tex"
        source.write_text("\\documentclass{article}\\usepackage{fontspec}"
                          "\\begin{document}Hôtel. $\\alpha+\\beta$.\\end{document}", encoding="utf-8")
        for engine in ("xelatex", "lualatex"):
            with self.subTest(engine=engine):
                if not shutil.which(engine):
                    if os.environ.get("LATEX_SKILLS_REQUIRE_TEX") == "1":
                        self.fail(f"{engine} is required for the real engine CI case")
                    continue
                report = check_build.build(source, self.work / engine, engine=engine,
                                           until_stable=True, require_resolved=True, timeout=120)
                self.assert_build_success(report)
                self.assertTrue(report["auxiliary_stable"])
                self.assertEqual(report["pdf"], "unicode.pdf")

    def test_reconstruction_example_retains_scripts_cells_and_visible_uncertainty(self):
        import pymupdf
        from test_pdf_extract import extract_pdf

        source = self.work / "reconstruction_edges.tex"
        shutil.copyfile(FIXTURES / "pdf2tex/reconstruction_edges.tex", source)
        before = source.read_bytes()
        report = check_build.build(source, self.work / "reconstruction build",
                                   until_stable=True, require_resolved=True)
        self.assert_build_success(report)
        self.assertEqual(source.read_bytes(), before)
        pdf = Path(report["output"]) / report["pdf"]
        evidence = extract_pdf.extract(pdf, self.work / "reconstruction evidence", characters=True)
        with pymupdf.open(pdf) as doc:
            self.assertEqual(doc.page_count, 1)
            text = " ".join(doc[0].get_text().split())
            words = doc[0].get_text("words")
        for visible in ("76.10", "0.30", "92.3%", "78.2%", "[42]", "A&B",
                        "Spread is blank", "entry was not recovered", "retained as (7)"):
            self.assertIn(visible, text)

        def word(value, above=None):
            matches = [item for item in words if item[4] == value and (above is None or item[1] < above)]
            self.assertEqual(len(matches), 1, (value, matches))
            return matches[0]

        mean, spread, measured = word("76.10"), word("0.30"), word("Measured")
        self.assertLess(mean[2], spread[0])
        self.assertLess(spread[2], measured[0])
        variant = word("Variant")
        row = [item for item in words if abs(item[1] - variant[1]) < 1]
        self.assertIn("--", [item[4] for item in row])
        self.assertIn("Not", [item[4] for item in row])
        self.assertAlmostEqual(next(item[0] for item in row if item[4] == "Not"), measured[0], places=3)
        spread_header = word("Spread", above=mean[1])
        left, right = min(spread[0], spread_header[0]), max(spread[2], spread_header[2])
        self.assertFalse(any(left < (item[0] + item[2]) / 2 < right for item in row), row)

        lines = [line for page in evidence["pages"] for block in page["blocks"]
                 for line in block.get("lines", [])]
        all_chars = [char for line in lines for span in line["spans"] for char in span["chars"]]

        def script_offsets(label):
            line = next(item for item in lines if "".join(span["text"] for span in item["spans"]).startswith(label))
            label_chars = [char for span in line["spans"] for char in span["chars"]]
            colon = next(char for char in label_chars if char["c"] == ":")
            x, baseline = colon["origin"]
            glyphs = [char for char in all_chars if char["c"] in {"a", "i", "2"}
                      and char["origin"][0] > x + 5 and baseline - 8 <= char["origin"][1] <= baseline + 4]
            self.assertEqual(len(glyphs), 3, (label, glyphs))
            origins = {char["c"]: char["origin"] for char in glyphs}
            self.assertEqual(set(origins), {"a", "i", "2"})
            base = origins["a"]
            return {symbol: (point[0] - base[0], point[1] - base[1]) for symbol, point in origins.items()}

        first, second, nested = [script_offsets(label) for label in ("Order A:", "Order B:", "Nested:")]
        for symbol in first:
            for a, b in zip(first[symbol], second[symbol]):
                # Independent PDF positions are rounded; 0.01 pt is subpixel
                # even at 300 DPI, far below the script-grouping difference.
                self.assertAlmostEqual(a, b, delta=0.01)
        self.assertGreater(first["i"][1], 0)
        self.assertLess(first["2"][1], 0)
        self.assertGreater(abs(first["2"][1] - nested["2"][1]), 1)

    def test_sealed_static_inspection_and_native_build_have_distinct_outcomes(self):
        from inspection_bundle import export_inspection
        from verify_artifacts import verify_inspection
        project = self.work / "manuscript"
        project.mkdir()
        (project / "main.tex").write_text("\\documentclass{article}\\begin{document}\\input{part}\\end{document}", encoding="utf-8")
        (project / "part.tex").write_text("Supplied value 42", encoding="utf-8")
        original = {path.name: path.read_bytes() for path in project.iterdir()}
        report = export_inspection(project, self.work / "sealed", engine="pdflatex", language="zh")
        self.assertEqual(report["status"], "ready")
        built = check_build.build(project / "main.tex", self.work / "native", require_resolved=True)
        self.assert_build_success(built)
        self.assertEqual({item["file"] for item in report["inputs"]}, {"main.tex", "part.tex"})
        self.assertEqual(original, {path.name: path.read_bytes() for path in project.iterdir()})
        (project / "part.tex").write_text("\\undefinedInspectionControl", encoding="utf-8")
        second = export_inspection(project, self.work / "static-only", engine="pdflatex")
        self.assertEqual(second["status"], "ready")
        failed = check_build.build(project / "main.tex", self.work / "failed-native")
        self.assertEqual(failed["status"], "failed")
        project.rename(self.work / "moved-manuscript")
        for directory in ("sealed", "static-only"):
            self.assertEqual(verify_inspection(self.work / directory)["status"], "verified")

    def test_installed_layout_example_adapts_to_column_and_minipage_widths(self):
        import pymupdf
        sys.path.insert(0, str(REPO / "scripts"))
        from install import install

        destination = self.work / "formatting skills"
        install(REPO, destination, ["latex-fmt"])
        example = destination / "latex-fmt/assets/layout-example.tex"
        before = example.read_bytes()
        content = example.read_text(encoding="utf-8")
        self.assertEqual(content.count(r"\documentclass[twocolumn]{article}"), 1)
        widths = {}
        for engine in ("pdflatex", "xelatex", "lualatex"):
            if not shutil.which(engine):
                if os.environ.get("LATEX_SKILLS_REQUIRE_TEX") == "1":
                    self.fail(f"{engine} is required for the layout integration case")
                continue
            for mode in ("onecolumn", "twocolumn"):
                with self.subTest(engine=engine, mode=mode):
                    source = self.work / f"layout-{engine}-{mode}.tex"
                    candidate = content.replace(r"\documentclass[twocolumn]{article}",
                                                rf"\documentclass[{mode}]{{article}}")
                    candidate = candidate.replace(r"\begin{document}",
                                                  r"\begin{document}\typeout{EXAMPLE-COLUMN-PT=\the\columnwidth}")
                    source.write_text(candidate, encoding="utf-8")
                    source_before = source.read_bytes()
                    report = check_build.build(source, self.work / f"{engine} {mode} build", engine=engine,
                                               until_stable=True, require_resolved=True)
                    self.assert_build_success(report)
                    self.assertEqual(source.read_bytes(), source_before)
                    last = report["steps"][-1]
                    log = (Path(report["output"]) / last["log"]).read_text(encoding="utf-8", errors="replace")
                    self.assertNotIn("Overfull", log)
                    width_pt = float(re.search(r"EXAMPLE-COLUMN-PT=([0-9.]+)pt", log).group(1))
                    widths[engine, mode] = width_pt
                    # TeX points are 1/72.27 inch; PDF points are 1/72 inch.
                    expected_width = 0.8 * width_pt * 72 / 72.27
                    with pymupdf.open(Path(report["output"]) / report["pdf"]) as doc:
                        text = " ".join(" ".join(page.get_text().split()) for page in doc)
                        panels = [drawing["rect"] for page in doc for drawing in page.get_drawings()
                                  if drawing["rect"].height < 1
                                  and abs(drawing["rect"].width - expected_width) < 0.05]
                        self.assertEqual(len(panels), 2, (expected_width, panels))
                        for page in doc:
                            self.assertTrue(all(0 <= item[0] < item[2] <= page.rect.width
                                                and 0 <= item[1] < item[3] <= page.rect.height
                                                for item in page.get_text("words")))
                    for value in ("76.10", "0.30", "78.20", "0.40", "Figure 1", "Table 1", "(1)"):
                        self.assertIn(value, text)
            self.assertGreater(widths[engine, "onecolumn"], widths[engine, "twocolumn"])
        self.assertEqual(example.read_bytes(), before)
