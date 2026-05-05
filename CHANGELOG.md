# Changelog

All notable changes to awesome-latex-skills.

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
- **file_patterns** in latex-fmt and paper-read config.yaml (consistency with other skills)
- **Version consistency test** — all SKILL.md versions match
- **Reference path existence test** — all paths mentioned in SKILL.md exist on disk
- **Edge case content test** — verifies Overleaf, preprint, Oxford comma, venue status guidance

### Changed
- All SKILL.md versions bumped from 1.0.0 to 1.1.0
- Fixed cross-reference: latex-rescue environment lookup now points to error-catalog.md (not package-conflicts.md)
- Test suite expanded from 103 to 127 tests

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
