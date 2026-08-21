from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import zotero_local_archive as archive
import zotero_local_write as local


class AttachmentPlanningTests(unittest.TestCase):
    def _descriptor(self) -> dict:
        return {"filename": "paper.pdf", "md5": "abcd"}

    def _child(self, *, key="ATCH0001", filename="", md5="", title="[A] Translation") -> dict:
        return {
            "key": key,
            "data": {
                "key": key,
                "itemType": "attachment",
                "parentItem": "PARENT01",
                "linkMode": "imported_file",
                "title": title,
                "filename": filename,
                "md5": md5,
            },
        }

    def test_no_same_title_child_plans_new(self) -> None:
        plan = archive.plan_attachment(
            [], parent_key="PARENT01", title="[A] Translation", descriptor=self._descriptor()
        )
        self.assertEqual(plan["action"], "NEW")

    def test_exact_existing_file_is_idempotent(self) -> None:
        plan = archive.plan_attachment(
            [self._child(filename="paper.pdf", md5="ABCD")],
            parent_key="PARENT01",
            title="[A] Translation",
            descriptor=self._descriptor(),
        )
        self.assertEqual(plan["action"], "ALREADY_VERIFIED")
        self.assertEqual(plan["candidate"]["key"], "ATCH0001")

    def test_empty_same_title_child_is_reused_after_interruption(self) -> None:
        plan = archive.plan_attachment(
            [self._child()],
            parent_key="PARENT01",
            title="[A] Translation",
            descriptor=self._descriptor(),
        )
        self.assertEqual(plan["action"], "REUSE_PARTIAL")

    def test_same_title_different_file_is_conflict(self) -> None:
        plan = archive.plan_attachment(
            [self._child(filename="old.pdf", md5="ffff")],
            parent_key="PARENT01",
            title="[A] Translation",
            descriptor=self._descriptor(),
        )
        self.assertEqual(plan["action"], "CONFLICT")
        self.assertEqual(plan["reason"], "SAME_TITLE_ATTACHMENT_HAS_DIFFERENT_FILE")

    def test_multiple_same_title_children_are_ambiguous(self) -> None:
        plan = archive.plan_attachment(
            [self._child(key="ATCH0001"), self._child(key="ATCH0002")],
            parent_key="PARENT01",
            title="[A] Translation",
            descriptor=self._descriptor(),
        )
        self.assertEqual(plan["action"], "CONFLICT")
        self.assertEqual(plan["reason"], "MULTIPLE_SAME_TITLE_ATTACHMENTS")


