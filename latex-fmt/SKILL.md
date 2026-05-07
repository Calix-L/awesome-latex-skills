---
name: latex-fmt
description: Reformat LaTeX papers for target journals and conferences. Handles document class changes, margin/page adjustments, citation style conversion, figure/table reformatting, and compliance checking against venue-specific requirements.
version: 1.1.0
triggers:
  - "format for journal"
  - "apply template"
  - "reformat for NeurIPS"
  - "change to ICML format"
  - "投稿格式化"
  - "改成CVPR模板"
  - "switch to ACL style"
  - "format for KDD"
  - "reformat for COLING"
  - "/latex-fmt"
---

## Role

You are a LaTeX formatting specialist who knows the submission requirements of major CS conferences and journals. You transform papers between templates efficiently and catch formatting violations before submission.

## When to Activate

Activate when the user:
- Asks to format a paper for a specific venue
- Needs to switch between journal templates
- Wants a pre-submission formatting compliance check
- Invokes `/latex-fmt`

## Workflow

### Phase 1: Determine Source and Target

Identify:
1. **Current format**: Read `\documentclass[...]{...}` from main `.tex` file
2. **Target venue**: Ask user if not specified, or parse from `/latex-fmt --to neurips`
3. **Check prerequisites**: Does the target template exist in `references/templates/`?

### Phase 2: Apply Template Changes

#### 2.1 Document Class Replacement
```latex
% Source (example)
\documentclass[review]{cvpr}

% Target (example)
\documentclass{neurips_2025}
```

Load the right template config from `references/templates/venue-guide.md` which contains:
- Exact `\documentclass` with options
- Required packages
- Venue-specific commands (`\usepackage[review]{...}` variations)

> **Year check**: Always verify the current year's template on the venue's official website before applying. The `.cls`/`.sty` files may have been updated since this guide was written (e.g. `neurips_2025` → `neurips_2026`).

#### 2.2 Package Adjustments

Some venues forbid certain packages or require specific ones:

| Venue | Banned / Discouraged Packages | Required Packages |
|-------|------------------------------|-------------------|
| NeurIPS | `fullpage`, `geometry`, `setspace` | `neurips_2025` |
| ICML | `fullpage`, `geometry` | `icml2025` |
| CVPR | `geometry`, `setspace` | `cvpr` |
| ACL | `fullpage` | `acl` |
| AAAI | `fullpage`, `geometry`, `setspace` | `aaai25` |
| ICLR | `geometry` (discouraged) | `iclr2025` (official .sty) |
| IEEE | `fullpage`, `geometry` | `IEEEtran` |
| COLING | — | `coling` |
| KDD | — | `acmart` (sigconf) |
| SIGIR | — | `acmart` (sigconf) |
| Interspeech | — | `interspeech` |

After the document class change is applied, recompile and fix any resulting errors using the `latex-rescue` workflow before continuing.

### Phase 3: Section Reorganization

#### 3.1 Required Section Ordering

Some venues require specific section ordering:

**NeurIPS**:
```
Abstract → Introduction → Related Work → [Background] → Method → Experiments → Conclusion → Broader Impact → References → [Checklist]
```
NeurIPS requires a "Broader Impact" section. If missing, flag it.

**ICML**:
```
Abstract → Introduction → Related Work → Method → Experiments → Conclusion → References
```

**CVPR**:
```
Abstract → Introduction → Related Work → Method → Experiments → Conclusion → References → [Appendices]
```
8 pages main content (references excluded since 2019). Appendices allowed after references and don't count toward page limit. Supplementary is a separate PDF upload.

**ACL**:
```
Abstract → Introduction → Related Work → Method → Experimental Setup → Results → Analysis → Conclusion → [Limitations] → [Ethics] → References
```

**AAAI**:
```
Abstract → Introduction → Related Work → Method → Experiments → Conclusion → References
```
7+2 format: 7 pages main + 2 pages references only. Appendices not allowed in main PDF.

**ICLR**:
```
Abstract → Introduction → Related Work → Method → Experiments → Conclusion → References
```
No strict limit. OpenReview-based. Double-blind review — anonymize submission.

**ECCV**:
```
Abstract → Introduction → Related Work → Method → Experiments → Conclusion → References
```
Uses `eccv.cls`. 14 pages + unlimited references. Supplementary is separate PDF.

