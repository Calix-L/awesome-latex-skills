# PDF Extraction Guide

## Python Libraries

### pymupdf (fitz) — primary tool

```python
import fitz

# Open PDF
doc = fitz.open("paper.pdf")
print(f"Pages: {doc.page_count}")
print(f"Metadata: {doc.metadata}")

# Metadata fields: title, author, subject, keywords, creator, producer, format, encryption
# "creator" often contains the TeX engine: "LaTeX with hyperref" / "XeTeX 0.9999" / "LuaHBTeX"
# "producer" may have: "pdfTeX-1.40.25" → engine + version

# ── Text extraction ──
for page_num, page in enumerate(doc):
    # Method 1: dict format with position + font data (recommended)
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block["type"] == 0:  # text block
            bbox = block["bbox"]  # (x0, y0, x1, y1)
            for line in block["lines"]:
                spans = line["spans"]
                for span in spans:
                    text = span["text"]
                    font = span["font"]
                    size = round(span["size"], 1)
                    flags = span["flags"]  # bitfield: 2^0=superscript, 2^1=italic, 2^2=serifed, 2^3=bold, 2^4=mono
                    color = span["color"]  # RGB as int
                    origin = span["origin"]  # (x, y) baseline
                    # Use these features to classify text type

    # Method 2: plain text (lossy, only for quick checks)
    plain_text = page.get_text("text")

    # Method 3: HTML (sometimes useful for structure)
    html = page.get_text("html")

# ── Image extraction ──
for page_num, page in enumerate(doc):
    images = page.get_images(full=True)
    for img_idx, img in enumerate(images):
        xref = img[0]  # reference number
        base_image = doc.extract_image(xref)
        img_bytes = base_image["image"]
        ext = base_image["ext"]  # 'png', 'jpeg', 'tiff', 'jp2'
        width = base_image["width"]
        height = base_image["height"]
        colorspace = base_image["colorspace"]
        # Save: figures/figure_p{page_num+1}_{img_idx+1}.{ext}
        with open(f"figures/figure_p{page_num+1}_{img_idx+1}.{ext}", "wb") as f:
            f.write(img_bytes)

# ── Table of Contents ──
toc = doc.get_toc()  # list of [level, title, page_num]
# level 1 = section, level 2 = subsection, level 3 = subsubsection
# Only works if PDF has a generated ToC (most LaTeX PDFs do)

# ── Links and annotations ──
for page in doc:
    for link in page.get_links():
        uri = link.get("uri")  # URL
        page_to = link.get("page")  # internal link target page
        rect = link.get("from")  # clickable area

# ── Font list ──
# pymupdf can't list all fonts directly; use system call:
# pdffonts paper.pdf (poppler-utils)
```

### pdfplumber — for table extraction

```python
import pdfplumber

with pdfplumber.open("paper.pdf") as pdf:
    for page in pdf.pages:
        # Extract tables with borders
        tables = page.extract_tables()
        for table in tables:
            # table is list of rows, each row is list of cell strings
            pass

        # Horizontal/vertical ruling lines
        lines = page.lines
        rects = page.rects
        edges = page.edges  # bounding edges of drawn rectangles

        # Extract words with position
        words = page.extract_words()
        for w in words:
            text = w["text"]
            x0, top, x1, bottom = w["x0"], w["top"], w["x1"], w["bottom"]
```

## Font Classification

Use font names from `pdffonts` or span data to classify:

| Font name contains | Means | Packages |
|---|---|---|
| CM / CMR / CMBX | Computer Modern | default (no package) |
| LMRoman / LMSans | Latin Modern | `\usepackage{lmodern}` |
| NimbusRom / Times | Times clone | `\usepackage{mathptmx}` or `txfonts` |
| NimbusSan / Helvetica | Sans-serif clone | `\usepackage{helvet}` |
| DejaVu / FreeSerif | Free font family | `\usepackage{dejavu}` (xelatex) |
| Custom .ttf/.otf name | System font | `\setmainfont{...}` (xelatex/lualatex) |

## Encoding Issues

Common ligature/encoding problems when extracting from PDF:

| PDF glyph | Actual characters |
|---|---|
| fi (ligature) | "f" + "i" (two chars) |
| fl (ligature) | "f" + "l" |
| ff (ligature) | "f" + "f" |
| en-dash (–) | `--` in LaTeX source |
| em-dash (—) | `---` in LaTeX source |
| Left/right quotes | `` ` `` or `'` in source |

Map glyph Unicode codepoints back to LaTeX input encoding.

## Multi-Column Handling

For two-column PDFs:
- Text blocks with x0 < page_width/2 → left column
- Text blocks with x0 > page_width/2 → right column
- Combine: read all left-column blocks top-to-bottom, then right-column blocks top-to-bottom
- Watch for spanning elements (figures, wide tables) that cross the column boundary