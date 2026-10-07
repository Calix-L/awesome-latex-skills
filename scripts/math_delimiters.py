"""Located literal math pairs, with conservative diagnostics; not a TeX interpreter."""
from bisect import bisect_right
import re

from tex_lexer import mask_tex

PAIRS = {"$": "$", "$$": "$$", r"\(": r"\)", r"\[": r"\]"}
TOKEN = re.compile(r"\\(?:[a-zA-Z@]+|[^\r\n])|\$\$?|[{}]")


def scan_math_delimiters(text):
    """Retain complete exact pairs and their multiplicity under ordinary catcodes.

    Control symbols consume escaped dollars/braces. In inline math a dollar
    closes before a following dollar is considered as another opener. Literal
    brace depth prevents a nested text/macro argument from silently closing an
    outer span. Mixed or nested modes are unverified, not a TeX validity verdict.
    No expansion, macro execution, conditional evaluation or file joining occurs.
    """
    masked = mask_tex(text)
    newlines = [m.start() for m in re.finditer("\n", masked)]
    spans, issues = [], []
    opened, offset, depth, valid = None, 0, 0, True

    def line(position):
        return bisect_right(newlines, position) + 1

    def issue(code, position, message):
        issues.append({"code": code, "line": line(position), "message": message})

    while (match := TOKEN.search(masked, offset)) is not None:
        token, position, offset = match.group(), match.start(), match.end()
        if token in {"{", "}"}:
            depth += 1 if token == "{" else -1
            continue
        if token not in PAIRS and token not in {r"\)", r"\]"}:
            continue
        if opened is None:
            if token in PAIRS:
                opened = (token, position, offset, depth)
                valid = True
            else:
                issue("math-delimiter-unexpected-end", position, f"No literal math opener for {token}")
            continue
        # $x$$y$ contains two inline pairs; the middle $$ is not a display pair.
        if opened[0] == "$" and token == "$$":
            token, offset = "$", position + 1
        expected = PAIRS[opened[0]]
        if depth != opened[3]:
            if valid:
                issue("math-delimiter-group-unverified", position,
                      "Math delimiters cross literal brace depths; nested/group-dependent math needs manual review")
            valid = False
            continue
        if token == expected:
            if valid:
                spans.append({"delimiter": opened[0], "closing": expected,
                              "mode": "inline" if opened[0] in {"$", r"\("} else "display",
                              "line": line(opened[1]), "end_line": line(position),
                              "content": masked[opened[2]:position]})
            opened = None
        else:
            if valid:
                issue("math-delimiter-mismatch", position,
                      f"Literal math uses {token}, expected {expected}; mixed/nested modes are unverified")
            valid = False
            if token in {r"\)", r"\]"}:
                opened = None
    if opened is not None:
        issue("math-delimiter-unclosed", opened[1],
              f"Unclosed literal math delimiter {opened[0]}; expected {PAIRS[opened[0]]}")
    return spans, issues
