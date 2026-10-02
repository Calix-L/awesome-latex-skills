# Table Reconstruction

Recover the cell grid and its contents before choosing a table style. Preserve
numbers, precision, units, empty cells, merged headers and footnotes. A table
that compiles can still place a value under the wrong heading.

## Establish the grid from the page

Record the source page, table number/caption, region, logical rows and columns,
and each merged region. Compare text coordinates with ruling lines and the
rendered original. Grouping blocks solely by equal `x0` or `y0` is insufficient:
numbers may be right aligned, cells can wrap, and headers can span columns.

Use the bundled extractor's `--render` for page evidence. `--chars` can help
inspect small superscripts and footnote markers; neither option segments tables.
Span `color` describes text ink, not the cell's background. Inspect the preview
or drawing objects for shading and rules.

`Page.find_tables()` can suggest candidates. A line-based strategy helps ruled
tables; a text-based strategy can help borderless tables but may detect ordinary
paragraphs as cells. Review the header, grid and values for every candidate.
The helper does not run this detector automatically.

```python
import pymupdf

with pymupdf.open("paper.pdf") as doc:
    page = doc[0]
    finder = page.find_tables(strategy="lines")
    candidates = []
    for table in finder.tables:
        candidates.append({
            "page": 1,
            "bbox": list(table.bbox),
            "rows": [list(row) for row in table.extract()],
            "cells": [list(cell) if cell is not None else None for cell in table.cells],
            "header": {"names": list(table.header.names),
                       "external": table.header.external,
                       "bbox": list(table.header.bbox)},
        })
# Only copied values remain usable here; page-bound detector objects do not.
```

Copy evidence while the page is alive. Detector objects become invalid when
their page is deleted or reassigned. External headers may sit outside the
detected body and need separate checking. Do not discard them as nearby prose.
See the [PyMuPDF table API](https://pymupdf.readthedocs.io/en/latest/page.html#Page.find_tables).

## Preserve cell meaning

| Observation | Reconstruction rule |
|---|---|
| `76.10` versus `76.1` | Preserve the displayed precision, including trailing zeros |
| Empty cell | Keep its column position; do not shift the following value left |
| Extracted `None` or missing cell box | Check for a merged region, truly empty cell, or detection failure; the value alone does not decide |
| `--`, `N/A`, `0`, inequality, or error bar | Preserve the exact visible content; these are not interchangeable |
| `Score (%)` or a unit in a grouped header | Retain which columns it applies to; do not silently convert units |
| Superscript letter or symbol | Map to the actual table note, not a mathematical exponent by default |
| Bold/highlighted entry | Confirm whether it denotes a best result, a group label, or another convention |
| Contradiction with prose or another table | Preserve both readings and flag the source locations; do not reconcile by guessing |

Keep a cell ledger with page/table, row, column, covered rows/columns, observed
text and bounding evidence. For unreadable content, show a visible uncertainty
marker in that cell and explain it in the notes. Retain a genuinely blank cell
as blank rather than filling every gap with a placeholder.

## Generate a candidate table

Use `\multicolumn` for a spanning header and `\multirow` only when needed, with
its package available. Account for continuation cells in later rows. Validate
the logical column occupancy rather than counting literal ampersands:
`\multicolumn{2}{...}{...}` consumes two columns, `\&` is literal prose, and
an embedded aligned math environment can contain its own alignment separators.

This four-column example preserves a grouped header, a literal ampersand,
trailing zeros, a dash and a deliberately blank cell. It requires `booktabs`.

```latex
\begin{tabular}{lrrl}
\toprule
Method & \multicolumn{2}{c}{Score (\%)} & Note \\
\cmidrule(lr){2-3}
 & Mean & Spread & \\
\midrule
A\&B & 76.10 & 0.30 & Measured \\
Variant & -{}- & & Not measured\textsuperscript{a} \\
\bottomrule
\end{tabular}

\smallskip
\textsuperscript{a}Spread is blank in the source; no value was supplied.
```

Escape prose such as `%`, `&`, `_` and `#` before inserting it into cells, but
do not indiscriminately escape already generated commands or math. Retain the
original caption wording, row order and notes. Do not rewrite the scientific
claim while reconstructing a table. The example uses `-{}-` for two literal
hyphens; ordinary `--` becomes an en dash in conventional TeX text. Choose the
form that matches the actual source marker.

Choose styling from the reconstruction target or supplied author kit. `booktabs`
is an optional presentation choice, not evidence of the PDF's original package.
Use `\linewidth` appropriate to the containing column/minipage; `table*` may be
appropriate for a full-width table in a two-column class when that class permits
it. Check legibility and float placement before shrinking an entire table.

## Verify cell by cell

Compile with the selected class/packages and compare the table with the source.
Check the row and column association of every number, merged-header coverage,
empty positions, units, signs, decimal precision, highlights and notes. Check
multi-page continuations separately. Extracting text from the resulting PDF
helps locate missing values, but cannot establish the grid or visual fidelity.

Report the verified cells and any unresolved positions. Source uncertainty
remains even when the table is syntactically valid and visually tidy.
