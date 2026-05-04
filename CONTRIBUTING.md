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

## PR Checklist

- Follow the existing table/format in the reference file
- One entry per line, brief descriptions
- Run `bash tests/run_tests.sh` — all must pass
- If unsure, open an issue first

## Code of Conduct

Be respectful and constructive. Report issues to zhenxinlin290@gmail.com.