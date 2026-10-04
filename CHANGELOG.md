# Changelog

All notable changes to awesome-latex-skills.

## 1.16.0 — 2026-10-05

### Fixed

- Source review now flags operator-only changes in common literal math environments such as `equation` and `align`, even when numbers, citation keys and delimited-math signals are unchanged.

### Added

- Schema-1 original/candidate math-environment inventories retain filenames, opening/closing lines and masked outer bodies. Iterative scanning preserves nested content, star variants and multiplicity; moved/reordered identical spans do not invent formula-content changes. Malformed/dynamic spans supply located issues instead of complete values, including unchanged sources.
- Bilingual offline reports add expandable side-by-side formula inventories and formula-change signals. New English/Chinese recipes and README/documentation navigation explain source-only use, actual build evidence, supported forms and interpretation limits.
- Twenty-seven portable regressions and two native regressions exercise literal boundaries, operator changes, malformed/deep inputs, byte binding, escaped reports, legacy rendering and all supported forms under real amsmath compilation. Fresh original-wheel and rebuilt-sdist first-use checks cover an operator-only change outside the checkout.

The scanner does not expand macros, evaluate conditions/groups, join environments across input files, validate complete TeX grammar, recognize custom outer math environments or establish mathematical equivalence/scientific fidelity. Existing report schemas and delimited-math helper behavior remain compatible.

## 1.15.0 — 2026-10-05

### Added

- `examples export` copies any of five skill cases or the complete English/Chinese manuscript from installed resources using only the standard library. It preserves source/assets/decisions and hidden configuration, includes the MIT license, and generates a standalone bilingual offline HTML/Markdown guide instead of repository-relative README instructions.
- Schema-1 source-copy receipts and complete integrity manifests, with `verify example` checking transferred initial deliveries independently of installation paths. Missing/changed/extra files and source-receipt disagreements fail; changed receipt bytes are not interpreted. Editing remains a separate copy operation.
- Source inventory/byte bounds, parsed-metadata fingerprint binding, staged publication, source rechecks and complete staged verification prevent partial deliveries on normal preparation failures. Export returns `exported-not-run` without calling models, compilers, copied scripts or PDF libraries.
- README editable-case entry, bilingual export recipes and a bilingual documentation index. `examples list` preserves its five existing entries and adds the six exportable case IDs.

### Validation

- Twenty-eight portable regressions cover all case copies, live escaped offline links, resource/source immutability, metadata/source changes, publication failures, staged tampering, bounds, relocation, malformed receipts and corruption.
- A native regression requires expected original failure, successful English/Chinese exported-candidate builds with resolved references, retained Chinese text/values and unchanged initial export integrity.
- Original wheel and independently rebuilt sdist first-use checks export complete/PDF cases without optional libraries, verify source bytes and Chinese guides, and distinguish moved valid deliveries from modified sources outside the checkout.

Cases remain synthetic maintainer demonstrations with answers/decisions, not blind agent tasks or efficacy results. Integrity checks establish initial-byte correspondence, not publisher authenticity or scientific quality. Existing run/build/review report schemas remain unchanged.

## 1.14.0 — 2026-10-05

### Added

- Read-only `doctor --project` reuses project configuration and literal inspection, preserves unresolved engine/backend selection, reports reachable source problems and retains observed-byte evidence. Combined blocked status remains separate from local prerequisite probes; invalid projects return structured errors without writes.
- `doctor --language zh` provides Chinese operator labels and environment actions while retaining original JSON/source/import evidence. Existing environment-only probes keep their default engine and direct helper interface.
- Five bilingual task recipes connect skills, commands, output artifacts and next checks. README entry tables route directly to project diagnosis, source/build review and the complete English/Chinese demonstration.
- A three-case, 12-run pilot documents isolation, real model attribution, concealed review conditions and complete failure reporting. Real-case provenance/acceptance requirements and tested-environment/interface expectations define the next contribution milestones without claiming real-paper or model-quality results.

### Validation

