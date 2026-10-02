#!/usr/bin/env python3
"""Extract page-aware PDF text, layout evidence, and optional embedded images."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
import tempfile


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


def extract(pdf, output, pages=None, images=False):
    pdf = Path(pdf).expanduser().resolve()
    output = Path(output).expanduser().absolute()
    if not pdf.is_file():
        raise ValueError(f"PDF does not exist: {pdf}")
    if output.exists() or output.is_symlink():
        raise ValueError(f"Output already exists; choose a new directory: {output}")
    output = output.resolve()
    pymupdf = load_pymupdf()
    with pymupdf.open(pdf) as doc:
        if not doc.is_pdf:
            raise ValueError("Input must be a PDF")
        if doc.needs_pass:
            raise ValueError("PDF requires a password; supply an authorized decrypted copy")
        indexes = select_pages(pages, doc.page_count)
        report = {
            "schema_version": 1, "source": pdf.name, "source_sha256": file_hash(pdf),
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
                          "text_status": "available" if text.strip() else "no-text", "images": []}
                if not text.strip():
                    report["warnings"].append(f"Page {index + 1} has no extractable text; it may be blank, graphic-only, or need OCR. Inspect the PDF.")
                text_pages.append(f"=== Page {index + 1} ===\n{text}")
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
            (bundle / "text.txt").write_text("\n\f\n".join(text_pages), encoding="utf-8")
            (bundle / "layout.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
    args = parser.parse_args(argv)
    try:
        report = extract(args.pdf, args.output, args.pages, args.images)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Extraction failed: {exc}", file=sys.stderr)
        return 1
    print(f"Extracted {len(report['pages'])}/{report['page_count']} pages and {len(report['images'])} embedded images to {args.output}")
    print("Read layout.json warnings and compare text.txt with the PDF before reconstruction.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
