from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import render_exact_mirror as renderer


class RendererSourcePathTests(unittest.TestCase):
    def test_relative_pdf_path_is_resolved_from_work_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / "work"
            work.mkdir()
            main = work / "main.pdf"
            main.write_bytes(b"%PDF-1.4\n")

            resolved = renderer._resolve_source_pdf(
                work,
                {"source_id": "SRC-M1", "pdf_path": "main.pdf"},
            )

            self.assertEqual(resolved, main.resolve())

    def test_absolute_pdf_path_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / "work"
            work.mkdir()
            source = Path(temporary) / "outside.pdf"
            source.write_bytes(b"%PDF-1.4\n")

            resolved = renderer._resolve_source_pdf(
                work,
                {"source_id": "SRC-M1", "pdf_path": str(source)},
            )

            self.assertEqual(resolved, source.resolve())

    def test_missing_relative_pdf_reports_resolved_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / "work"
            work.mkdir()

            with self.assertRaises(renderer.ExactMirrorRenderError) as context:
                renderer._resolve_source_pdf(
                    work,
                    {"source_id": "SRC-M1", "pdf_path": "main.pdf"},
                )

            self.assertIn(str(work / "main.pdf"), str(context.exception))


if __name__ == "__main__":
    unittest.main()
