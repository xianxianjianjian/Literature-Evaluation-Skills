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
        c.drawString(50, 640, "Sleep")
        c.drawString(82, 640, "spindles")
        c.showPage()
        c.save()

    def _ruled_table_pdf(self, path: Path) -> None:
        c = canvas.Canvas(str(path), pagesize=(500, 600), pageCompression=1)
        c.setFont("Helvetica", 10)
        xs = [50, 180, 310, 450]
        ys = [500, 470, 440, 410]
        for x in xs:
            c.line(x, 410, x, 500)
        for y in ys:
            c.line(50, y, 450, y)
        rows = [
            ["Header A", "Header B", "Header C"],
            ["Alpha", "1", "2"],
            ["Beta", "3", "4"],
        ]
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                c.drawString(xs[column_index] + 5, ys[row_index] - 20, value)
        c.showPage()
        c.save()

    def _borderless_table_pdf(self, path: Path) -> None:
        c = canvas.Canvas(str(path), pagesize=(500, 600), pageCompression=1)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, 530, "Table 1. Example results")
        c.setFont("Helvetica", 10)
        xs = [50, 180, 310]
        rows = [
            ["Header A", "Header B", "Header C"],
            ["Alpha", "1", "2"],
            ["Beta", "3", "4"],
        ]
        for row_index, row in enumerate(rows):
            y = 500 - row_index * 22
            for column_index, value in enumerate(row):
                c.drawString(xs[column_index] + 5, y, value)
        c.showPage()
        c.save()

    def _rotated_margin_pdf(self, path: Path) -> None:
        c = canvas.Canvas(str(path), pagesize=(600, 800), pageCompression=1)
        c.setFont("Helvetica", 10)
        c.drawString(50, 700, "Scientific body text remains translatable")
        c.saveState()
        c.translate(585, 80)
        c.rotate(90)
        c.setFont("Helvetica", 7)
        c.drawString(0, 0, "Downloaded from example.org by guest")
        c.restoreState()
        c.showPage()
        c.save()

    def _line_number_gutter_pdf(self, path: Path) -> None:
        c = canvas.Canvas(str(path), pagesize=(612, 792), pageCompression=1)
        c.setFont("Helvetica", 9)
        for index in range(1, 9):
            y = 710 - (index - 1) * 20
            c.drawRightString(52, y, str(index))
            c.drawString(70, y, f"Scientific manuscript line {index} remains body text")
        c.drawCentredString(306, 30, "1")
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

    def test_ruled_table_cells_are_not_merged_across_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pdf_path = Path(temporary) / "ruled-table.pdf"
            self._ruled_table_pdf(pdf_path)
            frames = extract_text_frames.extract_frames(pdf_path, "SRC-M1")
            table_frames = [frame for frame in frames if frame["kind"] == "table_cell"]
            texts = {frame["source_text"] for frame in table_frames}

            self.assertGreaterEqual(len(table_frames), 9)
            self.assertTrue({"Alpha", "Beta", "1", "2", "3", "4"}.issubset(texts))
            self.assertFalse(
                any("Alpha\nBeta" in frame["source_text"] for frame in table_frames),
                "separate table rows must never share one replacement frame",
            )

    def test_borderless_table_is_cell_aware(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pdf_path = Path(temporary) / "borderless-table.pdf"
            self._borderless_table_pdf(pdf_path)
            frames = extract_text_frames.extract_frames(pdf_path, "SRC-M1")
            table_frames = [frame for frame in frames if frame["kind"] == "table_cell"]
            texts = {frame["source_text"] for frame in table_frames}

            self.assertGreaterEqual(len(table_frames), 9)
            self.assertTrue({"Header A", "Header B", "Header C"}.issubset(texts))
            self.assertFalse(
                any("Alpha\nBeta" in frame["source_text"] for frame in frames),
                "borderless table columns must not be vertically merged",
            )

    def test_rotated_outer_margin_furniture_is_retained_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pdf_path = Path(temporary) / "margin-watermark.pdf"
            self._rotated_margin_pdf(pdf_path)
            frames = extract_text_frames.extract_frames(pdf_path, "SRC-M1")
            retained = [
                frame
                for frame in frames
                if frame["translation_action"] == "RETAIN_SOURCE"
            ]
            translated = [
                frame
                for frame in frames
                if frame["translation_action"] == "TRANSLATE"
            ]

            self.assertEqual(len(retained), 1)
            self.assertEqual(retained[0]["kind"], "identifier")
            self.assertEqual(retained[0]["retain_reason"], "IDENTIFIER")
            self.assertIn(retained[0]["rotation"], {90, 270})
            normalized = retained[0]["source_text"].replace(" ", "").lower()
            self.assertTrue(
                "downloaded" in normalized or "downloaded" in normalized[::-1],
                "rotated publisher/download furniture must remain identifiable",
            )
            self.assertFalse(
                any("Downloaded" in frame["source_text"] for frame in translated),
                "publisher/download margin furniture must never enter translation frames",
            )
            self.assertTrue(
                any("Scientific body text" in frame["source_text"] for frame in translated)
            )

    def test_sequential_line_number_gutter_is_retained_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pdf_path = Path(temporary) / "line-numbers.pdf"
            self._line_number_gutter_pdf(pdf_path)
            frames = extract_text_frames.extract_frames(pdf_path, "SRC-S1")
            retained = [
                frame
                for frame in frames
                if frame.get("retain_reason") == "IDENTIFIER"
                and "1\n2\n3" in frame["source_text"]
            ]
            translated = [
                frame
                for frame in frames
                if frame["translation_action"] == "TRANSLATE"
            ]

            self.assertEqual(len(retained), 1)
            self.assertEqual(retained[0]["kind"], "identifier")
            self.assertIn("7\n8", retained[0]["source_text"])
            self.assertFalse(
                any(
                    frame["source_text"].strip().isdigit()
                    for frame in translated
                    if "\n" in frame["source_text"]
                ),
                "sequential gutter line numbers must not become translation frames",
            )
            self.assertTrue(
                any("Scientific manuscript line" in frame["source_text"] for frame in translated)
            )


if __name__ == "__main__":
    unittest.main()
