from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import mirror_pdf
import render_exact_mirror
import validate_translation_package as validator
import workflow_state

try:
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
except ImportError:
    FontBuilder = TTGlyphPen = PdfReader = PdfWriter = canvas = None


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _source_pdf(path: Path, size: tuple[float, float], label: str) -> None:
    c = canvas.Canvas(str(path), pagesize=size, pageCompression=1)
    c.setFont("Helvetica", 10)
    c.drawString(30, size[1] - 60, f"{label} source paragraph")
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.rect(30, 170, 180, 80, fill=1, stroke=1)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(40, 210, "Speed")
    c.rect(30, 90, 180, 50, fill=0, stroke=1)
    c.drawString(40, 110, "Header")
    c.showPage()
    c.save()


def _boxes(page: object) -> dict[str, list[float]]:
    result = {}
    for evidence, attribute in {
        "media_box": "mediabox",
        "crop_box": "cropbox",
        "trim_box": "trimbox",
        "bleed_box": "bleedbox",
        "art_box": "artbox",
    }.items():
        box = getattr(page, attribute)
        result[evidence] = [float(box.left), float(box.bottom), float(box.right), float(box.top)]
    return result


def _test_simsun(root: Path, allow_installed: bool = True) -> Path | None:
    installed = Path(r"C:\Windows\Fonts\simsun.ttc")
    if allow_installed and installed.is_file():
        return installed
    if FontBuilder is None or TTGlyphPen is None:
        return None

    # CI cannot redistribute Windows SimSun. Build a tiny TrueType test double
    # whose family/resource name is SimSun and whose cmap covers this fixture.
    # Production still requires C:\Windows\Fonts\simsun.ttc and never calls this.
    codepoints = set(range(32, 127)) | {ord(char) for char in "中文正文速度表头分析"}
    glyph_order = [".notdef"] + [f"uni{codepoint:04X}" for codepoint in sorted(codepoints)]
    cmap = {codepoint: f"uni{codepoint:04X}" for codepoint in sorted(codepoints)}
    glyphs = {}
    metrics = {}
    for glyph_name in glyph_order:
        pen = TTGlyphPen(None)
        if glyph_name != "uni0020":
            pen.moveTo((80, 0))
            pen.lineTo((80, 700))
            pen.lineTo((720, 700))
            pen.lineTo((720, 0))
            pen.closePath()
        glyphs[glyph_name] = pen.glyph()
        metrics[glyph_name] = (800, 0)

    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(glyph_order)
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupOS2(
        sTypoAscender=800,
        sTypoDescender=-200,
        usWinAscent=800,
        usWinDescent=200,
    )
    builder.setupNameTable(
        {
            "familyName": "SimSun",
            "styleName": "Regular",
            "uniqueFontIdentifier": "Synthetic SimSun exact-mirror test fixture",
            "fullName": "SimSun",
            "psName": "SimSun",
            "version": "Version 1.0",
        }
    )
    builder.setupPost()
    builder.setupMaxp()
    output = root / "simsun.ttc"
    builder.save(str(output))
    return output


