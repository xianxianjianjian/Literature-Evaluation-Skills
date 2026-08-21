from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import workflow_state as state


class PaperIdentityStateTests(unittest.TestCase):
    def test_translation_cannot_start_without_paper_id(self) -> None:
        data = state.initial_manifest("2026-W34")
        data["stages"]["translation"]["status"] = "IN_PROGRESS"
        with self.assertRaises(state.WorkflowStateError):
            state.validate_manifest(data)

    def test_deep_reading_only_is_valid_after_minimal_intake_paper_id(self) -> None:
        data = state.initial_manifest("2026-W34")
        data["paper_id"] = "10.0000/deep-only"
        data["stages"]["deep_reading"]["status"] = "IN_PROGRESS"
        validated = state.validate_manifest(data)
        self.assertEqual(validated["paper_id"], "10.0000/deep-only")

    def test_search_complete_requires_selected_paper_id(self) -> None:
        data = state.initial_manifest("2026-W34")
        data["stages"]["search"]["status"] = "COMPLETE"
        with self.assertRaises(state.WorkflowStateError):
            state.validate_manifest(data)

    def test_output_cannot_start_without_paper_id(self) -> None:
        data = state.initial_manifest("2026-W34")
        data["outputs"]["C"]["status"] = "IN_PROGRESS"
        with self.assertRaises(state.WorkflowStateError):
            state.validate_manifest(data)


if __name__ == "__main__":
    unittest.main()