- Seventeen project-doctor regressions cover valid configurations and explicit overrides, missing resources/tools, ambiguous roots, unselected settings, reachable bibliography scope, source immutability, Chinese guidance, help and structured errors.
- Installed original-wheel and rebuilt-sdist checks exercise project configuration evidence, Chinese output, unchanged sources and missing-project errors outside the checkout.

Project diagnosis remains static and does not compile, repair, install or establish semantic fidelity. Preparation of a pilot does not execute a model or fill human scores.

## 1.13.0 — 2026-10-05

### Fixed

- Replace regex-only bibliography key extraction with iterative literal structure scanning. Parenthesis entries are recognized; entry-like text inside nested/quoted fields, string definitions and preambles cannot satisfy citations. Unfinished regions remain explicitly unverified and do not supply incomplete headers.
- Follow selected BibTeX comment scanning without treating percent signs as TeX comments. Other backend/unselected comment bodies containing markers remain unverified. Duplicate comparisons use exact keys, with ASCII-only case folding for selected BibTeX; citation lookup remains exact.

### Added

- Additive `bibliography_entries` inventory retains each key/type/file/header line in resource encounter order. Duplicate keys within/across reachable databases point to the first header; repeated database references are inventoried once. Bilingual offline HTML displays the inventory without interpreting it as full field/backend validation.
- Bilingual bibliography recipes and README navigation, a pinned reviewed primary-source record, and a reusable synthetic database fixture. Fresh wheel and rebuilt-sdist checks exercise header inventory, fake citations, parsed-byte binding and sealed Chinese reports outside the checkout.

### Validation

- Thirty portable regressions cover structure, comments, key collisions, locations, malformed/deep values, escaped HTML and bounded inventories, including an 8,000-entry control. Three native TeX regressions compare literal inventories to real BibTeX/Biber output, require fake references to remain unresolved, and confirm duplicate BibTeX keys fail.

This inventories literal entry headers, not complete bibliography grammar, aliases, inheritance, string expansion, scientific source validity or model quality. Existing report schema numbers and direct helpers remain compatible.

## 1.12.0 — 2026-10-05

### Added

- `project check --bundle NEW_DIRECTORY` stages bilingual offline HTML, JSON and a complete integrity manifest together outside the manuscript tree, rechecks observed source bytes, and publishes the directory only after preparation succeeds. Blocked inspections still export their diagnostics and preserve exit 1.
- Standard-library `verify inspection` checks transferred report directories without original manuscript/export paths. Missing, changed or extra files fail; manifest coverage and kind are validated. Report-byte integrity remains independent of static diagnostics, current-source correspondence and compilation.
- Full-paper runs export and verify both inspection bundles while retaining existing flat report filenames. Fresh wheel and rebuilt-sdist first-use checks verify moved bundles and require corrupted pages to fail.
- Bilingual README workflow tables and project/CLI/verification recipes document complete report sharing and export limits.

### Fixed

- Separate JSON/HTML exports prepare all content before writing, preventing render/serialization failures from leaving an early JSON file. Parent/child destination collisions are refused; separate-file I/O remains non-transactional, with bundles recommended for complete delivery.

### Validation

- Twenty-one portable regressions exercise publication failures, destination conflicts, source changes during rendering/sealing, offline moves, corrupt files and malformed manifests. A native TeX regression distinguishes clean static checks from real build failures while verifying both report inventories.

Publication uses a same-filesystem directory rename; inputs/destinations must remain unchanged during point-in-time checks. No concurrent editor lock, crash-durability, producer authentication or model-quality improvement is claimed.

## 1.11.0 — 2026-10-05

### Fixed

- Build/extraction CLI metadata uses the helpers' shared argument grammar. Repeated output options bind the effective last directory instead of the first; abbreviated/equal-form options and the end-of-options marker agree with execution. Earlier outputs and existing effective evidence are not reused.
- Configured builds normalize source/settings/flags from parsed arguments, honor explicit overrides, retain negative or dash-prefixed values correctly, and refuse ambiguous project/source selection. Help and argument-format errors return before configuration reads or helper execution.

