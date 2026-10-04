"""Offset-preserving literal TeX scanning under ordinary category codes.

This does not expand macros or evaluate conditionals/category-code changes.
"""
from bisect import bisect_right
import re

TOKEN = re.compile(r"%|\\(?:[a-zA-Z@]+|[^\r\n])")
ENVIRONMENT = re.compile(r"\s*\{(verbatim\*?|lstlisting|minted)\}")
LINE_BREAK = re.compile(r"[\r\n]")


def lex_tex(text):
    """Return masked source and located issues for unfinished literal regions."""
    pieces, issues = [], []
    offset = 0
    newlines = [match.start() for match in re.finditer("\n", text)]

    def hide(start, end):
        # Retain both characters of CRLF as well as exact source offsets.
        return re.sub(r"[^\r\n]", " ", text[start:end])

    def issue(code, position, message):
        issues.append({"code": code, "line": bisect_right(newlines, position) + 1,
                       "message": message})

    while (match := TOKEN.search(text, offset)) is not None:
        start, end, token = match.start(), match.end(), match.group()
        pieces.append(text[offset:start])
        if token == "%":
            newline = LINE_BREAK.search(text, end)
            end = newline.start() if newline else len(text)
            pieces.append(hide(start, end))
        elif token == r"\\":
            # Consume the control symbol once: its second slash is not a command.
            pieces.append(text[start:end])
        elif token == r"\verb":
            while end < len(text) and text[end] in " \t":
                end += 1
            if end < len(text) and text[end] == "*":
                end += 1
                while end < len(text) and text[end] in " \t":
                    end += 1
            newline = LINE_BREAK.search(text, end)
            line_end = newline.start() if newline else len(text)
            closing = text.find(text[end], end + 1, line_end) if end < line_end else -1
            if closing < 0:
                issue("unterminated-verb", start, "Inline verb has no closing delimiter on this line")
                end = line_end
            else:
                end = closing + 1
            pieces.append(hide(start, end))
        elif token == r"\begin" and (environment := ENVIRONMENT.match(text, end)):
            name = environment[1]
            closing = text.find(r"\end{" + name + "}", environment.end())
            if closing < 0:
                issue("unterminated-verbatim", start, f"No literal end marker for {name}")
                end = len(text)
            else:
                end = closing + len(r"\end{" + name + "}")
            pieces.append(hide(start, end))
        else:
            # Escaped percent/dollar/braces and math delimiters retain their text.
            pieces.append(text[start:end])
        offset = end
    pieces.append(text[offset:])
    return "".join(pieces), issues


def mask_tex(text):
    """Compatibility helper for callers that only need masked source."""
    return lex_tex(text)[0]
