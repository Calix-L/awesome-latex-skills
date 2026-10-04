"""Literal bibliography structure must not confuse value text with definitions."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bib_lexer


class BibliographyLexerTests(unittest.TestCase):
    def keys(self, text, backend=None):
        entries, issues = bib_lexer.scan_bibliography(text, backend)
        self.assertEqual(issues, [])
        return [entry["key"] for entry in entries]

    def test_braces_parentheses_and_mixed_case_types(self):
        text = '@Misc{first,title={Fixture}}\n@BoOk(second,title="Another",year=2026)'
        entries, issues = bib_lexer.scan_bibliography(text)
        self.assertEqual(issues, [])
        self.assertEqual(entries, [{"key": "first", "type": "misc", "line": 1}, {"key": "second", "type": "book", "line": 2}])

    def test_multiline_headers_preserve_crlf_and_unicode_locations(self):
        text = '说明\r\n@\r\narticle\r\n(\r\n supplied-key ,\r\n title={中文}\r\n)'
        entries, issues = bib_lexer.scan_bibliography(text)
        self.assertEqual(issues, [])
        self.assertEqual(entries[0]["line"], 2)
        self.assertEqual(entries[0]["key"], "supplied-key")

    def test_entry_like_markers_in_braced_values_are_not_headers(self):
        self.assertEqual(self.keys('@misc{actual,title={Text @misc{fake,title={nested}}}}'), ["actual"])

    def test_entry_like_markers_in_quoted_values_are_not_headers(self):
        self.assertEqual(self.keys('@misc(actual,title="Example @misc{fake,title={nested}}")'), ["actual"])

    def test_quotes_in_braced_values_and_nested_braces_in_quotes(self):
        self.assertEqual(self.keys('@misc{a,title={He said "hello" (2026)}}\n@misc(b,title="A {nested {brace}} (value)")'), ["a", "b"])

    def test_quoted_parentheses_do_not_end_entries(self):
        self.assertEqual(self.keys('@misc(a,title="Text ) (",note={More ) text})\n@misc{b,title={B}}'), ["a", "b"])

    def test_string_and_preamble_definitions_do_not_supply_entry_keys(self):
        text = '@string{abbr="@misc{string-fake,title={Fake}}"}\n@preamble("@misc{preamble-fake,title={Fake}}")\n@misc(real,title=abbr # { Fixture})'
        self.assertEqual(self.keys(text), ["real"])

    def test_percent_is_literal_in_values_and_not_a_tex_comment_at_top_level(self):
        text = '% @misc{active,title={100% of supplied text}}\n@misc(second,title="50% value")'
        self.assertEqual(self.keys(text, "bibtex"), ["active", "second"])

    def test_simple_balanced_comment_needs_no_backend_assumption(self):
        self.assertEqual(self.keys('@comment{Ordinary {nested} text}\n@misc(real,title={Real})'), ["real"])

    def test_selected_bibtex_comment_resumes_at_the_next_marker(self):
        self.assertEqual(self.keys('@comment{Text @misc{active,title={Fixture}}}\n@misc{after,title={After}}', "bibtex"), ["active", "after"])

    def test_unknown_or_biber_comment_marker_is_explicitly_unverified(self):
        text = '@comment{Text @misc{uncertain,title={Fixture}}}\n@misc{after,title={After}}'
        for backend in (None, "biber"):
            with self.subTest(backend=backend):
                entries, issues = bib_lexer.scan_bibliography(text, backend)
                self.assertEqual([entry["key"] for entry in entries], ["after"])
                self.assertEqual([item["code"] for item in issues], ["bib-comment-ambiguous"])

    def test_undelimited_bibtex_comment_does_not_hide_later_entries(self):
        self.assertEqual(self.keys('@comment Plain text\n@misc{actual,title={Fixture}}', "bibtex"), ["actual"])

    def test_unclosed_braced_value_does_not_rescan_nested_fake_headers(self):
        entries, issues = bib_lexer.scan_bibliography('@misc{broken,title={unfinished\n@misc{nested,title={Fake}}')
        self.assertEqual(entries, [])
        self.assertEqual([item["code"] for item in issues], ["bib-unclosed-region"])

    def test_unclosed_quoted_value_and_mismatched_delimiter_are_located(self):
        for text in ('@misc{broken,title="unfinished', '@misc(broken,title={x}}'):
            with self.subTest(text=text):
                entries, issues = bib_lexer.scan_bibliography('Comment\n' + text)
                self.assertEqual(entries, [])
                self.assertEqual(issues[-1]["code"], "bib-unclosed-region")
                self.assertTrue(all(item["line"] == 2 for item in issues))

    def test_backslashes_do_not_change_brace_balancing(self):
        entries, issues = bib_lexer.scan_bibliography(r'@misc{broken,title={\{ unmatched}}')
        self.assertEqual(entries, [])
        self.assertEqual(issues[-1]["code"], "bib-unclosed-region")

    def test_missing_keys_and_openers_do_not_become_known_entries(self):
        for text in ('@misc{,title={Fixture}}', '@misc no opener', '@{bad}'):
            with self.subTest(text=text):
                entries, issues = bib_lexer.scan_bibliography(text)
                self.assertEqual(entries, [])
                self.assertTrue(issues)

    def test_brace_entry_without_fields_is_a_literal_header(self):
        self.assertEqual(self.keys('@misc{empty}\n@misc{trailing,}'), ["empty", "trailing"])

    def test_top_level_marker_in_body_is_unverified_and_not_a_definition(self):
        entries, issues = bib_lexer.scan_bibliography('@misc{real,title=@misc{fake,title={Nested}}}')
        self.assertEqual([entry["key"] for entry in entries], ["real"])
        self.assertEqual([item["code"] for item in issues], ["bib-unexpected-marker"])

    def test_deep_values_use_no_python_recursion(self):
        self.assertEqual(self.keys('@misc{deep,title=' + '{' * 2500 + 'Text' + '}' * 2500 + '}'), ["deep"])

    def test_large_database_retains_exact_last_location(self):
        text = '\n'.join('@misc{k' + str(number) + ',title={Fixture}}' for number in range(8000))
        entries, issues = bib_lexer.scan_bibliography(text)
        self.assertEqual(issues, [])
        self.assertEqual(len(entries), 8000)
        self.assertEqual(entries[-1], {"key": "k7999", "type": "misc", "line": 8000})

    def test_inventory_bound_and_invalid_backend_are_refused(self):
        with patch.object(bib_lexer, "MAX_ENTRIES", 1):
            with self.assertRaisesRegex(ValueError, "inventory exceeds"):
                bib_lexer.scan_bibliography('@misc{a,}\n@misc{b,}')
        with self.assertRaises(ValueError):
            bib_lexer.scan_bibliography('', 'unsupported')
        with patch.object(bib_lexer, "MAX_ISSUES", 1):
            with self.assertRaisesRegex(ValueError, "structural issues"):
                bib_lexer.scan_bibliography('@@@')
