from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import zotero_bridge as zotero


class ZoteroCreatorSchemaTests(unittest.TestCase):
    def test_institutional_name_normalizes_to_fieldmode_creator(self) -> None:
        creators = zotero.normalized_creators(
            {
                "authors": [
                    {
                        "name": "World Sleep Society",
                        "creatorType": "author",
                    }
                ]
            }
        )
        self.assertEqual(
            creators,
            [
                {
                    "lastName": "World Sleep Society",
                    "fieldMode": 1,
                    "creatorType": "author",
                }
            ],
        )

    def test_explicit_fieldmode_rejects_first_name(self) -> None:
        with self.assertRaises(zotero.ZoteroBridgeError):
            zotero.normalized_creators(
                {
                    "authors": [
                        {
                            "firstName": "Not",
                            "lastName": "Institution",
                            "fieldMode": 1,
                        }
                    ]
                }
            )


if __name__ == "__main__":
    unittest.main()
