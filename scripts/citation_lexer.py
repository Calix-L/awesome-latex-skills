"""Literal citation arguments for common LaTeX, natbib and biblatex commands.

No macro expansion or package execution. Notes are consumed as text, not keys.
"""
import re
from tex_lexer import TOKEN

SINGLE_CITES = frozenset("""
cite Cite citep Citep citet Citet citealt Citealt citealp Citealp citenum
citeauthor Citeauthor citefullauthor citeyear citeyearpar citetalias citepalias
parencite Parencite textcite Textcite autocite Autocite footcite Footcite
footcitetext Footcitetext smartcite Smartcite supercite fullcite footfullcite
citetitle citedate citeurl notecite Notecite pnotecite Pnotecite fnotecite nocite
""".split())
MULTI_CITES = frozenset("""
cites Cites parencites Parencites textcites Textcites autocites Autocites
footcites Footcites footcitetexts Footcitetexts smartcites Smartcites supercites
""".split())
CITATION_NAMES = SINGLE_CITES | MULTI_CITES
FAMILY = re.compile(r"(?:[cC]ite[a-zA-Z]*|(?:[pPfFtTsSaA]?[vV]ol|paren|Paren|text|Text|auto|Auto|foot|Foot|smart|Smart|super|full|footfull|note|Note|pnote|Pnote|fnote)cite[a-zA-Z]*)\Z")
MAX_DEPTH = 128


def citation_candidate(name):
    # citetext wraps prose (possibly containing actual citations), not a key.
    return name != "citetext" and (name in CITATION_NAMES or FAMILY.fullmatch(name) is not None)


def group(text, start):
    """Read one TeX-delimited argument; braces protect note terminators."""
    opening = text[start]
    closing = {"{": "}", "[": "]", "(": ")"}[opening]
    depth = 1 if opening == "{" else 0
    cursor = start + 1
    while cursor < len(text):
        char = text[cursor]
        if char == "\\":
            token = TOKEN.match(text, cursor)
            cursor += len(token[0]) if token else 1
            continue
        if char == "{":
            depth += 1
            if depth > MAX_DEPTH:
                raise ValueError("Citation argument nesting exceeds 128 braces")
        elif char == "}":
            depth -= 1
            if depth < 0:
                raise ValueError("Citation note has an unmatched closing brace")
            if opening == "{" and depth == 0:
                return text[start + 1:cursor], cursor + 1
        elif char == closing and depth == 0:
            return text[start + 1:cursor], cursor + 1
        cursor += 1
    raise ValueError("Unclosed citation argument or note")


def citation_arguments(text, start, name):
    """Return complete literal groups plus any unsupported remainder.

    A malformed later multicite group does not erase earlier complete groups.
    The caller records the issue and never treats the inventory as exhaustive.
    """
    values = []
    cursor = start
    def spaces():
        nonlocal cursor
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
    def notes(delimiter):
        nonlocal cursor
        for _ in range(2):
            spaces()
            if cursor < len(text) and text[cursor] == delimiter:
                _, cursor = group(text, cursor)
            else:
                break
        spaces()
        if cursor < len(text) and text[cursor] == delimiter:
            raise ValueError("More than two citation notes are unsupported")
    try:
        if name in MULTI_CITES:
            notes("(")
        while True:
            notes("[")
            if cursor >= len(text) or text[cursor] != "{":
                raise ValueError("Citation key needs a literal braced argument")
            value, cursor = group(text, cursor)
            if any(char in value for char in "\\#{}") or any(not key.strip() for key in value.split(",")):
                raise ValueError("Dynamic, nested or empty citation keys are unverified")
            values.append(value.strip())
            spaces()
            if name not in MULTI_CITES or cursor >= len(text) or text[cursor] not in "[{":
                break
        return values, cursor, None
    except ValueError as exc:
        return values, cursor, str(exc)
