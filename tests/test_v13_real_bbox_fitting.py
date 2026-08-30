from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import render_exact_mirror

try:
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    FontBuilder = TTGlyphPen = pdfmetrics = TTFont = None


@unittest.skipIf(
    any(item is None for item in (FontBuilder, TTGlyphPen, pdfmetrics, TTFont)),
    "exact-mirror font dependencies are unavailable",
)
class RealPaperBBoxFittingTests(unittest.TestCase):
    def _fixture_font(self, root: Path) -> Path:
        # Non-copyright synthetic SimSun test double. Production SimSun is
        # validated separately on the Windows runner and is never redistributed.
        codepoints = set(range(32, 127)) | {ord("中")}
        glyph_order = [".notdef"] + [
            f"uni{codepoint:04X}" for codepoint in sorted(codepoints)
        ]
        cmap = {
            codepoint: f"uni{codepoint:04X}" for codepoint in sorted(codepoints)
        }
        glyphs = {}
        metrics = {}
        for glyph_name in glyph_order:
            pen = TTGlyphPen(None)
            if glyph_name != "uni0020":
                pen.moveTo((80, 0))
                pen.lineTo((80, 700))
                pen.lineTo((720, 700))
                pen.lineTo((720, 0))
                pen.closePath()
            glyphs[glyph_name] = pen.glyph()
            metrics[glyph_name] = (800, 0)

        builder = FontBuilder(1000, isTTF=True)
        builder.setupGlyphOrder(glyph_order)
        builder.setupCharacterMap(cmap)
        builder.setupGlyf(glyphs)
        builder.setupHorizontalMetrics(metrics)
        builder.setupHorizontalHeader(ascent=800, descent=-200)
        builder.setupOS2(
            sTypoAscender=800,
            sTypoDescender=-200,
            usWinAscent=800,
            usWinDescent=200,
        )
        builder.setupNameTable(
            {
                "familyName": "SimSun",
                "styleName": "Regular",
                "uniqueFontIdentifier": "Synthetic SimSun real-bbox fixture",
                "fullName": "SimSun",
                "psName": "SimSun",
                "version": "Version 1.0",
            }
        )
        builder.setupPost()
        builder.setupMaxp()
        output = root / "simsun.ttf"
        builder.save(str(output))
        return output

    def _frame(self) -> dict[str, object]:
        # Dimensions are rounded from a real supplementary-table text frame used
        # during the private release regression. No paper text is included.
        return {
            "bbox_pt": [41.4, 653.64064, 126.4376, 669.07864],
            "rotation": 0,
            "source_font_size_pt": 9.96,
            "source_leading_pt": 11.952,
        }

    def test_real_bbox_can_require_intermediate_97_percent_scale(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            font_path = self._fixture_font(Path(temporary))
            pdfmetrics.registerFont(TTFont("SimSun", str(font_path)))
            fitted = render_exact_mirror._layout("中" * 11, self._frame())
            self.assertIsNotNone(fitted)
            scale, lines = fitted
            self.assertEqual(scale, 0.97)
            self.assertEqual(len(lines), 1)

    def test_real_bbox_overflow_at_95_percent_is_not_silently_shrunk(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            font_path = self._fixture_font(Path(temporary))
            pdfmetrics.registerFont(TTFont("SimSun", str(font_path)))
            fitted = render_exact_mirror._layout("中" * 12, self._frame())
            self.assertIsNone(fitted)


if __name__ == "__main__":
    unittest.main()
