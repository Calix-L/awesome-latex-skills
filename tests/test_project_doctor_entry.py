"""Project-aware prerequisite checks preserve uncertainty and never perform builds."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doctor import diagnose_project, main
from project_doctor import initialize
from project_support import sha256


class ProjectDoctorEntryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "paper with spaces"
        self.root.mkdir()
        (self.root / "main.tex").write_text("\\documentclass{article}\n\\begin{document}Text.\\end{document}\n", encoding="utf-8")

    def call(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as stdout, contextlib.redirect_stderr(io.StringIO()) as stderr:
            code = main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    @patch("shutil.which", side_effect=lambda name: f"/tools/{name}")
    def test_configuration_is_used_and_sources_are_unchanged(self, tools):
        initialize(self.root, "main.tex", "xelatex", "biber")
        before = {p.name: sha256(p) for p in self.root.iterdir()}
        with patch("doctor.pdf_probe", side_effect=AssertionError("Unrequested PDF probe")):
            report = diagnose_project(self.root, ["latex-rescue"])
        self.assertEqual((report["engine"], report["backend"], report["status"]), ("xelatex", "biber", "ready"))
        self.assertEqual(report["project"]["root_selection"], "configuration")
        self.assertEqual(before, {p.name: sha256(p) for p in self.root.iterdir()})
        names = [c["name"] for c in report["checks"]]
        self.assertIn("biber", names)
        self.assertNotIn("pdflatex", names)

    @patch("shutil.which", side_effect=lambda name: f"/tools/{name}")
    def test_explicit_settings_override_without_rewriting_configuration(self, tools):
        initialize(self.root, "main.tex", "xelatex", "biber")
        config_hash = sha256(self.root / ".als.json")
        report = diagnose_project(self.root, ["latex-rescue"], engine="lualatex", backend="bibtex")
        self.assertEqual((report["engine"], report["backend"]), ("lualatex", "bibtex"))
        self.assertEqual(config_hash, sha256(self.root / ".als.json"))

    @patch("shutil.which", return_value="/tools/available")
    def test_missing_input_blocks_even_with_all_local_tools(self, tools):
        (self.root / "main.tex").write_text("\\documentclass{article}\n\\input{missing}\n", encoding="utf-8")
        report = diagnose_project(self.root, ["latex-rescue"], engine="pdflatex")
        self.assertTrue(report["local_prerequisites_met"])
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any(c["code"] == "missing-input" for c in report["project"]["diagnostics"]))
        code, out, err = self.call("--project", str(self.root), "--engine", "pdflatex", "--skill", "latex-rescue", "--json")
        self.assertEqual(code, 1, err)
        self.assertEqual(json.loads(out)["status"], "blocked")

    @patch("shutil.which", return_value="/tools/available")
    def test_unknown_references_need_review_without_fabricating_entries(self, tools):
        (self.root / "main.tex").write_text("\\documentclass{article}\n\\cite{missing}\n", encoding="utf-8")
        report = diagnose_project(self.root, ["latex-rescue"], engine="pdflatex")
        self.assertEqual(report["status"], "needs-review")
        self.assertEqual(report["project"]["bibliography_entries"], [])
        self.assertEqual(self.call("--project", str(self.root), "--engine", "pdflatex", "--skill", "latex-rescue", "--json")[0], 0)

    @patch("shutil.which", return_value=None)
    def test_missing_selected_backend_is_actionable(self, tools):
        initialize(self.root, "main.tex", "xelatex", "biber")
        report = diagnose_project(self.root, ["latex-rescue"])
        self.assertEqual(report["status"], "blocked")
        backend = next(c for c in report["checks"] if c["name"] == "biber")
        self.assertTrue(backend["required"])
        self.assertIn("PATH", backend["next_action"])

    @patch("shutil.which", return_value="/tools/available")
    def test_unconfigured_engine_is_not_guessed(self, tools):
        report = diagnose_project(self.root, ["latex-rescue"])
        self.assertIsNone(report["engine"])
        self.assertIsNone(report["project"]["engine"])
        self.assertFalse(report["local_prerequisites_met"])
        self.assertEqual(report["status"], "blocked")
        self.assertEqual([c["name"] for c in report["checks"]], ["python", "engine-selection", "latexmk"])
        self.assertNotIn("pdflatex", [c.args[0] for c in tools.call_args_list])

    @patch("shutil.which", return_value=None)
    def test_polish_with_unselected_engine_remains_advisory(self, tools):
        report = diagnose_project(self.root, ["latex-polish"])
        self.assertTrue(report["local_prerequisites_met"])
        self.assertEqual(report["status"], "needs-review")

    @patch("shutil.which", return_value="/tools/available")
    def test_reachable_bibliography_requires_actual_backend_for_rescue(self, tools):
        (self.root / "main.tex").write_text("\\documentclass{article}\n\\bibliography{refs}\n", encoding="utf-8")
        (self.root / "refs.bib").write_text('@article{known, title={Example}}\n', encoding="utf-8")
        report = diagnose_project(self.root, ["latex-rescue"], engine="pdflatex")
        self.assertIsNone(report["backend"])
        self.assertEqual(report["project"]["status"], "ready")
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["checks"][-1]["name"], "backend-selection")
        selected = diagnose_project(self.root, ["latex-rescue"], engine="pdflatex", backend="bibtex")
        self.assertEqual(selected["status"], "ready")
        polish = diagnose_project(self.root, ["latex-polish"], engine="pdflatex")
        self.assertTrue(polish["local_prerequisites_met"])
        self.assertEqual(polish["status"], "needs-review")

    @patch("shutil.which", return_value="/tools/available")
    def test_bibliography_in_unreachable_sources_does_not_require_backend(self, tools):
        (self.root / "unused.tex").write_text("\\bibliography{refs}\n", encoding="utf-8")
        report = diagnose_project(self.root, ["latex-rescue"], main="main.tex", engine="pdflatex")
        self.assertEqual(report["status"], "ready")
        self.assertNotIn("backend-selection", [c["name"] for c in report["checks"]])

    @patch("shutil.which", return_value="/tools/available")
    def test_ambiguous_roots_are_reported_without_selection(self, tools):
        (self.root / "other.tex").write_text("\\documentclass{article}\n", encoding="utf-8")
        report = diagnose_project(self.root, ["latex-rescue"], engine="pdflatex")
        self.assertIsNone(report["project"]["main"])
        self.assertEqual(report["project"]["root_candidates"], ["main.tex", "other.tex"])
        self.assertEqual(report["status"], "blocked")
        selected = diagnose_project(self.root, ["latex-rescue"], main="other.tex", engine="pdflatex")
        self.assertEqual(selected["project"]["main"], "other.tex")
        self.assertEqual(selected["status"], "ready")

    def test_invalid_config_returns_structured_error_without_writes(self):
        (self.root / ".als.json").write_text('{"schema":1,"main":"../outside.tex"}', encoding="utf-8")
        before = {p.name: sha256(p) for p in self.root.iterdir()}
        code, out, err = self.call("--project", str(self.root), "--json")
        self.assertEqual(code, 2)
        self.assertIn("error", json.loads(out))
        self.assertNotIn("Traceback", err)
        self.assertEqual(before, {p.name: sha256(p) for p in self.root.iterdir()})

    def test_nonexistent_project_returns_error_without_creating_it(self):
        missing = self.root / "missing"
        code, out, _ = self.call("--project", str(missing), "--json")
        self.assertEqual(code, 2)
        self.assertIn("error", json.loads(out))
        self.assertFalse(missing.exists())

    def test_main_without_project_is_refused(self):
        code, out, _ = self.call("--main", "main.tex", "--json")
        self.assertEqual(code, 2)
        self.assertIn("requires --project", json.loads(out)["error"])

    def test_help_does_not_read_project(self):
        with patch("doctor.diagnose_project", side_effect=AssertionError("Help inspected project")):
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
                main(["--project", str(self.root / "missing"), "--help"])
        self.assertEqual(result.exception.code, 0)

    @patch("shutil.which", return_value=None)
    def test_chinese_output_contains_action_and_keeps_actual_paths(self, tools):
        initialize(self.root, "main.tex", "xelatex", "biber")
        code, out, _ = self.call("--project", str(self.root), "--skill", "latex-rescue", "--language", "zh")
        self.assertEqual(code, 1)
        for text in ("综合状态:", "下一步", "所选引擎加入 PATH", str(self.root), "main.tex", "biber"):
            self.assertIn(text, out)

    @patch("shutil.which", return_value="/tools/available")
    def test_json_language_does_not_change_the_evidence(self, tools):
        args = ("--project", str(self.root), "--engine", "pdflatex", "--skill", "latex-rescue", "--json")
        en = json.loads(self.call(*args)[1])
        zh = json.loads(self.call(*args, "--language", "zh")[1])
        self.assertEqual(en, zh)
        self.assertTrue(en["project"]["observed_files"])

    def test_wrapper_from_external_cwd_retains_project_error(self):
        script = Path(__file__).resolve().parents[1] / "scripts/als.py"
        result = subprocess.run([sys.executable, str(script), "--json", "doctor", "--project", str(self.root / "missing")],
                                cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 2, result.stderr)
        envelope = json.loads(result.stdout)
        self.assertEqual(envelope["exit_code"], 2)
        self.assertIsNotNone(envelope["result"]["error"])
        self.assertEqual(list(self.root.iterdir()), [self.root / "main.tex"])


if __name__ == "__main__":
    unittest.main()
