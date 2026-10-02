"""Candidate repairs must retain author data and unresolved identities."""
from pathlib import Path
import re
import unittest

ERRORS = Path(__file__).resolve().parent / "fixtures" / "errors"


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.broken = (ERRORS / "broken_paper.tex").read_text(encoding="utf-8")
        self.fixed = (ERRORS / "expected_fixed.tex").read_text(encoding="utf-8")

    def test_repair_retains_reference_citation_and_label_keys(self):
        commands = r"\\(?:cite|ref|label)\{([^}]+)\}"
        original = set(re.findall(commands, self.broken))
        repaired = set(re.findall(commands, self.fixed))
        self.assertTrue(original <= repaired, original - repaired)

    def test_repair_retains_table_cells_and_ambiguous_original_equation(self):
        tables = re.findall(r"\\begin\{tabular\}.*?\\end\{tabular\}", self.fixed, re.S)
        self.assertTrue(any(re.search(r"A\s*&\s*B\s*&\s*C", table) for table in tables))
        original = r"x^a^b = \sum_{i=1}^{n} y_i^2"
        self.assertIn(original, self.broken)
        self.assertIn(original, self.fixed)
        self.assertIn("UNCERTAIN", self.fixed)
