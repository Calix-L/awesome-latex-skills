"""Literal label resolution and cross-reference review negative controls."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from project_doctor import commands, inspect_project
from reference_lexer import SINGLE_REFS, LIST_REFS, RANGE_REFS
from project_report import inspection_html
from review_project import content_tokens, review
from review_report import review_html
from inspection_bundle import export_inspection
from verify_artifacts import verify_inspection, verify_review


class CrossReferenceTests(unittest.TestCase):
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

    def test_single_commands_do_not_split_comma_keys(self):
        for name in SINGLE_REFS:
            with self.subTest(name=name):
                self.assertEqual(list(commands(rf"\{name}{{a,b}}"))[0]["keys"], ["a,b"])

    def test_list_commands_split_only_literal_list_keys(self):
        for name in LIST_REFS:
            with self.subTest(name=name):
                self.assertEqual(list(commands(rf"\{name}{{a, b}}"))[0]["keys"], ["a", "b"])

    def test_range_commands_keep_both_endpoint_roles(self):
        for name in RANGE_REFS:
            with self.subTest(name=name):
                rows = list(commands(rf"\{name}{{a}}{{b}}"))
                self.assertEqual([r["keys"] for r in rows], [["a"], ["b"]])
                self.assertEqual([r["reference_group"] for r in rows], [1, 2])

    def test_hyperref_text_is_not_target_and_nested_commands_remain_visible(self):
        rows = list(commands(r"\hyperref[a]{see \ref*{b} and \textcite{c}}"))
        self.assertEqual([(r["name"], r["value"]) for r in rows], [("hyperref", "a"), ("ref", "b"), ("textcite", "c")])
        self.assertTrue(rows[1]["starred"])

    def test_hyperref_prose_never_becomes_a_reference_key(self):
        report = self.check(r"\hyperref[a]{arbitrary, prose}\label{a}")
        self.assertFalse(report["diagnostics"])
        self.assertEqual([r["key"] for r in report["reference_inventory"]], ["a"])

    def test_legacy_hyperref_form_and_missing_text_are_unverified(self):
        for text in (r"\hyperref{url}{category}{name}{text}", r"\hyperref[a]", r"\hyperref[a]{unclosed"):
            with self.subTest(text=text):
                self.assertTrue(any("reference_issue" in r for r in commands(text)))

    def test_unexpected_options_are_not_silently_ignored(self):
        self.assertIn("reference_issue", list(commands(r"\ref[unsupported]{a}"))[0])
        row = list(commands(r"\label[equation]{a}"))[0]
        self.assertEqual(row["keys"], ["a"])

    def test_later_unclosed_range_argument_retains_partial_target(self):
        rows = list(commands("\\crefrange{a}\n{unclosed"))
        self.assertEqual(rows[0]["keys"], ["a"])
        self.assertIn("reference_issue", rows[1])
        self.assertEqual([r["line"] for r in rows], [1, 1])

    def test_dynamic_nested_empty_keys_and_depth_are_unverified(self):
        for text in (r"\label{\macro}", r"\nameref{a{b}}", r"\cref{a,,b}", r"\ref{}", r"\hyperref[{a}]{text}",
                     r"\label[" + "{" * 129 + "type" + "}" * 129 + "]{a}"):
            with self.subTest(text=text):
                self.assertTrue(any("reference_issue" in r for r in commands(text)))
                self.assertFalse(any(r["supported"] for r in commands(text)))

    def test_masked_examples_and_internal_commands_do_not_define_targets(self):
        text = "% \\label{fake}\n" + r"\verb|\nameref{fake}|\begin{verbatim}\crefrange{fake}{fake}\end{verbatim}\\label{fake}\ref@internal{fake}\label{a}"
        self.assertEqual([(r["name"], r["value"]) for r in commands(text)], [("label", "a")])

    def test_capital_and_starred_forms_keep_source_metadata(self):
        report = self.check(r"\Cref*{a}\nameref*{a}\label{a}")
        self.assertFalse(report["diagnostics"])
        self.assertTrue(all(r["starred"] for r in report["reference_inventory"]))

    def test_unsupported_starred_forms_do_not_invent_labels_or_targets(self):
        for name in ("label", "eqref", "Nameref", "hyperref"):
            with self.subTest(name=name):
                rows = list(commands(rf"\{name}*{{a}}"))
                self.assertFalse(any(r["supported"] for r in rows))
                self.assertTrue(any("reference_issue" in r for r in rows))

    def test_missing_second_endpoint_is_located(self):
        report = self.check("\\label{a}\n\\crefrange{a}{missing}")
        warning = next(r for r in report["diagnostics"] if r["code"] == "unknown-label")
        self.assertEqual((warning["file"], warning["line"]), ("main.tex", 3))
        self.assertEqual([r["resolution"] for r in report["reference_inventory"]], ["defined", "missing"])

    def test_duplicate_labels_point_to_first_and_every_later_definition(self):
        self.put("one.tex", "\\label{a}\n")
        self.put("two.tex", "\n\\label{a}\n\\label{a}\n")
        report = self.check(r"\input{one}\input{two}\ref{a}")
        warnings = [r for r in report["diagnostics"] if r["code"] == "duplicate-label"]
        self.assertEqual([(r["file"], r["line"]) for r in warnings], [("two.tex", 2), ("two.tex", 3)])
        self.assertTrue(all("one.tex:1" in r["message"] for r in warnings))
        row = report["reference_inventory"][0]
        self.assertEqual((row["resolution"], row["definition_count"]), ("ambiguous", 3))
        self.assertEqual(row["first_definition"], {"file": "one.tex", "line": 1})

    def test_forward_references_resolve_after_complete_dependency_scan(self):
        self.put("section.tex", "\n\\label{later}")
        report = self.check(r"\nameref{later}\input{section}")
        self.assertFalse(report["diagnostics"])
        self.assertEqual(report["reference_inventory"][0]["first_definition"], {"file": "section.tex", "line": 2})

    def test_excluded_includes_do_not_supply_label_definitions(self):
        self.put("unused.tex", r"\label{unused}")
        report = self.check(r"\includeonly{}\include{unused}\nameref{unused}")
        self.assertEqual(report["label_inventory"], [])
        self.assertEqual(report["reference_inventory"][0]["resolution"], "missing")

    def test_repeated_source_does_not_invent_additional_definitions(self):
        self.put("one.tex", r"\label{a}")
        report = self.check(r"\input{one}\input{one}\ref{a}")
        self.assertEqual(report["reference_inventory"][0]["definition_count"], 1)
        self.assertEqual([r["code"] for r in report["diagnostics"]], ["repeated-source"])

    def test_local_class_and_reloaded_package_keep_definition_origins(self):
        self.put("local.cls", r"\LoadClass{article}\label{class}")
        self.put("local.sty", r"\label{package}")
        self.put("main.tex", r"\documentclass{local}\usepackage{local}\RequirePackage{local}\ref{class}\ref{package}")
        with patch("project_doctor.shutil.which", return_value="test/tool"):
            report = inspect_project(self.paper, "main.tex", "pdflatex")
        self.assertFalse(report["diagnostics"])
        self.assertEqual([r["first_definition"]["file"] for r in report["reference_inventory"]], ["local.cls", "local.sty"])

    def test_comma_label_is_one_key_for_core_and_hyperref(self):
        report = self.check(r"\label{a,b}\ref{a,b}\hyperref[a,b]{text}")
        self.assertFalse(report["diagnostics"])
        self.assertEqual([r["key"] for r in report["reference_inventory"]], ["a,b", "a,b"])
        self.assertEqual(content_tokens(r"\label{a,b}\ref{a,b}")[1], {("label", "a,b"): 1, ("ref", "a,b"): 1})

    def test_exact_case_unicode_and_crlf_source_lines_are_retained(self):
        report = self.check("\\label{中文}\r\n\\label{A}\r\n\\nameref{中文}\\ref{a}")
        self.assertEqual([r["line"] for r in report["label_inventory"]], [2, 3])
        self.assertEqual([r["resolution"] for r in report["reference_inventory"]], ["defined", "missing"])

    def test_review_flags_hyperref_target_change_with_unchanged_text(self):
        result, record, output = self.reviewed(r"\hyperref[old]{Same text}", r"\hyperref[new]{Same text}", "zh")
        self.assertEqual(result["content_flags"], 1)
        self.assertEqual(set(record["content_audit"][0]), {"file", "requires_review", "reference_keys"})
        self.assertEqual(record["reference_inventory"]["after"][0]["key"], "new")
        self.assertIn("标签定义与交叉引用", (output / "report.html").read_text(encoding="utf-8"))
        self.assertEqual(verify_review(output)["status"], "verified")

    def test_review_flags_reversed_range_endpoints_even_with_same_keys(self):
        result, record, _ = self.reviewed(r"\crefrange{a}{b}", r"\crefrange{b}{a}")
        self.assertEqual(result["content_flags"], 1)
        self.assertIn("reference_keys", record["content_audit"][0])

    def test_list_order_only_does_not_flag_but_multiplicity_does(self):
        self.assertEqual(content_tokens(r"\Cref{a,b,a}")[1], content_tokens(r"\Cref{b,a,a}")[1])
        self.assertNotEqual(content_tokens(r"\Cref{a,b,a}")[1], content_tokens(r"\Cref{b,a}")[1])

    def test_unchanged_unsupported_references_are_visible_in_both_versions(self):
        result, record, _ = self.reviewed(r"\nameref{\target}", r"\nameref{\target}")
        self.assertEqual(result["source_scan_issues"], 2)
        self.assertEqual([r["code"] for r in record["source_scan_issues"]], ["reference-unverified"] * 2)

    def test_bilingual_html_escapes_targets_and_legacy_inspection_renders(self):
        report = self.check(r"\label{<img>}\nameref{<img>}")
        report["reference_inventory"][0]["first_definition"]["file"] = '<script>'
        for language in ("en", "zh"):
            page = inspection_html(report, language)
            self.assertIn("&lt;img&gt;", page)
            self.assertIn("&lt;script&gt;", page)
            self.assertNotIn("<img>", page)
            self.assertNotIn("<script>", page)
        del report["label_inventory"], report["reference_inventory"]
        self.assertIn("LaTeX project inspection", inspection_html(report))

    def test_legacy_review_without_inventories_renders(self):
        _, record, _ = self.reviewed(r"\label{a}\ref{a}", r"\label{a}\ref{a}")
        del record["label_inventory"], record["reference_inventory"]
        self.assertIn("Manuscript change review", review_html(record, {}))

    def test_sealed_reference_inventory_detects_modified_target(self):
        self.check(r"\label{a}\nameref{a}")
        output = self.root / "inspection"
        with patch("project_doctor.shutil.which", return_value="test/tool"):
            export_inspection(self.paper, output, "main.tex", "pdflatex", language="zh")
        self.assertEqual(verify_inspection(output)["status"], "verified")
        path = output / "inspection.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        report["reference_inventory"][0]["key"] = "changed"
        path.write_text(json.dumps(report), encoding="utf-8")
        self.assertEqual(verify_inspection(output)["status"], "failed")
