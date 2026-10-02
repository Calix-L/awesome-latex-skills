# Formatting Rules

Layout suggestions for ordinary LaTeX documents. Official venue templates and author instructions take precedence; do not impose these suggestions on a compliant submission.

## Fonts

- Follow the official template's font and size; do not substitute fonts or shrink text to meet a limit.
- In documents without a required template, `\usepackage{lmodern}` is an optional font choice.
- For XeLaTeX/LuaLaTeX: `\usepackage{fontspec}`, set a professional font like `\setmainfont{Times New Roman}` for journals requesting Times.

## Margins and Spacing

- Default margin: 1 inch (2.54cm) all around when no template specifies otherwise.
- Do NOT use `\usepackage{geometry}` unless you know the venue allows it (NeurIPS/ICML ban it).
- Do NOT use `\usepackage{setspace}` or `\linespread` to adjust line spacing unless required.
- Venue templates include their own spacing — trust the template.

## Headings

- `\section{}` for top-level, `\subsection{}` for second, `\subsubsection{}` for third.
- Keep heading titles short (< 8 words).
- Title case for conference papers (`Key Results on ImageNet`), sentence case for many journals (`Key results on ImageNet`). Be consistent.
- Don't number sections manually — let LaTeX handle it.

## Figures

- Vector graphics (PDF) preferred over raster (PNG) for plots and diagrams.
- Photos: PNG or JPG at 300 DPI minimum.
- `\includegraphics[width=\textwidth]{fig.pdf}` — use relative width specifications, never absolute cm unless you have a very specific reason.
- Place `\label{}` AFTER `\caption{}` inside figure environment.
- Figure caption goes BELOW the figure.
- Subfigure: use `\usepackage{subcaption}` (modern replacement for subfigure/subfig).

## Tables

- Use `\usepackage{booktabs}` for professional-looking tables:
  ```latex
  \toprule
  Header & Header \\
  \midrule
  Data & Data \\
  \bottomrule
  ```
- No vertical lines in professional tables.
- Table caption goes ABOVE the table.
- Place `\label{}` AFTER `\caption{}`.

## Mathematics

- Use `\begin{equation}` for numbered equations, `\[...\]` for unnumbered.
- Multi-line: `\begin{align}` (numbered per line) or `\begin{align*}` (unnumbered).
- Use `\bm{}` (from `bm` package) for bold math symbols.
- Punctuation within equations: include periods/commas inside math mode (AMS convention).

## Cross-References

- Use `\usepackage{cleveref}` for automatic type-aware references: `\cref{fig:arch}` → "Figure 1"
- Load `cleveref` after `hyperref` (an exception to the "hyperref last" rule; `glossaries[implicit]` is another).
- Label prefix conventions:
  - `fig:` for figures → `\label{fig:architecture}`
  - `tab:` for tables → `\label{tab:results}`
  - `eq:` for equations → `\label{eq:loss}`
  - `sec:` for sections → `\label{sec:method}`
  - `alg:` for algorithms → `\label{alg:training}`
  - `app:` for appendices → `\label{app:derivation}`

## Page Numbers

- Review and camera-ready page numbering follow the official template; anonymity alone does not determine numbering.
- DO NOT manually add or remove page numbers — the template should control this.

## Abstract

- Usually limited to 150-300 words (check venue; many cap at 250).
- Follow the kit's sample for abstract placement. Standard `article` and NeurIPS examples place it after `\maketitle`; other kits can use custom title blocks.
- No citations in abstract (exceptions: papers building directly on one prior work).

## Acknowledgments

- Only in camera-ready version (NOT in anonymous submission).
- Place before references section.
- Keep brief: funders, helpful discussions, specific contributors.

## Appendices

- Place AFTER references.
- Use `\appendix` command to switch numbering to letters (`Appendix A`, `Appendix B`).
- Appendices may contain supplementary experiments, derivations, implementation details.
- Most venues allow unlimited appendices but reviewers are not obligated to read them.

## Common Prohibitions

These are commonly banned by venue templates:
- `\usepackage{geometry}` — banned by NeurIPS, ICML, CVPR, IEEE
- `\vspace{}`, `\vskip`, manual spacing hacks
- `\enlargethispage{}`
- Changing font sizes mid-document
- Fullpage package
- Manual page breaks in submission version
- Color text (use `\textcolor` only for figures, not body text)

## Per-Venue Rules and Pre-Submission Checks

Use [the venue guide](templates/venue-guide.md) to locate official requirements
for the exact year, track, and stage. Package restrictions, required sections,
citation style, and anonymity are not universal.

Source searches can identify candidates for review, but are not compliance tests.
Inspect included `.tex` files and the rendered PDF. Confirm missing references
from the final build log; a grep loop over `\ref` misses custom macros, included
files, and escaped comments. Check actual content-page boundaries, metadata,
supplements, and bibliography using the requested kit.

## Project Structure Conventions

A clean LaTeX project follows this layout:

```
project/
├── main.tex              # documentclass + preamble + \input{} calls
├── sections/
│   ├── intro.tex         # \section{Introduction}
│   ├── related.tex       # \section{Related Work}
│   ├── method.tex        # \section{Method}
│   ├── experiments.tex   # \section{Experiments}
│   └── conclusion.tex    # \section{Conclusion}
├── figures/              # all images
├── tables/               # standalone table files (optional)
├── refs.bib              # bibliography database
└── supplementary.tex     # appendix (if allowed)
```

**Rules**:
- Small documents can remain in one file. Split sections only when it helps maintenance.
- Preserve an existing working project structure rather than reorganizing it for its own sake.
- Use `\input{sections/intro}` not `\include{sections/intro}` ( `\include` forces a page break and cannot be nested)
- Images go in `figures/`, referenced as `\includegraphics{figures/fig1.pdf}`

## Common Template Gotchas

| Template | Common mistake | Fix |
|---|---|---|
| NeurIPS | Adding `\usepackage{geometry}` | Template sets margins — remove it |
| ICML | Using `\cite{}` with author-year style | Use `\citep{}` / `\citet{}` (natbib) |
| CVPR | Treating `cvpr.sty` as a document class | Follow the kit: `article` plus `\usepackage[review]{cvpr}` |
| ACL | Forgetting `\usepackage[review]{acl}` | Required for anonymous submission |
| IEEE | Removing funding/author macros by a blanket rule | Follow the specific conference/journal template |
| AAAI | Using A4 paper | Must be letter: `\documentclass[letterpaper]{article}` |
| Any | Loading both `cite` and `natbib` | Remove `cite` — `natbib` supersedes it |