class DurableAttachmentTests(unittest.TestCase):
    def _file(self, root: Path) -> Path:
        path = root / "paper.pdf"
        path.write_bytes(b"%PDF-1.4\nsynthetic durable attachment")
        return path

    def _client(self) -> local.LocalWriteClient:
        return local.LocalWriteClient(
            api_base_url=local.DEFAULT_API_BASE_URL,
            server_id="SERVER123",
            api_key="KEY",
            remembered=True,
        )

    def _partial_child(self) -> dict:
        return {
            "key": "ATCH0001",
            "data": {
                "key": "ATCH0001",
                "itemType": "attachment",
                "parentItem": "PARENT01",
                "linkMode": "imported_file",
                "title": "[ORIGINAL] Main Article",
                "filename": "",
                "md5": None,
            },
        }

    def test_new_child_uploads_and_returns_json_safe_descriptor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._file(Path(tmp))
            verified = {"data": {"key": "ATCH0001"}}
            with (
                patch.object(archive, "read_parent", return_value={"data": {"itemType": "journalArticle"}}),
                patch.object(archive, "read_children", return_value=[]),
                patch.object(local, "create_attachment_item", return_value="ATCH0001") as create,
                patch.object(local, "upload_file_to_attachment", return_value=(local.file_descriptor(path), verified)) as upload,
            ):
                result = archive.attach_file(
                    self._client(),
                    "users/0",
                    parent_key="PARENT01",
                    path=path,
                    title="[ORIGINAL] Main Article",
                )
        self.assertEqual(result["status"], "ATTACHED_AND_VERIFIED")
        self.assertEqual(result["attachment_key"], "ATCH0001")
        self.assertIsInstance(result["descriptor"]["path"], str)
        create.assert_called_once()
        upload.assert_called_once()

    def test_partial_child_is_reused_without_creating_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._file(Path(tmp))
            with (
                patch.object(archive, "read_parent", return_value={}),
                patch.object(archive, "read_children", return_value=[self._partial_child()]),
                patch.object(local, "create_attachment_item") as create,
                patch.object(
                    local,
                    "upload_file_to_attachment",
                    return_value=(local.file_descriptor(path), {"data": {"key": "ATCH0001"}}),
                ) as upload,
            ):
                result = archive.attach_file(
                    self._client(),
                    "users/0",
                    parent_key="PARENT01",
                    path=path,
                    title="[ORIGINAL] Main Article",
                )
        self.assertEqual(result["status"], "ATTACHED_AND_VERIFIED")
        self.assertTrue(result["reused_partial_child"])
        self.assertEqual(result["attachment_key"], "ATCH0001")
        create.assert_not_called()
        upload.assert_called_once()

    def test_exact_existing_attachment_never_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._file(Path(tmp))
            descriptor = local.file_descriptor(path)
            existing = self._partial_child()
            existing["data"]["filename"] = descriptor["filename"]
            existing["data"]["md5"] = descriptor["md5"]
            with (
                patch.object(archive, "read_parent", return_value={}),
                patch.object(archive, "read_children", return_value=[existing]),
                patch.object(local, "create_attachment_item") as create,
                patch.object(local, "upload_file_to_attachment") as upload,
            ):
                result = archive.attach_file(
                    self._client(),
                    "users/0",
                    parent_key="PARENT01",
                    path=path,
                    title="[ORIGINAL] Main Article",
                )
        self.assertEqual(result["status"], "ALREADY_ATTACHED_AND_VERIFIED")
        self.assertEqual(result["attachment_key"], "ATCH0001")
        create.assert_not_called()
        upload.assert_not_called()

    def test_conflict_never_overwrites_existing_child(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._file(Path(tmp))
            existing = self._partial_child()
            existing["data"]["filename"] = "different.pdf"
            existing["data"]["md5"] = "ffff"
            with (
                patch.object(archive, "read_parent", return_value={}),
                patch.object(archive, "read_children", return_value=[existing]),
                patch.object(local, "create_attachment_item") as create,
                patch.object(local, "upload_file_to_attachment") as upload,
            ):
                result = archive.attach_file(
                    self._client(),
                    "users/0",
                    parent_key="PARENT01",
                    path=path,
                    title="[ORIGINAL] Main Article",
                )
        self.assertEqual(result["status"], "ATTACHMENT_CONFLICT")
        create.assert_not_called()
        upload.assert_not_called()

    def test_upload_failure_preserves_created_child_key_for_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._file(Path(tmp))
            with (
                patch.object(archive, "read_parent", return_value={}),
                patch.object(archive, "read_children", return_value=[]),
                patch.object(local, "create_attachment_item", return_value="ATCHFAIL"),
                patch.object(
                    local,
                    "upload_file_to_attachment",
                    side_effect=local.LocalAPIError("synthetic upload failure"),
                ),
            ):
                result = archive.attach_file(
                    self._client(),
                    "users/0",
                    parent_key="PARENT01",
                    path=path,
                    title="[ORIGINAL] Main Article",
                )
        self.assertEqual(result["status"], "ATTACHMENT_FILE_UPLOAD_INCOMPLETE")
        self.assertEqual(result["attachment_key"], "ATCHFAIL")
        self.assertIn("synthetic upload failure", result["error"])

    def test_server_identity_mismatch_stops_archive_read(self) -> None:
        client = self._client()
        with patch.object(local, "http_result", return_value=(412, b"mismatch", {})):
            with self.assertRaises(archive.ArchiveError):
                archive.server_bound_get(client, "/users/0/items/PARENT01")


if __name__ == "__main__":
    unittest.main()
