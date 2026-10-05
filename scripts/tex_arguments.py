"""Bounded iterative literal TeX argument reader; no expansion or execution."""
from tex_lexer import TOKEN

MAX_DEPTH = 128


def read_group(text, start):
    """Read one delimited argument; braces protect optional terminators."""
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
                raise ValueError("Literal argument nesting exceeds 128 braces")
        elif char == "}":
            depth -= 1
            if depth < 0:
                raise ValueError("Literal optional argument has an unmatched closing brace")
            if opening == "{" and depth == 0:
                return text[start + 1:cursor], cursor + 1
        elif char == closing and depth == 0:
            return text[start + 1:cursor], cursor + 1
        cursor += 1
    raise ValueError("Unclosed literal argument or note")
