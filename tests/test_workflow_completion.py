from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_deliverables as validator
import workflow_state as state


class FullWorkflowCompletionTests(unittest.TestCase):
    def _complete(self) -> dict:
        data = state.initial_manifest("2026-W34")
        data["paper_id"] = "10.0000/full"
        for name in state.STAGE_NAMES:
            data["stages"][name]["status"] = "COMPLETE"
        data["outputs"]["A"] = {
            "status": "COMPLETE",
            "zotero_attachment_key": "AKEY",
        }
        data["outputs"]["B"] = {
            "status": "COMPLETE",
            "zotero_attachment_key": "BKEY",
        }
        data["outputs"]["C"] = {
            "status": "COMPLETE",
            "git_path": "weekly_reviews/2026/2026-W34/weekly_review.md",
        }
        data["source_change"]["last_checked"] = "2026-08-21"
        return data

    def _check(self, data: dict) -> list[validator.Check]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.yaml"
            state.write_manifest(path, data)
            return validator.check_manifest(path, require_workflow_complete=True)

    def test_complete_workflow_passes_completion_checks(self) -> None:
        failures = [c.detail for c in self._check(self._complete()) if not c.passed]
        self.assertFalse(failures, failures)

    def test_pending_zotero_prevents_full_completion(self) -> None:
        data = self._complete()
        data["pending_zotero_actions"] = [{"action": "attach", "source_id": "SRC-M1"}]
        checks = self._check(data)
        target = next(c for c in checks if c.name == "workflow:no-pending-zotero")
        self.assertFalse(target.passed)

    def test_needs_update_prevents_full_completion(self) -> None:
        data = self._complete()
        data["stages"]["deep_reading"]["needs_update"] = True
        data["stages"]["deep_reading"]["update_reason"] = ["New SI"]
        checks = self._check(data)
        target = next(c for c in checks if c.name == "workflow:no-needs-update")
        self.assertFalse(target.passed)

    def test_complete_a_cannot_pair_with_incomplete_translation(self) -> None:
        data = self._complete()
        data["stages"]["translation"]["status"] = "PROVISIONAL"
        checks = self._check(data)
        target = next(c for c in checks if c.name == "manifest:A-translation")
        self.assertFalse(target.passed)


if __name__ == "__main__":
    unittest.main()
