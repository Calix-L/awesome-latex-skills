# Changelog

All notable changes to awesome-latex-skills.

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
