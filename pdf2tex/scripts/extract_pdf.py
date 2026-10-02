#!/usr/bin/env python3
"""Extract PDF text/layout evidence and an offline review, with optional images/previews."""

import argparse
import hashlib
from html import escape
import importlib
import json
import math
from pathlib import Path
import re
import sys
import tempfile

MAX_PREVIEW_PIXELS = 20_000_000


def write_review(bundle, report, texts):
    """Write a script-free, offline review with escaped source content."""
    css = (Path(__file__).resolve().parents[1] / "assets" / "review.css").read_text(encoding="utf-8")
    navigation, sections = [], []
    for page, text in zip(report["pages"], texts):
        number = page["page"]
        navigation.append(f'<a href="#page-{number}">Page {number}</a>')
        if page["preview"]:
            preview = page["preview"]
            visual = (f'<a href="{escape(preview["file"], quote=True)}" aria-label="Open full preview of page {number}">'
                      f'<img src="{escape(preview["file"], quote=True)}" width="{preview["width"]}" '
                      f'height="{preview["height"]}" loading="lazy" alt="PDF page {number}, including annotations"></a>'
                      f'<figcaption>{preview["dpi"]} DPI · annotations included · click to enlarge</figcaption>')
        else:
            visual = '<p class="empty">No preview requested. Use <code>--render</code> on a new extraction to compare page appearance.</p>'
        status = "Text extracted" if page["text_status"] == "available" else "No extractable text — inspect the page"
        content = f'<pre>{escape(text)}</pre>' if text.strip() else '<p class="empty">This page may be blank, graphic-only, or require a separate OCR workflow.</p>'
        sections.append(f'<section id="page-{number}" class="page" aria-labelledby="heading-{number}">'
                        f'<div class="page-heading"><h2 id="heading-{number}">Page {number:02}</h2>'
                        f'<span>{status}</span></div><div class="comparison">'
                        f'<figure>{visual}</figure><div class="text"><h3>Extracted text</h3>'
                        f'<p class="caption">Geometric order; verify columns, equations, tables, and citations.</p>{content}'
                        '</div></div></section>')
    warnings = "".join(f"<li>{escape(warning)}</li>" for warning in report["warnings"])
    metadata = "".join(f'<dt>{escape(str(key))}</dt><dd>{escape(str(value))}</dd>'
                       for key, value in report["metadata"].items() if value)
    selected = ", ".join(map(str, report["selected_pages"]))
    title = report["metadata"].get("title") or report["source"]
    html = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\' file:; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
            f'<title>{escape(str(title))} — PDF evidence</title><style>{css}</style></head><body>'
            '<header><p class="eyebrow">AWESOME LATEX SKILLS / PDF EVIDENCE</p>'
            f'<h1>{escape(str(title))}</h1><p class="intro">Compare the extracted text with the page before reconstructing LaTeX.</p>'
            f'<div class="facts"><span><strong>{len(report["pages"])}/{report["page_count"]}</strong> pages selected</span>'
            f'<span><strong>{len(report["images"])}</strong> embedded images exported</span>'
            '<span>Native text · no OCR</span></div></header>'
            '<main><section class="provenance" aria-label="Source and coverage">'
            f'<p><strong>Source</strong> {escape(report["source"])}<br><strong>Selected pages</strong> {selected}</p>'
            '<p><strong>Evidence files</strong> <a href="text.txt">Plain text</a> · <a href="layout.json">Layout JSON</a></p>'
            '<details><summary>Source fingerprint &amp; metadata</summary>'
            f'<p class="hash">SHA-256: {report["source_sha256"]}</p><p>Input SHA-256 matched before and after extraction. '
            f'Extractor: PyMuPDF {escape(str(report["extractor"]["version"]))}.</p><dl>{metadata}</dl></details></section>'
            f'<aside class="warnings" aria-label="Extraction warnings"><h2>Check before reuse</h2><ul>{warnings}</ul></aside>'
            f'<nav aria-label="Selected pages">{"".join(navigation)}</nav>{"".join(sections)}</main>'
            '<footer>Page appearance is evidence; extraction is not verified reconstruction. '
            'Share the entire directory to retain previews and evidence files.</footer></body></html>\n')
    (bundle / "report.html").write_text(html, encoding="utf-8")


