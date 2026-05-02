# Contributing to awesome-latex-skills

## How Skills Improve

These skills get better with more reference knowledge. The LLM has general LaTeX knowledge, but the reference files encode **specific, high-precision rules** that the LLM can't reliably produce every time. Every new error pattern, package conflict,0 and Chinglish fix you add directly improves the skill's output quality.

## Ways to Contribute

### Add an Error Pattern

Found a LaTeX error not in `latex-rescue/references/error-catalog.md`? Add it with:

1. The exact log error message
2. The source code pattern that triggers it
3. The minimal fix
4. Whether it's auto-fixable

Example:
```markdown
| `Illegal parameter number` | `\newcommand{\foo}[1]{#2}` | Change `#2` to `#1` (wrong param ref) |
```

### Add a Package Conflict

Found two packages that don't work together? Add to `latex-rescue/references/package-conflicts.md`:

1. Package A and Package B names
2. What breaks
3. The resolution

### Add a Phrasebank Entry

Good academic sentence templates → `latex-polish/references/academic-phrasebank.md`. Add under the appropriate section heading.

### Add a Chinglish Pattern

Chinese-English writing issues → `latex-polish/references/chinglish-patterns.md`. Include:
- The incorrect pattern (what CN authors write)
- The correct form
- Brief explanation of WHY it's wrong

### Add a Venue Template

New conference/journal formatting rules → `latex-fmt/references/templates/`. Include:
- `\documentclass` and options
- Required/forbidden packages
- Section ordering requirements
- Page limits
- Anonymization rules
- Any venue-specific gotchas

## PR Guidelines

1. Add patterns to the **existing reference files** (don't create a new file unless it's a fundamentally different category)
2. Follow the table format used in the file
3. Keep descriptions brief — one line per entry is ideal
4. If you're unsure whether a pattern is correct, open an issue first

## Testing

See `tests/` directory for test fixtures. After adding new error patterns, verify them against the test files:

```bash
cd tests/fixtures/errors
pdflatex -interaction=nonstopmode -file-line-error broken_paper.tex 2>&1 | tee test_output.log
```