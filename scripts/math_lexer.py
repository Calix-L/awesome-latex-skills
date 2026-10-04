"""Literal, located math-environment spans; no TeX expansion or grammar validation."""
from bisect import bisect_right
from collections import Counter
import re

from tex_lexer import TOKEN, mask_tex

MATH_ENVIRONMENTS = frozenset({"math", "displaymath", "equation", "equation*",
                             "eqnarray", "eqnarray*", "align", "align*", "alignat", "alignat*",
                             "flalign", "flalign*", "gather", "gather*", "multline", "multline*"})
ENVIRONMENT = re.compile(r"\s*\{([^{}\\\r\n]+)\}")


def scan_math_environments(text):
    """Capture complete outer supported environments, including their nested bodies.

    Comments/known verbatim are masked with offsets intact. Nested environments
    must balance literally. Malformed spans supply diagnostics, never complete
    formula values; repeated/moved complete formulas retain their multiplicity.
    Iterative stacks and name counts avoid recursion and repeated stack searches.
    """
    masked = mask_tex(text)
    newlines = [match.start() for match in re.finditer("\n", masked)]
    spans, issues, stack, counts = [], [], [], Counter()
    outer, valid = None, True

    def line(position):
        return bisect_right(newlines, position) + 1

    def issue(code, position, message):
        issues.append({"code": code, "line": line(position), "message": message})

    for token in TOKEN.finditer(masked):
        if token.group() not in {r"\begin", r"\end"}:
            continue
        argument = ENVIRONMENT.match(masked, token.end())
        if argument is None:
            if outer is not None:
                issue("math-environment-dynamic", token.start(), "Nonliteral environment name inside a math span")
                valid = False
            continue
        name = argument[1]
        opening = token.group() == r"\begin"
        if outer is None:
            if name not in MATH_ENVIRONMENTS:
                continue
            if not opening:
                issue("math-environment-unexpected-end", token.start(), f"No literal math opener for {name}")
                continue
            outer = (name, token.start(), argument.end())
            valid = True
        if opening:
            stack.append((name, token.start()))
            counts[name] += 1
            continue
        if not stack or stack[-1][0] != name:
            expected = stack[-1][0] if stack else outer[0]
            issue("math-environment-mismatch", token.start(), f"Math environment closes {name}, expected {expected}")
            valid = False
            if not counts[name]:
                continue
            while stack and stack[-1][0] != name:
                counts[stack.pop()[0]] -= 1
        counts[stack.pop()[0]] -= 1
        if not stack:
            if valid:
                spans.append({"environment": outer[0], "line": line(outer[1]),
                              "end_line": line(token.start()),
                              "content": masked[outer[2]:token.start()]})
            outer = None
            counts.clear()
    if outer is not None:
        # One located issue per unfinished outer span keeps deep invalid inputs bounded.
        issue("math-environment-unclosed", outer[1],
              f"Unclosed literal math environment {outer[0]}; open inner environment: {stack[-1][0]}")
    return spans, issues