### Added

- Additive schema-1 CLI `invocation` records the attempted interpreter, relative helper, exact arguments and working directory; preflight-only outcomes retain null. Logs and exit codes remain separate evidence of execution outcomes.
- Chinese command guide and bilingual README/CLI recipes for configuration, literal filenames, fresh outputs and machine reports.
- Twelve portable regression tests with real PDF extraction plus a native CLI test for both literal dash-prefixed roots and configured builds. Fresh wheel/rebuilt-sdist checks exercise project-independent help and argument preflight.

Native build/extraction report schemas and standalone helper behavior remain compatible. Successful tooling checks do not establish scientific fidelity or model-quality improvements.

## 1.10.0 — 2026-10-05

### Fixed

- Scan comments, control symbols and supported literal regions in source order. Commented verbatim openers cannot hide live dependencies or numeric/reference changes; escaped backslashes cannot create fake commands. Inline verb supports spaces, stars and numeric delimiters while preserving UTF-8 offsets and CRLF.
- Locate unfinished inline verbs and verbatim environments as unverified diagnostics; review HTML/JSON surfaces incomplete regions on both sides, including unchanged TeX/class/package sources.
- Bind configuration fingerprints to the bytes parsed, bound source/configuration reads even after inventory, and recheck observations on ambiguous-root returns. Additive `observed_files` records all root-selection/configuration/dependency reads separately from reachable `inputs`, with bilingual HTML sections.

### Validation

- Add 20 portable regressions and two native TeX tests comparing literal scan decisions with real recorder inputs and compilation failure. Source line lookup avoids repeated full-prefix counting; a 20,000-line control verifies locations.
- Fresh wheel and rebuilt-sdist checks exercise comment/verbatim/control-symbol handling and complete observation records outside the checkout. Update bilingual README/project/review guides with coverage and limitations.

Static literal scanning still does not evaluate macro expansion, grouping, conditionals, category-code changes or custom verbatim/package escape rules. No model-quality gain is claimed.

## 1.9.0 — 2026-10-05

### Added

- Standard-library offline `verify release` and `verify review` commands with structured findings, honest legacy coverage and preserved exit codes. No extraction, installation, network access or model execution is performed.
- Complete review-bundle integrity manifests covering HTML/JSON/diff and retained log/PDF/page evidence, portable verification without original project paths, and an HTML manifest link.
- Exact release asset/checksum coverage, source/skill ZIP inventories and fingerprints, wheel/sdist resource correspondence, member CRC checks and bounded ZIP/tar parsing. Links, escaping/duplicate/case-colliding entries, encrypted/split/unsupported ZIP metadata and malformed streams are refused.
- Bilingual verification guides, README/CLI/migration examples, native release integrity gates and fresh installed-package positive/negative checks.

Checks prove byte correspondence to stored manifests, not independent producer authentication, scientific fidelity or model-quality gain. Legacy unsealed reviews remain explicitly unverified.

## 1.8.0 — 2026-10-04

### Added

- Bilingual offline manuscript review with counts, file changes (including binary assets), readable added/removed content signals, author decisions, build states, retained artifact links and PDF comparisons. `review --language zh` and `paper --language zh` select Chinese interfaces; source evidence remains unchanged.
- Explicit review inventory coverage and per-build retained-file paths, SHA-256 hashes and byte sizes, including generated page previews. Chinese review guide and fresh installed-package source-review checks.

### Fixed

- Declared missing build evidence is refused rather than silently omitted. Reports/logs/PDFs are verified during retention; inputs and retained evidence are rechecked after rendering, before publication.
- Successful reports with unreadable input tracking and reserved evidence path collisions are refused. Source parsing binds to initially inventoried bytes; UTF-8 BOM and uppercase TeX filenames are handled.
- Review staging and publication use canonical paths, including macOS temporary-directory aliases and equivalent output parents.
- Escaped dollars no longer create false math regions; display-math contents and literal `nocite` keys participate in content signals. Unsupported nested reference arguments are not treated as literal keys.

