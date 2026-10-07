"""Read complete literal dependency arguments without expanding option contents."""
import re
from tex_arguments import read_group

DEPENDENCIES = frozenset('input include includeonly includegraphics graphicspath DeclareGraphicsExtensions bibliography addbibresource bibliographystyle'.split())
MAX_OPTIONS = 32


def dependency_arguments(text, start, name):
    cursor, value, options = start, '', ''
    def spaces():
        nonlocal cursor
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
    def group():
        nonlocal cursor
        try:
            result, cursor = read_group(text, cursor)
            return result
        except ValueError:
            cursor = len(text)  # Later contents of a malformed group are unverified.
            raise
    try:
        starred = text[cursor:cursor + 1] == '*'
        cursor += int(starred)
        spaces()
        limit = 2 if name == 'includegraphics' else 1 if name == 'addbibresource' else 0
        for _ in range(limit):
            if text[cursor:cursor + 1] != '[':
                break
            opening = cursor
            group()
            options += text[opening:cursor]
            spaces()
        if text[cursor:cursor + 1] == '[':
            opening = cursor
            count = limit
            while text[cursor:cursor + 1] == '[':
                count += 1
                if count > MAX_OPTIONS:
                    cursor = len(text)
                    raise ValueError('Dependency optional argument inventory exceeds 32 groups; later contents unverified')
                group()
                spaces()
            options += text[opening:cursor].rstrip()
            if text[cursor:cursor + 1] == '{':
                value = group()
            raise ValueError('Unexpected optional argument for this dependency command')
        if text[cursor:cursor + 1] == '{':
            value = group()
        elif name == 'input':
            if text[cursor:cursor + 1] == '"':
                closing = text.find('"', cursor + 1)
                newline = re.search(r'[\r\n]', text[cursor:])
                if closing < 0 or newline and closing >= cursor + newline.start():
                    cursor += newline.start() if newline else len(text) - cursor
                    raise ValueError('Unclosed quoted input filename on this line')
                value = text[cursor:closing + 1]
                cursor = closing + 1
            else:
                bare = re.match(r'[^\s{}]+', text[cursor:])
                if bare is None:
                    raise ValueError('Input needs a literal filename')
                value = bare[0]
                cursor += len(value)
        else:
            raise ValueError('Dependency needs a literal braced argument')
        value = value.strip()
        if starred and name != 'includegraphics':
            raise ValueError('Starred syntax for this dependency is unverified')
        if any(char in value for char in '\\#'):
            raise ValueError('Dynamic dependency arguments are unverified')
        if name == 'graphicspath':
            position = 0
            while position < len(value):
                if value[position].isspace():
                    position += 1
                    continue
                if value[position] != '{':
                    raise ValueError('Graphics paths need a list of literal braced directories')
                path, position = read_group(value, position)
                if any(char in path for char in '{}'):
                    raise ValueError('Nested graphics path directories are unverified')
        elif any(char in value for char in '{}'):
            raise ValueError('Nested dependency filenames are unverified')
        if not value and name not in {'includeonly', 'graphicspath', 'DeclareGraphicsExtensions'}:
            raise ValueError('Empty dependency filename is unverified')
        if name == 'bibliography' and any(not part.strip() for part in value.split(',')):
            raise ValueError('Bibliography needs nonempty literal database names')
        return value, options, cursor, None
    except ValueError as exc:
        return value, options, cursor, str(exc)


def declaration(command, filename):
    return {'file': filename, 'line': command['line'], 'command': command['name'],
            'value': command['value'], 'options': command['options'],
            'starred': command['starred'],
            'supported': command['supported'], 'issue': command.get('dependency_issue')}
