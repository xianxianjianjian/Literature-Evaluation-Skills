from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import zotero_local_write as local


class LocalAPIDiscoveryTests(unittest.TestCase):
    def test_discover_server_requires_server_id(self) -> None:
        with patch.object(
            local,
            "http_result",
            return_value=(200, b"{}", {"Zotero-API-Version": "3"}),
        ):
            with self.assertRaises(local.LocalAPIError):
                local.discover_server()

    def test_discover_server_reads_v3_server_id(self) -> None:
        with patch.object(
            local,
            "http_result",
            return_value=(
                200,
                b"{}",
                {"Zotero-API-Version": "3", "Zotero-Server-ID": "SERVER123"},
            ),
        ):
            info = local.discover_server()
        self.assertEqual(info["server_id"], "SERVER123")
        self.assertEqual(info["api_version"], "3")

    def test_authorize_returns_key_without_printing_or_persisting(self) -> None:
        body = json.dumps({"key": "K" * 32, "remember": True}).encode()
        with patch.object(local, "http_result", return_value=(200, body, {})) as request:
            key, remembered = local.authorize_write(
                local.DEFAULT_API_BASE_URL,
                "SERVER123",
            )
        self.assertEqual(key, "K" * 32)
        self.assertTrue(remembered)
        sent_headers = request.call_args.kwargs["headers"]
        self.assertEqual(sent_headers["Zotero-Server-ID"], "SERVER123")
        self.assertNotIn("Zotero-API-Key", sent_headers)


class LocalWriteClientTests(unittest.TestCase):
    def test_request_reauthorizes_once_after_401(self) -> None:
        client = local.LocalWriteClient(
            api_base_url=local.DEFAULT_API_BASE_URL,
            server_id="SERVER123",
            api_key="OLD",
        )
        calls = [
            (401, b"unauthorized", {}),
            (200, b"{}", {}),
        ]
        with (
            patch.object(local, "http_result", side_effect=calls),
            patch.object(local, "authorize_write", return_value=("NEW", False)) as authorize,
        ):
            status, _, _ = client.request(
                "/users/0/items",
                method="POST",
                data=b"[]",
                expected_statuses={200},
            )
        self.assertEqual(status, 200)
        self.assertEqual(client.api_key, "NEW")
        authorize.assert_called_once()

    def test_create_attachment_item_uses_parent_and_imported_file(self) -> None:
        client = local.LocalWriteClient(
            api_base_url=local.DEFAULT_API_BASE_URL,
            server_id="SERVER123",
            api_key="KEY",
        )
        response = {
            "successful": {
                "0": {
                    "key": "ATCH1234",
                    "data": {"key": "ATCH1234"},
                }
            },
            "unchanged": {},
            "failed": {},
        }
        with patch.object(
            client,
            "request",
            return_value=(200, json.dumps(response).encode(), {}),
        ) as request:
            key = local.create_attachment_item(
                client,
                "users/0",
                parent_key="PARENT01",
                title="[A] 中文全文翻译镜像版",
            )
        self.assertEqual(key, "ATCH1234")
        posted = json.loads(request.call_args.kwargs["data"].decode())
        self.assertEqual(posted[0]["itemType"], "attachment")
        self.assertEqual(posted[0]["parentItem"], "PARENT01")
        self.assertEqual(posted[0]["linkMode"], "imported_file")


