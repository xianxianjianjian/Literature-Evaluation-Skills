from __future__ import annotations

import argparse
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import terminology_registry as terms


class TerminologyHistoryEdgeTests(unittest.TestCase):
    def test_explicit_alternatives_do_not_erase_previous_preferred(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "terms.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                csv.writer(handle).writerow(terms.FIELDS)

            terms.command_add(
                argparse.Namespace(
                    registry=path,
                    term_id="TERM-0001",
                    english_term="arousal",
                    preferred_chinese="觉醒",
                    abbreviation=None,
                    alternative_chinese="唤醒",
                    discipline="sleep medicine",
                    subfield="sleep",
                    definition=None,
                    context="PSG arousal",
                    confidence="HIGH",
                    evidence_level="TE4",
                    evidence_ids="TERMEV-0001",
                    status="ACTIVE",
                    verified_date="2026-08-21",
                    notes=None,
                )
            )

            terms.command_update(
                argparse.Namespace(
                    registry=path,
                    term_id="TERM-0001",
                    abbreviation=None,
                    preferred_chinese="睡眠觉醒",
                    alternative_chinese="短暂觉醒; 微觉醒",
                    discipline=None,
                    subfield=None,
                    definition=None,
                    context=None,
                    confidence=None,
                    evidence_level="TE1",
                    evidence_ids="TERMEV-0002",
                    verified_date="2026-08-22",
                    note="Updated to guideline wording",
                )
            )

            row = terms.read_registry(path)[0]
            alternatives = terms.split_alternatives(row["Alternative_Chinese"])
            self.assertIn("觉醒", alternatives)
            self.assertIn("唤醒", alternatives)
            self.assertIn("短暂觉醒", alternatives)
            self.assertIn("微觉醒", alternatives)
            self.assertEqual(row["Preferred_Chinese"], "睡眠觉醒")


if __name__ == "__main__":
    unittest.main()