Consistency checks do not lock concurrent inputs or independently authenticate report producers. Literal signals and successful builds do not establish scientific fidelity.

## 1.7.0 — 2026-10-04

### Added

- Offline English/Chinese project inspection reports with located issues, next steps, selected tools, distinct missing/skipped/unverified dependency states and complete evidence. Full-paper examples and fresh package checks exercise the reports.
- Literal unbraced/quoted/multiline inputs, `includeonly`, local class/package loader variants, local bibliography-style fingerprints and cycle/repeated-source diagnostics.
- Source-order traversal, replacement graphics paths and extension-before-directory lookup, including explicit `DeclareGraphicsExtensions`; unsupported dynamic declarations invalidate older search assumptions.
- Chinese project guide, parsed-byte/configuration fingerprints and native recorder comparisons for class/input/graphics selection.

### Fixed

- Explicit/configured roots do not parse unrelated or excluded source contents. Reports identify root-candidate coverage.
- Generated/build/environment trees are pruned before inventory descent instead of traversing their contents; invalid configured main sources are refused before configuration is created.
- Inspection refuses inputs that change while being parsed rather than attaching a newer hash to older contents.

Static checks still do not emulate TeX macro/group/conditional execution or certify successful builds, scientific fidelity or submission compliance.

## 1.6.0 — 2026-10-04

### Added

- Explicit external-command benchmark runner with unchanged prompt stdin, prepared-task working directory, actual wall time/exit codes, binary-safe combined logs, failure/timeout retention and exclusive task locks. No model provider is selected or called by preparation/reporting.
- Execution evidence binds the attributed run, transcript and every submitted file; later changes are rejected. Retries require fresh tasks.
- Selected-case paired pilots, unfilled human review templates, per-condition measurement/review coverage, token totals and Markdown visibility for every scheduled outcome.
- Chinese evaluation guide and fresh installed wheel/source-package checks for all five skills and the complete synthetic runner/report workflow.

### Fixed

- Independent compilation-tool exceptions no longer discard valid execution and literal score evidence; builds retain an explicit unverified state and error.
- Installed CLI help names the console entry point as well as source invocation.

No model-quality improvement is claimed; process fixtures are synthetic regression controls.

## 1.5.1 — 2026-10-04

### Fixed

- Rejected repeated-session comparisons now reset their quality-review state to unverified, even when both rubric records exist. Scores stay unavailable while underlying reviews and rejection reasons remain retained.
- The session-reuse regression control covers this reviewed-pair case explicitly; its synthetic scores are not model evaluation results.

## 1.5.0 — 2026-10-04

### Added

- Installable Python wheel/source distribution, `als` console command and module entry point, with optional PDF/validation dependencies and resources usable outside the checkout.
- Multi-file project doctor with root selection, dependency/source locations, local classes/styles, graphics, bibliography keys, explicit engine/backend checks and reusable `.als.json` configuration.
- Offline unified source/build/PDF review with content-change signals, retained failure evidence, actual page previews and open author decisions.
- Complete synthetic English/Chinese manuscript with bibliography, appendix, grouped table and figure panels; native CI verifies failure before repair, successful candidates and unchanged sources.
- Repeated-trial blind task preparation and all-run accounting, distinct-session checks, transcript hashes, separate native builds/human review/time/measured cost and explicit missing-data states. No measured model gain is claimed.
- Current-date source-review CI gate, structured installation/quality issue forms, bilingual workflow documentation and release resource binding for wheel/source archives.

### Fixed

- Build reports fingerprint their produced PDF; review rejects mismatched input/PDF evidence and partial publication.
- Fresh package-install verification compares canonical interpreter paths on Windows and rebuilds the source distribution on every supported test platform.
- CI source dates use an explicit UTC+08:00 clock on all platforms.

## 1.4.0 — 2026-10-04

### Added

