# Table Reconstruction

Strategies for extracting table structure from PDF and generating tabular environments.

## Approach Overview

1. Detect table region (ruled area or text grid)
2. Extract cell boundaries (horizontal/vertical positions)
3. Extract cell text content
4. Determine column alignment
5. Generate `\begin{tabular}` with appropriate spec
6. Apply booktabs rules where detected

## Step 1: Detect Table Region

### Using pdfplumber (for tables with visible rules)

```python
import pdfplumber

with pdfplumber.open("paper.pdf") as pdf:
    page = pdf.pages[page_num]

    # Method 1: Extract bordered tables automatically
    tables = page.extract_tables()
    # Returns list of tables; each table is list of rows; each row is list of cell strings

    # Method 2: Manual detection using edges
    edges = page.edges
    lines = page.lines
    # Cluster lines into table regions
    # Horizontal line spans → table width
    # Vertical line spans → column boundaries
```

### Using pymupdf (for borderless tables)

```python
import fitz

doc = fitz.open("paper.pdf")
page = doc[page_num]
blocks = page.get_text("dict")["blocks"]

# Find text blocks that are:
# 1. Vertically aligned (share similar x-ranges across rows)
# 2. Closely spaced vertically (small y-gaps)
# 3. Contain short text (table cells are brief)
# 4. Often preceded by "Table <N>:" caption
```

## Step 2: Extract Cell Boundaries

### Column detection
```
1. Collect x0 of text blocks in the table region
2. Cluster x0 values (group spans that start at the same x position)
3. Sort clusters left-to-right → column boundaries
4. Check x1 values to confirm column widths
```

### Row detection
```
1. Collect y0 (top) of text blocks
2. Cluster by similar y0 values
3. Sort top-to-bottom → row boundaries
4. Use line.y values for ruled tables
```

## Step 3: Extract Cell Content

For each cell (column_i, row_j):
```
cell_text = ""
For text blocks where (x0 ≈ col_i_boundary) AND (y0 ≈ row_j_boundary):
    cell_text += block.text
```

## Step 4: Determine Column Alignment

| Content pattern | Alignment |
|---|---|
| Numbers, decimal points | `r` (right) |
| Short text, names | `l` (left) |
| Centered values ("±", "N/A") | `c` (center) |
| Long descriptive text | `p{<width>cm}` (paragraph) |

Automatic detection:
```
For each column:
  numeric_cells = count of cells matching ^[\d.-]+$
  if numeric_cells / total_cells > 0.5:
    alignment = 'r'
  else:
    alignment = 'l'
```

## Step 5: Detect Table Rules

Using pdfplumber lines/rects:
- Topmost horizontal line → `\toprule`
- Line between header and body → `\midrule`
- Bottommost horizontal line → `\bottomrule`
- Other internal horizontal lines → `\hline` or `\cmidrule{<i>-<j>}`
- Vertical lines → include `|` in column spec (though booktabs discourages them)

For borderless tables with booktabs style:
- No vertical lines detected → use `l r r r` format
- Only 3 horizontal lines → `\toprule`, `\midrule`, `\bottomrule`
- Partial rules → `\cmidrule{2-4}`, etc.

## Step 6: Generate Tabular Environment

### Basic format:
```latex
\begin{table}[t]
  \centering
  \caption{<extracted caption>}
  \label{tab:reconstructed_<N>}
  \begin{tabular}{<col_spec>}
    \toprule
    <header row> \\
    \midrule
    <data rows> \\
    \bottomrule
  \end{tabular}
\end{table}
```

### Column specification:
```
col_spec = ""
for each column:
  if vertical_line_left_detected:
    col_spec += "|"
  col_spec += alignment
  if vertical_line_right_detected:
    col_spec += "|"
```

## Step 7: Handle Special Cases

### Multi-Row / Multi-Column Cells

**Detection:** A cell spans wider than one column or taller than one row.

```latex
\multicolumn{<N>}{<align>}{<text>}
% [REVIEW: Verify multi-column span width]
```

Flag for manual review — automatic multi-column detection is error-prone.

### Headers in tables

**Detection:**
- Bold text in topmost row
- Under different background (from span/block color data)
- Under `\midrule`

### Table Notes / Footnotes

**Detection:**
- Small text below table body
- Starts with asterisk, dagger, or superscript
- Separate from main table rows

→ Separate from `\end{tabular}`, place as `\par\small <note text>`

### Rotated Headers

**Detection:** Text spans with unusual width/height ratio in header row.

→ Use `\rotatebox{90}{<text>}` or flag for manual review.

### Wide Tables (two-column docs)

**Detection:** Table width > column_width but < page_width.

→ Use `\begin{table*}...\end{table*}` instead of `\begin{table}`.

## Quality Checks

After reconstruction:
1. Column count consistent across all rows
2. All `&` separators correct (N-1 amp signs for N columns)
3. End-of-row `\\` present (except last row)
4. Rules matched (no isolated `\midrule`)
5. Special characters escaped (`%`, `&`, `#`, `_` in cell text)
6. Caption text is grammatically complete