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
  custom Codex home, invalid paths, CLI failures, and symlink refusal. Managed-update tests cover upstream additions/removals, local edit protection, adoption, receipts, interrupted updates, and recovery-file preservation. Cross-process lock tests verify refusal, retry after release, dry-run behavior, interruption, and replacement-lock preservation.
- **Bundles:** parse YAML; check supported frontmatter, matching names, shared
  versions, agent metadata, and local resource links. Mutation tests confirm
  broken bundles are rejected, including duplicate YAML keys, mixed unsupported keys,
  and unreferenced symlinks that cannot be installed. YAML merge overrides remain supported.
- **Documentation:** check README navigation, local Markdown/HTML image links,
  reference-style links, titled/parenthesized paths, multi-candidate `srcset`,
  formatted/Chinese/duplicate/setext heading anchors, self-contained selected-skill
  resources, nested documentation, UTF-8 failures, and finite positive SVG viewboxes.
  Markdown is parsed with markdown-it-py; code examples are not treated as live links.
  Invalid local paths and form-feed whitespace in HTML `srcset` return diagnostics without crashing.
- **PDF extraction:** generate real PDFs with Unicode, columns, raster/vector graphics, annotations, rotation, transparency masks, blank pages, and encryption; test page coverage, metadata, deduplication, whole-page preview pixels, DPI/size limits, existing outputs, failed rendering/publication, and execution from an installed bundle. Offline HTML checks cover coverage, real evidence links, escaped hostile text/metadata, changed-input refusal, and report failure without partial publication. No OCR service is used.
- **Prerequisites:** distinguish required local dependencies from advisory tools
  and manual checks; verify machine-readable reports and missing-tool exit codes.
- **Compilation:** generate figure assets in an isolated temporary directory;
  require the broken fixture to fail; build the corrected fixture twice and check
  exit codes, PDF output, TeX errors, and resolved/unresolved references. Run the
  bundled checker with real pdfLaTeX, XeLaTeX, LuaLaTeX, BibTeX, and Biber, including
  filenames/output paths with spaces, local/nested inputs, root job names, bibliography
  lookup, fontspec, bounded auxiliary settling, and strict unresolved-reference failures.
  Real integration also checks recorder manifests for chapters/styles/graphics,
  missing BibTeX/Biber databases, and compilation from an installed bundle with
  isolated Python and site packages disabled.
- **Build evidence:** portable tests cover existing/stale outputs, zero/nonzero
  exits with invalid PDFs or error logs, missing tools, explicit backend sequencing,
  launch failure, interruption, per-pass timeout/log retention, and installed-helper
  execution. Tests also verify output basenames, explicit job names, bounded settling,
  strict references, changed-root detection, and source preservation.
  Recorder tests verify local path resolution, spaces, deduplication, generated/external
  exclusions, retained per-pass FLS files, stale recorder removal, changed/missing
  inputs, and failure without reverting edits. Backend diagnostics and CLI failure
  evidence are checked independently of the prior engine log.

Compilation explicitly skips if `pdflatex` is unavailable locally. Set
`LATEX_SKILLS_REQUIRE_TEX=1` to fail when the compiler is missing; CI's Linux compile
job does this and requires all three engines and Biber for its integration cases. Portable checks run on Linux, Windows, and macOS with Python 3.10
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
