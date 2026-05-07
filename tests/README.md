# Tests

## Run

```bash
bash tests/run_tests.sh
```

## What it checks

| Test | What it validates |
|---|---|
| Error catalog coverage | `error-catalog.md` has entries, covers math mode, environment, encoding, and font errors |
| Expected fix consistency | `expected_fixed.tex` exists, similar size to broken, has FLAGGED markers |
| Polish reference completeness | All 4 reference files exist, chinglish patterns cover 18 categories |
| Polish sample patterns | Chinglish sample fixture contains patterns described in reference |
| Venue template coverage | Venue guide covers all 15 target venues |
| Fmt expected output | `post_neurips.tex` has correct documentclass, removed banned packages, flags Broader Impact, double-blind venue coverage |
| Paper-read coverage | Reference files exist, critical appraisal covers 4 key areas, double compile check |
| pdf2tex coverage | All 4 reference files exist, test fixture present, cross-skill references |
| Agent configs | Each skill has `config.yaml` with slash command trigger, latex-fmt has venue-specific triggers |
| SKILL.md triggers | Each SKILL.md has slash command trigger and 5+ triggers |
| SKILL.md structure | Each SKILL.md has Role, When to Activate, Workflow, Guardrails, Reference Files sections, valid frontmatter, and 2+ reference files |
| Chinese pattern coverage | Chinglish reference covers 10/10 major pattern categories |
| Version consistency | All SKILL.md files have the same version number |
| Reference file paths | All paths mentioned in SKILL.md Reference Files sections exist on disk |
| Edge case content | Overleaf guidance, preprint expectations, Oxford comma, venue status |
| Config consistency | All config.yaml files have file_patterns, slash command triggers, and platforms section |
| Cross-skill references | latex-rescue, pdf2tex cross-reference other skills; latex-polish cross-references latex-rescue |
| Compile test | `broken_paper.tex` produces a `.log` file (requires pdflatex) |

## Fixtures

| File | Purpose |
|---|---|
| `fixtures/errors/broken_paper.tex` | Deliberate errors for latex-rescue |
| `fixtures/errors/expected_fixed.tex` | Target output after rescue |
| `fixtures/polish/chinglish_sample.tex` | Chinglish patterns for latex-polish |
| `fixtures/fmt/pre_neurips.tex` | CVPR paper to convert for latex-fmt |
| `fixtures/fmt/post_neurips.tex` | Expected output after NeurIPS conversion |
| `fixtures/read/sample_paper.md` | Sample paper for paper-read analysis |
| `fixtures/pdf2tex/sample_extraction.md` | Simulated PDF extraction data for pdf2tex |
