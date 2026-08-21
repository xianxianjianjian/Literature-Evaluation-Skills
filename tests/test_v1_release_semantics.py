from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import history_manager as history
import validate_deliverables as validator
import workflow_state as state


class UsableV1ReleaseSemanticsTests(unittest.TestCase):
    def _academic_complete_manifest(self) -> dict:
        data = state.initial_manifest("2026-W34")
        data["paper_id"] = "paper-academic-complete"
        for stage in state.STAGE_NAMES:
            data["stages"][stage]["status"] = "COMPLETE"
        data["outputs"]["A"] = {
            "status": "COMPLETE",
            "zotero_attachment_key": None,
        }
        data["outputs"]["B"] = {
            "status": "COMPLETE",
            "zotero_attachment_key": None,
        }
        data["outputs"]["C"] = {
            "status": "COMPLETE",
            "git_path": "weekly_reviews/2026/2026-W34/weekly_review.md",
        }
        data["pending_zotero_actions"] = [
            {"action": "attach", "source_id": "SRC-M1"},
            {"action": "attach", "source_id": "A"},
            {"action": "attach", "source_id": "B"},
        ]
        data["source_change"]["last_checked"] = "2026-08-21"
        return data

    def test_academic_completion_passes_with_archive_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow_manifest.yaml"
            state.write_manifest(path, self._academic_complete_manifest())
            checks = validator.check_manifest(path, require_academic_complete=True)
            failures = [check.detail for check in checks if not check.passed]
            self.assertEqual(failures, [])

    def test_archive_completion_remains_strict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow_manifest.yaml"
            state.write_manifest(path, self._academic_complete_manifest())
            checks = validator.check_manifest(path, require_archive_complete=True)
            failed_names = {check.name for check in checks if not check.passed}
            self.assertIn("archive:A-zotero-key", failed_names)
            self.assertIn("archive:B-zotero-key", failed_names)
            self.assertIn("workflow:no-pending-zotero", failed_names)

    def test_completed_reading_history_does_not_require_zotero_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "workflow_manifest.yaml"
            state.write_manifest(manifest, self._academic_complete_manifest())
            record = {field: "" for field in history.READING_FIELDS}
            record.update(
                {
                    "Week": "2026-W34",
                    "Paper_ID": "paper-academic-complete",
                    "Title": "Synthetic Completed Reading",
                    "DOI": "10.0000/academic.complete",
                    "Completed_Date": "2026-08-21",
                }
            )
            verified = history.verify_completed_reading_manifest(manifest, record)
            self.assertEqual(verified["stages"]["deep_reading"]["status"], "COMPLETE")
            self.assertIsNone(verified["outputs"]["B"]["zotero_attachment_key"])

    def test_reading_history_still_rejects_real_academic_provisional_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = self._academic_complete_manifest()
            data["stages"]["deep_reading"]["status"] = "PROVISIONAL"
            data["outputs"]["B"]["status"] = "PROVISIONAL"
            manifest = root / "workflow_manifest.yaml"
            state.write_manifest(manifest, data)
            record = {field: "" for field in history.READING_FIELDS}
            record.update(
                {
                    "Week": "2026-W34",
                    "Paper_ID": "paper-academic-complete",
                    "Title": "Synthetic Incomplete Reading",
                    "DOI": "10.0000/academic.incomplete",
                    "Completed_Date": "2026-08-21",
                }
            )
            with self.assertRaises(history.HistoryError):
                history.verify_completed_reading_manifest(manifest, record)

    def test_scope_freeze_document_exists(self) -> None:
        self.assertTrue((ROOT / "docs" / "v1-scope-freeze.md").is_file())

    def test_reading_history_schema_allows_empty_archive_fields(self) -> None:
        path = ROOT / "knowledge" / "reading_history.csv"
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            header = next(csv.reader(handle))
        self.assertIn("Zotero_Item_Key", header)
        self.assertIn("A_Attachment_Key", header)
        self.assertIn("B_Attachment_Key", header)


if __name__ == "__main__":
    unittest.main()
