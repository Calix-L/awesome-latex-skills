# Structure Detection

Heuristics for detecting document structure from extracted PDF text blocks.

## Title Detection

The title block is usually at the top of page 1.

**Signals:**
- Largest font size on page 1
- Centered text (x-midpoint ≈ page_width/2)
- Bold weight
- Top of page (y < page_height * 0.3)
- Single block, may span multiple lines
- No number prefix

**Extraction:**
```
For each text block on page 1:
  if font_size == max(page1_font_sizes) and is_bold and is_centered:
    → \title{<text>}
```

## Author Block Detection

Directly below the title on page 1.

**Signals:**
- Smaller than title font, still centering
- Contains commas, "and", affiliations
- May have superscript markers ("*", "1", "†")
- Often in a different font/style than title
- Below title (higher y value), still in upper third of page

## Abstract Detection

**Signals:**
- Bold text block reading "Abstract" or "ABSTRACT"
- Following paragraph in smaller font or italic
- Positioned after author block, before first section heading
- Often single paragraph, sometimes justified differently

## Section Heading Detection

**Primary signals (in order of reliability):**
1. Font size larger than body text
2. Bold weight
3. Numbered prefix ("1.", "2.", "I.", "A.")
4. Vertical gap above (larger than normal line spacing)
5. Small set of words ("Introduction", "Related Work", "Method", "Experiments", "Conclusion", "References")

**Hierarchy classification:**
| Level | Font size (relative) | Numbering style | Example |
|---|---|---|---|
| `\section` | LARGEST (e.g. 12-14pt bold) | "1.", "2." | `\section{Introduction}` |
| `\subsection` | Medium (e.g. 10.5-11pt bold) | "1.1", "2.3" | `\subsection{Dataset}` |
| `\subsubsection` | Slightly above body, bold | "1.1.1" | `\subsubsection{Preprocessing}` |
| Paragraph heading | Body size, bold/italic, inline | None | `\paragraph{Setup.}` |

**Algorithm:**
```
For each text block that is bold and larger than body:
  1. Check proximity to previous block (gap > body_line_spacing * 1.5)
  2. Check text length (headings are short, < 100 chars)
  3. Check for numbering pattern
  4. Classify as section/subsection/subsubsection based on font size rank
```

**Edge cases:**
- Unnumbered sections: detect by font size + bold + position pattern only
- "Related Work" vs "Related Works": both common, don't auto-correct
- Appendices: often have letter prefixes ("Appendix A.", "A.")

## Body Text Detection

Everything that's not a heading, caption, footnote, header, or equation.

**Characteristics:**
- Most common font size on the page
- Regular (non-bold) weight
- Full-width blocks (x1 - x0 ≈ text width)
- Multiple lines, often indented

## Math Detection

### Inline math
**Signals:**
- Italic single characters (variables)
- Font name contains "CMMI" (Computer Modern Math Italic)
- Short runs (< 50 chars) of mixed italic/normal
- Contains math symbols (Greek in Unicode)

### Display math (equation)
**Signals:**
- Text block centered horizontally
- Surrounded by vertical gaps larger than normal line spacing
- Font name contains "CMMI" or "CMSY"
- May have equation number on right edge
- Isolated from surrounding paragraph text

## Table Detection

**Signals:**
- Grid of text blocks aligned in rows and columns
- Horizontal and vertical ruling lines (from pdfplumber)
- Alternating row fills (detected via background colors)
- "Table" in preceding caption
- Text blocks with tight x-alignment across rows

**Detection algorithm:**
```
1. Find horizontal lines (from pdfplumber page.lines/rects)
2. Find vertical lines
3. For each rectangular region bounded by lines:
   a. Extract text within the region
   b. Align text by column (matching x-ranges)
   c. Build matrix of cell contents
4. Also check for borderless tables (text alignment only)
```

## Figure Detection

**Signals:**
- Image blocks (block["type"] == 1 in pymupdf dict extraction)
- "Figure" in preceding or following caption text
- Caption text: "Figure <num>: <text>" or "Fig. <num>. <text>"

## Caption Detection

**Signals:**
- Text block immediately above or below a figure/table
- Starts with "Figure", "Fig.", or "Table" followed by a number
- Font size often slightly smaller than body text
- Sometimes italic

## Footer/Header Detection

**Signals:**
- Text at extreme top or bottom of page (y < 50 or y > page_height - 50)
- Repetitive across pages (same text, same position)
- Page numbers
- Running titles/authors

**Must be STRIPPED from reconstruction** unless it's part of the content.

## Citation Detection

### Numeric citations (common in IEEE, most CS venues)
- Pattern: `[<number>]` or `[<num>,<num>,<num>]`
- Example: `[42]` or `[3,7,12]` or `[1-5]`
→ `\cite{ref<num>}` with placeholder key

### Author-year citations (common in natural sciences)
- Pattern: `<Author> (<year>)` or `(<Author>, <year>)`
- Example: `Smith (2023)` or `(Smith, 2023)`
- → `\citet{smith2023}` or `\citep{smith2023}`

### Detection strategy:
```
For each text block:
  Search for regex patterns:
    - Numeric: \[([\d,\s-]+)\]
    - Author-year: \([A-Z][a-z]+.*?\d{4}\)
  Replace with \cite{refX} placeholder
  Record for bibliography mapping
```

## Footnote Detection

**Signals:**
- Text block at bottom of page
- Separated from body by a short horizontal rule
- Smaller font size
- May have superscript number at start of footnote text
- Corresponding superscript in body text above