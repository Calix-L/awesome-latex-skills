# Contributing

Contributions should solve a demonstrated problem and preserve scientific meaning. A phrasebank example is a wording option, not evidence for a new claim.

## How to Add

| Type | File | Format |
|---|---|---|
| Error pattern | `latex-rescue/references/error-catalog.md` | Log message → source pattern → fix → auto-fixable? |
| Package conflict | `latex-rescue/references/package-conflicts.md` | Package A + B → what breaks → resolution |
| Command → package mapping | `latex-rescue/references/error-catalog.md` | Command → required package (add to mapping table) |
| Chinglish pattern | `latex-polish/references/chinglish-patterns.md` | Wrong → correct → why |
| Phrasebank entry | `latex-polish/references/academic-phrasebank.md` | Under appropriate section heading |
| Venue template | `latex-fmt/references/templates/venue-guide.md` | documentclass, packages, limits, anonymization |

## Mainline

`main` is the only maintained development branch. Maintainer changes land
directly on `main` after local checks, then require its CI to pass before a
release tag. External contributors can open focused pull requests from their
forks against `main`; temporary contribution branches are not release branches.
Version tags identify the exact tested mainline commit.

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

Use the structured [bug](.github/ISSUE_TEMPLATE/bug_report.yml) and
[quality](.github/ISSUE_TEMPLATE/skill_quality.yml) forms for reproducible
failures. Include source locations and exact agent/model details when known;
never report fixture tests as measured model quality. Official-source changes
must update the [review register](maintenance/README.md) after actual review.

## Code of Conduct

Be respectful and constructive. Report issues to zhenxinlin290@gmail.com.
## Adding executable helpers

Put a helper inside the skill that needs it so selected installations remain
self-contained. State optional dependencies and use paths suitable for Windows,
macOS, and Linux. Do not write generated artifacts into the source bundle.

Test observable behavior with isolated temporary inputs and outputs: preserved
scientific tokens, failed operations, existing user files, page provenance, or
required build results. A test matching an instruction's wording does not
establish agent editing quality. Document any external/manual verification.

For installer changes, test the full batch and both ordinary failure and rollback
failure. Keep install receipts out of source bundles. For reference changes,
validate links/anchors and keep required resources within the skill directory.
