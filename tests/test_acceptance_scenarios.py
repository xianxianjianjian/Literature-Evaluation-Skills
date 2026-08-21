from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import mirror_pdf
import validate_deliverables as validator
import workflow_state as state


class SyntheticAcceptanceScenarios(unittest.TestCase):
    """Copyright-free structural acceptance scenarios for the frozen V1 contract.

    These tests protect routing/state/deliverable-helper behavior. They do not
    replace real-paper scientific acceptance, source audit, or visual QA.
    """

    def _write_manifest(self, root: Path, data: dict) -> Path:
        path = root / "workflow_manifest.yaml"
        state.write_manifest(path, data)
        return path

    def _assert_manifest_checks_pass(self, path: Path) -> None:
        checks = validator.check_manifest(path)
        failures = [check.detail for check in checks if not check.passed]
        self.assertFalse(failures, failures)

    def _fully_complete_manifest(self) -> dict:
        data = state.initial_manifest("2026-W34")
        data["paper_id"] = "10.0000-synthetic.t01"
        for stage in state.STAGE_NAMES:
            data["stages"][stage]["status"] = "COMPLETE"
        data["outputs"]["A"] = {
            "status": "COMPLETE",
            "zotero_attachment_key": "AKEY0001",
        }
        data["outputs"]["B"] = {
            "status": "COMPLETE",
            "zotero_attachment_key": "BKEY0001",
        }
        data["outputs"]["C"] = {
            "status": "COMPLETE",
            "git_path": "weekly_reviews/2026/2026-W34/weekly_review.md",
        }
        data["source_change"]["last_checked"] = "2026-08-21"
        return data

    def test_t01_ordinary_empirical_without_si_can_close_structurally(self) -> None:
        data = self._fully_complete_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_manifest(Path(tmp), data)
            self._assert_manifest_checks_pass(path)

    def test_t02_many_figures_tables_preserve_layout_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.pdf"
            source.write_bytes(b"%PDF-1.4\nsynthetic")
            page_map = root / "page_map.json"
            page_map.write_text(
                json.dumps(
                    {
                        "pages": [
                            {
                                "page_number": 1,
                                "text_blocks": [{"id": "p1"}],
                                "figure_placeholders": [
                                    {"id": "f1"}, {"id": "f2"}, {"id": "f3"}
                                ],
                                "table_placeholders": [{"id": "t1"}, {"id": "t2"}],
                            },
                            {
                                "page_number": 2,
                                "text_blocks": [{"id": "p2"}],
                                "figure_placeholders": [{"id": "f4"}],
                                "table_placeholders": [{"id": "t3"}],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                source_pdf=source,
                page_map=page_map,
                output_pdf=root / "A.pdf",
                strategy="strict-mirror",
                font_scale=1.10,
            )
            plan = mirror_pdf.create_plan(args)
            self.assertEqual(len(plan["pages"]), 2)
            self.assertEqual(len(plan["pages"][0]["figure_placeholders"]), 3)
            self.assertEqual(len(plan["pages"][0]["table_placeholders"]), 2)
            self.assertTrue(plan["layout_qc"]["visual_inspection_required"])

    def test_t03_main_plus_complex_si_can_remain_one_consistent_workflow(self) -> None:
        data = self._fully_complete_manifest()
        data["paper_id"] = "10.0000-synthetic.t03"
        # Complex SI is represented by source/evidence artifacts, not by inventing
        # extra workflow states. The manifest remains the single workflow truth.
        data["pending_zotero_actions"] = []
        validated = state.validate_manifest(data)
        self.assertEqual(validated["paper_id"], "10.0000-synthetic.t03")
        self.assertEqual(validated["stages"]["translation"]["status"], "COMPLETE")
        self.assertEqual(validated["stages"]["deep_reading"]["status"], "COMPLETE")

    def test_t04_missing_si_provisional_then_upgrade(self) -> None:
        data = state.initial_manifest("2026-W34")
        data["paper_id"] = "10.0000-synthetic.t04"
        data["stages"]["topic"]["status"] = "COMPLETE"
        data["stages"]["search"]["status"] = "PROVISIONAL"
        data["stages"]["translation"]["status"] = "PROVISIONAL"
        data["stages"]["deep_reading"]["status"] = "PROVISIONAL"
        data["outputs"]["A"]["status"] = "PROVISIONAL"
        data["outputs"]["B"]["status"] = "PROVISIONAL"
        data["outputs"]["C"] = {
            "status": "COMPLETE",
            "git_path": "weekly_reviews/2026/2026-W34/weekly_review.md",
        }
        data["pending_zotero_actions"].append(
            {"action": "attach", "source_id": "SRC-S1", "reason": "SI unavailable"}
        )
        state.validate_manifest(data)

        # SI later arrives: affected stages are explicitly reopened, then closed.
        data["stages"]["translation"]["needs_update"] = True
        data["stages"]["translation"]["update_reason"] = ["New SI SRC-S1 available"]
        data["stages"]["deep_reading"]["needs_update"] = True
        data["stages"]["deep_reading"]["update_reason"] = ["New SI affects methods/results audit"]
        state.validate_manifest(data)

        data["pending_zotero_actions"] = []
        data["stages"]["search"]["status"] = "COMPLETE"
        for stage_name in ("translation", "deep_reading"):
            data["stages"][stage_name]["status"] = "COMPLETE"
            data["stages"][stage_name]["needs_update"] = False
            data["stages"][stage_name]["update_reason"] = []
        data["outputs"]["A"] = {
            "status": "COMPLETE",
            "zotero_attachment_key": "AKEYT04",
        }
        data["outputs"]["B"] = {
            "status": "COMPLETE",
            "zotero_attachment_key": "BKEYT04",
        }
        state.validate_manifest(data)

    def test_search_only_is_valid_without_translation_or_deep_reading(self) -> None:
        data = state.initial_manifest("2026-W34")
        data["paper_id"] = "10.0000-search.only"
        data["stages"]["topic"]["status"] = "COMPLETE"
        data["stages"]["search"]["status"] = "COMPLETE"
        validated = state.validate_manifest(data)
        self.assertEqual(validated["stages"]["translation"]["status"], "NOT_STARTED")

    def test_translation_only_is_valid_after_minimal_intake(self) -> None:
        data = state.initial_manifest("2026-W34")
        data["paper_id"] = "10.0000-translation.only"
        data["stages"]["translation"]["status"] = "IN_PROGRESS"
        validated = state.validate_manifest(data)
        self.assertEqual(validated["stages"]["search"]["status"], "NOT_STARTED")

    def test_deep_reading_only_does_not_require_a(self) -> None:
        data = state.initial_manifest("2026-W34")
        data["paper_id"] = "10.0000-deep.only"
        data["stages"]["deep_reading"]["status"] = "IN_PROGRESS"
        validated = state.validate_manifest(data)
        self.assertEqual(validated["outputs"]["A"]["status"], "NOT_STARTED")

    def test_resume_from_blocker_requires_explicit_blocker_record(self) -> None:
        data = state.initial_manifest("2026-W34")
        data["paper_id"] = "10.0000-resume"
        data["stages"]["translation"]["status"] = "BLOCKED"
        data["blocking_issues"].append(
            {
                "stage": "translation",
                "type": "SOURCE_BINARY_UNAVAILABLE",
                "detail": "Synthetic source PDF missing",
                "source_id": "SRC-M1",
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_manifest(Path(tmp), data)
            self._assert_manifest_checks_pass(path)

    def test_zotero_downgrade_uses_provisional_and_pending_actions(self) -> None:
        data = state.initial_manifest("2026-W34")
        data["paper_id"] = "10.0000-zotero.down"
        data["stages"]["search"]["status"] = "PROVISIONAL"
        data["pending_zotero_actions"] = [
            {"action": "find_or_create_parent", "paper_id": data["paper_id"]},
            {"action": "attach", "source_id": "SRC-M1"},
        ]
        validated = state.validate_manifest(data)
        self.assertEqual(len(validated["pending_zotero_actions"]), 2)
        self.assertEqual(validated["stages"]["search"]["status"], "PROVISIONAL")

    def test_new_si_marks_only_affected_stages_for_update(self) -> None:
        data = self._fully_complete_manifest()
        data["stages"]["translation"]["needs_update"] = True
        data["stages"]["translation"]["update_reason"] = ["New SI SRC-S2"]
        data["stages"]["deep_reading"]["needs_update"] = True
        data["stages"]["deep_reading"]["update_reason"] = ["SRC-S2 changes method audit"]
        validated = state.validate_manifest(data)
        self.assertFalse(validated["stages"]["search"]["needs_update"])
        self.assertTrue(validated["stages"]["translation"]["needs_update"])
        self.assertTrue(validated["stages"]["deep_reading"]["needs_update"])


if __name__ == "__main__":
    unittest.main()
