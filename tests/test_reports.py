"""Tests for the PDF exports."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import reports  # noqa: E402


class PdfTests(unittest.TestCase):
    def assertPdf(self, data):
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertIn(b"%%EOF", data[-1024:])

    def test_text_pdf_with_symbols(self):
        self.assertPdf(reports.text_pdf("Work order", "test", "Δp* = 10.7 kPa ± 0.9\nClean the strainer before 2026-12-10"))

    def test_tool_pdf(self):
        self.assertPdf(reports.tool_pdf(
            "Cavitation Shield", "Will the pump cavitate?", "test",
            [("NPSH status", "SAFE", "target met", "SAFE")],
            [("Table", [["A", "B"], ["1", "2"]]), ("Text", "Line one\nLine two")]))


if __name__ == "__main__":
    unittest.main()
