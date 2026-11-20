"""Tests for the PDF exports and the Arabic text preparation used in them."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import arabic  # noqa: E402
import reports  # noqa: E402


class ArabicTests(unittest.TestCase):
    def test_contextual_forms(self):
        # سلم: seen initial, lam medial, meem final.
        self.assertEqual(arabic.shape("سلم"), "ﺳﻠﻢ")

    def test_lam_alef_ligature(self):
        self.assertEqual(arabic.shape("لا"), "ﻻ")
        self.assertEqual(arabic.shape("سلا"), "ﺳﻼ")

    def test_right_joining_letter_breaks_the_word(self):
        # دب: dal does not join to the left, so beh is isolated.
        self.assertEqual(arabic.shape("دب"), "ﺩﺏ")

    def test_visual_order_keeps_latin_runs(self):
        line = arabic.visual("الضغط 10.7 kPa الآن")
        self.assertIn("10.7 kPa", line)
        self.assertTrue(line.index("10.7 kPa") > 0)

    def test_latin_text_untouched(self):
        self.assertEqual(arabic.visual("Clean the strainer (PLANNED)."), "Clean the strainer (PLANNED).")


class PdfTests(unittest.TestCase):
    def assertPdf(self, data):
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertIn(b"%%EOF", data[-1024:])

    def test_text_pdf_with_arabic_and_symbols(self):
        self.assertPdf(reports.text_pdf("Work order", "test", "Δp* = 10.7 kPa ± 0.9\nتنظيف المصفاة قبل 2026-12-10"))

    def test_tool_pdf(self):
        self.assertPdf(reports.tool_pdf(
            "Cavitation Shield", "Will the pump cavitate?", "test",
            [("NPSH status", "SAFE", "target met", "SAFE")],
            [("Table", [["A", "B"], ["1", "2"]]), ("Text", "Line one\nLine two")]))


if __name__ == "__main__":
    unittest.main()