- Unified project CLI with versioned JSON envelopes, preserved native exit codes and fresh-output evidence handling.
- Ten blind-preparation evaluation tasks across all five skills, input/context fingerprints, attributed paired comparison and evidence-backed human review.
- Five complete synthetic worked examples with native build/extraction verification, source diffs, protected invariants, page previews and downloadable CI evidence.
- Offline primary-source review register with explicit scope, review dates and pending/due states.
- Deterministic source/skill ZIP packaging, per-file SHA-256 manifests, manual release packaging workflow and migration guidance.
- Bilingual README case gallery and an illustrated output overview, with direct paths to real examples and quality documentation.

### Fixed

- Release packaging handles Windows line endings and refuses symlinked source files.
- Project validation checks VERSION alignment and ignores documented generated-output roots.
- README polishing examples retain the original capability qualifier.
- PDF worked-case notes preserve distinct metric labels without assuming that their values contradict; individual release ZIPs retain the MIT license.

## Development leading to 1.4.0

### Added
- Self-contained installed formatting example with real one/two-column, pdfLaTeX/XeLaTeX/LuaLaTeX checks for local panel widths, resolved references, overflow and preserved data.
- Manual polishing cases for retained components/causality, uncertainty, percentage interpretation, distinct terminology and LaTeX argument roles.
- Optional PDF character origins/bounding boxes with preserved span text and page geometry for cropped/rotated preview comparison.
- Detailed dependency reports with running Python, PyMuPDF version/module path, failure reasons and suggested next steps.
- Executable table-reference coverage and a real-compiled reconstruction fixture for scripts, merged headers, blank cells, precision and visible uncertainty.
- Per-pass TeX recorder retention and observed local input SHA-256 manifests, with changed/unreadable input detection and explicit coverage limits.
- Per-step engine/backend diagnostics and direct CLI failure locations in schema-3 build reports.
- Real recorder, missing-database, and isolated installed-helper compilation checks.
- Offline PDF review reports with page/text comparison, selected-page navigation, light/dark responsive styling, source evidence, escaped metadata, and no remote dependencies.
- Input fingerprint checks that refuse PDF evidence publication after concurrent source changes.
- Exclusive installer locks with cross-process conflict checks, revalidated plans, and explicit interrupted-process recovery guidance.
- Optional selected-page PNG previews with source page numbers, rotation/annotations, configurable DPI, and bounded raster size.
- Bounded auxiliary convergence and strict unresolved-reference checks, with root-source change detection and schema-2 build reports.
- Mandatory XeLaTeX/LuaLaTeX fontspec integration checks alongside pdfLaTeX, BibTeX, and Biber.
- Bundled fresh-build checker with selected engine/backend, per-pass logs, timeout and interruption evidence, JSON reports, and stale-PDF protection.
- Real pdfLaTeX/BibTeX/Biber integration cases plus portable build-failure tests and installed-helper coverage.
- Opt-in managed updates with SHA-256 receipts, legacy adoption, local edit protection, interrupted-update rollback, and preserved recovery files.
- Bundled page-aware PDF extraction CLI with selected pages, UTF-8 text, layout evidence, optional deduplicated images, and separate soft masks.
- Real PDF behavior tests and minimum-supported PyMuPDF coverage in the existing cross-platform CI matrix.
- Validation of nested documentation, skill reference anchors, and self-contained selected-skill resources.
- Redesigned bilingual READMEs with an editorial LaTeX wordmark, outlined typography, responsive light/dark covers, a numbered task catalog, and expandable setup/FAQ sections.
- Read-only prerequisite doctor with explicit engine/backend choices and JSON output.
- README link/anchor and SVG validation, plus prerequisite behavior regression tests.
- Standard-library Python installer for Claude Code and Codex, including selected bundles, custom destinations, dry runs, idempotence, and conflict protection.
- Native Codex UI metadata and supported skill frontmatter (`metadata.version`).
- Portable YAML/resource validation and behavioral installer/validator tests.
- CI matrix for Windows, macOS, and Linux plus mandatory TeX fixture compilation.

