from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import zotero_bridge as zotero


class ZoteroParentCreateTests(unittest.TestCase):
    def _metadata_file(self, root: Path, **overrides) -> Path:
        metadata = {
            "itemType": "journalArticle",
            "title": "Synthetic Test Paper",
            "authors": [
                {
                    "firstName": "Ada",
                    "lastName": "Lovelace",
                    "creatorType": "author",
                }
            ],
            "journal": "Journal of Synthetic Tests",
            "year": "2026",
            "volume": "1",
            "issue": "2",
            "pages": "10-20",
            "doi": "https://doi.org/10.0000/SYNTHETIC.001",
            "url": "https://example.org/synthetic",
            "language": "en",
        }
        metadata.update(overrides)
        path = root / "metadata.json"
        path.write_text(json.dumps(metadata), encoding="utf-8")
        return path

    def _args(self, metadata: Path, *, yes: bool) -> argparse.Namespace:
        return argparse.Namespace(
            command="create",
            metadata=metadata,
            yes=yes,
            api_base_url="http://127.0.0.1:23119/api",
            connector_base_url="http://127.0.0.1:23119",
            timeout=1.0,
        )

    def test_metadata_maps_to_saveitems_payload(self) -> None:
        metadata = {
            "itemType": "journalArticle",
            "title": "Paper",
            "authors": [
                {"firstName": "Ada", "lastName": "Lovelace", "creatorType": "author"}
            ],
            "journal": "Journal",
            "year": 2026,
            "doi": "doi:10.0000/TEST",
            "url": "https://example.org/paper",
        }
        payload = zotero.create_preview(metadata)
        self.assertEqual(payload["uri"], "https://example.org/paper")
        self.assertEqual(len(payload["items"]), 1)
        item = payload["items"][0]
        self.assertEqual(item["itemType"], "journalArticle")
        self.assertEqual(item["title"], "Paper")
        self.assertEqual(item["publicationTitle"], "Journal")
        self.assertEqual(item["date"], "2026")
        self.assertEqual(item["DOI"], "10.0000/test")
        self.assertEqual(item["attachments"], [])
        self.assertEqual(item["creators"][0]["lastName"], "Lovelace")

    def test_free_text_author_string_is_rejected(self) -> None:
        with self.assertRaises(zotero.ZoteroBridgeError):
            zotero.create_preview(
                {
                    "title": "Paper",
                    "authors": ["Ada Lovelace"],
                    "doi": "10.0000/test",
                }
            )

    def test_parent_create_rejects_attachment_payload(self) -> None:
        with self.assertRaises(zotero.ZoteroBridgeError):
            zotero.create_preview(
                {
                    "title": "Paper",
                    "authors": [],
                    "doi": "10.0000/test",
                    "attachments": [{"path": "/tmp/paper.pdf"}],
                }
            )

    def test_without_yes_only_previews_and_never_probes_or_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            metadata = self._metadata_file(Path(tmp))
            stream = StringIO()
            with (
                patch.object(zotero, "probe_api") as probe_api,
                patch.object(zotero, "probe_connector") as probe_connector,
                patch.object(zotero, "request_http") as request_http,
                redirect_stdout(stream),
            ):
                code = zotero.command_create(self._args(metadata, yes=False))
            payload = json.loads(stream.getvalue())
            self.assertEqual(code, 3)
            self.assertEqual(payload["status"], zotero.CONFIRMATION_REQUIRED)
            self.assertEqual(payload["would_post_to"], zotero.CREATE_ROUTE)
            self.assertIn("No Zotero write was performed", payload["note"])
            probe_api.assert_not_called()
            probe_connector.assert_not_called()
            request_http.assert_not_called()

    def test_duplicate_precheck_refuses_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            metadata = self._metadata_file(Path(tmp))
            duplicate = {
                "key": "DUPL0001",
                "data": {
                    "key": "DUPL0001",
                    "itemType": "journalArticle",
                    "title": "Synthetic Test Paper",
                    "DOI": "10.0000/synthetic.001",
                },
            }
            stream = StringIO()
            with (
                patch.object(zotero, "probe_api", return_value=(True, {}, None)),
                patch.object(zotero, "probe_connector", return_value=(True, "Zotero is running", None)),
                patch.object(zotero, "find_parent_matches", return_value=[duplicate]),
                patch.object(zotero, "request_http") as request_http,
                redirect_stdout(stream),
            ):
                code = zotero.command_create(self._args(metadata, yes=True))
            payload = json.loads(stream.getvalue())
            self.assertEqual(code, 6)
            self.assertEqual(payload["status"], "DUPLICATE_PARENT_FOUND")
            self.assertEqual(payload["matches"][0]["key"], "DUPL0001")
            request_http.assert_not_called()

    def test_http_201_plus_exact_postwrite_match_is_verified_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            metadata = self._metadata_file(Path(tmp))
            created = {
                "key": "NEWP0001",
                "data": {
                    "key": "NEWP0001",
                    "itemType": "journalArticle",
                    "title": "Synthetic Test Paper",
                    "DOI": "10.0000/synthetic.001",
                },
            }
            stream = StringIO()
            with (
                patch.object(zotero, "probe_api", return_value=(True, {}, None)),
                patch.object(zotero, "probe_connector", return_value=(True, "Zotero is running", None)),
                patch.object(zotero, "find_parent_matches", return_value=[]),
                patch.object(zotero, "request_http", return_value=(201, "", {})) as request_http,
                patch.object(zotero, "verify_created_parent", return_value=[created]),
                redirect_stdout(stream),
            ):
                code = zotero.command_create(self._args(metadata, yes=True))
            payload = json.loads(stream.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(payload["status"], "CREATED_AND_VERIFIED")
            self.assertEqual(payload["item_key"], "NEWP0001")
            request_http.assert_called_once()
            call = request_http.call_args
            self.assertTrue(call.args[0].endswith(zotero.CREATE_ROUTE))
            self.assertEqual(call.kwargs["method"], "POST")
            posted = json.loads(call.kwargs["data"].decode("utf-8"))
            self.assertEqual(posted["items"][0]["DOI"], "10.0000/synthetic.001")

    def test_http_201_without_postwrite_match_does_not_claim_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            metadata = self._metadata_file(Path(tmp))
            stream = StringIO()
            with (
                patch.object(zotero, "probe_api", return_value=(True, {}, None)),
                patch.object(zotero, "probe_connector", return_value=(True, "Zotero is running", None)),
                patch.object(zotero, "find_parent_matches", return_value=[]),
                patch.object(zotero, "request_http", return_value=(201, "", {})),
                patch.object(zotero, "verify_created_parent", return_value=[]),
                redirect_stdout(stream),
            ):
                code = zotero.command_create(self._args(metadata, yes=True))
            payload = json.loads(stream.getvalue())
            self.assertEqual(code, 5)
            self.assertEqual(payload["status"], "WRITE_SUCCEEDED_BUT_NOT_VERIFIED")
            self.assertIn("Do not mark Zotero ingest COMPLETE", payload["note"])

    def test_ambiguous_postwrite_matches_do_not_claim_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            metadata = self._metadata_file(Path(tmp))
            matches = [
                {"key": "ONE", "data": {"DOI": "10.0000/synthetic.001"}},
                {"key": "TWO", "data": {"DOI": "10.0000/synthetic.001"}},
            ]
            stream = StringIO()
            with (
                patch.object(zotero, "probe_api", return_value=(True, {}, None)),
                patch.object(zotero, "probe_connector", return_value=(True, "Zotero is running", None)),
                patch.object(zotero, "find_parent_matches", return_value=[]),
                patch.object(zotero, "request_http", return_value=(201, "", {})),
                patch.object(zotero, "verify_created_parent", return_value=matches),
                redirect_stdout(stream),
            ):
                code = zotero.command_create(self._args(metadata, yes=True))
            payload = json.loads(stream.getvalue())
            self.assertEqual(code, 5)
            self.assertEqual(payload["status"], "WRITE_SUCCEEDED_VERIFICATION_AMBIGUOUS")

    def test_attach_remains_explicitly_unsupported(self) -> None:
        args = argparse.Namespace(
            parent_key="PARENT01",
            file=Path("paper.pdf"),
            name="[ORIGINAL] Main Article",
        )
        stream = StringIO()
        with redirect_stdout(stream):
            code = zotero.command_attach_unavailable(args)
        payload = json.loads(stream.getvalue())
        self.assertEqual(code, 3)
        self.assertEqual(payload["status"], zotero.ATTACH_UNSUPPORTED)
        self.assertIn("Do not claim an attachment exists", payload["next_action"])


if __name__ == "__main__":
    unittest.main()
