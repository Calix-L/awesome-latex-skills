"""Project inspection and review must retain evidence without mutating manuscripts."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from als import configured_build
import project_doctor
from project_support import ROOT, read_json, sha256, write_new_json
import review_project
from run_paper_example import run_paper


class ManuscriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def put(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def build_record(self, project, status="failed"):
        source = project / "main.tex"
        folder = self.root / f"build-{project.name}"
        folder.mkdir()
        report = {"schema": 3, "status": status, "source": str(source), "source_sha256": sha256(source),
                  "source_unchanged": True, "steps": [], "local_inputs": [{"path": "main.tex", "observations": [{"sha256": sha256(source), "error": None}]}],
                  "failure": "Deliberate fixture failure" if status == "failed" else None}
        if status == "success":
            import pymupdf
            with pymupdf.open() as document:
                page = document.new_page()
                page.insert_text((70, 70), "Actual PDF fixture")
                document.save(folder / "main.pdf")
            report.update(pdf="main.pdf", pdf_sha256=sha256(folder / "main.pdf"))
        write_new_json(folder / "build-report.json", report)
        return folder / "build-report.json"

    def test_static_graph_ignores_comments_and_verbatim(self):
        self.put("project/main.tex", "\\documentclass{article}\n% \\input{lost}\n\\verb|\\ref{lost}|\n\\begin{verbatim}\n\\input{also-lost}\n\\end{verbatim}\n\\input{sections/result}\n\\bibliography{references}\n")
        self.put("project/sections/result.tex", "\\label{sec:result} \\ref{sec:result} \\cite{known}")
        self.put("project/references.bib", "@misc{known, title={Real supplied entry}}")
        report = project_doctor.inspect_project(self.root / "project")
        self.assertEqual({d["requested"] for d in report["dependencies"]}, {"sections/result", "references"})
        self.assertEqual([d["code"] for d in report["diagnostics"]], ["engine-unverified"])

    def test_multiple_roots_require_explicit_selection(self):
        self.put("project/a.tex", "\\documentclass{article}")
        self.put("project/b.tex", "\\documentclass{article}")
        report = project_doctor.inspect_project(self.root / "project")
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["root_candidates"], ["a.tex", "b.tex"])

    def test_missing_assets_keys_and_package_are_located_without_edits(self):
        source = self.put("project/main.tex", "\\documentclass{article}\n\\usepackage{styles/missing}\n\\includegraphics{missing}\n\\ref{unknown}\n\\cite{absent}\n")
        original = source.read_bytes()
        report = project_doctor.inspect_project(source.parent)
        codes = {d["code"] for d in report["diagnostics"]}
        self.assertTrue({"missing-local-package", "missing-input", "unknown-label", "unknown-citation"}.issubset(codes))
        self.assertEqual(next(d["line"] for d in report["diagnostics"] if d["code"] == "missing-input"), 3)
        self.assertEqual(source.read_bytes(), original)

    def test_nested_root_uses_its_actual_working_directory(self):
        self.put("project/paper/main.tex", "\\documentclass{article}\n\\input{part}")
        self.put("project/paper/part.tex", "Supplied contents")
        report = project_doctor.inspect_project(self.root / "project", "paper/main.tex")
        self.assertEqual(report["dependencies"][0]["file"], "paper/part.tex")

    def test_external_and_dynamic_paths_are_unverified(self):
        self.put("project/main.tex", "\\documentclass{article}\n\\input{../outside}\n\\includegraphics{\\figureName}\n")
        report = project_doctor.inspect_project(self.root / "project")
        self.assertTrue({"external-or-dynamic-path", "dynamic-reference"}.issubset({d["code"] for d in report["diagnostics"]}))

    def test_local_class_is_followed_to_its_missing_dependency(self):
        self.put("project/main.tex", "\\documentclass{styles/local}")
        self.put("project/styles/local.cls", "\\RequirePackage{styles/absent}")
        report = project_doctor.inspect_project(self.root / "project")
        self.assertEqual(report["dependencies"][0]["file"], "styles/local.cls")
        self.assertEqual(next(item["file"] for item in report["diagnostics"] if item["code"] == "missing-local-package"), "styles/local.cls")

    def test_project_config_is_reusable_and_never_overwritten(self):
        self.put("project/main.tex", "\\documentclass{article}")
        project = self.root / "project"
        project_doctor.initialize(project, "main.tex", "xelatex", "bibtex", 3)
        with self.assertRaises(FileExistsError):
            project_doctor.initialize(project, "main.tex")
        args = configured_build(["--project", str(project), "--output", "new-run", "--engine", "lualatex"])
        self.assertEqual(Path(args[0]).resolve(), (project / "main.tex").resolve())
        self.assertIn("bibtex", args)
        self.assertIn("3", args)
        self.assertNotIn("xelatex", args)

    def test_config_rejects_escaping_main_and_invalid_passes(self):
        self.put("project/main.tex", "\\documentclass{article}")
        for main, passes in (("../outside.tex", 2), ("main.tex", True), ("main.tex", 6)):
            config = {"schema": 1, "main": main, "engine": "pdflatex", "backend": None, "passes": passes}
            self.put("project/.als.json", json.dumps(config))
            with self.assertRaises(ValueError):
                project_doctor.load_config(self.root / "project")

    def test_fontspec_engine_and_explicit_backend_mismatch(self):
        self.put("project/main.tex", "\\documentclass{article}\n\\usepackage{fontspec}\n\\usepackage[backend=biber]{biblatex}")
        with patch.object(project_doctor.shutil, "which", return_value="/fixture/tool"):
            report = project_doctor.inspect_project(self.root / "project", engine="pdflatex", backend="bibtex")
        self.assertTrue({"engine-mismatch", "backend-mismatch"}.issubset({d["code"] for d in report["diagnostics"]}))

    def test_review_flags_changed_values_keys_and_math(self):
        self.put("before/main.tex", "Mean 76.10. \\cite{original} $x^2$\n")
        self.put("after/main.tex", "Mean 96.10. \\cite{other} $x^3$\n[UNCERTAIN: verify source]\n")
        output = self.root / "review"
        result = review_project.review(self.root / "before", self.root / "after", output)
        evidence = read_json(output / "review.json")
        self.assertEqual(result["content_flags"], 1)
        self.assertEqual(result["open_decisions"], 1)
        self.assertTrue({"numbers", "reference_keys", "simple_math"}.issubset(evidence["content_audit"][0]))
        self.assertEqual(result["builds"]["after"], "unverified")

    def test_configuration_change_is_visible_without_scientific_content_flag(self):
        self.put("before/main.tex", "Original 76.10\n")
        self.put("after/main.tex", "Original 76.10\n")
        self.put("before/.als.json", '{"engine":"pdflatex","passes":2}')
        self.put("after/.als.json", '{"engine":"xelatex","passes":3}')
        result = review_project.review(self.root / "before", self.root / "after", self.root / "review")
        self.assertEqual(result["changed_files"], 1)
        self.assertEqual(result["content_flags"], 0)
        self.assertIn("xelatex", (self.root / "review/changes.diff").read_text(encoding="utf-8"))

    def test_review_escapes_artifacts_and_notes_and_has_no_remote_dependencies(self):
        self.put("before/main.tex", "Original\n")
        self.put("after/main.tex", "<script>alert(1)</script>\n")
        notes = self.put("notes.txt", '<img src="https://example.invalid/tracker">')
        review_project.review(self.root / "before", self.root / "after", self.root / "review", notes=notes)
        page = (self.root / "review/report.html").read_text(encoding="utf-8")
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn('<img src="https://', page)
        self.assertIn("Content-Security-Policy", page)

    def test_stale_build_source_is_rejected_without_partial_publication(self):
        self.put("before/main.tex", "Original\n")
        source = self.put("after/main.tex", "Candidate\n")
        record = self.build_record(source.parent)
        source.write_text("Changed later\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            review_project.review(self.root / "before", source.parent, self.root / "review", after_build=record)
        self.assertFalse((self.root / "review").exists())

    def test_changed_recorded_chapter_is_rejected(self):
        self.put("before/main.tex", "Original\n")
        self.put("after/main.tex", "Candidate\n")
        chapter = self.put("after/chapter.tex", "Supplied 76.10")
        record = self.build_record(self.root / "after")
        data = read_json(record)
        data["local_inputs"].append({"path": "chapter.tex", "observations": [{"sha256": sha256(chapter), "error": None}]})
        record.write_text(json.dumps(data), encoding="utf-8")
        chapter.write_text("Changed 96.10", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "recorded input changed"):
            review_project.review(self.root / "before", self.root / "after", self.root / "review", after_build=record)
        self.assertFalse((self.root / "review").exists())

    def test_verified_pdf_is_copied_and_tampering_is_rejected(self):
        self.put("before/main.tex", "Original\n")
        self.put("after/main.tex", "Candidate\n")
        record = self.build_record(self.root / "after", "success")
        review_project.review(self.root / "before", self.root / "after", self.root / "review", after_build=record)
        report = read_json(self.root / "review/review.json")
        self.assertEqual(report["builds"]["after"]["pdf_binding"], "fingerprint-matched")
        self.assertTrue((self.root / "review/evidence/after/pages/page-0001.png").is_file())
        with (record.parent / "main.pdf").open("ab") as stream:
            stream.write(b"changed")
        with self.assertRaisesRegex(ValueError, "PDF changed"):
            review_project.review(self.root / "before", self.root / "after", self.root / "refused", after_build=record)
        self.assertFalse((self.root / "refused").exists())

    def test_review_refuses_existing_and_nested_destinations(self):
        self.put("before/main.tex", "Original\n")
        self.put("after/main.tex", "Candidate\n")
        for output in (self.root / "before/review", self.root / "after"):
            with self.assertRaisesRegex(ValueError, "new and outside"):
                review_project.review(self.root / "before", self.root / "after", output)

    def test_review_input_change_or_render_failure_publishes_nothing(self):
        self.put("before/main.tex", "Original\n")
        self.put("after/main.tex", "Candidate\n")
        with patch.object(review_project, "render", side_effect=OSError("Deliberate output failure")):
            with self.assertRaises(OSError):
                review_project.review(self.root / "before", self.root / "after", self.root / "review")
        self.assertFalse((self.root / "review").exists())

    def test_full_manuscript_portable_run_keeps_builds_unverified(self):
        with patch("run_paper_example.shutil.which", return_value=None):
            with self.assertRaisesRegex(ValueError, "native checks"):
                run_paper(self.root / "strict")
            result = run_paper(self.root / "portable", allow_unverified=True, language="zh")
        self.assertEqual(result["status"], "partial")
        self.assertTrue(result["sources_unchanged"])
        self.assertEqual(result["review"]["content_flags"], 0)
        self.assertEqual(result["review"]["open_decisions"], 1)
        self.assertTrue(all(status == "unverified" for status in result["builds"].values()))
        self.assertTrue((self.root / "portable/inspection-before.html").is_file())
        self.assertTrue((self.root / "portable/inspection-after.html").is_file())
        self.assertEqual({side: entry["status"] for side, entry in result["inspection_integrity"].items()},
                         {"before": "verified", "after": "verified"})
        for side in ("before", "after"):
            self.assertTrue((self.root / f"portable/inspection-{side}/integrity.json").is_file())
        self.assertIn("论文修改审阅", (self.root / "portable/review/report.html").read_text(encoding="utf-8"))
        self.assertIn("LaTeX 项目检查", (self.root / "portable/inspection-after.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
