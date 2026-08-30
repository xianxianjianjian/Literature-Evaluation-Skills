from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import extract_text_frames

try:
    from reportlab.pdfgen import canvas
except ImportError:
    canvas = None


@unittest.skipIf(canvas is None, "reportlab is unavailable")
class TextFrameExtractionTests(unittest.TestCase):
    def _two_column_pdf(self, path: Path) -> None:
        c = canvas.Canvas(str(path), pagesize=(600, 800), pageCompression=1)
        c.setFont("Helvetica", 9)
        c.drawString(50, 700, "Left column sentence one")
        c.drawString(50, 688, "Left column sentence two")
        c.drawString(330, 700, "Right column sentence one")
        c.drawString(330, 688, "Right column sentence two")

        # Draw two words separately so there is no explicit PDF space glyph.
        # The extractor should infer the word boundary from glyph geometry.
        c.drawString(50, 640, "Sleep")
        c.drawString(82, 640, "spindles")
        c.showPage()
        c.save()

    def test_parallel_columns_are_not_concatenated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pdf_path = Path(temporary) / "columns.pdf"
            self._two_column_pdf(pdf_path)
            frames = extract_text_frames.extract_frames(pdf_path, "SRC-M1")
            source_texts = [frame["source_text"] for frame in frames]

            self.assertTrue(any("Left column sentence one" in text for text in source_texts))
            self.assertTrue(any("Right column sentence one" in text for text in source_texts))
            self.assertFalse(
                any("Left column" in text and "Right column" in text for text in source_texts),
                "parallel journal columns must never be merged into one translation frame",
            )

    def test_word_boundary_is_preserved_or_inferred(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pdf_path = Path(temporary) / "spacing.pdf"
            self._two_column_pdf(pdf_path)
            frames = extract_text_frames.extract_frames(pdf_path, "SRC-M1")
            joined = "\n".join(frame["source_text"] for frame in frames)
            self.assertIn("Sleep spindles", joined)
            self.assertNotIn("Sleepspindles", joined)


if __name__ == "__main__":
    unittest.main()