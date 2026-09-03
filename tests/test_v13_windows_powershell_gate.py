from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_strict_real_paper_gate.ps1"


class WindowsPowerShellGateCompatibilityTests(unittest.TestCase):
    def test_gate_does_not_require_powershell_6_iswindows_variable(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("if (-not $IsWindows)", text)
        self.assertIn('$env:OS -eq "Windows_NT"', text)

    def test_reviewed_ledger_path_skips_only_legacy_recovery(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('[string]$ReviewedLedger = ""', text)
        self.assertIn('Copy-Item -LiteralPath $ReviewedLedger -Destination $LedgerPath -Force', text)
        self.assertIn('render_exact_mirror.py', text)
        self.assertIn('validate_translation_package.py', text)
        self.assertIn('STRICT REAL-PAPER GATE: PASS', text)


if __name__ == "__main__":
    unittest.main()
