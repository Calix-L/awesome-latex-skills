# NeurIPS 2026 / 2025

> Verify the current year's `.cls` on the official NeurIPS site before starting.

## Document Class
```latex
\documentclass{neurips_2025}
% OR for preprint (reveals author names)
% \documentclass[preprint]{neurips_2025}
```

## Required Packages
The `neurips_2025.cls` already loads: `amsmath`, `amssymb`, `natbib`, `hyperref`, `booktabs`, `graphicx`, `xcolor`.

Do NOT load: `fullpage`, `geometry`, `setspace` (conflicts with template). `enumitem` may cause spacing issues with some template versions — test before using.

## Sections Required
1. Abstract
2. Introduction
3. Related Work
4. Method / Approach
5. Experiments
6. Conclusion
7. Broader Impact (MANDATORY — flag if missing)
8. Acknowledgments (ONLY in camera-ready, NOT in submission)
9. References
10. Checklist (separate file, required)

## Page Limit
- 9 pages main content
- Unlimited references and appendices
- Appendices after references

## Anonymization
- Remove all `\author{}` content (use `\author{Anonymous}` or leave empty)
- Remove acknowledgments section
- Check for self-references: "our prior work [1]" reveals identity
- Remove funding information

## Submission Tips
- Checklist file must be uploaded as separate PDF
- Use PDF figures only (no EPS)
- Compile with pdflatex (strongly recommended; the template is designed for pdflatex). XeLaTeX may work for CJK authors but requires minor adjustments.

---

# ICML 2026 / 2025

> Verify the current year's `.cls` on the official ICML site before starting.

## Document Class
```latex
\documentclass{icml2025}
```

## Required Packages
The `icml2025.sty` provides the official submission format. Do NOT override with custom packages.

## Page Limit
- 8 pages main + unlimited references and appendices

## Anonymization
- Double-blind review: remove all identifying information
- Self-citations must be in third person ("Smith et al. [1] showed..." not "In our prior work [1]...")

## Unique Requirements
- Author contributions must be listed in camera-ready (not during review)
- Code/data release encouraged but not required

---

# CVPR 2026

## Document Class
```latex
\documentclass[review]{cvpr}
% For camera-ready
% \documentclass[final]{cvpr}
```

## Page Limit
- 8 pages main content (references do NOT count toward page limit since CVPR 2019)
- Supplementary material upload is separate PDF

## Unique Requirements
- Figures should work in B&W print (many reviewers print)
- Color is OK but ensure B&W readability

---

# ACL / EMNLP 2026

> ACL and EMNLP use the same template but have different page limits and requirements.

## Document Class
```latex
\documentclass{article}
\usepackage[review]{acl}    % For review/anonymous submission
% \usepackage{acl}           % For camera-ready
```

## Page Limit
- ACL: 8 pages + unlimited references and appendices
- EMNLP: 8 pages + unlimited references and appendices

## Unique Requirements
- **Limitations section required** (ACL mandates it, EMNLP strongly encourages it)
- Ethics/Broader Impact section encouraged
- AI writing assistant disclosure: must state whether LLM was used

---

# IEEE Template (Computer Society / Transactions)

## Document Class
```latex
\documentclass[conference]{IEEEtran}
```

## Page Limit
- Conference: typically 6-8 pages
- Transactions: typically 8-14 pages (check specific journal)

## Unique Requirements
- Specific citation style: `\bibliographystyle{IEEEtran}`
- No `\thanks{}` for conference papers
- Author block has specific format — don't deviate

---

# Nature / Science

## Note
Both Nature and Science have their own submission systems with custom templates. The templates are provided upon acceptance (or download from their sites). These are not standard LaTeX document classes — they are full custom class files.

## Common for Both
- Very strict length limits (body text ~1,500-3,000 words depending on article type; Nature uses word counts, not page limits)
- Methods section is often placed at the end or as supplementary
- Figures are usually reviewed separately from text
- Extensive supplementary information expected

## Key Differences from CS Venues
- Adapting LaTeX to these templates is a major rewrite, not a simple `\documentclass` change
- Flag to user: this requires substantial structural reorganization
- Reference style: Nature uses `\bibliographystyle{naturemag}`, Science uses their own

---

# AAAI 2026

## Document Class
```latex
\documentclass[letterpaper]{article}
\usepackage{aaai25}
```

## Page Limit
- 7 pages + 2 extra pages for references only (9 total with refs)

## Unique
- Must use letter paper (not A4)
- Strictly 2-column format
- Abstract limited to 200 words

---

# ICLR 2026

## Document Class
```latex
\documentclass{article}
\usepackage{iclr2025}   % Official template
```

## Page Limit
- No strict limit, but reviewers stop reading at ~10 pages

## Unique
- OpenReview-based (pre-print visible during review)
- Discussions happen publicly between reviewers and authors
- Double-blind review: anonymize all submissions
- Anonymization of supplementary material also required

---

# ECCV 2026

## Document Class
```latex
\documentclass[review]{eccv}
% For camera-ready
% \documentclass[final]{eccv}
```

## Page Limit
- 14 pages main content + unlimited references
- Supplementary material is a separate PDF upload

## Anonymization
- Double-blind review: remove all identifying information
- Self-citations must be in third person

## Unique
- Figures should work in B&W print (reviewers may print)
- Strong emphasis on reproducibility: code release expected
- Uses `eccv.cls` which sets 2-column format

---

# TMLR

## Document Class
```latex
\documentclass{article}
% TMLR uses standard article class with OpenReview formatting
```

## Page Limit
- No strict page limit
- Typical submissions: 10-20 pages

## Unique
- OpenReview-based (non-anonymous, NOT double-blind)
- Rolling submissions (no deadline)
- Journal-style review process (not conference)
- No supplementary material upload — appendices go in main PDF