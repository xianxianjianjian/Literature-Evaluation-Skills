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
    def _complete(self, *, zotero_keys: bool = True) -> dict:
        data = state.initial_manifest("2026-W34")
        data["paper_id"] = "10.0000/full"
        for name in state.STAGE_NAMES:
            data["stages"][name]["status"] = "COMPLETE"
        data["outputs"]["A"] = {
            "status": "COMPLETE",
            "zotero_attachment_key": "AKEY" if zotero_keys else None,
        }
        data["outputs"]["B"] = {
            "status": "COMPLETE",
            "zotero_attachment_key": "BKEY" if zotero_keys else None,
        }
        data["outputs"]["C"] = {
            "status": "COMPLETE",
            "git_path": "weekly_reviews/2026/2026-W34/weekly_review.md",
        }
        data["source_change"]["last_checked"] = "2026-08-21"
        return data

    def _check(
        self,
        data: dict,
        *,
        academic: bool = False,
        archive: bool = False,
        legacy: bool = False,
    ) -> list[validator.Check]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.yaml"
            state.write_manifest(path, data)
            return validator.check_manifest(
                path,
                require_academic_complete=academic,
                require_archive_complete=archive,
                require_workflow_complete=legacy,
            )

    def test_academic_complete_allows_pending_zotero_and_missing_archive_keys(self) -> None:
        data = self._complete(zotero_keys=False)
        data["pending_zotero_actions"] = [
            {"action": "attach", "source_id": "SRC-M1"},
            {"action": "attach", "source_id": "A"},
            {"action": "attach", "source_id": "B"},
        ]
        failures = [c.detail for c in self._check(data, academic=True) if not c.passed]
        self.assertFalse(failures, failures)

    def test_archive_complete_requires_zotero_keys_and_no_pending_actions(self) -> None:
        data = self._complete(zotero_keys=False)
        data["pending_zotero_actions"] = [{"action": "attach", "source_id": "SRC-M1"}]
        checks = self._check(data, archive=True)
        self.assertFalse(next(c for c in checks if c.name == "archive:A-zotero-key").passed)
        self.assertFalse(next(c for c in checks if c.name == "archive:B-zotero-key").passed)
        self.assertFalse(next(c for c in checks if c.name == "workflow:no-pending-zotero").passed)

    def test_archive_complete_passes_with_verified_keys(self) -> None:
        failures = [c.detail for c in self._check(self._complete(), archive=True) if not c.passed]
        self.assertFalse(failures, failures)

    def test_legacy_workflow_complete_remains_archive_strict(self) -> None:
        data = self._complete(zotero_keys=False)
        checks = self._check(data, legacy=True)
        target = next(c for c in checks if c.name == "archive:A-zotero-key")
        self.assertFalse(target.passed)

    def test_needs_update_prevents_academic_completion(self) -> None:
        data = self._complete(zotero_keys=False)
        data["stages"]["deep_reading"]["needs_update"] = True
        data["stages"]["deep_reading"]["update_reason"] = ["New SI"]
        checks = self._check(data, academic=True)
        target = next(c for c in checks if c.name == "academic:no-needs-update")
        self.assertFalse(target.passed)

    def test_complete_a_cannot_pair_with_incomplete_translation(self) -> None:
        data = self._complete(zotero_keys=False)
        data["stages"]["translation"]["status"] = "PROVISIONAL"
        checks = self._check(data)
        target = next(c for c in checks if c.name == "manifest:A-translation")
        self.assertFalse(target.passed)


if __name__ == "__main__":
    unittest.main()
