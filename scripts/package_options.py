"""Bounded literal package/class loader arguments and biblatex backend options."""
from tex_arguments import read_group
from tex_lexer import TOKEN

LOADERS = frozenset('documentclass LoadClass LoadClassWithOptions usepackage RequirePackage RequirePackageWithOptions'.split())


def loader_arguments(text, start, name):
    cursor = start
    options = ''
    def spaces():
        nonlocal cursor
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
    try:
        spaces()
        if text[cursor:cursor + 1] == '[':
            if name.endswith('WithOptions'):
                raise ValueError('Forwarding loaders do not take a direct option list before the name')
            opening = cursor
            _, cursor = read_group(text, cursor)
            options = text[opening:cursor]
            spaces()
        if text[cursor:cursor + 1] != '{':
            raise ValueError('Loader needs one optional option list and a literal braced name list')
        value, cursor = read_group(text, cursor)
        if not value.strip() or any(char in value for char in '\\#{}') or any(not name.strip() for name in value.split(',')):
            raise ValueError('Dynamic, nested or empty class/package names are unverified')
        if name in {'documentclass', 'LoadClass', 'LoadClassWithOptions'} and ',' in value:
            raise ValueError('Class loaders need one literal name, not a package name list')
        # The kernel accepts an optional minimum release date after the name.
        spaces()
        if text[cursor:cursor + 1] == '[':
            _, cursor = read_group(text, cursor)
        return value.strip(), options, cursor, None
    except ValueError as exc:
        return '', options, cursor, str(exc)


def backend_options(options):
    """Return all exact backend assignments and issues; do not choose an override."""
    if not options:
        return [], []
    body, end = read_group(options, 0)
    if end != len(options):
        raise ValueError('Expected one complete package option list')
    cursor = opening = 0
    pieces = []
    while cursor < len(body):
        if body[cursor] == '{':
            _, cursor = read_group(body, cursor)
            continue
        if body[cursor] == '\\':
            token = TOKEN.match(body, cursor)
            cursor += len(token[0]) if token else 1
            continue
        if body[cursor] == ',':
            pieces.append(body[opening:cursor].strip())
            opening = cursor + 1
        cursor += 1
    pieces.append(body[opening:].strip())
    values, issues = [], []
    for piece in pieces:
        key, separator, value = piece.partition('=')
        key = key.strip()
        if any(char in key for char in '\\#{}'):
            issues.append('Dynamic option names may hide a backend assignment')
            continue
        if key != 'backend':
            continue
        value = value.strip()
        if value.startswith('{'):
            value_body, end = read_group(value, 0)
            if end == len(value):
                value = value_body.strip()
        values.append(value)
        if not separator or value not in {'biber', 'bibtex'}:
            issues.append('Backend value is dynamic, invalid or outside the supported biber/bibtex build tools: ' + value)
    if len(set(values)) > 1:
        issues.append('Conflicting backend assignments; option precedence is not evaluated')
    return values, issues


def declaration(command, filename, name):
    row = {'file': filename, 'line': command['line'], 'command': command['name'],
           'name': name, 'options': command['options']}
    issues = []
    if name == 'biblatex' and command['name'] in {'usepackage', 'RequirePackage', 'RequirePackageWithOptions'}:
        values, issues = backend_options(command['options'])
        row.update(backend_options=values, backend_options_complete=not issues)
    return row, issues
