"""Static dependency and offline report controls for practical source trees."""
import json
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import project_doctor
from project_report import inspection_html, write_inspection_html
from project_support import read_json, sha256


class InspectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "paper"
        self.project.mkdir()

    def put(self, filename, text):
        path = self.project / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def check(self):
        with patch.object(project_doctor.shutil, "which", return_value="synthetic/tool"):
            return project_doctor.inspect_project(self.project, main="main.tex", engine="pdflatex")

    def test_unbraced_quoted_and_multiline_inputs_retain_locations_and_keys(self):
        self.put("main.tex", "\\documentclass{article}\n\\input section\n\\input \"with spaces.tex\"\n\\cite{\nknown,\nsecond\n}\n\\bibliography{refs}\n")
        self.put("section.tex", "\\label{section}\\ref{section}")
        self.put("with spaces.tex", "Supplied text")
        self.put("refs.bib", "@misc{known, title={Fixture}}\n@misc{second, title={Fixture}}")
        report = self.check()
        self.assertEqual(report["diagnostics"], [])
        self.assertEqual([(item["requested"], item["line"]) for item in report["dependencies"]], [("section", 2), ("with spaces.tex", 3), ("refs", 8)])

    def test_nested_local_classes_packages_and_bibliography_style_are_recorded(self):
        self.put("main.tex", "\\documentclass{styles/top}\n\\bibliographystyle{styles/local}")
        self.put("styles/top.cls", "\\LoadClassWithOptions{styles/base}")
        self.put("styles/base.cls", "\\RequirePackageWithOptions{styles/extra}")
        self.put("styles/extra.sty", "\\RequirePackage{styles/missing}")
        style = self.put("styles/local.bst", "% synthetic bibliography-style fixture")
        report = self.check()
        self.assertEqual(next(item["file"] for item in report["diagnostics"] if item["code"] == "missing-local-package"), "styles/extra.sty")
        self.assertIn({"file": "styles/local.bst", "sha256": sha256(style)}, report["inputs"])

    def test_includeonly_excludes_includes_but_never_inputs(self):
        self.put("main.tex", "\\documentclass{article}\n\\includeonly{one}\n\\include{one}\n\\include{missing}\n\\input{required}\n")
        self.put("one.tex", "Active chapter")
        report = self.check()
        skipped = next(item for item in report["dependencies"] if item["requested"] == "missing")
        self.assertTrue(skipped["skipped"])
        self.assertIsNone(skipped["exists"])
        missing = [item for item in report["diagnostics"] if item["code"] == "missing-input"]
        self.assertEqual(len(missing), 1)
        self.assertIn("required", missing[0]["message"])
        self.assertNotIn("missing.tex", {item["file"] for item in report["inputs"]})
        self.put("main.tex", "\\documentclass{article}\\includeonly{}\\include{missing}")
        self.assertEqual(self.check()["diagnostics"], [])

    def test_explicit_root_does_not_parse_an_excluded_or_unrelated_invalid_source(self):
        self.put("main.tex", "\\documentclass{article}\\includeonly{}\\include{invalid}")
        (self.project / "invalid.tex").write_bytes(b"\xff")
        report = self.check()
        self.assertEqual(report["diagnostics"], [])
        self.assertEqual([item["file"] for item in report["inputs"]], ["main.tex"])
        self.assertEqual(report["root_candidate_scope"], "selected-main-only")
        with self.assertRaises(UnicodeError):
            project_doctor.inspect_project(self.project)

    def test_graphics_declarations_apply_in_execution_order_and_replace_old_paths(self):
        self.put("main.tex", "\\documentclass{article}\n\\includegraphics{first}\n\\input settings\n\\includegraphics{first}\n\\graphicspath{{other/}}\n\\includegraphics{first}")
        self.put("settings.tex", "\\graphicspath{{figures/}}")
        self.put("figures/first.pdf", "synthetic path fixture, not a PDF")
        report = self.check()
        graphics = [item for item in report["dependencies"] if item["command"] == "includegraphics"]
        self.assertEqual([item["exists"] for item in graphics], [False, True, False])
        self.assertEqual(graphics[1]["file"], "figures/first.pdf")

    def test_graphics_extensions_precede_directories_and_explicit_order_is_honored(self):
        self.put("main.tex", "\\documentclass{article}\\graphicspath{{a/}{b/}}\\includegraphics{figure}\\DeclareGraphicsExtensions{.png,.pdf}\\includegraphics{figure}")
        self.put("a/figure.png", "synthetic path fixture")
        self.put("b/figure.pdf", "synthetic path fixture")
        graphics = [item for item in self.check()["dependencies"] if item["command"] == "includegraphics"]
        self.assertEqual([item["file"] for item in graphics], ["b/figure.pdf", "a/figure.png"])

    def test_dynamic_redeclaration_does_not_reuse_a_stale_graphics_search(self):
        self.put("main.tex", "\\documentclass{article}\\graphicspath{{old/}}\\graphicspath{{\\unknown}}\\includegraphics{figure}")
        self.put("old/figure.pdf", "synthetic path fixture")
        report = self.check()
        self.assertEqual({item["code"] for item in report["diagnostics"]}, {"dynamic-reference", "graphics-search-unverified"})
        self.assertNotIn("old/figure.pdf", {item["file"] for item in report["inputs"]})

    def test_nested_macro_arguments_are_visible_as_unverified(self):
        self.put("main.tex", "\\documentclass{article}\\input{\\pathmacro{part}}")
        self.assertIn("dynamic-reference", {item["code"] for item in self.check()["diagnostics"]})

    def test_internal_macro_names_are_not_misread_as_bare_inputs(self):
        self.put("main.tex", r"\documentclass{article}\makeatletter\def\input@path{{external/}}\makeatother")
        report = self.check()
        self.assertEqual(report["dependencies"], [])
        self.assertEqual(report["diagnostics"], [])

    def test_cycles_and_repeated_inputs_are_visible_without_unbounded_recursion(self):
        self.put("main.tex", "\\documentclass{article}\\input{one}\\input{one}")
        self.put("one.tex", "\\input{main}")
        report = self.check()
        self.assertEqual(report["status"], "blocked")
        self.assertEqual({item["code"] for item in report["diagnostics"]}, {"dependency-cycle", "repeated-source"})
        self.assertEqual(len(report["inputs"]), 2)

    def test_repeated_package_loading_does_not_repeat_its_contents(self):
        self.put("main.tex", "\\documentclass{article}\\usepackage{local}\\RequirePackage{local}")
        self.put("local.sty", "\\label{unique}")
        self.assertEqual(self.check()["diagnostics"], [])

    def test_config_refuses_non_tex_generated_and_invalid_utf8_before_writing(self):
        self.put("notes.md", "not a TeX root")
        self.put("work/main.tex", "\\documentclass{article}")
        bad = self.project / "bad.tex"
        bad.write_bytes(b"\xff")
        for name in ("notes.md", "work/main.tex", "bad.tex"):
            with self.assertRaises((ValueError, UnicodeError)):
                project_doctor.initialize(self.project, name)
            self.assertFalse((self.project / ".als.json").exists())

    def test_generated_and_environment_trees_are_not_traversed_or_root_candidates(self):
        self.put("main.tex", "\\documentclass{article}")
        for name in (".venv", "venv", "node_modules", "work", ".git"):
            self.put(name + "/unrelated.tex", "\\documentclass{article}")
        actual_scandir = project_doctor.os.scandir
        def guarded(path):
            if Path(path).name in project_doctor.GENERATED:
                raise PermissionError("Synthetic unreadable generated directory")
            return actual_scandir(path)
        with patch.object(project_doctor.os, "scandir", side_effect=guarded):
            report = project_doctor.inspect_project(self.project)
        self.assertEqual(report["main"], "main.tex")
        self.assertEqual(report["root_candidates"], ["main.tex"])
        self.assertEqual([item["file"] for item in report["inputs"]], ["main.tex"])

    def test_changed_source_cannot_be_bound_to_older_parsed_contents(self):
        main = self.put("main.tex", "\\documentclass{article}\\input{one}")
        self.put("one.tex", "Original")
        actual = project_doctor.commands
        def mutate(text):
            if "\\input" in text:
                main.write_text("Changed after parsing", encoding="utf-8")
            yield from actual(text)
        with patch.object(project_doctor, "commands", side_effect=mutate):
            with self.assertRaisesRegex(ValueError, "changed during inspection"):
                self.check()

    def test_html_retains_missing_and_skipped_states_and_escapes_hostile_strings(self):
        self.put("main.tex", "\\documentclass{article}\\includeonly{}\\include{excluded}\\input{missing}")
        report = self.check()
        report["root"] = '<script src="https://example.invalid/tracker">'
        page = inspection_html(report, "zh", "inspection #1.json")
        self.assertIn("LaTeX 项目检查", page)
        self.assertIn("被 includeonly 排除；未检查", page)
        self.assertIn("Missing", inspection_html(report))
        self.assertIn("尚未编译", page)
        self.assertNotIn("<script", page)
        self.assertIn("&lt;script", page)
        self.assertIn('href="inspection%20%231.json"', page)
        self.assertIn("Content-Security-Policy", page)
        output = self.root / "inspection.html"
        write_inspection_html(output, report)
        with self.assertRaises(FileExistsError):
            write_inspection_html(output, report)

    def test_automatic_ambiguous_root_report_keeps_all_observation_fingerprints(self):
        first = self.put("main.tex", "\\documentclass{article}")
        other = self.put("other.tex", "\\documentclass{article}")
        report = project_doctor.inspect_project(self.project)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["inputs"], [])
        self.assertEqual(report["observed_files"], [{"file": "main.tex", "sha256": sha256(first)},
                                                     {"file": "other.tex", "sha256": sha256(other)}])
        page = inspection_html(report, "zh")
        self.assertIn("全部已读取文件校验值", page)
        self.assertIn(sha256(other), page)

    def test_root_selection_observations_are_distinct_from_reachable_dependencies(self):
        self.put("main.tex", "\\documentclass{article}\\input{chapter}")
        self.put("chapter.tex", "Active")
        self.put("notes.tex", "Unrelated notes")
        with patch.object(project_doctor.shutil, "which", return_value="synthetic/tool"):
            automatic = project_doctor.inspect_project(self.project, engine="pdflatex")
        self.assertEqual({item["file"] for item in automatic["observed_files"]}, {"main.tex", "chapter.tex", "notes.tex"})
        self.assertEqual({item["file"] for item in automatic["inputs"]}, {"main.tex", "chapter.tex"})
        self.assertEqual({item["file"] for item in self.check()["observed_files"]}, {"main.tex", "chapter.tex"})

    def test_ambiguous_selection_rechecks_inputs_before_returning(self):
        self.put("main.tex", "\\documentclass{article}")
        other = self.put("other.tex", "\\documentclass{article}")
        actual = project_doctor.commands
        def mutate(text):
            other.write_text("Changed after root discovery", encoding="utf-8")
            yield from actual(text)
        with patch.object(project_doctor, "commands", side_effect=mutate):
            with self.assertRaisesRegex(ValueError, "changed during inspection"):
                project_doctor.inspect_project(self.project)

    def test_configuration_fingerprint_binds_bytes_parsed_even_after_restore(self):
        self.put("main.tex", "\\documentclass{article}")
        project_doctor.initialize(self.project, "main.tex")
        config = self.project / ".als.json"
        original = config.read_bytes()
        different = original.replace(b"pdflatex", b"lualatex")
        actual = project_doctor.read_source
        def replaced_read(path):
            if Path(path).name == ".als.json" and replaced_read.once:
                replaced_read.once = False
                return different  # bytes seen during a concurrent replacement
            return actual(path)  # original file restored before final observation
        replaced_read.once = True
        with patch.object(project_doctor, "read_source", side_effect=replaced_read):
            with self.assertRaisesRegex(ValueError, "changed during inspection: .als.json"):
                self.check()

    def test_configuration_is_in_observations_with_its_parsed_fingerprint(self):
        self.put("main.tex", "\\documentclass{article}")
        project_doctor.initialize(self.project, "main.tex")
        report = self.check()
        self.assertIn({"file": ".als.json", "sha256": sha256(self.project / ".als.json")}, report["observed_files"])
        self.assertEqual(report["configuration_sha256"], sha256(self.project / ".als.json"))
        self.put("selected.tex", "\\documentclass{article}")
        explicit = project_doctor.inspect_project(self.project, main="selected.tex")
        self.assertEqual({item["file"] for item in explicit["observed_files"]}, {".als.json", "main.tex", "selected.tex"})
        self.assertEqual([item["file"] for item in explicit["inputs"]], ["selected.tex"])

    def test_bounded_reads_refuse_growth_and_oversized_configuration(self):
        source = self.put("main.tex", "\\documentclass{article}")
        with patch.object(project_doctor, "MAX_SOURCE_BYTES", 10):
            with self.assertRaisesRegex(ValueError, "size limit"):
                project_doctor.read_source(source)
        self.put(".als.json", " " * 65)
        with patch.object(project_doctor, "MAX_SOURCE_BYTES", 64):
            with self.assertRaisesRegex(ValueError, "size limit"):
                project_doctor.load_config(self.project)

    def test_unclosed_literal_regions_are_located_once_in_automatic_and_local_sources(self):
        self.put("main.tex", "\\documentclass{article}\\usepackage{local}\n\\verb|unfinished\n")
        self.put("local.sty", "\\begin{verbatim}\n\\input{not-real}")
        with patch.object(project_doctor.shutil, "which", return_value="synthetic/tool"):
            report = project_doctor.inspect_project(self.project, engine="pdflatex")
        self.assertEqual(report["status"], "needs-review")
        self.assertEqual([(item["code"], item["file"], item["line"]) for item in report["diagnostics"]],
                         [("unterminated-verb", "main.tex", 2), ("unterminated-verbatim", "local.sty", 1)])

    def test_cli_keeps_blocked_exit_and_refuses_output_collisions_before_writing(self):
        self.put("main.tex", "\\documentclass{article}\\input{missing}")
        cli = Path(__file__).resolve().parents[1] / "scripts/als.py"
        report, page = self.root / "inspection.json", self.root / "inspection.html"
        result = subprocess.run([sys.executable, str(cli), "--json", "project", "check", str(self.project), "--output", str(report), "--html", str(page), "--html-language", "zh"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)["result"]["status"], "blocked")
        self.assertEqual(read_json(report)["html"], str(page))
        self.assertIn("inspection.json", page.read_text(encoding="utf-8"))
        other = self.root / "new.json"
        with contextlib.redirect_stdout(io.StringIO()):
            code = project_doctor.main(["check", str(self.project), "--output", str(other), "--html", str(page)])
        self.assertEqual(code, 2)
        self.assertFalse(other.exists())
