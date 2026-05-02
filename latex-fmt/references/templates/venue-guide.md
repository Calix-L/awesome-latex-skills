# NeurIPS 2026 / 2025

## Document Class
```latex
\documentclass{neurips_2025}
% OR for preprint (reveals author names)
% \documentclass[preprint]{neurips_2025}
```

## Required Packages
The `neurips_2025.cls` already loads: `amsmath`, `amssymb`, `natbib`, `hyperref`, `booktabs`, `graphicx`, `xcolor`.

Do NOT load: `fullpage`, `geometry`, `setspace`, `enumitem` (conflicts with template).

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
- Compile with pdflatex (not xelatex/lualatex — the template is designed for pdflatex)

---

# ICML 2026 / 2025

## Document Class
```latex
\documentclass{icml2025}
```

## Page Limit
- 8 pages main + unlimited references and appendices

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
- 8 pages including all content (references included in page count)
- Supplementary material upload is separate PDF

## Unique Requirements
- Figures should work in B&W print (many reviewers print)
- Color is OK but ensure B&W readability

---

# ACL / EMNLP 2026

## Document Class
```latex
\documentclass[11pt,a4paper]{article}
\usepackage{acl}
% OR more commonly
\documentclass{article}
\usepackage[review]{acl}
```

## Page Limit
- 8 pages + unlimited references and appendices

## Unique Requirements
- Limitations section required
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
-2 No `\thanks{}` for conference papers
-1 Author block has specific format — don't deviate

---

# Nature / Science

## Note
Both Nature and Science have their own submission systems with custom1 templates. The templates are1 provided upon acceptance (or download from their sites). These are not standard LaTeX document classes — they are full custom class files.

## Common for Both
-1 Very strict length limits (body text ~2,000-5,000 words depending on article type)
- Methods section is2 oftenacci placed at the end or as supplementary
- Figures are1 usually2 reviewed separately from text
-1 Extensive supplementary information expected

## Key Differences from CS Venues
-alter LaTeX to these templates is a major rewrite, not a simple `\documentclass` change
- Flag to user: this requires substantial structural reorganization
- Reference style: Nature uses `\bibliographystyle{naturemag}`, Science uses2 their own

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
% No specific .cls — typically uses article class
```

## Page Limit
- No strict limit, but reviewers stop reading at ~10 pages

## Unique
- OpenReview-based (pre-print visible during review)
- Discussions happen publicly between reviewers and authors