### Fixed
- Polishing examples preserve multi-head attention, experimental conditions and claim strength instead of deleting components or adding causal connections.
- Section guidance adapts to article/evidence type without compulsory numerical gains, fixed sentence/citation quotas or fabricated disclosures.
- Formatting guidance uses local available widths, actual kit/package/citation conventions and available fonts rather than universal layout, bibliography or section-placement rules.
- Math reconstruction now distinguishes grouping from equivalent script order, relation spacing from norm delimiters, and glyph candidates from original macros.
- Table/structure guidance preserves empty/merged cells, literal markers, source discrepancies, footnotes and unmatched references instead of silently inferring content.
- Broken PyMuPDF imports retain their actual errors rather than being reported as an absent package; unsupported versions and module shadowing are identified.
- The synthetic reconstruction fixture no longer claims an original engine, package or bibliography setup and explicitly preserves its conflicting accuracy values.
- Failed BibTeX/Biber diagnostics now come from the failed backend instead of the preceding TeX pass; recognized errors cannot pass on a zero exit code.
- Root fingerprint failures are detected before output creation, and ordinary failed builds still check whether the root changed.
- Repository validation rejects duplicate YAML keys and uninstallable unreferenced symlinks, preserves YAML merge overrides, and reports malformed local paths or HTML srcset whitespace without crashing.
- Critical appraisal now matches evidence to claim type and reading purpose instead of using arbitrary baseline-age/gain thresholds, universal significance rules, or mandatory accept/reject verdicts.
- Build output names now follow the root document by default; explicit job names and nested include auxiliary directories are supported.
- Engine passes cannot reuse an earlier pass's PDF, and per-step logs use a separate directory to avoid output-basename collisions.
- BibTeX receives output basenames with spaces as a single literal argument; failing real-build tests include transcript excerpts for diagnosis.
- Rescue references now preserve bibliography artifacts, distinguish modern input encoding from font support, avoid guessed conversions and success-rate claims, correct glossary hyperlink load order, and retain official template package choices.
- Polishing examples no longer introduce unsupplied significance or automatically weaken warranted universal claims.
- Documentation checks now parse Markdown links and headings rather than relying on link regexes; reference links, titles, code fences, nested relative paths, HTML srcset, UTF-8 errors, and invalid SVG dimensions are covered.
- Skill instructions now distinguish evidence from inference, preserve modality and claim strength, and avoid reading-time promises and venue-status shortcuts.
- PDF guidance retains spanning blocks, uses current font APIs, and avoids guessing original engines/classes or fixed OCR accuracy.
- Reference repair guidance preserves unknown keys and does not assign arbitrary targets; PR template links and checks work across platforms.
- Corrected fixtures preserve table data, unresolved citation/label keys, and ambiguous math rather than silently deleting or guessing content.
- NeurIPS examples load a style package with `article`; official rules determine impact discussion, checklist location, and review/final length.
- Corrected KDD 2026 research and TMLR anonymity guidance with dated official sources; other venue rules are verified for the requested target before use.
- Rescue diagnostics no longer count only `!` errors, lose engine failures behind `tee`, or disable scientific content to obtain a build.
- Bilingual installation docs explain full-resource access, prerequisites, existing-install conflicts, and verification limits.

## v1.2.0 — 2025-05-07

### Fixed
- CHANGELOG test count corrected from 151 to 162
- latex-fmt SKILL.md now lists ECCV, COLING, and Interspeech as double-blind venues
- latex-polish SKILL.md verification step now runs pdflatex twice for cross-references
- error-catalog Quick-Map table now includes Encoding Errors and Font Errors entries
- Critical appraisal count updated from 43 to 50+ to reflect v1.1.0 additions
- tests/README.md corrected chinglish category count from 10/10 to 18

