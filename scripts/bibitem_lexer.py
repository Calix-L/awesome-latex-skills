"""Read literal manual bibliography keys without interpreting display labels."""
from tex_arguments import read_group


def bibitem_argument(text, start):
    """Return (key or None, consumed offset, issue); never expand key tokens."""
    cursor = start
    def spaces():
        nonlocal cursor
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
    try:
        spaces()
        if text[cursor:cursor + 1] == "*":
            raise ValueError("Starred bibitem syntax is unverified")
        if text[cursor:cursor + 1] == "[":
            _, cursor = read_group(text, cursor)
            spaces()
        if text[cursor:cursor + 1] != "{":
            raise ValueError("Bibitem needs a literal braced key after its optional display label")
        key, cursor = read_group(text, cursor)
        key = key.strip()
        if not key or any(char in key for char in "\\#{}"):
            raise ValueError("Dynamic, nested or empty bibitem keys are unverified")
        return key, cursor, None
    except ValueError as exc:
        return None, cursor, str(exc)
