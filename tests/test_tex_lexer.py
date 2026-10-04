"""Literal scanning regressions: examples must not alter real dependencies."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from project_doctor import commands
from review_project import content_tokens
from tex_lexer import lex_tex, mask_tex


class LiteralScannerTests(unittest.TestCase):
    def inputs(self, text):
        return [(item["value"], item["line"]) for item in commands(text) if item["name"] == "input"]

    def test_commented_environment_opener_cannot_hide_live_input(self):
        text = "% \\begin{verbatim}\n\\input{live}\n% \\end{verbatim}\n"
        self.assertEqual(self.inputs(text), [("live", 2)])
        self.assertEqual(lex_tex(text)[1], [])

    def test_commented_verb_opener_cannot_consume_later_content(self):
        text = "% \\verb|example\n\\input{live}|\n"
        self.assertEqual(self.inputs(text), [("live", 2)])
        self.assertEqual(lex_tex(text)[1], [])

    def test_control_symbols_and_backslash_parity_do_not_create_fake_commands(self):
        for count in range(1, 9):
            with self.subTest(backslashes=count):
                text = "\\" * count + "input{target}"
                self.assertEqual(self.inputs(text), [("target", 1)] if count % 2 else [])
        self.assertEqual(self.inputs(r"\\verb|\input{live}|"), [("live", 1)])
        self.assertEqual(self.inputs("\\\\begin{verbatim}\n\\input{live}"), [("live", 2)])
        dynamic = list(commands(r"\input{prefix\\suffix}"))
        self.assertEqual(dynamic[0]["value"], r"prefix\\suffix")

    def test_escaped_percent_is_not_a_comment_but_even_slashes_are(self):
        self.assertEqual(self.inputs(r"\% \input{live}"), [("live", 1)])
        self.assertEqual(self.inputs(r"\\% \input{hidden}"), [])
        self.assertEqual(self.inputs(r"\\\% \input{live}"), [("live", 1)])

    def test_inline_verb_handles_spaces_star_percent_and_digit_delimiters(self):
        for literal in (r"\verb|\input{hidden}%99|", r"\verb* 1\input{hidden}%991", r"\verb *\input{hidden}%99*",
                        r"\verb  a\input{hidden}%99a", r"\verb%\input{hidden}99%"):
            with self.subTest(literal=literal):
                text = literal + r"\input{live}"
                self.assertEqual(self.inputs(text), [("live", 1)])
                self.assertEqual(content_tokens(text)[0], {})
                self.assertEqual(lex_tex(text)[1], [])
        self.assertEqual(lex_tex(r"\verb * 1\input{hidden}1")[1][0]["code"], "unterminated-verb")

    def test_inline_verb_does_not_consume_the_next_line_after_missing_delimiter(self):
        text = "\\verb|\\input{hidden}\n\\input{live}\n"
        self.assertEqual(self.inputs(text), [("live", 2)])
        self.assertEqual(lex_tex(text)[1][0]["code"], "unterminated-verb")
        self.assertEqual(lex_tex(text)[1][0]["line"], 1)

    def test_missing_delimiter_at_eof_and_after_star_are_located(self):
        for text in ("\\verb", "\\verb*  ", "\\verb\r\n\\input{live}"):
            with self.subTest(text=text):
                self.assertEqual(lex_tex(text)[1][0]["code"], "unterminated-verb")

    def test_literal_environment_masks_comments_nested_examples_and_numbers(self):
        for name in ("verbatim", "verbatim*", "lstlisting", "minted"):
            text = ("\\begin {" + name + "}\n% \\verb|\n\\input{hidden} 42 $x^7$\n"
                    "\\end{" + name + "}\n\\input{live}")
            with self.subTest(environment=name):
                self.assertEqual(self.inputs(text), [("live", 5)])
                self.assertEqual(content_tokens(text)[0], {})
                self.assertEqual(lex_tex(text)[1], [])

    def test_unclosed_environment_is_masked_and_explicitly_unverified(self):
        text = "\\input{live}\n\\begin{minted}{tex}\n\\input{hidden} 99"
        self.assertEqual(self.inputs(text), [("live", 1)])
        self.assertEqual(lex_tex(text)[1][0]["code"], "unterminated-verbatim")
        self.assertEqual(lex_tex(text)[1][0]["line"], 2)

    def test_offsets_crlf_unicode_math_and_escaped_symbols_are_preserved(self):
        text = "中文\\% \\verb|99|\r\n% example\r\n$42$ \\(x\\) \\input{live}"
        masked = mask_tex(text)
        self.assertEqual(len(masked), len(text))
        for index, char in enumerate(text):
            if char in "\r\n":
                self.assertEqual(masked[index], char)
        self.assertEqual(self.inputs(text), [("live", 3)])
        self.assertEqual(content_tokens(text)[0], {"42": 1})
        self.assertEqual(content_tokens(text)[2], {("$", "42"): 1, (r"\(", "x"): 1})

    def test_many_comments_and_commands_retain_last_location(self):
        text = ("% \\begin{verbatim}\n\\input{live}\n" * 10000)
        found = self.inputs(text)
        self.assertEqual(len(found), 10000)
        self.assertEqual(found[-1], ("live", 20000))
