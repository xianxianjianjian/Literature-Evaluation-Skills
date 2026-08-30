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


if __name__ == "__main__":
    unittest.main()
