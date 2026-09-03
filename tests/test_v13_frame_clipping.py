from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import render_exact_mirror_v13 as renderer


class FakePath:
    def __init__(self) -> None:
        self.rectangles = []

    def rect(self, x: float, y: float, width: float, height: float) -> None:
        self.rectangles.append((x, y, width, height))


class FakeCanvas:
    def __init__(self) -> None:
        self.path = FakePath()
        self.clips = []

    def beginPath(self):
        return self.path

    def clipPath(self, path, stroke=1, fill=0):
        self.clips.append((path, stroke, fill))


class FrameClippingTests(unittest.TestCase):
    def test_clip_matches_exact_reviewed_bbox(self) -> None:
        canvas = FakeCanvas()
        frame = {"bbox_pt": [10.0, 20.0, 40.0, 55.0]}
        renderer._clip_to_frame(canvas, frame)

        self.assertEqual(canvas.path.rectangles, [(10.0, 20.0, 30.0, 35.0)])
        self.assertEqual(len(canvas.clips), 1)
        self.assertEqual(canvas.clips[0][1:], (0, 0))


if __name__ == "__main__":
    unittest.main()
