from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Phase8IntegrationInventoryTests(unittest.TestCase):
    def test_required_phase8_zotero_files_exist(self) -> None:
        required = [
            "scripts/zotero_bridge.py",
            "scripts/zotero_local_write.py",
            "scripts/zotero_local_archive.py",
            "shared/zotero-policy.md",
            "skills/literature-search/references/zotero-ingest.md",
            "docs/zotero-write-adapter.md",
            "docs/zotero-local-attachments.md",
            "tests/test_zotero_local_write.py",
            "tests/test_zotero_local_archive.py",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual(missing, [], f"Missing Phase-8 integration files: {missing}")

    def test_phase8_policy_no_longer_claims_local_api_is_globally_read_only(self) -> None:
        paths = [
            ROOT / "shared/zotero-policy.md",
            ROOT / "skills/literature-search/references/zotero-ingest.md",
            ROOT / "README.md",
        ]
        forbidden = [
            "Zotero Desktop Local API `/api/` 只读",
            "Local API under `/api/` remains read-only",
            "LOCAL_FILE_ATTACH_ROUTE_NOT_IMPLEMENTED_OR_VERIFIED",
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                self.assertNotIn(phrase, text, f"Stale Phase-7 capability text in {path}: {phrase}")


if __name__ == "__main__":
    unittest.main()
