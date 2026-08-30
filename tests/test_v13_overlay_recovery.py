from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import recover_overlay_translation as recovery

try:
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfgen import canvas
except ImportError:
    PdfReader = PdfWriter = pdfmetrics = UnicodeCIDFont = canvas = None


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


def _write_package(root: Path) -> tuple[Path, Path]:
    work = root / "work"
    work.mkdir()
    source = root / "source.pdf"
    overlay = root / "overlay.pdf"
    reference = root / "reference.pdf"

    c = canvas.Canvas(str(source), pagesize=(300, 400), pageCompression=1)
    c.setFont("Helvetica", 10)
    c.drawString(30, 330, "Sleep spindle memory")
    c.save()

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    c = canvas.Canvas(str(overlay), pagesize=(300, 400), pageCompression=1)
    c.setFillColorRGB(1, 1, 1)
    c.rect(28, 324, 170, 20, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("STSong-Light", 10)
    c.drawString(30, 330, "中文译文ABC 123")
    c.save()

    source_reader = PdfReader(str(source))
    overlay_reader = PdfReader(str(overlay))
    writer = PdfWriter()
    page = source_reader.pages[0]
    page.merge_page(overlay_reader.pages[0])
    writer.add_page(page)
    with reference.open("wb") as handle:
        writer.write(handle)

    source_page = PdfReader(str(source)).pages[0]
    inventory = {
        "schema_version": 2,
        "scope": "FULL_MIRROR",
        "layout_fidelity": "EXACT_TEXT_FRAME",
        "sources": [
            {
                "source_id": "SRC-M",
                "role": "MAIN",
                "page_count": 1,
                "pdf_path": str(source),
                "status": "AVAILABLE",
            }
        ],
        "pages": [
            {
                "source_id": "SRC-M",
                "source_page": 1,
                "output_page": 1,
                **_boxes(source_page),
                "rotation": 0,
                "unit_ids": ["TU-1"],
                "object_ids": [],
                "frame_ids": ["TF-1"],
            }
        ],
        "units": [
            {"unit_id": "TU-1", "source_id": "SRC-M", "source_page": 1, "kind": "body"}
        ],
        "objects": [],
    }
    (work / "source_inventory.json").write_text(
        json.dumps(inventory), encoding="utf-8"
    )
    frame = {
        "frame_id": "TF-1",
        "source_id": "SRC-M",
        "source_page": 1,
        "unit_id": "TU-1",
        "kind": "body",
        "bbox_pt": [28, 324, 198, 344],
        "rotation": 0,
        "reading_order": 1,
        "source_font": "Helvetica",
        "source_font_size_pt": 10,
        "source_leading_pt": 12,
        "weight": "regular",
        "alignment": "left",
        "background": "uniform-white",
        "translation_action": "TRANSLATE",
        "source_text": "Sleep spindle memory",
        "reviewed": True,
    }
    (work / "text_frame_inventory.jsonl").write_text(
        json.dumps(frame) + "\n", encoding="utf-8"
    )
    return work, reference


@unittest.skipIf(
    any(item is None for item in (PdfReader, PdfWriter, pdfmetrics, UnicodeCIDFont, canvas)),
    "PDF dependencies are unavailable",
)
class OverlayRecoveryTests(unittest.TestCase):
    def test_source_layer_is_subtracted_and_overlay_text_is_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work, reference = _write_package(Path(temporary))
            output = work / "translation_ledger.jsonl"
            report = recovery.recover(work, reference, output)
            row = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])
            self.assertEqual(row["source_text"], "Sleep spindle memory")
            self.assertEqual(row["translated_text"], "中文译文ABC 123")
            self.assertNotIn("Sleep spindle memory", row["translated_text"])
            self.assertEqual(
                row["untranslated_tokens"],
                [
                    {
                        "text": "ABC",
                        "reason": "RETAINED_IN_REVIEWED_REFERENCE_TRANSLATION",
                    }
                ],
            )

    def test_missing_overlay_text_is_a_hard_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work, _ = _write_package(root)
            with self.assertRaises(recovery.OverlayRecoveryError):
                recovery.recover(work, root / "source.pdf", work / "translation_ledger.jsonl")
            report = json.loads(
                (work / "overlay_recovery_report.json").read_text(encoding="utf-8")
            )
            self.assertFalse(report["passed"])
            self.assertEqual(report["missing_frame_ids"], ["TF-1"])


if __name__ == "__main__":
    unittest.main()
