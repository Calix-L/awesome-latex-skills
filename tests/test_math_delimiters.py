"""Synthetic controls for located math pairs, ambiguous source and offline evidence."""
from collections import Counter
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from math_delimiters import scan_math_delimiters
from review_project import review, simple_math, content_tokens
from review_report import review_html
from verify_artifacts import verify_review


class DelimiterScannerTests(unittest.TestCase):
    def test_four_pairs_have_locations_modes_and_literal_bodies(self):
        spans, issues = scan_math_delimiters("$a$\n$$b\nc$$\n\\(d\\)\n\\[e\\]")
        self.assertFalse(issues)
        self.assertEqual([(s["delimiter"], s["closing"], s["mode"], s["line"], s["end_line"], s["content"]) for s in spans],
                         [("$", "$", "inline", 1, 1, "a"), ("$$", "$$", "display", 2, 3, "b\nc"),
                          (r"\(", r"\)", "inline", 4, 4, "d"), (r"\[", r"\]", "display", 5, 5, "e")])

    def test_adjacent_inline_pairs_are_separate(self):
        self.assertEqual(list(simple_math("$x$$y$")), [("$", "x"), ("$", "y")])

    def test_inline_then_display_is_context_sensitive(self):
        self.assertEqual(list(simple_math("$x$$$y$$")), [("$", "x"), ("$$", "y")])

    def test_currency_and_escaped_symbols_do_not_open_math(self):
        self.assertEqual(list(simple_math(r"Cost \$5; \$$x$ \\$y$ $a+\$b$")),
                         [("$", "x"), ("$", "y"), ("$", r"a+\$b")])

    def test_comment_and_verbatim_math_is_inactive(self):
        text = "% $bad\n\\verb|\\(bad|\n\\begin{verbatim}$bad\\end{verbatim}\n$x$"
        spans, issues = scan_math_delimiters(text)
        self.assertFalse(issues)
        self.assertEqual([(s["content"], s["line"]) for s in spans], [("x", 4)])

    def test_comment_cannot_close_active_formula(self):
        spans, issues = scan_math_delimiters("$x\n% $\n")
        self.assertFalse(spans)
        self.assertEqual([(i["code"], i["line"]) for i in issues], [("math-delimiter-unclosed", 1)])

    def test_unicode_and_crlf_locations(self):
        spans, _ = scan_math_delimiters("中文\r\n\\[α\r\nβ\\]")
        self.assertEqual((spans[0]["line"], spans[0]["end_line"], spans[0]["content"]), (2, 3, "α\r\nβ"))

    def test_orphan_closer_is_located(self):
        spans, issues = scan_math_delimiters("\n\\) then \\]")
        self.assertFalse(spans)
        self.assertEqual([i["code"] for i in issues], ["math-delimiter-unexpected-end"] * 2)
        self.assertEqual([i["line"] for i in issues], [2, 2])

    def test_mismatched_close_does_not_supply_formula_and_later_pair_recovers(self):
        spans, issues = scan_math_delimiters(r"\(bad\] then \[good\]")
        self.assertEqual([s["content"] for s in spans], ["good"])
        self.assertEqual([i["code"] for i in issues], ["math-delimiter-mismatch"])

    def test_all_unclosed_openers_are_located(self):
        for opener in ("$", "$$", r"\(", r"\["):
            with self.subTest(opener=opener):
                spans, issues = scan_math_delimiters("\n" + opener + "x+y")
                self.assertFalse(spans)
                self.assertEqual((issues[0]["code"], issues[0]["line"]), ("math-delimiter-unclosed", 2))

    def test_incomplete_display_has_no_complete_value(self):
        spans, issues = scan_math_delimiters("$$x+y$")
        self.assertFalse(spans)
        self.assertEqual([i["code"] for i in issues], ["math-delimiter-mismatch", "math-delimiter-unclosed"])

    def test_balanced_braces_and_escaped_braces_retain_formula(self):
        text = r"$\frac{x}{y}+\{z\}$"
        self.assertEqual(list(simple_math(text)), [("$", r"\frac{x}{y}+\{z\}")])

    def test_group_dependent_math_is_unverified_not_silently_truncated(self):
        spans, issues = scan_math_delimiters(r"$a+\text{$b$}$ then $c$")
        self.assertEqual([s["content"] for s in spans], ["c"])
        self.assertEqual([i["code"] for i in issues], ["math-delimiter-group-unverified"])

    def test_mixed_exact_pair_forms_are_unverified(self):
        spans, issues = scan_math_delimiters(r"\(x$ then \)")
        self.assertFalse(spans)
        self.assertEqual([i["code"] for i in issues], ["math-delimiter-mismatch"])

    def test_many_pairs_and_deep_braces_use_iterative_scan(self):
        text = "$" + "{" * 4000 + "x" + "}" * 4000 + "$" + "$y$" * 8000
        spans, issues = scan_math_delimiters(text)
        self.assertFalse(issues)
        self.assertEqual(len(spans), 8001)
        self.assertEqual(Counter(s["content"] for s in spans)["y"], 8000)


class DelimiterReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="delimited-review-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.before, self.after, self.output = [self.root / name for name in ("before", "after", "review")]
        self.before.mkdir()
        self.after.mkdir()

    def run_review(self, old, new, language="en", filename="main.tex"):
        for folder, text in ((self.before, old), (self.after, new)):
            (folder / filename).write_text(text, encoding="utf-8")
        result = review(self.before, self.after, self.output, language=language)
        return result, json.loads((self.output / "review.json").read_text(encoding="utf-8"))

    def test_operator_edit_has_existing_compatible_signal_and_new_locations(self):
        result, record = self.run_review("\n$x+y$", "\n$x-y$")
        self.assertEqual(result["content_flags"], 1)
        self.assertEqual(set(record["content_audit"][0]), {"file", "requires_review", "simple_math"})
        self.assertEqual(record["math_delimiter_inventory"]["after"][0]["line"], 2)
        self.assertEqual(len(content_tokens("$x$")), 3)
        self.assertEqual(record["schema"], 1)

    def test_unchanged_malformed_sources_are_reported_on_both_sides(self):
        result, record = self.run_review("\n\\(x+y\\]", "\n\\(x+y\\]", language="zh")
        self.assertEqual((result["changed_files"], result["content_flags"], result["source_scan_issues"]), (0, 0, 2))
        self.assertEqual(record["math_delimiter_inventory"], {"before": [], "after": []})
        self.assertEqual({(i["side"], i["file"], i["line"]) for i in record["source_scan_issues"]},
                         {("before", "main.tex", 2), ("after", "main.tex", 2)})

    def test_moving_and_reordering_equal_formulas_only_changes_locations(self):
        _, record = self.run_review("$x$ $y$", "\n$y$\n$x$")
        self.assertFalse(record["content_audit"])
        self.assertEqual([s["line"] for s in record["math_delimiter_inventory"]["after"]], [2, 3])

    def test_duplicate_removal_preserves_multiplicity(self):
        _, record = self.run_review("$x$$x$", "$x$")
        self.assertEqual(record["content_audit"][0]["simple_math"]["removed"], [["('$', 'x')", 1]])

    def test_inventory_covers_added_removed_styles_classes_excludes_bib(self):
        for folder, filename in ((self.before, "removed.tex"), (self.after, "added.tex"),
                                 (self.after, "math.sty"), (self.after, "math.cls"), (self.after, "refs.bib")):
            (folder / filename).write_text("$x$", encoding="utf-8")
        review(self.before, self.after, self.output)
        record = json.loads((self.output / "review.json").read_text(encoding="utf-8"))
        self.assertEqual({s["file"] for s in record["math_delimiter_inventory"]["before"]}, {"removed.tex"})
        self.assertEqual({s["file"] for s in record["math_delimiter_inventory"]["after"]}, {"added.tex", "math.sty", "math.cls"})

    def test_bilingual_html_escaping_and_self_contained_transfer(self):
        _, record = self.run_review("$x<y$", "$x>y & z$", language="zh", filename="a&.tex")
        page = (self.output / "report.html").read_text(encoding="utf-8")
        self.assertIn("带源码位置的定界符公式", page)
        self.assertIn("a&amp;.tex:1", page)
        self.assertIn("x&gt;y &amp; z", page)
        self.assertNotIn("x>y & z", page)
        self.assertIn("Located delimited math", review_html(record, {}, language="en"))
        shutil.rmtree(self.before)
        shutil.rmtree(self.after)
        moved = self.root / "moved"
        self.output.rename(moved)
        self.assertEqual(verify_review(moved)["status"], "verified")

    def test_legacy_reports_without_delimiter_inventory_still_render(self):
        _, record = self.run_review("$x$", "$y$")
        record.pop("math_delimiter_inventory")
        record.pop("math_delimiter_scope")
        page = review_html(record, {})
        self.assertNotIn("Located delimited math", page)
        self.assertIn("Delimited math", page)


if __name__ == "__main__":
    unittest.main()
