# PDF Extraction Guide

## Start with the bundled helper

Use [extract_pdf.py](../scripts/extract_pdf.py) for repeatable extraction and
[requirements.txt](../requirements.txt) for its optional dependency. It writes
page-delimited UTF-8 text and a JSON evidence report to a new output directory.
It does not perform OCR, infer the original source, or reconstruct LaTeX.

| Output | Evidence retained |
|---|---|
| `report.html` | Offline page/text comparison, selected-page navigation, coverage, warnings, and expandable source metadata. Open directly in a browser; keep the entire directory together. |
| `text.txt` | Text with original selected-page numbers; no semantic cleanup. |
| `layout.json` | Source SHA-256, tool version, metadata, bookmarks, page geometry/rotation, raw text blocks/spans/font data, optional character positions, image placements, and warnings. |
| `images/` (optional) | Unique embedded raster images and separately recorded soft masks. |
| `pages/` (optional) | Selected whole-page RGB PNG previews, with original page numbers, rotation/crop handling, annotations, and dimensions/DPI recorded in JSON. |

Page selection is one-based: `--pages 1-3,5`. Duplicates are removed and pages
remain in document order. Without `--pages`, all pages are selected. Existing
output directories are refused. Use a different destination for each attempt.

For visual evidence including vectors and composite figures:

```sh
python pdf2tex/scripts/extract_pdf.py paper.pdf --output evidence --pages 1-3 --images --render --dpi 144
```

`--render` saves whole pages, not segmented figures or OCR text. `--dpi` accepts
72–300 (default 144); previews exceeding 20 million pixels per page are refused
before rendering. Lower the DPI or select other pages. Rendering failure publishes
no partial bundle. Preview annotations are included; account for them when comparing
publication artwork. The schema-2 `layout.json` includes each page's optional
`preview` record and `source_unchanged` fingerprint check.

## Review offline

Open `report.html` directly in a browser. With `--render`, each selected page
appears beside its extracted text; without it, the report explains that a preview
was not requested. Page navigation retains original PDF page numbers, including
gaps in selected coverage. No-text pages are visible rather than silently omitted.
The report adapts to narrow screens and dark mode and supports browser printing.

The HTML includes its stylesheet and has no scripts, external fonts or remote
resources. PDF text and metadata are escaped as text, never inserted as executable
markup or source-supplied links. Previews, `text.txt` and `layout.json` use relative
links; share the complete output directory, not just the HTML file.

Source SHA-256 is checked before opening and again after extracting the selected
pages. If it differs, no output bundle is published; retry with a stable copy.
This detects ordinary concurrent edits, but does not lock or freeze the input or
establish authenticity. The helper itself never writes to the input PDF.

Inspect column order, formulas, tables and figure labels against the previews or
original PDF. The report displays extraction evidence and warnings; it does not
certify completeness, reading order or reconstructed LaTeX.

## Inspect text and fonts

The preferred import name is `pymupdf`; avoid the unrelated package named `fitz`.
For targeted inspection:

```python
import pymupdf

with pymupdf.open("paper.pdf") as doc:
    page = doc[0]
    flags = pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES
    evidence = page.get_text("dict", flags=flags, sort=False)
    print(page.get_fonts(full=True))
    for block in evidence["blocks"]:
        for line in block["lines"]:
            for span in line["spans"]:
                print(span["text"], span["font"], span["size"], span["bbox"])
```

Span font names and page font resources help interpret headings and notation.
Subset prefixes and font substitutions can obscure the original font choice.
Neither font format nor the PDF creator string proves the TeX engine, document
class, or package list. Record those choices as inferred when reconstructing.

