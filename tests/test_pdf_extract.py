import importlib.util
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "pdf2tex" / "scripts" / "extract_pdf.py"
spec = importlib.util.spec_from_file_location("extract_pdf", SCRIPT)
extract_pdf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract_pdf)


class ReviewParser(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags, self.links, self.ids, self.text = [], [], [], []
        self.feed(text)

    def handle_starttag(self, tag, attributes):
        self.tags.append(tag)
        attrs = dict(attributes)
        self.links.extend(attrs[key] for key in ("href", "src") if key in attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if any(key.startswith("on") for key in attrs):
            raise AssertionError("Unexpected executable HTML attribute")

    def handle_data(self, data):
        self.text.append(data)


class PdfExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.pdf = self.root / "paper with spaces.pdf"
        self.output = self.root / "extracted paper"
        pixmap = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 8, 8), 1)
        pixmap.clear_with(128)
        self.image = pixmap.tobytes("png")
        with pymupdf.open() as doc:
            page = doc.new_page()
            page.insert_text((310, 100), "Right column: 91.7%")
            page.insert_text((40, 100), "Left column: +3.2 points; refX")
            page.insert_text((40, 150), "中文测试", fontname="china-s")
            xref = page.insert_image(pymupdf.Rect(40, 190, 80, 230), stream=self.image)
            page = doc.new_page()
            page.insert_text((40, 100), "Second page")
            page.insert_image(pymupdf.Rect(40, 190, 80, 230), xref=xref)
            doc.new_page()
            doc.set_metadata({"title": "Extraction fixture"})
            doc.set_toc([[1, "First section", 1]])
            doc.save(self.pdf)

    def test_text_layout_metadata_and_unicode_survive(self):
        original = self.pdf.read_bytes()
        report = extract_pdf.extract(self.pdf, self.output)
        text = (self.output / "text.txt").read_text(encoding="utf-8")
        layout = json.loads((self.output / "layout.json").read_text(encoding="utf-8"))
        self.assertIn("中文测试", text)
        self.assertIn("+3.2 points; refX", text)
        self.assertIn("=== Page 2 ===", text)
        self.assertEqual(layout["metadata"]["title"], "Extraction fixture")
        self.assertEqual(layout["toc"], [[1, "First section", 1]])
        spans = [span for block in report["pages"][0]["blocks"] for line in block["lines"] for span in line["spans"]]
        self.assertTrue(all("bbox" in span and "font" in span for span in spans))
        self.assertEqual(self.pdf.read_bytes(), original)

    def test_selected_pages_keep_original_numbers(self):
        report = extract_pdf.extract(self.pdf, self.output, "3,1,1")
        self.assertEqual(report["selected_pages"], [1, 3])
        self.assertNotIn("=== Page 2 ===", (self.output / "text.txt").read_text(encoding="utf-8"))

    def test_offline_review_preserves_coverage_and_links_to_real_evidence(self):
        extract_pdf.extract(self.pdf, self.output, "1,3", render=True, dpi=72)
        review = ReviewParser((self.output / "report.html").read_text(encoding="utf-8"))
        self.assertIn("page-1", review.ids)
        self.assertIn("page-3", review.ids)
        self.assertNotIn("page-2", review.ids)
        self.assertIn("中文测试", "".join(review.text))
        self.assertIn("No extractable text", "".join(review.text))
        self.assertIn("1, 3", "".join(review.text))
        self.assertIn("text.txt", review.links)
        self.assertIn("layout.json", review.links)
        self.assertNotIn("script", review.tags)
        self.assertNotIn("link", review.tags)
        for link in review.links:
            if link.startswith("#"):
                self.assertIn(link[1:], review.ids)
            else:
                self.assertTrue((self.output / link).is_file(), link)

    def test_review_escapes_pdf_text_and_metadata(self):
        malicious = '</pre><script>alert("x")</script><img src="https://example.org/pixel" onerror="alert(1)"> & text'
        with pymupdf.open(self.pdf) as doc:
            doc[0].insert_text((40, 300), malicious, fontsize=5)
            doc.set_metadata({"title": malicious, "author": '<a href="javascript:alert(1)">Author</a>'})
            doc.saveIncr()
        extract_pdf.extract(self.pdf, self.output, "1")
        html = (self.output / "report.html").read_text(encoding="utf-8")
        review = ReviewParser(html)
        self.assertIn(malicious, "".join(review.text))
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("script", review.tags)
        self.assertNotIn("img", review.tags)
        self.assertFalse(any(link.startswith(("https:", "javascript:")) for link in review.links))
        self.assertIn("No preview requested", "".join(review.text))
        self.assertIn("Content-Security-Policy", html)

    def test_changed_input_is_not_published_with_a_misleading_fingerprint(self):
        original_open = pymupdf.open

        def edit_then_open(path):
            path.write_bytes(path.read_bytes() + b"\n% externally changed\n")
            return original_open(path)

        with patch.object(pymupdf, "open", side_effect=edit_then_open):
            with self.assertRaisesRegex(ValueError, "changed during extraction"):
                extract_pdf.extract(self.pdf, self.output)
        self.assertTrue(self.pdf.read_bytes().endswith(b"% externally changed\n"))
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".pdf2tex-*")), [])

    def test_review_failure_publishes_no_partial_evidence(self):
        with patch.object(extract_pdf, "write_review", side_effect=OSError("review failed")):
            with self.assertRaisesRegex(OSError, "review failed"):
                extract_pdf.extract(self.pdf, self.output, render=True, dpi=72)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".pdf2tex-*")), [])

    def test_invalid_ranges_publish_nothing(self):
        for value in ("0", "4", "2-1", "1-", "", "1,,2", "../1", "1-9999999999"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                extract_pdf.extract(self.pdf, self.output, value)
            self.assertFalse(self.output.exists())

    def test_blank_page_is_flagged_without_claiming_it_is_scanned(self):
        report = extract_pdf.extract(self.pdf, self.output, "3")
        self.assertEqual(report["pages"][0]["text_status"], "no-text")
        self.assertTrue(any("may be blank" in warning for warning in report["warnings"]))

    def test_images_are_optional(self):
        report = extract_pdf.extract(self.pdf, self.output)
        self.assertEqual(report["images"], [])
        self.assertFalse((self.output / "images").exists())
        self.assertFalse((self.output / "pages").exists())
        self.assertTrue(all(page["preview"] is None for page in report["pages"]))

    def test_selected_page_previews_keep_numbers_pixels_and_annotations(self):
        with pymupdf.open(self.pdf) as doc:
            page = doc[1]
            page.draw_rect(pymupdf.Rect(100, 180, 250, 250), color=(1, 0, 0), fill=(1, 0, 0))
            page.add_rect_annot(pymupdf.Rect(280, 180, 350, 250)).update()
            page.set_rotation(90)
            doc.saveIncr()
        before = self.pdf.read_bytes()
        report = extract_pdf.extract(self.pdf, self.output, "2-3", render=True, dpi=72)
        self.assertEqual({p.name for p in (self.output / "pages").iterdir()}, {"page-0002.png", "page-0003.png"})
        with pymupdf.open(self.pdf) as original:
            for page in report["pages"]:
                preview = page["preview"]
                saved = pymupdf.Pixmap(self.output / preview["file"])
                expected = original[page["page"] - 1].get_pixmap(dpi=72, colorspace=pymupdf.csRGB, alpha=False, annots=True)
                self.assertEqual((saved.width, saved.height), (preview["width"], preview["height"]))
                self.assertEqual(saved.samples, expected.samples)
                self.assertEqual(saved.alpha, 0)
        self.assertEqual(self.pdf.read_bytes(), before)

    def test_invalid_or_excessive_preview_resolution_publishes_nothing(self):
        for value in (0, 71, 301, float("nan"), 144.5, True):
            with self.subTest(dpi=value), self.assertRaises(ValueError):
                extract_pdf.extract(self.pdf, self.output, render=True, dpi=value)
        oversized = self.root / "oversized.pdf"
        with pymupdf.open() as doc:
            doc.new_page(width=6000, height=6000)
            doc.save(oversized)
        with self.assertRaisesRegex(ValueError, "pixels"):
            extract_pdf.extract(oversized, self.output, render=True, dpi=72)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".pdf2tex-*")), [])

    def test_rendering_failure_leaves_no_partial_output(self):
        with patch.object(pymupdf.Page, "get_pixmap", side_effect=RuntimeError("render failed")):
            with self.assertRaisesRegex(RuntimeError, "render failed"):
                extract_pdf.extract(self.pdf, self.output, render=True)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".pdf2tex-*")), [])

    def test_image_deduplication_placements_and_soft_mask(self):
        report = extract_pdf.extract(self.pdf, self.output, images=True)
        self.assertEqual(len(report["images"]), 1)
        item = report["images"][0]
        self.assertTrue((self.output / item["file"]).is_file())
        self.assertIsNotNone(item["soft_mask"])
        self.assertTrue((self.output / item["soft_mask"]).is_file())
        self.assertEqual(report["pages"][0]["images"][0]["xref"], report["pages"][1]["images"][0]["xref"])
        self.assertEqual(len(report["pages"][0]["images"][0]["bbox"]), 4)

    def test_existing_output_remains_untouched(self):
        self.output.mkdir()
        keep = self.output / "personal.tex"
        keep.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "already exists"):
            extract_pdf.extract(self.pdf, self.output)
        self.assertEqual(keep.read_text(), "keep")

    def test_corrupt_and_encrypted_inputs_publish_nothing(self):
        bad = self.root / "bad.pdf"
        bad.write_bytes(b"invalid PDF")
        with self.assertRaises((RuntimeError, ValueError)):
            extract_pdf.extract(bad, self.output)
        locked = self.root / "locked.pdf"
        with pymupdf.open(self.pdf) as doc:
            doc.save(locked, encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="reader")
        with self.assertRaisesRegex(ValueError, "password"):
            extract_pdf.extract(locked, self.output)
        self.assertFalse(self.output.exists())

    def test_publish_failure_leaves_no_partial_output(self):
        with patch.object(Path, "rename", side_effect=OSError("simulated publish failure")), self.assertRaises(OSError):
            extract_pdf.extract(self.pdf, self.output, images=True)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".pdf2tex-*")), [])

    def test_installed_helper_runs_from_outside_repository(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from install import install
        destination = self.root / "skills"
        install(ROOT, destination, ["pdf2tex"])
        result = subprocess.run([sys.executable, str(destination / "pdf2tex" / "scripts" / "extract_pdf.py"),
                                 str(self.pdf), "--output", str(self.output), "--pages", "2", "--render", "--dpi", "72"],
                                cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((self.output / "layout.json").read_text())["selected_pages"], [2])
        self.assertTrue((self.output / "pages/page-0002.png").is_file())
        self.assertTrue((self.output / "report.html").is_file())

    def test_missing_dependency_has_actionable_error_and_help_still_works(self):
        command = [sys.executable, "-I", "-S", str(SCRIPT)]
        result = subprocess.run(command + ["--help"], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(command + [str(self.pdf), "--output", str(self.output)], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 1)
        self.assertIn("PyMuPDF is required", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_unsupported_dependency_version_is_rejected_before_writing(self):
        module = SimpleNamespace(open=pymupdf.open, Document=pymupdf.Document, VersionBind="1.24.9")
        with patch.object(extract_pdf.importlib, "import_module", return_value=module), self.assertRaisesRegex(RuntimeError, "Supported PyMuPDF"):
            extract_pdf.extract(self.pdf, self.output)
        self.assertFalse(self.output.exists())