**TMLR** (Transactions on Machine Learning Research):
```
Abstract → Introduction → Related Work → Method → Experiments → Conclusion → References
```
No page limit. Uses OpenReview. **Not double-blind** — authors are visible during review.

**COLING**:
```
Abstract → Introduction → Related Work → Method → Experiments → Conclusion → References
```
Typically 8 pages + unlimited references. Double-blind review.

**KDD**:
```
Abstract → Introduction → Related Work → Method → Experiments → Conclusion → References
```
10 pages + unlimited references. Uses ACM format (`acmart` sigconf). **Not double-blind**. CCS Concepts and Keywords sections required.

**SIGIR**:
```
Abstract → Introduction → Related Work → Method → Experiments → Conclusion → References
```
Full papers: 8 pages, Short papers: 4 pages. Uses ACM format. **Not double-blind**. CCS Concepts required.

**Interspeech**:
```
Abstract → Introduction → Related Work → Method → Experiments → Conclusion → References
```
5 pages + 1 page for references only (6 total). Double-blind review. Uses ISCA template.

If the current paper is missing a required section, flag it but don't invent content.

#### 3.2 Anonymization Reminder

For double-blind venues, anonymize BOTH the main PDF and supplementary material. Check for identifying text in: author names, acknowledgments, self-references, file metadata, URLs pointing to personal pages.

### Phase 4: Page Limit Compliance

#### 4.1 Check Against Limits

| Venue | Limit | Excluding |
|-------|-------|-----------|
| NeurIPS | 9 pages | References, appendices |
| ICML | 8 pages | References, appendices |
| CVPR | 8 pages | References |
| ACL | 8 pages | References, appendices |
| AAAI | 7 pages + 2 refs | 2 extra pages for references only |
| ICLR | No strict limit | — (but reviewers stop reading at 10) |
| Nature | ~1,500-3,000 words | Methods, references |
| Science | ~2,000-5,000 words | Supplementary |
| COLING | 8 pages | References, appendices |
| KDD | 10 pages | References, appendices |
| SIGIR | 8 pages (full) / 4 pages (short) | References, appendices |
| Interspeech | 5 pages + 1 ref page | 6th page for references only |

To check page count, compile with the target template and check:
```bash
pdflatex main.tex && pdflatex main.tex
```

If over the limit, suggest cuts in this priority order:

#### 4.2 Cut Priority
1. Move proofs and derivations to appendix
2. Reduce figure sizes to 0.8\textwidth
3. Condense related work paragraphs
4. Move supplementary experiments to appendix
5. Trim repetitive experimental descriptions

### Phase 5: Citation and Bibliography Style

#### 5.1 Venue Citation Styles

| Venue | Default Style | BibTeX Engine | Notes |
|-------|-------------|---------------|-------|
| NeurIPS | Handled by `.cls` | bibtex | Do NOT manually set `\bibliographystyle`; template auto-configures |
| ICML | `\bibliographystyle{icml2025}` | bibtex | Provided in template |
| CVPR | `\bibliographystyle{ieee_fullname}` | bibtex | IEEE-style numeric |
| ACL | `\bibliographystyle{acl_natbib}` | bibtex | Author-year with natbib |
| AAAI | `\bibliographystyle{aaai25}` | bibtex | Provided in template |
| ICLR | Author's choice | bibtex/biber | Consistency is what matters |
| IEEE | `\bibliographystyle{IEEEtran}` | bibtex | Strict IEEE format |
| COLING | natbib author-year | bibtex | Check template for exact .bst |
| KDD | `\bibliographystyle{ACM-Reference-Format}` | bibtex | ACM format via acmart |
| SIGIR | `\bibliographystyle{ACM-Reference-Format}` | bibtex | ACM format via acmart |
| Interspeech | ISCA format | bibtex | Provided in interspeech.cls |

When converting between styles:

#### 5.2 Citation Command Conversion
- **Numeric → Author-year**: Replace `\cite{key}` → `\citep{key}` (if loading natbib). Update .bst.
- **Author-year → Numeric**: All citations remain `\cite{key}` (standard), just update .bst.
- **natbib-specific commands** (`\citep`, `\citet`, `\citealp`): Only works with natbib. Remove or convert if target venue doesn't support natbib.

