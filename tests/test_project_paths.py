"""Nested manuscript paths, canonical evidence and project boundary controls."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from project_paths import dependency_path
from project_support import safe_path, read_json, sha256
import project_doctor
from inspection_bundle import export_inspection
from project_report import inspection_html
from verify_artifacts import verify_inspection


class ProjectPaths(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.project = self.root / "project"
        for name in ("paper", "shared", "styles", "figures", "paper/chapters"):
            (self.project / name).mkdir(parents=True, exist_ok=True)
        self.put("paper/main.tex", r"\documentclass{article}")

    def put(self, name, content):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def check(self):
        with patch.object(project_doctor.shutil, "which", return_value="synthetic/tool"):
            return project_doctor.inspect_project(self.project, "paper/main.tex", "pdflatex")

    def test_internal_parent_and_dot_paths_return_canonical_names(self):
        for path in ("../shared/part.tex", "./../shared/./part.tex", "chapters/../../shared/part.tex"):
            with self.subTest(path=path):
                self.assertEqual(dependency_path(self.project, "paper", path), self.project / "shared/part.tex")

    def test_dot_prefixed_paths_still_work_at_project_root(self):
        self.assertEqual(dependency_path(self.project, ".", "./paper/main.tex"), self.project / "paper/main.tex")

    def test_escaping_and_returning_paths_are_both_refused(self):
        for path in ("../../outside.tex", "../../project/paper/main.tex"):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "leaves the project"):
                dependency_path(self.project, "paper", path)

    def test_absolute_drive_control_and_macro_separators_are_refused(self):
        for path in ("/outside.tex", "C:/outside.tex", "C:outside.tex", "../shared\\part.tex", "bad\x00.tex", "bad\n.tex", "bad\r.tex"):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "literal relative"):
                dependency_path(self.project, "paper", path)

    def test_absolute_graphics_base_cannot_be_hidden_by_a_later_fragment(self):
        with self.assertRaisesRegex(ValueError, "literal relative"):
            dependency_path(self.project, "paper", "/outside/", "../shared/part.tex")

    def test_cancelled_missing_directory_is_not_treated_as_a_real_route(self):
        with self.assertRaisesRegex(ValueError, "existing directory"):
            dependency_path(self.project, "paper", "missing/../main.tex")

    def test_cancelled_regular_file_and_dot_after_file_are_refused(self):
        for path in ("main.tex/../main.tex", "main.tex/./main.tex"):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "existing directory"):
                dependency_path(self.project, "paper", path)

    def test_cancelled_symlink_is_refused_even_if_final_name_is_internal(self):
        link = self.project / "paper/link"
        try:
            link.symlink_to(self.project / "shared", target_is_directory=True)
        except OSError:
            self.skipTest("Host cannot create directory symlinks")
        for path in ("link/../main.tex", "link/part.tex"):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "Symlink"):
                dependency_path(self.project, "paper", path)

    def test_manifest_and_configured_main_paths_remain_strict(self):
        for path in ("paper/../paper/main.tex", "./paper/main.tex"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    safe_path(self.project, path)
                with self.assertRaises(ValueError):
                    project_doctor.initialize(self.project, path)
        self.assertFalse((self.project / ".als.json").exists())

    def test_parent_inputs_use_main_directory_including_nested_source_commands(self):
        self.put("paper/main.tex", r"\documentclass{article}\input{../shared/part}")
        self.put("shared/part.tex", r"\input{./local}\label{shared}")
        self.put("paper/local.tex", r"\ref{shared}")
        report = self.check()
        self.assertEqual(report["diagnostics"], [])
        self.assertEqual([r["file"] for r in report["dependencies"]], ["shared/part.tex", "paper/local.tex"])
        self.assertEqual(report["dependencies"][1]["from"], "shared/part.tex")

    def test_class_package_and_bibliography_style_names_are_canonical(self):
        self.put("paper/main.tex", r"\documentclass{../styles/top}\bibliographystyle{../styles/local}")
        self.put("styles/top.cls", r"\LoadClass{article}\RequirePackage{../styles/settings}")
        self.put("styles/settings.sty", r"\input{../shared/part}")
        self.put("shared/part.tex", "Shared")
        self.put("styles/local.bst", "% synthetic style; no backend execution asserted")
        report = self.check()
        self.assertEqual(report["diagnostics"], [])
        self.assertEqual({r["file"] for r in report["inputs"]},
                         {"paper/main.tex", "styles/top.cls", "styles/settings.sty", "styles/local.bst", "shared/part.tex"})
        self.assertEqual(report["package_inventory"][0]["name"], "../styles/top")

    def test_bibliography_and_addbibresource_parent_paths_supply_known_keys(self):
        for declaration in (r"\bibliography{../shared/refs}", r"\addbibresource{../shared/refs.bib}"):
            with self.subTest(declaration=declaration):
                self.put("paper/main.tex", r"\documentclass{article}\cite{known}" + declaration)
                self.put("shared/refs.bib", "@misc{known, title={Synthetic}}")
                report = self.check()
                self.assertEqual(report["diagnostics"], [])
                self.assertEqual(report["bibliography_entries"][0]["file"], "shared/refs.bib")

    def test_graphicspath_parent_lookup_preserves_extension_priority(self):
        self.put("paper/main.tex", r"\documentclass{article}\graphicspath{{../figures/}{./}}"
                 r"\DeclareGraphicsExtensions{.png,.pdf}\includegraphics{plot}")
        self.put("figures/plot.png", "Synthetic asset")
        self.put("paper/plot.pdf", "Synthetic unused asset")
        report = self.check()
        self.assertEqual(report["diagnostics"], [])
        self.assertEqual(report["dependencies"][0]["file"], "figures/plot.png")
        self.assertNotIn("paper/plot.pdf", {r["file"] for r in report["observed_files"]})

    def test_direct_parent_graphics_and_missing_parent_files_keep_source_locations(self):
        self.put("paper/main.tex", "\\documentclass{article}\n\\includegraphics{../figures/plot.pdf}\n\\input{../shared/missing}\n")
        self.put("figures/plot.pdf", "Synthetic asset")
        report = self.check()
        self.assertEqual([(r["code"], r["line"]) for r in report["diagnostics"]], [("missing-input", 3)])
        self.assertEqual(report["dependencies"][0]["file"], "figures/plot.pdf")
        self.assertFalse(report["dependencies"][1]["exists"])

    def test_includeonly_remains_literal_and_skips_missing_parent_targets(self):
        self.put("paper/main.tex", r"\documentclass{article}\includeonly{../shared/one}"
                 r"\include{../shared/one}\include{../shared/missing}\input{../shared/part}")
        self.put("shared/one.tex", "One")
        self.put("shared/part.tex", "Part")
        report = self.check()
        self.assertEqual(report["diagnostics"], [])
        self.assertTrue(report["dependencies"][1]["skipped"])
        self.assertEqual([r["file"] for r in report["dependencies"]], ["shared/one.tex", None, "shared/part.tex"])

    def test_path_alias_cycle_is_detected_with_canonical_names(self):
        self.put("paper/main.tex", r"\documentclass{article}\input{../shared/part}")
        self.put("shared/part.tex", r"\input{../paper/main}")
        report = self.check()
        self.assertEqual([r["code"] for r in report["diagnostics"]], ["dependency-cycle"])
        self.assertIn("paper/main.tex -> shared/part.tex -> paper/main.tex", report["diagnostics"][0]["message"])

    def test_repeated_alias_is_observed_once_and_flagged(self):
        self.put("paper/main.tex", r"\documentclass{article}\input{../shared/part}\input{chapters/../../shared/part}")
        self.put("shared/part.tex", "Shared")
        report = self.check()
        self.assertEqual([r["code"] for r in report["diagnostics"]], ["repeated-source"])
        self.assertEqual([r["file"] for r in report["inputs"]].count("shared/part.tex"), 1)

    def test_external_paths_are_unverified_and_never_read(self):
        outside = self.root / "outside.tex"
        outside.write_bytes(b"\xff")
        self.put("paper/main.tex", r"\documentclass{article}\input{../../outside}\usepackage{../../outside}")
        report = self.check()
        self.assertEqual([r["code"] for r in report["diagnostics"]], ["external-or-dynamic-path", "external-package"])
        self.assertEqual([r["file"] for r in report["observed_files"]], ["paper/main.tex"])

    def test_html_and_sealed_inventory_keep_literal_request_and_canonical_evidence(self):
        part = self.put("shared/part.tex", "Shared")
        self.put("paper/main.tex", r"\documentclass{article}\input{../shared/part}")
        for language in ("en", "zh"):
            output = self.root / language
            with patch.object(project_doctor.shutil, "which", return_value="synthetic/tool"):
                report = export_inspection(self.project, output, "paper/main.tex", "pdflatex", language=language)
            self.assertEqual(report["diagnostics"], [])
            self.assertEqual(report["dependencies"][0]["requested"], "../shared/part")
            self.assertIn({"file": "shared/part.tex", "sha256": sha256(part)}, report["inputs"])
            self.assertEqual(verify_inspection(output)["status"], "verified")
            self.assertIn("../shared/part", inspection_html(report, language))
            self.assertEqual(read_json(output / "inspection.json")["dependencies"][0]["file"], "shared/part.tex")


if __name__ == "__main__":
    unittest.main()
