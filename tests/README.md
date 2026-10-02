# Tests

Python 3.10+ is required. From the repository root:

```sh
python -m pip install -r requirements-dev.txt
python scripts/validate_repo.py
python -m unittest discover -s tests -v
```

On systems with Bash, `bash tests/run_tests.sh` runs the same checks.
To run one area: `python -m unittest discover -s tests -p test_install.py -v`.

## What the checks prove

- **Installation:** complete resource roundtrip, selected skills, dry runs,
  repeat installs, existing edits, batch preflight, rollback, paths with spaces,
  custom Codex home, invalid paths, CLI failures, and symlink refusal. Managed-update tests cover upstream additions/removals, local edit protection, adoption, receipts, interrupted updates, and recovery-file preservation.
- **Bundles:** parse YAML; check supported frontmatter, matching names, shared
  versions, agent metadata, and local resource links. Mutation tests confirm
  broken bundles are rejected.
- **Documentation:** check README navigation, local Markdown/HTML image links,
  Chinese and duplicate heading anchors, self-contained selected-skill resources, nested documentation, and well-formed light/dark SVG assets.
- **PDF extraction:** generate real PDFs with Unicode, columns, raster images, transparency masks, blank pages, and encryption; test page coverage, metadata, deduplication, existing outputs, publication failure, and execution from an installed bundle. No OCR service is used.
- **Prerequisites:** distinguish required local dependencies from advisory tools
  and manual checks; verify machine-readable reports and missing-tool exit codes.
- **Compilation:** generate figure assets in an isolated temporary directory;
  require the broken fixture to fail; build the corrected fixture twice and check
  exit codes, PDF output, TeX errors, and resolved/unresolved references.

Compilation explicitly skips if `pdflatex` is unavailable locally. Set
`LATEX_SKILLS_REQUIRE_TEX=1` to fail when the compiler is missing; CI's Linux compile
job does this. Portable checks run on Linux, Windows, and macOS with Python 3.10
and 3.13. Ubuntu/Python 3.10 also checks the minimum supported PyMuPDF 1.24.10; other portable jobs use the resolved current version. No build artifacts are written into the repository.

These checks validate packaging and fixture behavior. They do **not** measure an
AI agent's editing quality or prove compliance with a venue's current rules.

## Fixtures

| Path | Use |
|---|---|
| `fixtures/errors/broken_paper.tex` | Deliberate syntax errors plus unresolved author decisions |
| `fixtures/errors/expected_fixed.tex` | Compilable candidate retaining data, keys, and uncertainty markers |
| `fixtures/polish/chinglish_sample.tex` | Manual writing evaluation |
| `fixtures/fmt/pre_neurips.tex` / `post_neurips.tex` | Historical conversion example; official templates and bibliography not bundled |
| `fixtures/read/sample_paper.md` | Manual reading evaluation |
| `fixtures/pdf2tex/sample_extraction.md` | Manual reconstruction evaluation |

The last four areas need an agent evaluation and artifact review; fixture
presence alone is not an end-to-end test. Formatting examples must use the exact
venue/year/track/stage requested by the author.
