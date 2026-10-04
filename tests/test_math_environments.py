"""Synthetic controls for literal formula changes and located review evidence."""
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from math_lexer import MATH_ENVIRONMENTS, scan_math_environments
import review_project
from verify_artifacts import verify_review


def formula(body="x+y", environment="equation"):
    return rf"\begin{{{environment}}}{body}\end{{{environment}}}"


class MathScannerTests(unittest.TestCase):
    def test_supported_environment_forms_retain_literal_body(self):
        for name in MATH_ENVIRONMENTS:
            with self.subTest(name=name):
                spans, issues = scan_math_environments(formula(environment=name))
                self.assertEqual(spans, [{"environment": name, "line": 1, "end_line": 1, "content": "x+y"}])
                self.assertEqual(issues, [])

    def test_nested_split_matrix_and_text_are_one_outer_span(self):
        body = r"\begin{split}x&=\begin{bmatrix}a&b\\c&d\end{bmatrix}\\y&=z\end{split}"
        spans, issues = scan_math_environments(formula(body))
        self.assertEqual([s["content"] for s in spans], [body])
        self.assertEqual(issues, [])

    def test_outer_arguments_and_optional_positions_are_preserved(self):
        body = r"{2}x&=y& a&=b\\\begin{aligned}[t]u&=v\end{aligned}"
        self.assertEqual(scan_math_environments(formula(body, "alignat"))[0][0]["content"], body)

    def test_unicode_crlf_and_multiline_markers_have_source_locations(self):
        text = "中文\r\n\\begin\r\n{equation}\r\nx+y\r\n\\end\r\n{equation}"
        spans, issues = scan_math_environments(text)
        self.assertEqual((spans[0]["line"], spans[0]["end_line"]), (2, 5))
        self.assertEqual(spans[0]["content"], "\r\nx+y\r\n")
        self.assertEqual(issues, [])

    def test_comments_and_verbatim_examples_do_not_supply_formula_values(self):
        fake = formula("hidden")
        text = "% " + fake + "\n" + r"\verb|" + fake + "|\n" + r"\begin{verbatim}" + fake + r"\end{verbatim}"
        self.assertEqual(scan_math_environments(text), ([], []))

    def test_comment_end_cannot_close_live_span(self):
        spans, issues = scan_math_environments("\\begin{equation}x\n% \\end{equation}\n")
        self.assertEqual(spans, [])
        self.assertEqual(issues[0]["code"], "math-environment-unclosed")

    def test_control_symbols_and_longer_control_words_are_not_openers(self):
        text = r"\\begin{equation}fake\\end{equation} \beginning{equation} \begin@{equation}"
        self.assertEqual(scan_math_environments(text), ([], []))
        self.assertEqual(scan_math_environments(r"\\" + formula())[0][0]["content"], "x+y")

    def test_custom_environments_are_not_guessed_as_outer_math(self):
        self.assertEqual(scan_math_environments(formula(environment="customequation")), ([], []))
        self.assertEqual(scan_math_environments(formula(environment="aligned")), ([], []))

    def test_custom_literal_inner_names_balance_without_expansion(self):
        body = r"\begin{my-inner}x\end{my-inner}"
        self.assertEqual(scan_math_environments(formula(body)),
                         ([{"environment": "equation", "line": 1, "end_line": 1, "content": body}], []))

    def test_starred_and_unstarred_markers_must_match(self):
        spans, issues = scan_math_environments(r"\begin{align*}x\end{align}")
        self.assertFalse(spans)
        self.assertEqual([i["code"] for i in issues], ["math-environment-mismatch", "math-environment-unclosed"])

    def test_wrong_nested_close_invalidates_outer_then_recovers(self):
        text = r"\begin{equation}\begin{split}x\end{equation}" + formula("valid", "align")
        spans, issues = scan_math_environments(text)
        self.assertEqual([s["content"] for s in spans], ["valid"])
        self.assertEqual([i["code"] for i in issues], ["math-environment-mismatch"])

    def test_unmatched_supported_end_is_located(self):
        self.assertEqual(scan_math_environments("\n\\end{gather}")[1][0]["line"], 2)
        self.assertEqual(scan_math_environments(r"\end{gather}")[1][0]["code"], "math-environment-unexpected-end")

    def test_dynamic_inner_names_are_unverified_not_complete_values(self):
        spans, issues = scan_math_environments(formula(r"\begin{\custom}x\end{\custom}"))
        self.assertFalse(spans)
        self.assertEqual([i["code"] for i in issues], ["math-environment-dynamic"] * 2)

    def test_unsupported_outer_dynamic_name_is_not_invented(self):
        self.assertEqual(scan_math_environments(r"\begin{\custom}x\end{\custom}"), ([], []))

    def test_large_inventory_and_deep_nesting_are_iterative(self):
        spans, issues = scan_math_environments((formula() + "\n") * 8000)
        self.assertEqual(len(spans), 8000)
        self.assertEqual(spans[-1]["line"], 8000)
        self.assertFalse(issues)
        body = r"\begin{inner}" * 4000 + "x" + r"\end{inner}" * 4000
        self.assertEqual(scan_math_environments(formula(body))[0][0]["content"], body)

    def test_deep_mismatched_nesting_produces_bounded_diagnostics(self):
        text = r"\begin{equation}" + r"\begin{inner}" * 4000 + r"\end{equation}"
        spans, issues = scan_math_environments(text)
        self.assertFalse(spans)
        self.assertEqual(len(issues), 1)


class MathReviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="math-review-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for side in ("before", "after"):
            (self.root / side).mkdir()
        self.output = self.root / "review"

    def write(self, side, content, filename="main.tex"):
        path = self.root / side / filename
        path.write_text(content, encoding="utf-8")
        return path

    def run_review(self, old, new, filename="main.tex", language="en"):
        self.write("before", old, filename)
        self.write("after", new, filename)
        result = review_project.review(self.root / "before", self.root / "after", self.output, language=language)
        return result, json.loads((self.output / "review.json").read_text(encoding="utf-8"))

    def test_operator_only_change_with_same_numbers_and_keys_is_flagged(self):
        result, report = self.run_review(formula("x+y"), formula("x-y"))
        self.assertEqual(result["content_flags"], 1)
        audit = report["content_audit"][0]
        self.assertEqual(set(audit), {"file", "requires_review", "math_environments"})
        self.assertIn("x-y", audit["math_environments"]["added"][0][0])
        self.assertEqual(report["schema"], 1)
        self.assertEqual(len(review_project.content_tokens("$x$")), 3)

    def test_relocation_and_reordering_do_not_invent_formula_changes(self):
        _, report = self.run_review(formula("x") + formula("y"), "\n" + formula("y") + formula("x"))
        self.assertFalse(report["content_audit"])
        self.assertEqual(report["math_environment_inventory"]["after"][0]["line"], 2)

    def test_duplicate_removal_retains_multiplicity(self):
        _, report = self.run_review(formula("x") * 2, formula("x"))
        self.assertEqual(report["content_audit"][0]["math_environments"]["removed"], [["('equation', 'x')", 1]])

    def test_environment_type_change_is_a_visible_signal(self):
        _, report = self.run_review(formula("x", "equation"), formula("x", "equation*"))
        self.assertIn("math_environments", report["content_audit"][0])

    def test_added_and_removed_sources_compare_formula_values(self):
        self.write("before", formula(), "removed.tex")
        self.write("after", formula("y"), "added.tex")
        review_project.review(self.root / "before", self.root / "after", self.output)
        report = json.loads((self.output / "review.json").read_text(encoding="utf-8"))
        self.assertEqual(len(report["content_audit"]), 2)
        self.assertTrue(all("math_environments" in item for item in report["content_audit"]))

    def test_unchanged_incomplete_formulas_are_visible_on_both_sides(self):
        result, report = self.run_review(r"\begin{equation}x", r"\begin{equation}x", language="zh")
        self.assertEqual(result["changed_files"], 0)
        self.assertEqual(result["source_scan_issues"], 2)
        self.assertEqual({i["side"] for i in report["source_scan_issues"]}, {"before", "after"})
        self.assertEqual(report["math_environment_inventory"], {"before": [], "after": []})
        self.assertIn("未验证项", (self.output / "report.html").read_text(encoding="utf-8"))

    def test_styles_and_classes_are_scanned_but_bibliography_is_not_math(self):
        for filename in ("custom.sty", "custom.cls", "refs.bib"):
            self.write("before", formula("x"), filename)
            self.write("after", formula("y"), filename)
        review_project.review(self.root / "before", self.root / "after", self.output)
        report = json.loads((self.output / "review.json").read_text(encoding="utf-8"))
        self.assertEqual({i["file"] for i in report["math_environment_inventory"]["after"]}, {"custom.sty", "custom.cls"})
        self.assertEqual({i["file"] for i in report["content_audit"]}, {"custom.sty", "custom.cls"})

    def test_html_escapes_formula_file_and_located_bilingual_details(self):
        _, report = self.run_review(formula("x<y"), formula("x>y & z"), filename='a&.tex', language="zh")
        page = (self.output / "report.html").read_text(encoding="utf-8")
        self.assertIn("公式环境变化", page)
        self.assertIn("带源码位置的公式环境", page)
        self.assertIn("a&amp;.tex:1", page)
        self.assertIn("x&gt;y &amp; z", page)
        self.assertNotIn("x>y & z", page)
        parser = HTMLParser()
        parser.feed(page)
        self.assertEqual(verify_review(self.output)["status"], "verified")
        self.assertEqual(report["builds"]["after"]["status"], "unverified")

    def test_legacy_html_report_without_additive_math_fields_still_renders(self):
        from review_report import review_html
        _, report = self.run_review(formula("x"), formula("y"))
        report.pop("math_environment_inventory")
        report.pop("math_environment_scope")
        report["content_audit"] = []
        self.assertIn("Manuscript change review", review_html(report, {}))

    def test_source_mutation_after_formula_parsing_prevents_publication(self):
        self.write("before", formula())
        after = self.write("after", formula("x-y"))
        render = review_project.render
        def mutate(*args):
            render(*args)
            after.write_text(formula("z"), encoding="utf-8")
        with patch.object(review_project, "render", side_effect=mutate):
            with self.assertRaisesRegex(ValueError, "inputs changed"):
                review_project.review(self.root / "before", self.root / "after", self.output)
        self.assertFalse(self.output.exists())

    def test_standard_library_cli_from_external_cwd_and_moved_bundle(self):
        self.write("before", formula())
        self.write("after", formula("x-y"))
        process = subprocess.run([sys.executable, "-S", str(REPO / "scripts/als.py"), "--json", "review",
                                  "--before", str(self.root / "before"), "--after", str(self.root / "after"),
                                  "--output", str(self.output), "--language", "zh"],
                                 cwd=self.root, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["result"]["content_flags"], 1)
        moved = self.root / "moved"
        self.output.rename(moved)
        self.assertEqual(verify_review(moved)["status"], "verified")
        (moved / "review.json").write_text("changed", encoding="utf-8")
        self.assertEqual(verify_review(moved)["status"], "failed")
