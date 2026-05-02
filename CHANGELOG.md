# Changelog

## 1.1.0 (2026-05-03)

### New Skill
- **pdf2tex**: Convert PDF documents back into editable LaTeX source. pymupdf-based extraction, intelligent structure detection, math/table reconstruction.

### Visual Improvements
- 7 terminal-style PNG demo images for all 5 skills
- Mermaid architecture and workflow diagrams in README
- Before/after diff blocks for each skill
- Python asset generation script (regeneratable)

### Infrastructure
- GitHub Actions CI workflow (tests on push/PR)
- Issue templates (bug report, feature request, new pattern)
- PR template with submission checklist
- CODE_OF_CONDUCT.md, SECURITY.md
- Test suite extended: 38 tests covering all 5 skills

---

## 1.0.0 (2026-05-02)

### Skills
- **latex-rescue**: Diagnose and fix LaTeX compilation errors. 50+ error patterns, 13 categories, engine auto-detection, quick-entry mode.
- **latex-polish**: Improve academic writing style. Light/moderate/strict modes, 7-section-aware strategies, 16 Chinese author pattern categories.
- **latex-fmt**: Reformat papers for 9+ major CS venues (NeurIPS, ICML, CVPR, ACL, AAAI, ICLR, ECCV, TMLR, IEEE, Nature, Science).
- **paper-read**: Read and analyze academic papers. Skim/read/deep levels, critical appraisal framework, cross-paper comparison.

### Infrastructure
- Test suite: 29 tests, automated runner, fixtures for all skills
- Agent configs: Claude Code + OpenAI-compatible per skill
- 14 reference files with curated domain knowledge