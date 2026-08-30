from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import extract_text_frames


class LigatureExtractionTests(unittest.TestCase):
    def test_shifted_ligature_stays_on_visual_line_and_normalizes(self) -> None:
        # Real JNeurosci PDFs can expose a typographic ligature several points
        # above neighboring glyph boxes even though it is on the same baseline.
        chars = [
            {
                "text": "Signi",
                "x0": 10.0,
                "x1": 35.0,
                "top": 100.0,
                "bottom": 109.0,
                "fontname": "FixtureFont",
                "size": 9.0,
            },
            {
                "text": "ﬁ",
                "x0": 35.0,
                "x1": 39.0,
                "top": 97.7,
                "bottom": 106.7,
                "fontname": "FixtureFont",
                "size": 9.0,
            },
            {
                "text": "cance",
                "x0": 39.0,
                "x1": 63.0,
                "top": 100.0,
                "bottom": 109.0,
                "fontname": "FixtureFont",
                "size": 9.0,
            },
        ]

        groups = extract_text_frames._line_groups(chars, 600.0)
        self.assertEqual(len(groups), 1)
        record = extract_text_frames._line_record(groups[0])
        self.assertEqual(record["text"], "Significance")
        self.assertNotIn("ﬁ", record["text"])

    def test_shifted_ligature_is_not_stolen_by_interleaved_other_column(self) -> None:
        # Reduced from Sjøgård et al. Main p2: the right-column line is
        # vertically between the shifted ﬁ and the remainder of the true
        # left-column line. A streaming expanded tolerance can therefore put
        # the ligature into the wrong column before horizontal splitting.
        chars = [
            {
                "text": "right column line",
                "x0": 300.0,
                "x1": 520.0,
                "top": 521.56,
                "bottom": 530.06,
                "fontname": "FixtureFont",
                "size": 9.5,
            },
            {
                "text": "ﬁ",
                "x0": 102.16,
                "x1": 107.21,
                "top": 524.65,
                "bottom": 534.15,
                "fontname": "FixtureFont",
                "size": 9.5,
            },
            {
                "text": "EEG, and MEG ",
                "x0": 42.0,
                "x1": 102.16,
                "top": 527.09,
                "bottom": 536.59,
                "fontname": "FixtureFont",
                "size": 9.5,
            },
            {
                "text": "ndings that memory consolidation is associated",
                "x0": 107.21,
                "x1": 285.0,
                "top": 527.09,
                "bottom": 536.59,
                "fontname": "FixtureFont",
                "size": 9.5,
            },
        ]

        groups = extract_text_frames._line_groups(chars, 600.0)
        records = [extract_text_frames._line_record(group)["text"] for group in groups]
        self.assertIn("right column line", records)
        self.assertIn("EEG, and MEG findings that memory consolidation is associated", records)
        self.assertNotIn("fi", records)
        self.assertEqual(len(records), 2)


if __name__ == "__main__":
    unittest.main()
