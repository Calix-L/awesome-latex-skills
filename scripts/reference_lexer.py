"""Literal label targets for core, hyperref/nameref and cleveref commands."""
from tex_arguments import read_group

SINGLE_REFS = frozenset("ref eqref pageref autoref autopageref nameref Nameref namecref nameCref lcnamecref namecrefs nameCrefs lcnamecrefs".split())
LIST_REFS = frozenset("cref Cref cpageref Cpageref labelcref labelcpageref".split())
RANGE_REFS = frozenset("crefrange Crefrange cpagerefrange Cpagerefrange".split())
REFERENCE_NAMES = SINGLE_REFS | LIST_REFS | RANGE_REFS | {"hyperref"}
UNSTARRED_ONLY = {"label", "eqref", "Nameref", "hyperref"}


def reference_arguments(text, start, name):
    """Keep complete targets and an explicit issue for any incomplete remainder."""
    values = []
    cursor = start
    def spaces():
        nonlocal cursor
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
    def argument(delimiter):
        nonlocal cursor
        spaces()
        if cursor >= len(text) or text[cursor] != delimiter:
            raise ValueError("Reference target needs " + ("a bracketed label" if delimiter == "[" else "a literal braced argument"))
        value, cursor = read_group(text, cursor)
        return value.strip()
    try:
        spaces()
        if name == "label" and text[cursor:cursor + 1] == "[":
            argument("[")  # cleveref's explicit type; not interpreted.
        for _ in range(2 if name in RANGE_REFS else 1):
            value = argument("[" if name == "hyperref" else "{")
            keys = [part.strip() for part in value.split(",")] if name in LIST_REFS else [value]
            if any(not key or any(char in key for char in "\\#{}") for key in keys):
                raise ValueError("Dynamic, nested or empty reference keys are unverified")
            values.append(keys)
        if name == "hyperref":
            spaces()
            if cursor >= len(text) or text[cursor] != "{":
                raise ValueError("Hyperref label form needs braced link text")
            read_group(text, cursor)  # Validate closure; leave inner commands visible.
        return values, cursor, None
    except ValueError as exc:
        return values, cursor, str(exc)
