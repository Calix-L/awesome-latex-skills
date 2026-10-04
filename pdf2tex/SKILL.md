---
name: pdf2tex
description: Reconstruct editable LaTeX from PDF content using page-aware extraction and visual comparison. Preserve source evidence, flag uncertain math/tables/citations, and distinguish text extraction, OCR, reconstruction, and verified compilation.
metadata:
  version: "1.12.0"
---

## Establish the reconstruction target

Inspect the PDF, requested pages, available tools, and desired output. Determine
whether the user wants content recovery or close visual reconstruction. Preserve
the original PDF and write new artifacts to a separate destination.

A PDF may expose text, font names, coordinates, images, and metadata. It does
not reliably encode its original document class, packages, macros, bibliography
database, comments, or source-file boundaries. Font/creator metadata is evidence
for a candidate setup, not proof of the original engine or class.

## Extract evidence

When PyMuPDF is available, use the bundled helper from this skill's own directory.
The following paths are relative to the repository root; for an installed skill,
substitute its actual location. Dependency installation is separate from extraction.

```sh
python -m pip install -r pdf2tex/requirements.txt
python pdf2tex/scripts/extract_pdf.py paper.pdf --output extraction --pages 1-3,5 --images --render
```

The helper creates a new directory with `report.html`, `text.txt`, `layout.json`, and optional
embedded images and whole-page PNG previews when requested. It records page numbers, raw text spans/font/position data,
metadata, selected-page coverage, and warnings. It refuses existing output
directories and refuses publication if the input fingerprint changes during
extraction. Open `report.html` for offline page/text review; keep the entire
directory together when sharing. It performs no OCR or conversion.

Read [PDF extraction guide](references/pdf-extraction-guide.md) for API details,
alternative readers, columns, fonts, and OCR. Sorted text is not guaranteed
reading order; inspect page layouts and use coordinates. Images can be repeated
or carry separate soft masks. Vector figures and composite panels often need
a page crop or another export workflow. Use optional `--render` previews to
inspect selected pages, including vector/composite figures; these are visual
evidence, not OCR or segmented assets. `--dpi` accepts 72–300 with a per-page pixel limit.

Use optional `--chars` when inspecting scripts or small notation. It adds
character origins/bounding boxes while retaining span text. Page geometry and
rotation matrices help relate unrotated text coordinates to rendered previews;
positions are evidence for candidate readings, not an automatic math parser.

A page without text may be blank, graphical, or scanned. Check it visually before
choosing OCR. OCR requires separate tools and cannot establish the correctness
of equations or tables. Retain page provenance and flag OCR-derived uncertainty.
For a password-protected PDF, use an authorized readable copy.

## Reconstruct without inventing content

Use [structure detection](references/structure-detection.md) to interpret blocks,
[math reconstruction](references/math-reconstruction.md) for notation, and
[table reconstruction](references/table-reconstruction.md) for cells and merged
regions. These heuristics need comparison with the rendered original.

- Select an available class and engine suitable for the target; state inferred
  choices. Use a supplied official author kit when exact publication layout is required.
- Preserve selected-page coverage, section order, prose, equations, table values,
  captions, footnotes, and references. Escape LaTeX-special characters in prose
  without indiscriminately escaping math or generated commands.
- Associate citation markers with bibliography entries only when the mapping
  is supported. Keep unmatched markers and uncertainty visible; do not invent
  bibliographic metadata or silently assign the nearest reference.
- Preserve ambiguous glyphs, merged table cells, missing images, and illegible
  content as source evidence with `% [UNCERTAIN: ...]` or a visible placeholder.
  A comment alone must not hide missing content from the generated document.
- Remove headers/footers or join hyphenated lines only after checking that they
  are layout artifacts. Preserve meaningful hyphens and repeated scientific text.
- Do not guess original macros or file splitting. A self-contained source is a
  useful default, not a claim that it matches the original organization.

## Build, compare, and deliver

Use the selected engine and actual bibliography backend, with additional passes
for cross-references. `latex-rescue` can help when available. If tools or assets
are unavailable, preserve the source and report compilation as unverified.

Compare the rendered reconstruction with the selected original pages: completeness,
reading order, math symbols, tables, figure appearances, captions, and citations.
Matching page counts does not establish fidelity. Check merged cells and OCR
math manually, and distinguish a visual approximation from content verification.

Deliver the new source/assets, input version and selected pages, extraction and
OCR methods actually used, inferred class/engine, build and visual-check results,
and uncertainty locations. Separate recovered content from placeholders. Do not
promise exact original source, perfect reconstruction, or immediate compilation.
Use `latex-polish` or `latex-fmt` only for a further requested editing task.
