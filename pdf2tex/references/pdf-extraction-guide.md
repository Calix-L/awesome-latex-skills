# PDF Extraction Guide

## Start with the bundled helper

Use [extract_pdf.py](../scripts/extract_pdf.py) for repeatable extraction and
[requirements.txt](../requirements.txt) for its optional dependency. It writes
page-delimited UTF-8 text and a JSON evidence report to a new output directory.
It does not perform OCR, infer the original source, or reconstruct LaTeX.

| Output | Evidence retained |
|---|---|
| `text.txt` | Text with original selected-page numbers; no semantic cleanup. |
| `layout.json` | Source SHA-256, tool version, metadata, bookmarks, page dimensions/rotation, raw text blocks/spans/font data, image placements, and warnings. |
| `images/` (optional) | Unique embedded raster images and separately recorded soft masks. |

Page selection is one-based: `--pages 1-3,5`. Duplicates are removed and pages
remain in document order. Without `--pages`, all pages are selected. Existing
output directories are refused. Use a different destination for each attempt.

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