@unittest.skipIf(
    any(item is None for item in (PdfReader, canvas)),
    "exact-mirror dependencies are unavailable",
)
class ExactMirrorTests(unittest.TestCase):
    def _package(self, root: Path) -> tuple[Path, Path]:
        font_path = _test_simsun(root)
        if font_path is None:
            self.skipTest("SimSun or a CI synthetic SimSun fixture is unavailable")
        work = root / "work"
        work.mkdir()
        main_pdf = root / "main.pdf"
        si_pdf = root / "si.pdf"
        _source_pdf(main_pdf, (300, 400), "Main")
        _source_pdf(si_pdf, (320, 420), "SI")
        sources = [
            ("SRC-M1", "MAIN", main_pdf),
            ("SRC-S1", "SI", si_pdf),
        ]
        frames: list[dict[str, object]] = []
        pages: list[dict[str, object]] = []
        objects: list[dict[str, object]] = []
        ledger: list[dict[str, object]] = []
        output_page = 0
        for source_id, role, pdf_path in sources:
            output_page += 1
            page = PdfReader(str(pdf_path)).pages[0]
            height = float(page.mediabox.top)
            body_id = f"TF-{source_id}-BODY"
            figure_id = f"TF-{source_id}-FIG"
            cell_id = f"TF-{source_id}-CELL"
            source_frames = [
                (body_id, "body", [30, height - 65, 210, height - 45], "uniform-white", "中文正文"),
                (figure_id, "figure_label", [38, 205, 100, 225], "uniform-color", "速度"),
                (cell_id, "table_cell", [38, 105, 120, 125], "uniform-white", "表头"),
            ]
            for index, (frame_id, kind, bbox, background, translated) in enumerate(source_frames, 1):
                unit_id = frame_id.replace("TF-", "TU-")
                frame = {
                    "frame_id": frame_id,
                    "source_id": source_id,
                    "source_page": 1,
                    "unit_id": unit_id,
                    "kind": kind,
                    "bbox_pt": bbox,
                    "rotation": 0,
                    "reading_order": index,
                    "source_font": "Helvetica",
                    "source_font_size_pt": 10,
                    "source_leading_pt": 12,
                    "weight": "regular",
                    "alignment": "left",
                    "background": background,
                    "translation_action": "TRANSLATE",
                    "reviewed": True,
                }
                if background == "uniform-color":
                    frame["background_rgb"] = [0.9, 0.9, 0.9]
                frames.append(frame)
                ledger.append(
                    {
                        "unit_id": unit_id,
                        "source_id": source_id,
                        "source_page": 1,
                        "section": "Body",
                        "unit_index": index,
                        "kind": kind,
                        "source_status": "READABLE",
                        "translation_status": "TRANSLATED",
                        "output_pages": [output_page],
                        "issue_ids": [],
                        "frame_ids": [frame_id],
                        "source_text": "source",
                        "translated_text": translated,
                        "font_scale_used": 1.0,
                        "fit_status": "FIT",
                        "untranslated_tokens": [],
                    }
                )
            figure_object = f"FIG-{source_id}"
            table_object = f"TAB-{source_id}"
            objects.extend(
                [
                    {
                        "object_id": figure_object,
                        "source_id": source_id,
                        "source_page": 1,
                        "kind": "figure",
                        "bbox_pt": [30, 170, 210, 250],
                        "label_frame_ids": [figure_id],
                    },
                    {
                        "object_id": table_object,
                        "source_id": source_id,
                        "source_page": 1,
                        "kind": "table",
                        "bbox_pt": [30, 90, 210, 140],
                        "label_frame_ids": [],
                        "table_structure": {
                            "rows": 1,
                            "columns": 1,
                            "header_rows": 1,
                            "merged_cells": 0,
                            "footnotes": 0,
                        },
                        "cells": [
                            {
                                "row": 1,
                                "column": 1,
                                "row_span": 1,
                                "column_span": 1,
                                "bbox_pt": [30, 90, 210, 140],
                                "frame_id": cell_id,
                            }
                        ],
                    },
                ]
            )
            pages.append(
                {
                    "source_id": source_id,
                    "source_page": 1,
                    "output_page": output_page,
                    **_boxes(page),
                    "rotation": 0,
                    "unit_ids": [item[0].replace("TF-", "TU-") for item in source_frames],
                    "object_ids": [figure_object, table_object],
                    "frame_ids": [item[0] for item in source_frames],
                }
            )
        inventory = {
            "schema_version": 2,
            "scope": "FULL_MIRROR",
            "layout_fidelity": "EXACT_TEXT_FRAME",
            "sources": [
                {
                    "source_id": source_id,
                    "role": role,
                    "page_count": 1,
                    "pdf_path": str(pdf_path),
                    "status": "AVAILABLE",
                }
                for source_id, role, pdf_path in sources
            ],
            "pages": pages,
            "units": [
                {
                    "unit_id": row["unit_id"],
                    "source_id": row["source_id"],
                    "source_page": 1,
                    "kind": row["kind"],
                }
                for row in ledger
            ],
            "objects": objects,
        }
        _write_json(work / "source_inventory.json", inventory)
        _write_jsonl(work / "text_frame_inventory.jsonl", frames)
        _write_jsonl(work / "translation_ledger.jsonl", ledger)
        (work / "translation_issues.jsonl").write_text("", encoding="utf-8")
        font_map = {
            "schema_version": 1,
            "cjk_font_family": "SimSun",
            "font_path": str(font_path),
            "ttc_face_index": 0,
            "fallback_allowed": False,
            "regular_mode": "embedded-subset",
            "bold_mode": "synthetic-stroke",
            "italic_mode": "synthetic-shear",
            "expected_pdf_font_name": "SimSun",
        }
        _write_json(work / "font_map.json", font_map)
        output = root / "A.pdf"
        args = argparse.Namespace(
            source_inventory=work / "source_inventory.json",
            text_frame_inventory=work / "text_frame_inventory.jsonl",
            font_map=work / "font_map.json",
            output_pdf=output,
            layout_fidelity="EXACT_TEXT_FRAME",
            cjk_font_family="SimSun",
            minimum_font_scale=0.95,
        )
        plan = mirror_pdf.create_exact_plan(args)
        _write_json(work / "mirror_layout_plan.json", plan)
        return work, output

    def test_exact_main_and_si_render_and_validate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work, output = self._package(Path(temporary))
            render_exact_mirror.render(work, output)
            checks = validator.validate_package(
                work, output, "FULL_MIRROR", "EXACT_TEXT_FRAME"
            )
            failures = {check.code: check.detail for check in checks if not check.passed}
            self.assertEqual(failures, {})

    def test_extension_page_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work, _ = self._package(Path(temporary))
            path = work / "mirror_layout_plan.json"
            plan = json.loads(path.read_text(encoding="utf-8"))
            plan["pages"][0]["extension_page"] = True
            with self.assertRaises(mirror_pdf.MirrorPlanError):
                mirror_pdf.validate_plan_data(plan)

    def test_font_scale_below_95_percent_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work, output = self._package(Path(temporary))
            path = work / "translation_ledger.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            rows[0]["font_scale_used"] = 0.949
            _write_jsonl(path, rows)
            failures = {
                check.code
                for check in validator.validate_package(
                    work, output, "FULL_MIRROR", "EXACT_TEXT_FRAME"
                )
                if not check.passed
            }
            self.assertIn("ledger:exact-schema", failures)

    def test_shifted_replacement_region_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work, output = self._package(Path(temporary))
            render_exact_mirror.render(work, output)
            plan_path = work / "mirror_layout_plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["pages"][0]["replacement_regions"][0]["bbox_pt"][0] += 2
            _write_json(plan_path, plan)
            failures = {
                check.code
                for check in validator.validate_package(
                    work, output, "FULL_MIRROR", "EXACT_TEXT_FRAME"
                )
                if not check.passed
            }
            self.assertIn("layout:replacement-regions", failures)

    def test_unaccounted_english_in_translation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work, output = self._package(Path(temporary))
            path = work / "translation_ledger.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            rows[0]["translated_text"] = "中文 sleep spindle"
            _write_jsonl(path, rows)
            render_exact_mirror.render(work, output)
            failures = {
                check.code
                for check in validator.validate_package(
                    work, output, "FULL_MIRROR", "EXACT_TEXT_FRAME"
                )
                if not check.passed
            }
            self.assertIn("semantic:english-accounting", failures)

    def test_extra_output_page_fails_one_to_one_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work, output = self._package(Path(temporary))
            render_exact_mirror.render(work, output)
            reader = PdfReader(str(output))
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            writer.add_blank_page(width=100, height=100)
            with output.open("wb") as handle:
                writer.write(handle)
            failures = {
                check.code
                for check in validator.validate_package(
                    work, output, "FULL_MIRROR", "EXACT_TEXT_FRAME"
                )
                if not check.passed
            }
            self.assertIn("layout:page-count", failures)

    def test_non_simsun_font_map_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work, output = self._package(Path(temporary))
            font_map_path = work / "font_map.json"
            font_map = json.loads(font_map_path.read_text(encoding="utf-8"))
            font_map["cjk_font_family"] = "Noto Serif CJK SC"
            _write_json(font_map_path, font_map)
            failures = {
                check.code
                for check in validator.validate_package(
                    work, output, "FULL_MIRROR", "EXACT_TEXT_FRAME"
                )
                if not check.passed
            }
            self.assertIn("font:map", failures)


class ExactWorkflowProfileTests(unittest.TestCase):
    def test_new_manifest_defaults_to_simsun_exact_mirror(self) -> None:
        translation = workflow_state.initial_manifest("2026-W35")["stages"]["translation"]
        self.assertEqual(translation["scope"], "FULL_MIRROR")
        self.assertEqual(translation["layout_fidelity"], "EXACT_TEXT_FRAME")
        self.assertEqual(translation["cjk_font_family"], "SimSun")
        self.assertEqual(translation["minimum_font_scale"], 0.95)

    def test_old_manifest_normalizes_to_legacy_structural(self) -> None:
        manifest = workflow_state.initial_manifest("2026-W35")
        translation = manifest["stages"]["translation"]
        del translation["layout_fidelity"]
        del translation["cjk_font_family"]
        del translation["minimum_font_scale"]
        normalized = workflow_state.validate_manifest(manifest)
        self.assertEqual(
            normalized["stages"]["translation"]["layout_fidelity"],
            "LEGACY_STRUCTURAL",
        )


if __name__ == "__main__":
    unittest.main()
