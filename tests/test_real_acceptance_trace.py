from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import workflow_state as state


class RealAcceptanceTraceTests(unittest.TestCase):
    """Protect the factual state of the suspended Mullins 2025 acceptance trace."""

    def test_mullins_trace_remains_valid_and_unfabricated(self) -> None:
        # The active week can be reassigned to another paper. Keep this actual
        # historical trace fixed rather than enforcing Mullins on current data.
        manifest = ROOT / "tests" / "fixtures" / "legacy" / "mullins_2026_w34_manifest.yaml"
        before = manifest.read_bytes()
        data = state.load_manifest(manifest)

        self.assertEqual(data["paper_id"], "10.1111-jsr.14281")
        self.assertEqual(data["stages"]["topic"]["status"], "COMPLETE")
        self.assertEqual(data["stages"]["search"]["status"], "PROVISIONAL")
        self.assertEqual(data["stages"]["translation"]["status"], "BLOCKED")
        self.assertEqual(data["stages"]["deep_reading"]["status"], "NOT_STARTED")
        self.assertEqual(data["outputs"]["A"]["status"], "BLOCKED")
        self.assertEqual(data["outputs"]["B"]["status"], "NOT_STARTED")
        self.assertEqual(data["outputs"]["C"]["status"], "NOT_STARTED")

        blocker_types = {
            item["type"]
            for item in data["blocking_issues"]
            if item.get("stage") == "translation"
        }
        self.assertIn("SOURCE_BINARY_UNAVAILABLE", blocker_types)
        self.assertTrue(data["pending_zotero_actions"])
        self.assertEqual(data["source_change"]["last_checked"], "2026-08-21")
        self.assertEqual(data["contract_version"], "1.4.1")
        self.assertEqual(manifest.read_bytes(), before)

    def test_current_week_can_change_paper_without_changing_historical_trace(self) -> None:
        manifest = ROOT / "weekly_reviews" / "2026" / "2026-W34" / "workflow_manifest.yaml"
        before = manifest.read_bytes()
        current = state.load_manifest(manifest)
        self.assertEqual(current["week"], "2026-W34")
        self.assertTrue(current["paper_id"])
        self.assertEqual(manifest.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
