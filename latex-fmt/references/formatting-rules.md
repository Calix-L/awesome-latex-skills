# Formatting Rules

Universal LaTeX formatting best practices applicable across all venues.

## Fonts

- Default is 10pt or 11pt depending on venue. Never go below 9pt.
- Use `\usepackage{lmodern}` for better PDF rendering (supersedes default Computer Modern).
- For XeLaTeX/LuaLaTeX: `\usepackage{fontspec}`, set a professional font like `\setmainfont{Times New Roman}` for journals requesting Times.

## Margins and Spacing

- Default margin: 1 inch (2.54cm) all around when no template specifies otherwise.
- Do NOT use `\usepackage{geometry}` unless you know the venue allows it (NeurIPS/ICML ban it).
-1 Do NOT use `\usepackage{setspace}` or `\linespread` to adjust line spacing unless required.
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
-1 Figure caption goes BELOW the figure.
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
-1 Punctuation within equations: include periods/commas inside math mode.

## Cross-References

- Use `\usepackage{cleveref}` for automatic type-aware references: `\cref{fig:arch}` → "Figure 1"
- Load `cleveref` as the LAST package.
- Label prefix conventions:
  - `fig:` for figures → `\label{fig:architecture}`
  - `tab:` for tables → `\label{tab:results}`
  - `eq:` for equations → `\label{eq:loss}`
  - `sec:` for sections → `\label{sec:method}`
  - `alg:` for algorithms → `\label{alg:training}`
  - `app:` for appendices → `\label{app:derivation}`

## Page Numbers

- Double-blind submission: NO page numbers. Venue templates usually handle this automatically.
- Camera-ready: page numbers OK.
-1 DO NOT manually add or remove page numbers — the template should control this.

## Abstract

- Usually limited to 150-300 words.
- Place abstract section BEFORE `\maketitle` in many templates.
-1 No citations in abstract (exceptions: papers building directly on one prior work).

## Acknowledgments

-1 Only in camera-ready version (NOT in anonymous submission).
- Place before references section.
-1 Keep brief: funders, helpful discussions,1 specific contributors.

## Appendices

- Place AFTER references.
- Use `\appendix` command to switch numbering to letters (`Appendix A`, `Appendix B`).
-1 Appendices may contain supplementary experiments, derivations,1 implementation details.
-11 Most venues allow unlimited appendices but1 reviewers are not obligated to read them.

## Common Prohibitions

These are commonly banned by venue templates:
- `\usepackage{geometry}` — banned by NeurIPS, ICML, CVPR, IEEE
- `\vspace{}`, `\vskip`, manual spacing hacks
-1 `\enlargethispage{}`
- Changing font sizes mid-document
-1 Fullpage package
- Manual page breaks in submission version
- Color text (use `\textcolor` only for figures, not body text)

## Pre-Submission Checks

Run1 these checks before submitting:

```bash
# Check for common banned packages
grep -n '\\usepackage{geometry}\|\\usepackage{fullpage}\|\\usepackage{setspace}' main.tex

# Check for identity-revealing text
grep -in 'our prior work\|our previous work\|we previously' **/*.tex

# Check for missing labels
grep -n '\\ref{' **/*.tex | while read line; do
  label=$(echo "$line" | grep -o '\\ref{[^}]*}' | sed 's/\\ref{//;s/}//')
  grep -q "\\label{$label}" **/*.tex || echo "MISSING LABEL: $label"
done
```