# Tests

## Run

```bash
bash tests/run_tests.sh
```

## What it checks

| Test | What it validates |
|---|---|
| Error catalog coverage | `error-catalog.md` has entries, covers math mode and environment errors |
| Expected fix consistency | `expected_fixed.tex` exists, similar size to broken, has FLAGGED markers |
| Polish reference completeness | All 4 reference files exist, chinglish patterns cover 10/10 categories |
| Venue template coverage | Venue guide covers all 11 target venues |
| Paper-read coverage | Reference files exist, critical appraisal covers 4 key areas |
| pdf2tex coverage | All 4 reference files exist |
| Agent configs | Each skill has `config.yaml` with slash command trigger |
| SKILL.md triggers | Each SKILL.md has slash command trigger and 5+ triggers |
| SKILL.md structure | Each SKILL.md has Role, When to Activate, Workflow, Guardrails, Reference Files sections, valid frontmatter, and 2+ reference files |
| Chinese pattern coverage | Chinglish reference covers 10/10 major pattern categories |
| Compile test | `broken_paper.tex` produces a `.log` file (requires pdflatex) |

## Fixtures

| File | Purpose |
|---|---|
| `fixtures/errors/broken_paper.tex` | Deliberate errors for latex-rescue |
| `fixtures/errors/expected_fixed.tex` | Target output after rescue |
| `fixtures/polish/chinglish_sample.tex` | Chinglish patterns for latex-polish |
| `fixtures/fmt/pre_neurips.tex` | CVPR paper to convert for latex-fmt |
| `fixtures/read/sample_paper.md` | Sample paper for paper-read analysis |
