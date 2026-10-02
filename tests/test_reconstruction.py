"""Execute the documented table candidate example on actual PDF evidence."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from markdown_it import MarkdownIt
import pymupdf

REPO = Path(__file__).resolve().parents[1]


class ReconstructionReferenceTests(unittest.TestCase):
    def test_documented_detector_retains_precision_and_empty_column_after_page_close(self):
        guide = (REPO / "pdf2tex/references/table-reconstruction.md").read_text(encoding="utf-8")
        snippets = [token.content for token in MarkdownIt().parse(guide)
                    if token.type == "fence" and token.info == "python"]
        self.assertEqual(len(snippets), 1)
        with tempfile.TemporaryDirectory() as temporary:
            pdf = Path(temporary) / "paper.pdf"
            with pymupdf.open() as doc:
                page = doc.new_page()
                for x in (100, 200, 300, 400):
                    page.draw_line((x, 100), (x, 190))
                for y in (100, 130, 160, 190):
                    page.draw_line((100, y), (400, y))
                for row, values in enumerate((("Method", "Mean", "Spread"),
                                               ("A&B", "76.10", "0.30"),
                                               ("Variant", "--", ""))):
                    for column, value in enumerate(values):
                        if value:
                            page.insert_text((110 + 100 * column, 120 + 30 * row), value, fontsize=10)
                doc.save(pdf)
            before = pdf.read_bytes()
            code = snippets[0] + ('\nimport json\nfrom pathlib import Path\n'
                                  'Path("candidates.json").write_text(json.dumps(candidates), encoding="utf-8")\n')
            result = subprocess.run([sys.executable, "-c", code], cwd=temporary,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(pdf.read_bytes(), before)
            candidates = json.loads((Path(temporary) / "candidates.json").read_text(encoding="utf-8"))
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["page"], 1)
        self.assertEqual(candidate["bbox"], [100, 100, 400, 190])
        self.assertEqual(candidate["rows"][0], ["Method", "Mean", "Spread"])
        self.assertEqual(candidate["rows"][1], ["A&B", "76.10", "0.30"])
        self.assertEqual(candidate["rows"][2][:2], ["Variant", "--"])
        self.assertIn(candidate["rows"][2][2], ("", None))
        self.assertEqual(len(candidate["cells"]), 9)
        self.assertEqual(candidate["header"]["names"], ["Method", "Mean", "Spread"])
