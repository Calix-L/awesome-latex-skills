"""Inventory literal .bib entry headers; never expand fields or certify a database."""
from bisect import bisect_right
import re

MAX_ENTRIES = 10_000
MAX_ISSUES = 10_000
TYPE = re.compile(r"\s*([A-Za-z][A-Za-z0-9_-]*)\s*")
KEY = re.compile(r"\s*([^\s,{}]+)\s*,")
ASCII_FOLD = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def scan_bibliography(text, backend=None):
    """Return complete, located headers and uncertain structural regions.

    Braces in BibTeX values balance even after backslashes; quotes inside a
    braced value are literal. A percent sign is not a TeX comment here.
    BibTeX resumes searching for @ immediately after @comment. Without that
    selected backend, balanced comments containing @ remain unverified.
    """
    if backend not in (None, "bibtex", "biber"):
        raise ValueError("Unsupported bibliography backend")
    newlines = [match.start() for match in re.finditer("\n", text)]
    entries, issues = [], []
    def issue(code, offset, message):
        issues.append({"code": code, "line": bisect_right(newlines, offset) + 1, "message": message})
        if len(issues) > MAX_ISSUES:
            raise ValueError(f"Bibliography scan exceeds {MAX_ISSUES} structural issues")
    position = 0
    while (start := text.find("@", position)) != -1:
        header = TYPE.match(text, start + 1)
        if header is None:
            issue("bib-entry-header", start, "Unsupported bibliography marker or entry type")
            position = start + 1
            continue
        entry_type = header[1].lower()
        position = header.end()
        if entry_type == "comment" and backend == "bibtex":
            continue
        if position >= len(text) or text[position] not in "{(":
            issue("bib-entry-header", start, "No supported brace/parenthesis opener after bibliography type")
            continue
        opener = text[position]
        closer = "}" if opener == "{" else ")"
        body_start = position + 1
        depth, quoted = 0, False
        position = body_start
        unexpected = False
        while position < len(text):
            char = text[position]
            if depth:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
            elif char == "{":
                depth = 1
            elif char == '"':
                quoted = not quoted
            elif quoted and char == "}":
                issue("bib-unbalanced-value", start, "Unbalanced brace in quoted bibliography value; remaining headers are not scanned")
                position = len(text)
                break
            elif not quoted and char == closer:
                break
            elif not quoted and char == "}":
                issue("bib-unbalanced-value", start, "Unmatched brace in parenthesis-delimited bibliography entry; remaining headers are not scanned")
                position = len(text)
                break
            elif not quoted and char == "@" and entry_type != "comment":
                unexpected = True
            position += 1
        if position >= len(text):
            issue("bib-unclosed-region", start, "Unclosed bibliography entry/value; remaining headers are not scanned")
            break
        body = text[body_start:position]
        position += 1
        if entry_type == "comment":
            if "@" in body:
                issue("bib-comment-ambiguous", start, "Comment contains @; backend-specific comment handling is not verified without explicit BibTeX selection")
            continue
        if unexpected:
            issue("bib-unexpected-marker", start, "Unquoted top-level @ in bibliography body; field syntax needs native backend review")
        if entry_type in {"string", "preamble"}:
            continue
        key = KEY.match(body)
        # BibTeX permits a brace-delimited entry with no fields or trailing comma.
        empty = re.fullmatch(r"\s*([^\s,{}]+)\s*", body) if opener == "{" else None
        if key is None and empty is None:
            issue("bib-entry-key", start, "No supported literal bibliography key before the field list")
            continue
        entries.append({"key": (key or empty)[1], "type": entry_type,
                        "line": bisect_right(newlines, start) + 1})
        if len(entries) > MAX_ENTRIES:
            raise ValueError(f"Bibliography inventory exceeds {MAX_ENTRIES} entries")
    return entries, issues
