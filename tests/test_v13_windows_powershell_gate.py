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


if __name__ == "__main__":
    unittest.main()
