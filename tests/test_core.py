from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import history_manager as history
import mirror_pdf
import terminology_registry as terms
import validate_deliverables as validator
import workflow_state as state
import zotero_bridge as zotero


class WorkflowStateTests(unittest.TestCase):
    def test_initial_manifest_contains_v1_resume_fields(self) -> None:
        data = state.initial_manifest("2026-W34")
        self.assertEqual(data["workflow_id"], "2026-W34-weekly-literature-evaluation")
        self.assertEqual(data["blocking_issues"], [])
        for stage in state.STAGE_NAMES:
            self.assertFalse(data["stages"][stage]["needs_update"])
            self.assertEqual(data["stages"][stage]["update_reason"], [])

    def test_waiting_user_is_reserved_for_two_gate_stages(self) -> None:
        data = state.initial_manifest("2026-W34")
        data["stages"]["translation"]["status"] = "WAITING_USER"
        with self.assertRaises(state.WorkflowStateError):
            state.validate_manifest(data)

    def test_older_manifest_is_additively_normalized(self) -> None:
        data = state.initial_manifest("2026-W34")
        del data["blocking_issues"]
        del data["stages"]["search"]["needs_update"]
        del data["stages"]["search"]["update_reason"]
        normalized = state.validate_manifest(data)
        self.assertEqual(normalized["blocking_issues"], [])
        self.assertFalse(normalized["stages"]["search"]["needs_update"])


class HistoryTests(unittest.TestCase):
    def _csv(self, path: Path, fields: list[str]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerow(fields)

    def test_selection_duplicate_scope_is_week_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "selection.csv"
            self._csv(path, history.SELECTION_FIELDS)
            base = {field: "" for field in history.SELECTION_FIELDS}
            base.update({
                "Week": "2026-W34",
                "Paper_ID": "10.1111-jsr.14281",
                "Title": "Paper",
                "DOI": "10.1111/jsr.14281",
            })
            history.append_record(path, history.SELECTION_FIELDS, base, record_type="selection")
            with self.assertRaises(history.HistoryError):
                history.append_record(path, history.SELECTION_FIELDS, base, record_type="selection")
            later = dict(base)
            later["Week"] = "2026-W35"
            history.append_record(path, history.SELECTION_FIELDS, later, record_type="selection")
            self.assertEqual(len(history.read_rows(path, history.SELECTION_FIELDS)), 2)

    def test_completed_reading_is_globally_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reading.csv"
            self._csv(path, history.READING_FIELDS)
            first = {field: "" for field in history.READING_FIELDS}
            first.update({
                "Week": "2026-W34",
                "Paper_ID": "paper-a",
                "Title": "Paper",
                "DOI": "10.1/example",
            })
            history.append_record(path, history.READING_FIELDS, first, record_type="reading")
            second = dict(first)
            second["Week"] = "2026-W35"
            with self.assertRaises(history.HistoryError):
                history.append_record(path, history.READING_FIELDS, second, record_type="reading")


class TerminologyTests(unittest.TestCase):
    def _empty_registry(self, path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerow(terms.FIELDS)

    def _args(self, path: Path, term_id: str, discipline: str, context: str) -> argparse.Namespace:
        return argparse.Namespace(
            registry=path,
            term_id=term_id,
            english_term="arousal",
            preferred_chinese="觉醒",
            abbreviation=None,
            alternative_chinese=None,
            discipline=discipline,
            subfield="sleep",
            definition=None,
            context=context,
            confidence="HIGH",
            evidence_level="TE4",
            evidence_ids="TERMEV-0001",
            status="ACTIVE",
            verified_date="2026-08-21",
            notes=None,
        )

    def test_same_english_term_can_exist_in_different_contexts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "terms.csv"
            self._empty_registry(path)
            terms.command_add(self._args(path, "TERM-0001", "sleep medicine", "PSG arousal"))
            terms.command_add(self._args(path, "TERM-0002", "psychology", "emotional arousal"))
            self.assertEqual(len(terms.read_registry(path)), 2)

    def test_equivalent_context_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "terms.csv"
            self._empty_registry(path)
            terms.command_add(self._args(path, "TERM-0001", "sleep medicine", "PSG arousal"))
            with self.assertRaises(terms.TerminologyError):
                terms.command_add(self._args(path, "TERM-0002", "sleep medicine", "PSG arousal"))


class DeliverableValidatorTests(unittest.TestCase):
    def test_comment_count_excludes_other_sections(self) -> None:
        markdown = "## 中文摘要\n" + ("摘要" * 600) + "\n## 评论\n真正评论内容\n## 评阅人\nX\n"
        comment = validator.extract_comment_section(markdown)
        self.assertEqual(comment, "真正评论内容")
        self.assertEqual(validator.effective_chinese_characters(comment), 6)

    def test_docx_base_schema_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "B.docx"
            text = "文献定位 摘要 引言 方法 结果 讨论 创新 局限 改进 迁移 术语"
            xml = (
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
            )
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", xml)
            result = validator.check_docx_b(path, required=True)
            self.assertTrue(result.passed, result.detail)


class MirrorPlanTests(unittest.TestCase):
    def test_plan_preserves_frozen_strategy_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "source.pdf"
            pdf.write_bytes(b"%PDF-1.4\nfixture")
            page_map = root / "map.json"
            page_map.write_text(json.dumps({"pages": [{}]}), encoding="utf-8")
            args = argparse.Namespace(
                source_pdf=pdf,
                page_map=page_map,
                output_pdf=root / "A.pdf",
                strategy="strict-mirror",
                font_scale=1.10,
            )
            plan = mirror_pdf.create_plan(args)
            self.assertEqual(
                plan["strategy_order"],
                ["strict-mirror", "adaptive-mirror", "readable-extension"],
            )
            self.assertEqual(plan["pages"][0]["adaptive_font_sizing"]["minimum_font_pt"], 8.5)
            mirror_pdf.validate_plan_data(plan)


class ZoteroBridgeTests(unittest.TestCase):
    def test_connector_availability_does_not_enable_unverified_writes(self) -> None:
        payload = zotero.status_payload(
            api_available=True,
            connector_available=True,
        )
        self.assertTrue(payload["local_api"]["available"])
        self.assertTrue(payload["connector"]["available"])
        self.assertFalse(payload["writes"]["enabled"])
        self.assertEqual(payload["writes"]["implemented"], [])
        self.assertEqual(
            payload["writes"]["reason"],
            "WRITE_ROUTE_NOT_IMPLEMENTED_OR_VERIFIED",
        )

    def test_pending_command_only_emits_manifest_template(self) -> None:
        args = argparse.Namespace(
            action="attach",
            paper_id="paper-1",
            reason="Zotero unavailable",
            source_id="SRC-M1",
            expected_attachment_name="[ORIGINAL] Main Article",
        )
        stream = StringIO()
        with redirect_stdout(stream):
            code = zotero.command_pending_template(args)
        payload = json.loads(stream.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["pending_zotero_action"]["action"], "attach")
        self.assertIn("does not modify Zotero", payload["note"])


if __name__ == "__main__":
    unittest.main()