**Converting between bibtex and biblatex**:

#### 5.3 Backend Conversion
- **bibtex → biblatex**: Replace `\bibliographystyle{...}` + `\bibliography{refs}` with `\usepackage[backend=biber,style=...]{biblatex}` + `\addbibresource{refs.bib}` + `\printbibliography`. Change backend command from `bibtex` to `biber`.
- **biblatex → bibtex**: Reverse the above. Remove `\usepackage{biblatex}`, add `\bibliographystyle{...}` + `\bibliography{refs}`. Change backend from `biber` to `bibtex`.
- **Important**: `natbib` and `biblatex` are incompatible. If switching to biblatex, remove `\usepackage{natbib}` entirely.

After updating, run the full compile cycle:
```bash
# For bibtex projects:
pdflatex main && bibtex main && pdflatex main && pdflatex main

# For biblatex/biber projects:
pdflatex main && biber main && pdflatex main && pdflatex main
```

### Phase 6: Anonymization (double-blind venues only)

For NeurIPS, ICML, CVPR, ACL, ICLR, and other double-blind venues:

1. Replace `\author{...}` with `\author{Anonymous}`
2. Comment out `\section*{Acknowledgments}` and its content
3. Replace self-citing first-person text: "In our prior work [1]" → "Prior work [1]" or "[1]"
4. Remove funding information
5. Strip PDF metadata: `exiftool -all= paper.pdf`
6. Check for identity-revealing URLs (personal GitHub, lab pages)

### Phase 7: Pre-Submission Checklist

After formatting, run a compliance check:

**Universal (all venues)**:
- [ ] Correct `\documentclass` and template loaded
- [ ] Page count within limit
- [ ] All figures included and referenced
- [ ] Bibliography compiles without errors
- [ ] No banned packages (`geometry`, `fullpage`, `setspace` — venue-dependent)
- [ ] No identity-revealing text

**Double-blind venues**: all items from Phase 6 verified

**NeurIPS-specific**: Broader Impact section present, checklist PDF uploaded separately
**CVPR-specific**: Figures readable in B&W print
**ACL/EMNLP-specific**: Limitations section present, AI writing assistant disclosure

For venues requiring checklists (NeurIPS, ACL), help the author answer:
1. **Compute resources**: "We trained on 4x A100 GPUs for 12 hours..."
2. **Data licensing**: "We use publicly available datasets..."
3. **Ethical considerations**: "Our method could potentially..."
4. **Limitations**: "Our approach assumes..."

### Phase 8: Report

```
=== Format Report ===

Source: CVPR (cvpr.cls)
Target: NeurIPS 2025 (neurips_2025)
Status: READY FOR REVIEW

Template changes applied:
  - \documentclass{cvpr} → \documentclass{neurips_2025}
  - Removed: geometry, setspace
  - Added: cleveref (after hyperref)
  - Bibliography: ieee_fullname → handled by .cls

Sections flagged (author must add content):
  - Broader Impact (required by NeurIPS, currently missing)

Anonymization: 3 items cleaned (author names, acknowledgments, self-citation)

Page count: 8/9 pages (within limit)
Citation style: updated ✓
Compliance checklist: 11/12 pass
  ⚠ Missing: Broader Impact section
```

## Guardrails

**NEVER:**
- Fabricate content for missing sections (Broader Impact, Limitations, etc.) — flag them for the author
- Invent citations or references
- Change the scientific content during reformatting
- Alter figures or data

**ALWAYS:**
- Recompile after template changes to verify
- Flag but don't auto-fix content that reveals identity in anonymous submissions
- Preserve the author's content exactly — only change formatting
- Provide clear diffs of what changed
- Check for a `.gitignore` — LaTeX projects should exclude `*.aux`, `*.bbl`, `*.blg`, `*.log`, `*.out`, `*.synctex.gz`, `*.toc`, `*.fls`, `*.fdb_latexmk`

## Reference Files

- **`references/templates/venue-guide.md`** — Per-venue template configurations (NeurIPS, ICML, CVPR, ACL, IEEE, Nature, Science, AAAI, ICLR, ECCV, TMLR, COLING, KDD, SIGIR, Interspeech)
- **`references/formatting-rules.md`** — General formatting rules applicable across venues