class FileUploadTests(unittest.TestCase):
    def _file(self, root: Path) -> Path:
        path = root / "artifact.pdf"
        path.write_bytes(b"%PDF-1.4\nsynthetic artifact bytes")
        return path

    def test_file_descriptor_computes_protocol_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._file(Path(tmp))
            descriptor = local.file_descriptor(path)
            self.assertEqual(descriptor["filename"], "artifact.pdf")
            self.assertEqual(descriptor["filesize"], path.stat().st_size)
            self.assertEqual(
                descriptor["md5"], hashlib.md5(path.read_bytes()).hexdigest()
            )
            self.assertEqual(descriptor["content_type"], "application/pdf")
            self.assertIsInstance(descriptor["mtime"], int)

    def test_upload_authorization_posts_if_none_match(self) -> None:
        client = local.LocalWriteClient(
            api_base_url=local.DEFAULT_API_BASE_URL,
            server_id="SERVER123",
            api_key="KEY",
        )
        descriptor = {
            "md5": "abc",
            "filename": "a.pdf",
            "filesize": 12,
            "mtime": 123456,
        }
        auth = {
            "url": "/api/local/uploads/UPLOAD1",
            "uploadKey": "UPLOAD1",
            "contentType": "application/pdf",
            "prefix": "",
            "suffix": "",
        }
        with patch.object(
            client,
            "request",
            return_value=(200, json.dumps(auth).encode(), {}),
        ) as request:
            payload = local.upload_authorization(
                client,
                "users/0",
                "ATCH1234",
                descriptor,
            )
        self.assertEqual(payload["uploadKey"], "UPLOAD1")
        self.assertEqual(request.call_args.kwargs["headers"]["If-None-Match"], "*")
        body = request.call_args.kwargs["data"].decode()
        self.assertIn("md5=abc", body)
        self.assertIn("filename=a.pdf", body)

    def test_send_authorized_upload_posts_file_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._file(Path(tmp))
            descriptor = local.file_descriptor(path)
            authorization = {
                "url": "/api/local/uploads/UPLOAD1",
                "uploadKey": "UPLOAD1",
                "contentType": "application/pdf",
                "prefix": "",
                "suffix": "",
            }
            with patch.object(local, "http_result", return_value=(201, b"", {})) as request:
                upload_key = local.send_authorized_upload(
                    local.DEFAULT_API_BASE_URL,
                    descriptor,
                    authorization,
                    timeout=1.0,
                )
            self.assertEqual(upload_key, "UPLOAD1")
            self.assertEqual(request.call_args.kwargs["data"], path.read_bytes())
            self.assertEqual(
                request.call_args.kwargs["headers"]["Content-Type"],
                "application/pdf",
            )

    def test_exists_short_circuits_byte_upload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            descriptor = local.file_descriptor(self._file(Path(tmp)))
            with patch.object(local, "http_result") as request:
                upload_key = local.send_authorized_upload(
                    local.DEFAULT_API_BASE_URL,
                    descriptor,
                    {"exists": 1},
                    timeout=1.0,
                )
            self.assertIsNone(upload_key)
            request.assert_not_called()

    def test_register_upload_requires_204(self) -> None:
        client = local.LocalWriteClient(
            api_base_url=local.DEFAULT_API_BASE_URL,
            server_id="SERVER123",
            api_key="KEY",
        )
        with patch.object(client, "request", return_value=(204, b"", {})) as request:
            local.register_upload(client, "users/0", "ATCH1234", "UPLOAD1")
        self.assertEqual(request.call_args.kwargs["expected_statuses"], {204})
        self.assertEqual(request.call_args.kwargs["headers"]["If-None-Match"], "*")

    def test_verify_attachment_requires_parent_filename_and_md5(self) -> None:
        descriptor = {
            "filename": "artifact.pdf",
            "md5": "abcd",
        }
        item = {
            "data": {
                "itemType": "attachment",
                "parentItem": "PARENT01",
                "linkMode": "imported_file",
                "filename": "artifact.pdf",
                "md5": "ABCD",
            }
        }
        with patch.object(local, "read_item", return_value=item):
            verified = local.verify_attachment(
                local.DEFAULT_API_BASE_URL,
                "users/0",
                "ATCH1234",
                parent_key="PARENT01",
                descriptor=descriptor,
            )
        self.assertEqual(verified, item)

    def test_upload_file_to_attachment_runs_three_phase_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._file(Path(tmp))
            client = local.LocalWriteClient(
                api_base_url=local.DEFAULT_API_BASE_URL,
                server_id="SERVER123",
                api_key="KEY",
            )
            auth = {
                "url": "/api/local/uploads/UPLOAD1",
                "uploadKey": "UPLOAD1",
                "contentType": "application/pdf",
                "prefix": "",
                "suffix": "",
            }
            verified = {"data": {"key": "ATCH1234"}}
            with (
                patch.object(local, "upload_authorization", return_value=auth) as authorize,
                patch.object(local, "send_authorized_upload", return_value="UPLOAD1") as upload,
                patch.object(local, "register_upload") as register,
                patch.object(local, "verify_attachment", return_value=verified) as verify,
            ):
                descriptor, result = local.upload_file_to_attachment(
                    client,
                    "users/0",
                    "ATCH1234",
                    path,
                    parent_key="PARENT01",
                )
            self.assertEqual(result, verified)
            self.assertEqual(descriptor["filename"], "artifact.pdf")
            authorize.assert_called_once()
            upload.assert_called_once()
            register.assert_called_once()
            verify.assert_called_once()


if __name__ == "__main__":
    unittest.main()