### Added
- Cross-skill references in latex-rescue SKILL.md (suggests `/latex-polish` and `/latex-fmt` after fixing)
- Cross-skill references in pdf2tex SKILL.md (suggests `/latex-rescue`, `/latex-polish`, `/latex-fmt` after reconstruction)
- Venue-specific triggers in latex-fmt SKILL.md and config.yaml (`format for SIGIR`, `format for Interspeech`)
- Test: error catalog covers encoding and font errors
- Test: latex-polish recommends double compilation for verification
- Test: latex-fmt SKILL.md identifies double-blind venues correctly
- Test: latex-rescue and pdf2tex cross-reference other skills
- Test: latex-fmt config has venue-specific triggers
- Test suite expanded from 162 to 168 tests

## v1.1.0 — 2025-05-05

### Added
- **Overleaf edge case** in latex-rescue — workflow for users without local CLI
- **Preprint/venue expectations** in paper-read — adjust skepticism by publication status (peer-reviewed vs preprint vs workshop vs journal vs tech report)
- **Oxford comma guidance** in latex-polish style-guardrails — with ambiguity example
- **Venue status reading guidance** in reading-framework — detailed per-status reading strategy
- **Reviewer response templates** in academic-phrasebank — acknowledging feedback, addressing concerns, declining changes
- **Dataset/benchmark paper type** in reading-framework
- **18 Greek letter variants** in math-reconstruction (varepsilon, vartheta, varrho, varsigma, etc.)
- **14 operator/symbol mappings** in math-reconstruction (oplus, otimes, dagger, cdots, etc.)
- **6 critical appraisal items** — data verification, ablation isolation, terminology/notation/abstract consistency
- **Broader Impact/Ethics and Acknowledgments** section guidance in section-anatomy and latex-polish SKILL.md
- **12 additional typo patterns** in error-catalog (documnetclass, seciton, biblography, etc.)
- **11 additional environment→package mappings** in error-catalog (split, aligned, bmatrix, theorem, proof, etc.)
- **Common Error Chains** in debug-workflow and error-catalog (5 chains with examples)
- **2 new Chinglish categories** (#17 "Based on" misuse, #18 redundant "the") — now 18 total
- **OCR fallback section** in pdf-extraction-guide with Tesseract code
- **Multi-column detection code** in pdf-extraction-guide
- **Reproducibility Red Flags** quick-check section in critical-appraisal (10 items)
- **Reading for Implementation** strategy in reading-framework
- **Project structure conventions** and **Common Template Gotchas** in formatting-rules
- **.gitignore guidance** in latex-fmt for LaTeX projects
- **file_patterns** in latex-fmt and paper-read config.yaml (consistency with other skills)
- **Version consistency test** — all SKILL.md versions match
- **Reference path existence test** — all paths mentioned in SKILL.md exist on disk
- **Edge case content test** — verifies Overleaf, preprint, Oxford comma, venue status guidance
- **Config consistency test** — all config.yaml have file_patterns, slash triggers, platforms
- **Reference depth test** — error chains, OCR fallback, chinglish category count
- **CHANGELOG.md** — tracking project changes
- **CI version consistency step** in test.yml

### Changed
- All SKILL.md versions bumped from 1.0.0 to 1.1.0
- Fixed cross-reference: latex-rescue environment lookup now points to error-catalog.md (not package-conflicts.md)
- paper-read SKILL.md now cross-references reading-framework's venue status section
- Test suite expanded from 103 to 162 tests

## v1.0.0 — 2025-05-04

### Added
- Initial release with 5 skills: latex-rescue, latex-polish, latex-fmt, paper-read, pdf2tex
- 80+ error patterns in latex-rescue error catalog
- 14 known package conflicts documented
- 16 Chinglish pattern categories
- 100+ phrasebank sentence templates
- 11 venue formatting rules (NeurIPS, ICML, CVPR, ACL, ICLR, ECCV, AAAI, TMLR, IEEE, Nature, Science)
- 40+ critical appraisal checklist items
- 80+ math glyph → LaTeX mappings
- 15 reference files total
- Tokyo Night themed SVG banner
- CI workflow with YAML validation and test suite
- 103 passing tests
