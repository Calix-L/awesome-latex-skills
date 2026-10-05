"""Citation grammar, missed-key controls and portable report evidence."""
from collections import Counter
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from citation_lexer import SINGLE_CITES, MULTI_CITES
from project_doctor import commands, inspect_project
from project_report import inspection_html
from inspection_bundle import export_inspection
from review_project import content_tokens, review
from verify_artifacts import verify_inspection, verify_review
from review_report import review_html


class CitationTests(unittest.TestCase):
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
        return path

    def check(self, body, refs="@misc{a,title={A}}\n@misc{b,title={B}}"):
        self.put("main.tex", "\\documentclass{article}\n" + body)
        self.put("refs.bib", refs)
        with patch("project_doctor.shutil.which", return_value="test/tool"):
            return inspect_project(self.paper, "main.tex", "pdflatex", "biber")

    def test_common_single_command_families_find_keys(self):
        for name in sorted(SINGLE_CITES):
            with self.subTest(name=name):
                rows = list(commands(rf"\{name}[see {{nested ] text}}][p. 7]{{a,b}}"))
                self.assertEqual(len(rows), 1)
                self.assertTrue(rows[0]["supported"])
                self.assertEqual(rows[0]["value"], "a,b")

    def test_multicite_families_keep_every_group(self):
        for name in sorted(MULTI_CITES):
            with self.subTest(name=name):
                rows = list(commands(rf"\{name}(see {{nested ) text}})(all)[note][p.]{{a}}[p.]{{b,a}}"))
                self.assertEqual([r["value"] for r in rows], ["a", "b,a"])
                self.assertEqual([r["citation_group"] for r in rows], [1, 2])

    def test_missing_key_in_second_group_is_located(self):
        report = self.check("\\parencites{a}\n[p. 9]{missing}\n\\addbibresource{refs.bib}")
        issue = next(r for r in report["diagnostics"] if r["code"] == "unknown-citation")
        self.assertEqual((issue["file"], issue["line"]), ("main.tex", 2))
        self.assertIn("missing", issue["message"])
        self.assertEqual([r["key"] for r in report["citation_inventory"]], ["a", "missing"])
        self.assertEqual(report["citation_inventory"][1]["group"], 2)

    def test_notes_with_escaped_delimiters_are_not_keys(self):
        rows = list(commands(r"\citep[see \] and {nested ]}][\textit{p. 2}]{a}"))
        self.assertEqual([r["value"] for r in rows], ["a"])

    def test_comments_between_arguments_retain_command_line(self):
        text = "\n\\textcites% ignored {fake}\n[see]% ignored\n{a}\n{b}"
        rows = list(commands(text))
        self.assertEqual([r["value"] for r in rows], ["a", "b"])
        self.assertEqual([r["line"] for r in rows], [2, 2])

    def test_star_and_capital_variants_are_preserved(self):
        report = self.check(r"\Citep*{a}\Textcite{b}\addbibresource{refs.bib}")
        self.assertFalse(report["diagnostics"])
        self.assertEqual([(r["command"], r["starred"]) for r in report["citation_inventory"]], [("Citep", True), ("Textcite", False)])

    def test_citetext_prose_is_not_a_key_and_nested_citations_survive(self):
        report = self.check(r"\citetext{private communication; \citealp{a}}\addbibresource{refs.bib}")
        self.assertFalse(report["diagnostics"])
        self.assertEqual([r["key"] for r in report["citation_inventory"]], ["a"])

    def test_comment_verbatim_and_control_symbol_examples_are_ignored(self):
        text = "% \\parencite{fake}\n" + r"\verb|\cite{fake}|\begin{verbatim}\autocite{fake}\end{verbatim}\\cite{fake}\cite{a}"
        self.assertEqual([r["value"] for r in commands(text)], ["a"])

    def test_nocite_wildcard_is_inventory_only(self):
        report = self.check(r"\nocite{*,a}\cite{*}\addbibresource{refs.bib}")
        self.assertEqual([r["key"] for r in report["citation_inventory"]], ["*", "a", "*"])
        self.assertEqual(sum(r["code"] == "unknown-citation" for r in report["diagnostics"]), 1)

    def test_malformed_notes_are_unverified_without_guessed_keys(self):
        for text in (r"\parencite[missing{a}", r"\cites(unclosed{a}", r"\cite[one][two][three]{a}", r"\cite[bad}]{a}"):
            with self.subTest(text=text):
                rows = list(commands(text))
                self.assertTrue(any("citation_issue" in r for r in rows))
                self.assertFalse(any(r["supported"] for r in rows))

    def test_nested_dynamic_and_empty_keys_are_not_claimed(self):
        for value in (r"\key", "a{b}", "#1", "a,,b", "", "a,"):
            with self.subTest(value=value):
                rows = list(commands(r"\autocite{" + value + "}"))
                self.assertFalse(any(r["supported"] for r in rows))
                self.assertIn("citation_issue", rows[0])

    def test_later_bad_group_keeps_partial_inventory_and_explicit_issue(self):
        report = self.check(r"\parencites{a}{\key}\addbibresource{refs.bib}")
        self.assertEqual([r["key"] for r in report["citation_inventory"]], ["a"])
        self.assertEqual([r["code"] for r in report["diagnostics"]], ["citation-unverified"])
        self.assertEqual(report["status"], "needs-review")

    def test_special_volume_and_custom_cite_forms_are_unverified(self):
        for name in ("volcite", "Pvolcites", "citefield", "citecustom", "citelist"):
            with self.subTest(name=name):
                rows = list(commands(rf"\{name}{{volume}}{{key}}"))
                self.assertIn("citation_issue", rows[0])
                self.assertFalse(rows[0]["supported"])

    def test_depth_bound_is_iterative_and_reports_issue(self):
        for count, supported in ((100, True), (129, False)):
            rows = list(commands(r"\cite[" + "{" * count + "note" + "}" * count + "]{a}"))
            self.assertEqual(rows[0]["supported"], supported)

    def test_key_matching_is_exact_and_unicode_is_retained(self):
        report = self.check(r"\parencite{A,中文}\addbibresource{refs.bib}", "@misc{a,title={A}}\n@misc{中文,title={B}}")
        self.assertEqual([r["key"] for r in report["citation_inventory"]], ["A", "中文"])
        self.assertEqual(sum(r["code"] == "unknown-citation" for r in report["diagnostics"]), 1)

    def test_included_source_citations_keep_file_location(self):
        self.put("section.tex", "\n\\textcite{a}")
        report = self.check(r"\input{section}\addbibresource{refs.bib}")
        self.assertEqual((report["citation_inventory"][0]["file"], report["citation_inventory"][0]["line"]), ("section.tex", 2))

    def test_input_after_citation_is_not_swallowed(self):
        rows = list(commands(r"\cites{a}{b}\input{section}"))
        self.assertEqual([(r["name"], r["value"]) for r in rows], [("cites", "a"), ("cites", "b"), ("input", "section")])

    def test_review_detects_operator_independent_second_group_key_change(self):
        before, after = self.root / "before", self.root / "after"
        for folder, key in ((before, "a"), (after, "b")):
            folder.mkdir()
            (folder / "main.tex").write_text(r"\documentclass{article}\parencites{same}{" + key + "}", encoding="utf-8")
        output = self.root / "review"
        result = review(before, after, output, language="zh")
        evidence = json.loads((output / "review.json").read_text(encoding="utf-8"))
        self.assertEqual(result["content_flags"], 1)
        self.assertEqual(set(evidence["content_audit"][0]), {"file", "requires_review", "reference_keys"})
        self.assertEqual(evidence["citation_inventory"]["after"][1]["key"], "b")
        self.assertIn("带源码位置的文献引用", (output / "report.html").read_text(encoding="utf-8"))
        self.assertEqual(verify_review(output)["status"], "verified")

    def test_review_retains_multiplicity_without_flagging_order_only(self):
        self.assertEqual(content_tokens(r"\cites{a}{b,a}")[1], content_tokens(r"\cites{b}{a,a}")[1])
        self.assertNotEqual(content_tokens(r"\cites{a}{b,a}")[1], content_tokens(r"\cites{a}{b}")[1])
        self.assertEqual(content_tokens(r"\textcite{a}")[1], Counter({("textcite", "a"): 1}))

    def test_unchanged_unverified_citations_appear_in_both_review_sides(self):
        before, after = self.root / "before", self.root / "after"
        for folder in (before, after):
            folder.mkdir()
            (folder / "main.tex").write_text(r"\documentclass{article}\volcite{1}{a}", encoding="utf-8")
        output = self.root / "review"
        result = review(before, after, output)
        self.assertEqual(result["source_scan_issues"], 2)
        self.assertEqual(result["content_flags"], 0)

    def test_bilingual_html_escapes_keys_and_paths(self):
        report = self.check(r"\cite{<img>}&\addbibresource{refs.bib}")
        for language in ("en", "zh"):
            page = inspection_html(report, language)
            self.assertIn("&lt;img&gt;", page)
            self.assertNotIn("<img>", page)
            self.assertIn("main.tex:2", page)
            self.assertIn("scope=\"col\"", page)
            self.assertIn("Content-Security-Policy", page)

    def test_legacy_inspection_without_inventory_still_renders(self):
        report = self.check(r"\cite{a}\addbibresource{refs.bib}")
        del report["citation_inventory"]
        self.assertIn("LaTeX project inspection", inspection_html(report))

    def test_legacy_review_without_inventory_still_renders(self):
        before, after = self.root / "before", self.root / "after"
        for folder in (before, after):
            folder.mkdir()
            (folder / "main.tex").write_text(r"\documentclass{article}\cite{a}", encoding="utf-8")
        output = self.root / "review"
        review(before, after, output)
        report = json.loads((output / "review.json").read_text(encoding="utf-8"))
        del report["citation_inventory"]
        self.assertIn("Manuscript change review", review_html(report, {}))

    def test_unclosed_later_group_keeps_complete_keys(self):
        rows = list(commands(r"\cites{a}[unclosed{b}"))
        self.assertEqual([r["value"] for r in rows if r["supported"]], ["a"])
        self.assertTrue(any("citation_issue" in r for r in rows))

    def test_internal_control_names_do_not_match_prefixes(self):
        self.assertEqual(list(commands(r"\citep@internal{fake}\parencite@internal{fake}")), [])

    def test_sealed_inspection_preserves_keys_and_detects_changed_inventory(self):
        self.check(r"\textcite{a}\addbibresource{refs.bib}")
        output = self.root / "inspection"
        with patch("project_doctor.shutil.which", return_value="test/tool"):
            export_inspection(self.paper, output, "main.tex", "pdflatex", "biber", "zh")
        self.assertEqual(verify_inspection(output)["status"], "verified")
        path = output / "inspection.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(report["citation_inventory"][0]["key"], "a")
        report["citation_inventory"][0]["key"] = "changed"
        path.write_text(json.dumps(report), encoding="utf-8")
        self.assertEqual(verify_inspection(output)["status"], "failed")
