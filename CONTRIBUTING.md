# Contributing

Every error pattern, phrasebank entry, and Chinglish fix directly improves output quality.

## How to Add

| Type | File | Format |
|---|---|---|
| Error pattern | `latex-rescue/references/error-catalog.md` | Log message → source pattern → fix → auto-fixable? |
| Package conflict | `latex-rescue/references/package-conflicts.md` | Package A + B → what breaks → resolution |
| Command → package mapping | `latex-rescue/references/error-catalog.md` | Command → required package (add to mapping table) |
| Chinglish pattern | `latex-polish/references/chinglish-patterns.md` | Wrong → correct → why |
| Phrasebank entry | `latex-polish/references/academic-phrasebank.md` | Under appropriate section heading |
| Venue template | `latex-fmt/references/templates/venue-guide.md` | documentclass, packages, limits, anonymization |

## Branch Naming

| Type | Prefix | Example |
|------|--------|---------|
| New feature / content | `feat/` | `feat/add-coling-venue` |
| Bug fix | `fix/` | `fix/chinglish-category-count` |
| Documentation | `docs/` | `docs/contributing-guide` |

## Commit Style

- Use imperative mood: `Add ...`, `Fix ...`, `Remove ...`
- Keep subject line under 72 characters
- One logical change per commit
- Examples:
  - `Add COLING venue template to latex-fmt`
  - `Fix duplicate \usepackge entry in error-catalog`
  - `Add 3 Chinglish patterns for preposition misuse`

## PR Checklist

- Follow the existing table/format in the reference file
- One entry per line, brief descriptions
- Run `bash tests/run_tests.sh` — all must pass
- If adding a new venue, update `venue-guide.md`, `formatting-rules.md` Per-Venue Quick Reference table, and SKILL.md if needed
- If unsure, open an issue first

## Review Process

1. Open a PR against `main`
2. CI must pass (YAML validation + version consistency + test suite)
3. At least one review before merge
4. Squash-merge preferred for single-logical-change PRs

## Code of Conduct

Be respectful and constructive. Report issues to zhenxinlin290@gmail.com.