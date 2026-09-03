from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import render_exact_mirror as renderer


class _FakeMergedPage:
    def merge_page(self, _page, over=True):  # pragma: no cover - should not be called
        raise AssertionError("retain-only page must not create or merge an overlay")


class _FakeWriter:
    def __init__(self) -> None:
        self.pages: list[_FakeMergedPage] = []

    def add_page(self, _page) -> None:
        self.pages.append(_FakeMergedPage())

    def write(self, handle) -> None:
        handle.write(b"%PDF-retain-only-test")


class _FakeSourceReader:
    def __init__(self, _value) -> None:
        self.pages = [object()]


class _FakeCanvas:
    def save(self) -> None:
        pass


class _FakeCanvasModule:
    @staticmethod
    def Canvas(_buffer, pagesize=None, pageCompression=1):
        return _FakeCanvas()


class RetainOnlyPageTests(unittest.TestCase):
    def test_retain_only_page_is_copied_without_reading_zero_page_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / "work"
            work.mkdir()
            source_pdf = work / "main.pdf"
            source_pdf.write_bytes(b"%PDF-source")
            font_path = work / "simsun.ttc"
            font_path.write_bytes(b"synthetic-font-fixture")
            output = Path(temporary) / "out.pdf"

            inventory = {
                "sources": [
                    {
                        "source_id": "SRC-M1",
                        "role": "MAIN",
                        "page_count": 1,
                        "pdf_path": "main.pdf",
                    }
                ],
                "pages": [
                    {
                        "output_page": 1,
                        "source_id": "SRC-M1",
                        "source_page": 1,
                        "frame_ids": ["F1"],
                        "media_box": [0, 0, 100, 100],
                    }
                ],
            }
            frames = {
                "F1": {
                    "frame_id": "F1",
                    "translation_action": "RETAIN_SOURCE",
                }
            }
            font_map = {"font_path": str(font_path)}
            plan = {
                "output_pdf": str(output.resolve()),
                "pages": [
                    {
                        "output_page_number": 1,
                        "replacement_regions": [],
                    }
                ],
            }

            def fake_load_json(path: Path, _label: str):
                if path.name == "source_inventory.json":
                    return inventory
                if path.name == "font_map.json":
                    return font_map
                if path.name == "mirror_layout_plan.json":
                    return plan
                raise AssertionError(path)

            with (
                mock.patch.object(renderer, "load_json", side_effect=fake_load_json),
                mock.patch.object(renderer, "load_jsonl", return_value=[]),
                mock.patch.object(renderer, "validate_exact_inventory", return_value=inventory),
                mock.patch.object(renderer, "validate_text_frames", return_value=frames),
                mock.patch.object(renderer, "validate_exact_ledger", return_value={}),
                mock.patch.object(renderer, "validate_font_map", return_value=font_map),
                mock.patch.object(renderer, "validate_plan_data", return_value=plan),
                mock.patch.object(renderer, "PdfReader", _FakeSourceReader),
                mock.patch.object(renderer, "PdfWriter", _FakeWriter),
                mock.patch.object(renderer, "canvas", _FakeCanvasModule),
                mock.patch.object(renderer.pdfmetrics, "registerFont"),
                mock.patch.object(renderer, "TTFont", return_value=object()),
            ):
                report = renderer.render(work, output)

            self.assertTrue(report["passed"])
            self.assertEqual(report["rendered_frames"], [])
            self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