API details: [PyMuPDF Page reference](https://pymupdf.readthedocs.io/en/latest/page.html).

## Character detail and page coordinates

For formulas, small superscripts or table notes, add `--chars`:

```sh
python pdf2tex/scripts/extract_pdf.py paper.pdf --output detailed-evidence --pages 1 --chars --render
```

The schema-2 report adds `text_detail`: `spans` by default or `characters`
with this option. Character mode uses `rawdict` and adds each span's `chars`
entries (`c`, `origin`, `bbox`). It also reconstructs the existing `span.text`
field, so consumers can continue reading span text. Plain text and HTML content
are unchanged; JSON grows with the number of characters. No glyph recognition
or mathematical parsing is performed.

Every page records `geometry` with `mediabox`, `cropbox`, displayed `rect`,
`rotation_matrix` and `derotation_matrix`. Text positions are in unrotated
PyMuPDF coordinates, whose y axis points down. To relate a character to a
rotated preview, apply the recorded rotation matrix, then scale by DPI/72:

```python
# record is one entry from layout.json's pages array; char is a chars entry.
rotation = pymupdf.Matrix(*record["geometry"]["rotation_matrix"])
point = pymupdf.Point(*char["origin"]) * rotation
scale = record["preview"]["dpi"] / 72
pixel_origin = (point.x * scale, point.y * scale)
```

This example requires a requested preview. Do not subtract the crop-box offset
again from extracted text coordinates. Use bounding boxes for glyph regions
and the line's `dir` for nonhorizontal text; an origin is a baseline point,
not the top-left ink pixel. Compare with the original rather than inferring a
formula solely from coordinates.

See [PyMuPDF RAWDICT](https://pymupdf.readthedocs.io/en/latest/textpage.html)
and [page geometry](https://pymupdf.readthedocs.io/en/latest/page.html).

## Reading order and columns

`get_text("text", sort=True)` sorts geometrically; it cannot establish semantic
reading order for every layout. The helper keeps original block evidence in JSON
so a reconstruction does not depend solely on that sorted text.

For columns, inspect both `x0` and `x1`, not just a block's left edge. Keep
full-width titles, equations, and captions. Determine vertical bands separated
by spanning elements, then read each band in its actual column order. Preserve
every block and flag overlapping or ambiguous regions rather than dropping them.
Rotated pages and mixed layouts require visual checking.

Do not join hyphenated words or remove repeated lines until confirming the page
layout. A hyphen can belong to a scientific term and repeated text can be meaningful.

Background: [PyMuPDF text recipes](https://pymupdf.readthedocs.io/en/latest/recipes-text.html).

## Images and figure appearance

An embedded image is not necessarily an entire figure. A figure can combine
vector lines, labels, raster panels, and a caption. The helper deduplicates
embedded images by xref and records each visible placement on selected pages.

Soft masks are exported separately and referenced in JSON. Recombine a mask
with its image, or render a crop of the figure, before treating it as a recovered
asset. Inline images without usable xrefs are flagged. Compare colors,
transparency, orientation, labels, and panel boundaries with the original page.
Whole-page previews from `--render` retain visible vector/raster compositions for
comparison; they are not a substitute for selecting the correct figure region.

Background: [PyMuPDF image recipes](https://pymupdf.readthedocs.io/en/latest/recipes-images.html).

## Tables

Table text alone does not encode cell boundaries or merged-cell meaning. Use
the span coordinates, ruling lines, and rendered page to reconstruct rows and
columns. `Page.find_tables()` or a separately installed table-extraction tool
can provide candidates; preserve empty cells and verify merged regions.
See [table reconstruction](table-reconstruction.md) for content checks.

## OCR when a page has no text

No extractable text does not prove that a page is scanned; inspect blank and
graphic-only pages first. When OCR is appropriate, configure Tesseract and the
needed language data separately. PyMuPDF can create a reusable OCR TextPage:

```python
with pymupdf.open("scan.pdf") as doc:
    page = doc[0]
    ocr_page = page.get_textpage_ocr(language="eng", dpi=300, full=True)
    text = page.get_text("text", textpage=ocr_page)
```

Preserve page provenance and distinguish OCR text from the native text layer.
OCR quality depends on language, resolution, layout, and symbols; no fixed
accuracy is assumed. Verify math and tables against the scan. The bundled
extractor does not invoke OCR or install its dependencies.

Setup details: [PyMuPDF OCR guide](https://pymupdf.readthedocs.io/en/latest/recipes-ocr.html).
