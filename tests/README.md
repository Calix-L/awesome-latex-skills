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

- **Complete projects and review:** multi-file dependency lookup, ambiguous roots,
  missing assets/local packages, reference keys, explicit engine/backend conflicts,
  reusable configuration, bounded paths, immutable originals, content-change signals,
  escaped offline HTML, author decisions, stale build/PDF rejection and atomic review
  publication. Native CI verifies the complete English/Chinese manuscript and
  retains its original failure, repaired PDFs and review bundle.
- **Literal project inspection:** unbraced/quoted/multiline input, include-only
  exclusions, class/package loader variants, bibliography styles, source-order
  graphics paths and explicit extension priorities, dynamic invalidation, source
  cycles, repeated packages, exact parsed-byte binding and pruned environments.
  Source-order comment/verbatim/control-symbol masking, numeric verb delimiters,
  CRLF/Unicode offsets, unfinished literal regions, bounded reads, full observation
  records on ambiguous selection and restored-configuration races are covered.
  Escaped English/Chinese HTML reports preserve missing/skipped/unverified states,
  blocked exit codes and fresh destinations. Native tests compare the selected
  class/input/graphics files with real TeX recorder inputs and verify that a late
  graphics path cannot repair an earlier missing lookup.
- **Python distributions:** build a wheel/source distribution on every portable
  matrix platform, install in fresh environments outside the checkout, check the
  running interpreter, module/console entry points and bundled resource roundtrip,
  all five skill bundles, and an installed synthetic command-runner pilot with
  an unfilled review template and missing-pair report; then independently rebuild
  the source distribution and repeat first-use checks.
  CLI controls verify shared helper grammars, last-value output binding,
  abbreviations/equal forms, literal option-like filenames, project overrides,
  preflight-only help/errors and recorded execution attempts. Real PDF extraction
  and native source/configured builds verify the actual evidence directories.
- **Repeated-trial accounting:** 60-task blind preparation, deterministic randomized
  scheduling, all missing/failed runs, reused-session refusal, raw-transcript binding,
  finite actual measurement fields, unchanged criteria and null missing human/cost
  data. Selected-case pilots, command stdin/cwd, non-UTF-8 transcript bytes,
  failed/startup/timeout outcomes, active locks, submission/record/transcript
  tampering, blank-review refusal and independent build-tool errors are covered.
  Unit fixtures are explicitly synthetic and do not count as model responses.

- **Project workflows:** blind baseline/skill preparation, protected literals and negative controls, changed-input/context rejection, actual human review excerpts, attribution/session/settings checks, CLI execution from another directory, fresh evidence handling, source review dates, deterministic archives and checksums. Native CI runs all five worked examples and attaches logs, PDFs and previews. These tests validate the tooling; model editing quality requires the separate [evaluation protocol](../docs/evaluation.md).

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
  Reports identify the running Python, supported PyMuPDF versions, missing modules,
  native/import failures and shadowing module paths; broken required dependencies
  block PDF extraction without blocking reading of supplied text.
- **Reconstruction evidence:** character extraction preserves span/plain text and
  Unicode, including geometry that maps a cropped/rotated page's glyphs to its
  preview pixels. Execute the documented table detector against a real ruled PDF
  and verify trailing zeros, empty-column positions and copied evidence after close.
  Real compilation also checks equivalent versus nested scripts, merged headers,
  literal hyphens/ampersands, blank-cell placement, retained equation tags and
  visible discrepancy/citation notes in the reconstructed PDF.
- **Compilation:** generate figure assets in an isolated temporary directory;
  require the broken fixture to fail; build the corrected fixture twice and check
  exit codes, PDF output, TeX errors, and resolved/unresolved references. Run the
  bundled checker with real pdfLaTeX, XeLaTeX, LuaLaTeX, BibTeX, and Biber, including
  filenames/output paths with spaces, local/nested inputs, root job names, bibliography
  lookup, fontspec, bounded auxiliary settling, and strict unresolved-reference failures.
  Real integration also checks recorder manifests for chapters/styles/graphics,
  missing BibTeX/Biber databases, and compilation from an installed bundle with
  isolated Python and site packages disabled.
  The installed `latex-fmt` layout example is compiled in one/two-column modes
  with all three engines; PDF drawing widths verify the minipage's local width,
  while logs/references/data and page bounds check overflow, resolution and
  retained values. Installed and copied source files remain unchanged by builds.
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

Offline integrity tests verify complete release/review inventories without
extracting or executing archives, and check moved review folders without the
original projects. Negative controls cover changed/missing/extra files,
legacy coverage, malformed checksum/hash/size/path records, archive-source
mismatches despite refreshed outer checksums, traversal/duplicate/link members,
truncated gzip and decompression errors. ZIP directory/member bounds and tar
metadata/expanded offsets are checked before oversized reads. Native full-paper
and fresh installed wheel/sdist workflows also run the verifier; installed
negative controls modify the source diff and require exit 1.

Review negative controls mutate reports/logs/PDFs during copying and inputs or
page previews after rendering; no final review bundle may be published.
Declared missing logs, reserved evidence-path collisions, unreadable successful
input tracking and mismatched parsed bytes are also refused. Real PDF fixtures
check every retained file's hash/size, legacy PDF identity and offline links.
Source tests cover escaped dollars, display delimiters, literal `nocite`,
Chinese interfaces, uppercase TeX filenames, binary changes and inventory scope.
Fresh installed wheels and rebuilt source packages run Chinese source review
without a PDF dependency; the native release example uses Chinese reports.

| Path | Use |
|---|---|
| `fixtures/errors/broken_paper.tex` | Deliberate syntax errors plus unresolved author decisions |
| `fixtures/errors/expected_fixed.tex` | Compilable candidate retaining data, keys, and uncertainty markers |
| `fixtures/polish/chinglish_sample.tex` | Manual writing evaluation |
| `fixtures/polish/meaning_cases.md` | Manual review of causality, scope, percentages, terminology and LaTeX argument roles |
| `fixtures/fmt/pre_neurips.tex` / `post_neurips.tex` | Historical conversion example; official templates and bibliography not bundled |
| `fixtures/read/sample_paper.md` | Manual reading evaluation |
| `fixtures/pdf2tex/sample_extraction.md` | Manual reconstruction evaluation |
| `fixtures/pdf2tex/reconstruction_edges.tex` | Compiled/extracted notation and table evidence, with visible unresolved content |
| `../latex-fmt/assets/layout-example.tex` | Bundled self-contained layout example compiled after selected installation |

Writing/reading fixtures and historical venue examples need an agent evaluation
and artifact review; their presence alone is not an end-to-end test. The automated
layout example checks ordinary LaTeX behavior, not official submission compliance.
Formatting tasks must use the exact venue/year/track/stage requested by the author.
