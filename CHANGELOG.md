# Changelog

All notable changes to awesome-latex-skills.

## Unreleased

### Added
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
