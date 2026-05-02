# Roadmap

## 1.0 — Current (LaTeX Core)

- [x] `latex-rescue`: Compile, parse errors, classify 10 categories, fix typos/math/brackets/environments
- [x] `latex-rescue`: xelatex/lualatex auto-detection and engine switching
- [x] `latex-rescue`: Quick entry mode (user pastes error message directly)
- [x] `latex-rescue`: Verbatim/lstlisting content protection in guardrails
- [x] `latex-polish`: Light/moderate/strict modes, 7-section-aware polishing
- [x] `latex-polish`: Experimental Setup section guidance
- [x] `latex-polish`: 5 concrete before/after examples embedded in SKILL.md
- [x] `latex-polish`: Full Chinglish catalog (16 categories, 190 lines)
- [x] `latex-fmt`: Venue template switching, page limits, anonymization, compliance checklist
- [x] `latex-fmt`: Complete AAAI and ICLR coverage in all phases
- [x] `latex-fmt`: Venue-by-venue citation style table with conversion rules
- [x] `latex-fmt`: Formatting-rules.md (118 lines, universal LaTeX rules)
- [x] Agent configs: Claude Code + OpenAI-compatible per skill
- [x] Test suite: 29 tests, fixtures for all 3 skills, automated runner
- [x] Error catalog: 85+ patterns across 10+ categories
- [x] Academic phrasebank: 9 sections with curated templates

## 1.1 — Polish & Expand (Next)
- [ ] `latex-fmt`: Add arxiv.org-specific formatting mode
- [ ] `latex-fmt`: Multi-venue diff (show exactly what changes between CVPR → NeurIPS)

## v2.0 — Full Academic Suite

### Paper Reading
- [x] `paper-read`: PDF + arXiv extraction, 3 reading levels (skim/read/deep), structured analysis
- [x] `paper-read`: Claims vs evidence mapping, critical appraisal checklist, cross-paper comparison
- [ ] `lit-map`: Citation graph + research lineage visualization

### Publishing Workflow
- [ ] `review-response`: Parse reviewer comments → generate response letter
- [ ] `cover-letter`: Generate tailored cover letters for journal submissions
- [ ] `checklist-gen`: Auto-populate NeurIPS/ACL submission checklists

### Grants & Career
- [ ] `grant-writing`: Funding proposal (国自然/NSF) structure and critique
- [ ] `academic-cv`: Maintain yaml CV data → render per-style PDF
- [ ] `tenure-packet-prep`: Organize tenure materials

### Collaboration
- [ ] `paper-diff`: Semantic diff for co-author review ("what changed in the Method section?")
- [ ] `author-guide`: Track contributions and generate author statements

## v3.0 — Beyond Academia

- [ ] Multi-language: Full Chinese (中文) academic writing support
- [ ] Integration: CI-ready skill for auto-checking LaTeX on push
- [ ] Web UI: Dashboard for skill configuration and batch processing
- [ ] Community repository: User-contributed error patterns, phrasebank additions

## Reference Count Targets

| Reference File | Current | Target v1.1 | Target v2.0 |
|---|---|---|---|
| error-catalog.md | 85+ patterns | 100+ | 150+ |
| package-conflicts.md | 15 conflicts | 25+ | 40+ |
| chinglish-patterns.md | 16 categories | 20+ | 30+ |
| academic-phrasebank.md | 9 sections | 10 sections | 12 sections |
| venue-guide.md | 9 venues | 12 venues | 20 venues |