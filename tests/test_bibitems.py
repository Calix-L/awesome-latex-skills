"""Manual bibliography compatibility, review signals and evidence controls."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from project_doctor import commands, inspect_project
from project_report import inspection_html
from review_project import content_tokens, review
from review_report import review_html
from inspection_bundle import export_inspection
from verify_artifacts import verify_inspection, verify_review


class BibitemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paper = self.root / "paper"
        self.paper.mkdir()

    def put(self, name, text):
        path = self.paper / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def check(self, body):
        self.put("main.tex", "\\documentclass{article}\n" + body)
        with patch("project_doctor.shutil.which", return_value="test/tool"):
            return inspect_project(self.paper, "main.tex", "pdflatex")

    def reviewed(self, old, new, language="en"):
        for side, text in (("before", old), ("after", new)):
            folder = self.root / side
            folder.mkdir()
            (folder / "main.tex").write_text("\\documentclass{article}\n" + text, encoding="utf-8")
        output = self.root / "review"
        result = review(self.root / "before", self.root / "after", output, language=language)
        return result, json.loads((output / "review.json").read_text(encoding="utf-8")), output

    def test_plain_and_optional_display_labels_supply_only_mandatory_keys(self):
        rows = list(commands(r"\bibitem{plain} Title. \bibitem[Author(2020)]{named} Title."))
        self.assertEqual([(r["name"], r["value"]) for r in rows], [("bibitem", "plain"), ("bibitem", "named")])

    def test_nested_display_braces_protect_closing_bracket_and_skip_commands(self):
        rows = list(commands(r"\bibitem[{text ] \cite{display} \ref{label}}(2020)]{real} \cite{body}"))
        self.assertEqual([(r["name"], r["value"]) for r in rows], [("bibitem", "real"), ("cite", "body")])

    def test_comment_whitespace_and_crlf_keep_command_opening_line(self):
        text = "\r\n\\bibitem % comment\r\n [Author(2020)] % note\r\n {real}"
        row = list(commands(text))[0]
        self.assertEqual((row["line"], row["value"]), (2, "real"))

    def test_masked_and_internal_commands_do_not_supply_keys(self):
        text = "% \\bibitem{fake}\n" + r"\verb|\bibitem{fake}|\begin{verbatim}\bibitem{fake}\end{verbatim}\\bibitem{fake}\bibitem@internal{fake}\bibitem{real}"
        self.assertEqual([r["value"] for r in commands(text)], ["real"])

    def test_empty_dynamic_nested_and_starred_keys_are_unverified(self):
        for text in (r"\bibitem{}", r"\bibitem{\macro}", r"\bibitem{#1}", r"\bibitem{a{b}}", r"\bibitem*{a}"):
            with self.subTest(text=text):
                rows = list(commands(text))
                self.assertFalse(any(r["supported"] for r in rows))
                self.assertTrue(any("bibitem_issue" in r for r in rows))

    def test_missing_unclosed_extra_optional_and_depth_are_unverified(self):
        for text in (r"\bibitem", r"\bibitem[a", r"\bibitem[a]{b", r"\bibitem[a][b]{c}",
                     r"\bibitem[" + "{" * 129 + "label" + "}" * 129 + "]{key}"):
            with self.subTest(text=text):
                self.assertTrue(any("bibitem_issue" in r for r in commands(text)))
                self.assertFalse(any(r["supported"] for r in commands(text)))

    def test_forward_manual_entries_resolve_without_a_backend(self):
        report = self.check(r"\begin{document}\cite{a,b}\begin{thebibliography}{9}\bibitem{a} A. \bibitem[Bob(2020)]{b} B. \end{thebibliography}\end{document}")
        self.assertEqual(report["diagnostics"], [])
        self.assertIsNone(report["backend"])
        self.assertEqual(report["bibliography_entries"], [])
        self.assertEqual([r["key"] for r in report["bibitem_inventory"]], ["a", "b"])

    def test_unknown_citation_remains_located(self):
        report = self.check("\\bibitem{a}\n\\cite{missing}")
        warning = next(r for r in report["diagnostics"] if r["code"] == "unknown-citation")
        self.assertEqual((warning["file"], warning["line"]), ("main.tex", 3))

    def test_cross_file_duplicates_locate_first_and_every_later_definition(self):
        self.put("one.tex", "\\bibitem{a}\n")
        self.put("two.tex", "\n\\bibitem{a}\n\\bibitem{a}")
        report = self.check(r"\cite{a}\input{one}\input{two}")
        warnings = [r for r in report["diagnostics"] if r["code"] == "duplicate-bibitem-key"]
        self.assertEqual([(r["file"], r["line"]) for r in warnings], [("two.tex", 2), ("two.tex", 3)])
        self.assertTrue(all("one.tex:1" in r["message"] for r in warnings))
        self.assertEqual([r["definition_count"] for r in report["bibitem_inventory"]], [3, 3, 3])

    def test_excluded_includes_do_not_supply_manual_entries(self):
        self.put("unused.tex", r"\bibitem{unused}")
        report = self.check(r"\includeonly{}\include{unused}\cite{unused}")
        self.assertEqual(report["bibitem_inventory"], [])
        self.assertTrue(any(r["code"] == "unknown-citation" for r in report["diagnostics"]))

    def test_repeated_input_and_package_reload_do_not_invent_duplicates(self):
        self.put("one.tex", r"\bibitem{a}")
        self.put("local.sty", r"\bibitem{b}")
        report = self.check(r"\input{one}\input{one}\usepackage{local}\RequirePackage{local}\cite{a,b}")
        self.assertEqual([r["key"] for r in report["bibitem_inventory"]], ["a", "b"])
        self.assertEqual([r["code"] for r in report["diagnostics"]], ["repeated-source"])

    def test_manual_and_database_keys_combine_without_inventing_generated_duplicates(self):
        self.put("refs.bib", "@misc{shared,title={Synthetic}}\n@misc{database,title={Synthetic}}")
        report = self.check(r"\bibitem{manual}\bibitem{shared}\bibliography{refs}\cite{manual,shared,database}")
        self.assertFalse(any(r["code"] in {"unknown-citation", "duplicate-bib-key", "duplicate-bibitem-key"} for r in report["diagnostics"]))
        overlap = next(r for r in report["diagnostics"] if r["code"] == "bibliography-key-overlap")
        self.assertEqual((overlap["severity"], overlap["file"], overlap["line"]), ("unverified", "refs.bib", 1))
        self.assertIn("main.tex:2", overlap["message"])

    def test_exact_case_unicode_and_comma_definition_keys(self):
        report = self.check(r"\bibitem{Key}\bibitem{key}\bibitem{文献}\bibitem{a,b}\cite{Key,key,文献}")
        self.assertEqual(report["diagnostics"], [])
        self.assertEqual([r["key"] for r in report["bibitem_inventory"]], ["Key", "key", "文献", "a,b"])
        self.assertEqual(content_tokens(r"\bibitem{a,b}")[1], {("bibitem", "a,b"): 1})

    def test_only_definition_key_change_is_a_review_signal(self):
        result, report, output = self.reviewed(r"\bibitem[Author]{old} Title.", r"\bibitem[Author]{new} Title.", "zh")
        self.assertEqual((result["content_flags"], result["source_scan_issues"]), (1, 0))
        self.assertEqual(set(report["content_audit"][0]), {"file", "requires_review", "reference_keys"})
        self.assertEqual(report["bibitem_inventory"]["after"][0]["key"], "new")
        self.assertNotIn("definition_count", report["bibitem_inventory"]["after"][0])
        self.assertIn("手写参考文献条目", (output / "report.html").read_text(encoding="utf-8"))
        self.assertEqual(verify_review(output)["status"], "verified")

    def test_display_and_title_text_do_not_become_key_change_signals(self):
        old = r"\bibitem[Author]{same} Original title."
        new = r"\bibitem[Writer]{same} Revised title."
        self.assertEqual(content_tokens(old)[1], content_tokens(new)[1])
        result, report, _ = self.reviewed(old, new)
        self.assertEqual(result["content_flags"], 0)
        self.assertEqual(len(report["changes"]), 1)

    def test_entry_multiplicity_and_definition_citation_roles_remain_distinct(self):
        self.assertNotEqual(content_tokens(r"\bibitem{a}")[1], content_tokens(r"\bibitem{a}\bibitem{a}")[1])
        self.assertNotEqual(content_tokens(r"\bibitem{a}\cite{b}")[1], content_tokens(r"\bibitem{b}\cite{a}")[1])

    def test_unchanged_unsupported_definition_reports_both_versions(self):
        result, report, _ = self.reviewed(r"\bibitem{\macro}", r"\bibitem{\macro}")
        self.assertEqual((result["content_flags"], result["source_scan_issues"]), (0, 2))
        self.assertEqual({r["side"] for r in report["source_scan_issues"]}, {"before", "after"})
        self.assertEqual(report["bibitem_inventory"], {"before": [], "after": []})

    def test_review_inventories_inactive_source_without_claiming_resolution(self):
        for side in ("before", "after"):
            folder = self.root / side
            folder.mkdir()
            (folder / "main.tex").write_text(r"\documentclass{article}", encoding="utf-8")
            (folder / "unused.tex").write_text(r"\bibitem{unused}", encoding="utf-8")
        output = self.root / "review"
        review(self.root / "before", self.root / "after", output)
        report = json.loads((output / "review.json").read_text(encoding="utf-8"))
        self.assertEqual(report["bibitem_inventory"]["before"], [{"file": "unused.tex", "line": 1, "key": "unused"}])

    def test_bilingual_html_escapes_manual_entry_keys_and_supports_legacy(self):
        report = self.check(r"\bibitem{<tag>}\cite{<tag>}")
        for language, title in (("en", "Manual bibliography entries"), ("zh", "手写参考文献条目")):
            page = inspection_html(report, language)
            self.assertIn(title, page)
            self.assertIn("&lt;tag&gt;", page)
            self.assertNotIn("<tag>", page)
            self.assertNotIn("<script", page)
        del report["bibitem_inventory"]
        self.assertNotIn("Manual bibliography entries", inspection_html(report))
        _, legacy, _ = self.reviewed(r"\bibitem{<tag>}", r"\bibitem{<other>}")
        self.assertIn("&lt;other&gt;", review_html(legacy, {}))
        del legacy["bibitem_inventory"]
        self.assertNotIn("Manual bibliography entries", review_html(legacy, {}))

    def test_sealed_inspection_rechecks_inventory_bytes(self):
        self.check(r"\bibitem{a}\cite{a}")
        output = self.root / "inspection"
        with patch("project_doctor.shutil.which", return_value="test/tool"):
            report = export_inspection(self.paper, output, "main.tex", "pdflatex", language="zh")
        self.assertEqual(report["bibitem_inventory"][0]["key"], "a")
        self.assertEqual(verify_inspection(output)["status"], "verified")
        data = json.loads((output / "inspection.json").read_text(encoding="utf-8"))
        data["bibitem_inventory"][0]["key"] = "changed"
        (output / "inspection.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(verify_inspection(output)["status"], "failed")
