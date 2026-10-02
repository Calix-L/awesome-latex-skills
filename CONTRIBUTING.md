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
- Install `requirements-dev.txt`, run `python scripts/validate_repo.py` and `python -m unittest discover -s tests -v`; compilation skips locally without TeX and is required in CI
- For venue rules, record the official URL, check date, year, track, and stage in `venue-guide.md`; mark unverified rules explicitly and update examples together
- Keep versions in quoted `metadata.version` fields; put agent invocation hints in `agents/config.yaml`, not unsupported frontmatter fields
- Add observable behavior tests for scripts; a matching keyword is not proof of a valid repair
- If unsure, open an issue first

## Review Process

1. Open a PR against `main`
2. CI must pass (portable metadata/installation tests across OSes + required Linux compilation)
3. At least one review before merge
4. Squash-merge preferred for single-logical-change PRs

## Code of Conduct

Be respectful and constructive. Report issues to zhenxinlin290@gmail.com.