def load_pymupdf():
    try:
        module = importlib.import_module("pymupdf")
    except (ImportError, OSError) as exc:
        raise RuntimeError('PyMuPDF is required: python -m pip install "PyMuPDF>=1.24.10,<2"') from exc
    if not all(hasattr(module, name) for name in ("open", "Document", "VersionBind")):
        raise RuntimeError("The imported pymupdf module is not PyMuPDF")
    version = re.match(r"^(\d+)\.(\d+)\.(\d+)", str(module.VersionBind))
    if not version or not (1, 24, 10) <= tuple(map(int, version.groups())) < (2, 0, 0):
        raise RuntimeError('Supported PyMuPDF required: python -m pip install "PyMuPDF>=1.24.10,<2"')
    return module


def select_pages(spec, count):
    """Return unique zero-based indexes in document order from a 1-based range."""
    if count < 1:
        raise ValueError("The PDF has no pages")
    if spec is None:
        return list(range(count))
    selected = set()
    for part in spec.split(","):
        match = re.fullmatch(r"\s*([0-9]+)(?:-([0-9]+))?\s*", part)
        if not match:
            raise ValueError("Use page numbers or closed ranges, for example --pages 1-3,5")
        start, end = int(match[1]), int(match[2] or match[1])
        if start < 1 or end < start or end > count:
            raise ValueError(f"Invalid page range {part!r}; PDF has {count} pages")
        selected.update(range(start - 1, end))
    return sorted(selected)


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract(pdf, output, pages=None, images=False, render=False, dpi=144):
    pdf = Path(pdf).expanduser().resolve()
    output = Path(output).expanduser().absolute()
    if not pdf.is_file():
        raise ValueError(f"PDF does not exist: {pdf}")
    if not isinstance(dpi, int) or isinstance(dpi, bool) or not 72 <= dpi <= 300:
        raise ValueError("Preview resolution must be an integer from 72 to 300 DPI")
    if output.exists() or output.is_symlink():
        raise ValueError(f"Output already exists; choose a new directory: {output}")
    output = output.resolve()
    pymupdf = load_pymupdf()
    source_sha256 = file_hash(pdf)
    with pymupdf.open(pdf) as doc:
        if not doc.is_pdf:
            raise ValueError("Input must be a PDF")
        if doc.needs_pass:
            raise ValueError("PDF requires a password; supply an authorized decrypted copy")
        indexes = select_pages(pages, doc.page_count)
        report = {
            "schema_version": 2, "source": pdf.name, "source_sha256": source_sha256,
            "source_unchanged": True,
            "extractor": {"name": "PyMuPDF", "version": pymupdf.VersionBind},
            "page_count": doc.page_count, "selected_pages": [i + 1 for i in indexes],
            "metadata": doc.metadata, "toc": doc.get_toc(), "pages": [], "images": [],
            "warnings": ["Sorted plain text is not guaranteed reading order, especially across columns. Use block coordinates and the original PDF.",
                         "Embedded images do not include all vector figures or complete figure panels. No OCR or LaTeX reconstruction was performed."],
        }
        text_pages, image_files = [], {}
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".pdf2tex-", dir=output.parent) as temporary:
            bundle = Path(temporary) / "bundle"
            bundle.mkdir()
            for index in indexes:
                page = doc[index]
                flags = pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES
                layout = page.get_text("dict", flags=flags, sort=False)
                text = page.get_text("text", sort=True)
                record = {"page": index + 1, "width": layout["width"], "height": layout["height"],
                          "rotation": page.rotation, "blocks": layout["blocks"],
                          "text_status": "available" if text.strip() else "no-text", "images": [], "preview": None}
                if not text.strip():
                    report["warnings"].append(f"Page {index + 1} has no extractable text; it may be blank, graphic-only, or need OCR. Inspect the PDF.")
                text_pages.append(text)
                if render:
                    width = math.ceil(page.rect.width * dpi / 72) + 2
                    height = math.ceil(page.rect.height * dpi / 72) + 2
                    if width * height > MAX_PREVIEW_PIXELS:
                        raise ValueError(f"Page {index + 1} preview exceeds {MAX_PREVIEW_PIXELS:,} pixels; use a lower --dpi or select other pages")
                    filename = f"pages/page-{index + 1:04}.png"
                    (bundle / "pages").mkdir(exist_ok=True)
                    pixmap = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False, annots=True)
                    pixmap.save(bundle / filename)
                    record["preview"] = {"file": filename, "width": pixmap.width,
                                         "height": pixmap.height, "dpi": dpi, "annotations": True}
                    del pixmap
                if images:
                    for info in page.get_image_info(xrefs=True):
                        xref = info["xref"]
                        if not xref:
                            report["warnings"].append(f"Page {index + 1}: inline image without an extractable xref; use a page crop if needed.")
                            continue
                        if xref not in image_files:
                            image = doc.extract_image(xref)
                            if not image or not re.fullmatch(r"[a-zA-Z0-9]+", image["ext"]):
                                raise ValueError(f"Could not extract embedded image xref {xref}")
                            filename = f"images/image-{xref}.{image['ext']}"
                            (bundle / "images").mkdir(exist_ok=True)
                            (bundle / filename).write_bytes(image["image"])
                            item = {"xref": xref, "file": filename, "width": image["width"], "height": image["height"], "soft_mask": None}
                            if image.get("smask"):
                                mask = doc.extract_image(image["smask"])
                                if not mask or not re.fullmatch(r"[a-zA-Z0-9]+", mask["ext"]):
                                    raise ValueError(f"Could not extract soft mask for image {xref}")
                                item["soft_mask"] = f"images/mask-{image['smask']}.{mask['ext']}"
                                (bundle / item["soft_mask"]).write_bytes(mask["image"])
                                report["warnings"].append(f"Image {xref} has a separate soft mask; combine it or use a page crop to preserve appearance.")
                            image_files[xref] = item
                        record["images"].append({"xref": xref, "bbox": list(info["bbox"]), "file": image_files[xref]["file"]})
                report["pages"].append(record)
            report["images"] = list(image_files.values())
            if file_hash(pdf) != source_sha256:
                raise ValueError("Input PDF changed during extraction; retry with a stable copy")
            (bundle / "text.txt").write_text("\n\f\n".join(f"=== Page {page['page']} ===\n{text}"
                                                          for page, text in zip(report["pages"], text_pages)), encoding="utf-8")
            (bundle / "layout.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            write_review(bundle, report, text_pages)
            if output.exists() or output.is_symlink():
                raise ValueError(f"Output appeared during extraction: {output}")
            bundle.rename(output)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="New output directory; never reuse an existing directory")
    parser.add_argument("--pages", help="1-based page numbers/ranges, e.g. 1-3,5; default: all")
    parser.add_argument("--images", action="store_true", help="Export visible embedded raster images, including separate soft masks")
    parser.add_argument("--render", action="store_true", help="Save selected whole-page PNG previews for visual comparison; no OCR")
    parser.add_argument("--dpi", type=int, default=144, help="Preview resolution, 72–300 DPI (default 144); 20 million pixels maximum per page")
    args = parser.parse_args(argv)
    try:
        report = extract(args.pdf, args.output, args.pages, args.images, args.render, args.dpi)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Extraction failed: {exc}", file=sys.stderr)
        return 1
    print(f"Extracted {len(report['pages'])}/{report['page_count']} pages and {len(report['images'])} embedded images to {args.output}")
    print("Open report.html for offline page/text review; compare with the PDF before reconstruction.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
