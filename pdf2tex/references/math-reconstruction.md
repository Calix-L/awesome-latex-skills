# Math Reconstruction

Recover the visible notation and grouping before choosing LaTeX commands. A PDF
glyph, font name, or position does not identify the original macro or prove the
author's mathematical intent. Keep unresolved readings visible in the output.

## Collect character evidence

Use the bundled extractor with `--chars --render` on a new output directory.
The resulting `layout.json` retains each span's `text`, font and size and adds
`chars`, whose entries contain `c`, `origin` and `bbox`. Default span extraction
does not provide individual character positions. The helper performs no OCR.

Compare the character sequence with the original page. Missing glyphs, faulty
Unicode maps, ligatures and OCR substitutions can produce plausible but wrong
notation. Keep a record of the page, equation/tag, bounding region, candidate
reading and unresolved alternatives.

Text coordinates use the unrotated PyMuPDF page space, with y increasing down
the page. Page previews reflect the page's crop and rotation. The report includes
`geometry` with boxes and rotation/derotation matrices; use the rotation matrix
before comparing coordinates with a preview, then scale by DPI/72. Do not
subtract the crop-box offset again from already extracted text coordinates.
For nonhorizontal text, inspect the line's `dir`; axis-aligned boxes alone do
not describe the glyph orientation.

API details: [TextPage DICT and RAWDICT](https://pymupdf.readthedocs.io/en/latest/textpage.html)
and [page coordinates and rotation](https://pymupdf.readthedocs.io/en/latest/page.html).

## Choose commands from context

These are candidates, not a reversible Unicode-to-source dictionary. Verify
the result with the chosen math font and the surrounding equation.

| Visible notation | Candidate LaTeX | Check |
|---|---|---|
| α, β, γ, Γ, Δ, Ω | `\alpha`, `\beta`, `\gamma`, `\Gamma`, `\Delta`, `\Omega` | Case and glyph identity |
| ε / ϵ, φ / ϕ | `\epsilon` / `\varepsilon`, `\phi` / `\varphi` | Variant conventions depend on the math setup; match the rendered glyph rather than a fixed code-point rule |
| ≤, ≥, ≠, ≈ | `\leq`, `\geq`, `\neq`, `\approx` | Relation identity; do not substitute approximate equality for equality |
| ∈, ⊂, ⊆ | `\in`, `\subset`, `\subseteq` | Membership versus containment; strict versus non-strict |
| ∥ between related objects | `\parallel` | A relation, with relation spacing |
| Double bars enclosing a norm | `\lVert x\rVert` | Paired delimiters from `amsmath`; do not turn every double bar into a parallel relation |
| ∅ | `\emptyset` or `\varnothing` | Glyph appearance; the latter needs `amssymb` in a conventional pdfLaTeX setup |
| ℝ, ℤ, ℕ | `\mathbb{R}`, `\mathbb{Z}`, `\mathbb{N}` | `amsfonts`/`amssymb`, or an appropriate `unicode-math` setup |
| ∑, ∏, ∫ | `\sum`, `\prod`, `\int` | Limits, operator scope and display style |
| Named operators | `\sin`, `\log`, `\lim`, or `\operatorname{...}` | Upright operator versus an italic product of variables |
| Arrow or accent above a symbol | `\vec{x}`, `\hat{x}`, `\bar{x}` | Which symbols the accent covers |

Declare the packages used by a conventional example, such as `amsmath` and
`amssymb`. Do not copy these assumptions into a supplied official kit without
checking its existing math setup. Unicode math is valid with suitable engines,
fonts and packages; a non-ASCII character is not inherently a TeX error.

## Recover grouping before typesetting

Smaller glyphs above or below a baseline suggest scripts, but also occur in
fractions, limits, accents and adjacent lines. Inspect character origins and
the page together. Font size alone cannot determine the parent expression.

| Source | Meaning or effect |
|---|---|
| `a_i^2` and `a^2_i` | Both attach the same subscript and superscript to `a`; their input order does not change the meaning |
| `a_{i^2}` | The exponent belongs inside the subscript |
| `a_{ij}` | Both `i` and `j` belong in the subscript |
| `a_ij` | Only `i` is subscripted; `j` remains on the baseline |
| `\frac{a+b}{c}` | Both `a` and `b` are in the numerator |
| `a+\frac{b}{c}` | Only `b` is in the numerator |

Brace multi-character scripts and fraction groups explicitly. A horizontal
stroke may be a minus sign, fraction bar, overline, or a table rule; check its
extent and surrounding symbols before generating `\frac` or an accent.
Preserve matrix dimensions, empty entries, delimiters and cases conditions.
Do not replace an ambiguous symbol with a more familiar formula.

## Preserve equation layout and references

Choose `equation` for a single numbered display, `align` for aligned relations,
`gather` for separate centered equations, and `multline` for a long equation
split across lines. Choose the corresponding unnumbered form when the original
has no number. These environments require the appropriate `amsmath` setup.

Recover visible equation numbers and referring text together. A partial PDF
may start with equation (7); automatic numbering from (1) would change the
recovered references. A candidate may use `\tag{7}` with a newly documented
label. Do not claim that the label is the original source key.

For a doubtful glyph, keep its alternatives in a source comment and a visible
note or placeholder. A compiling guess with only a hidden comment is insufficient.

Environment details: [official amsmath user guide](https://www.latex-project.org/help/documentation/amsldoc.pdf).

## Verify the reconstruction

1. Compare each selected equation with the original: glyphs, scripts, groups,
   delimiters, limits, line breaks and tags.
2. Check the notation against nearby definitions without silently correcting
   a possible error in the paper. Report discrepancies separately.
3. Compile with the selected engine and math packages, then inspect the rendered
   equations. Compilation establishes syntax acceptance, not mathematical fidelity.
4. Deliver page/equation locations for every unresolved reading.

Simple counts of dollar signs or braces are not syntax validation: escaped
characters, comments, verbatim text and macros need parsing context. Use the
actual compiler log and a visual comparison.
