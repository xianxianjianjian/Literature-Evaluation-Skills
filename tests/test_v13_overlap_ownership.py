from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_translation_package_v13 as validator


def frame(frame_id: str, bbox: list[float]) -> tuple[str, dict]:
    return frame_id, {"frame_id": frame_id, "bbox_pt": bbox}


class OverlapOwnershipTests(unittest.TestCase):
    def test_single_owner_is_preserved(self) -> None:
        owner = validator._select_owner([frame("A", [0, 0, 20, 20])])
        self.assertIsNotNone(owner)
        self.assertEqual(owner[0], "A")

    def test_unique_smallest_overlapping_frame_owns_glyph(self) -> None:
        owner = validator._select_owner(
            [
                frame("large", [0, 0, 100, 100]),
                frame("small", [10, 10, 30, 30]),
            ]
        )
        self.assertIsNotNone(owner)
        self.assertEqual(owner[0], "small")

    def test_equal_area_overlap_remains_ambiguous(self) -> None:
        owner = validator._select_owner(
            [
                frame("A", [0, 0, 20, 20]),
                frame("B", [5, 5, 25, 25]),
            ]
        )
        self.assertIsNone(owner)

    def test_glyph_center_can_be_owned_when_metric_bbox_overhangs(self) -> None:
        candidate = {"bbox_pt": [10, 10, 30, 30]}
        self.assertTrue(
            validator._center_in_frame(candidate, [9.7, 15, 20, 25])
        )


if __name__ == "__main__":
    unittest.main()
