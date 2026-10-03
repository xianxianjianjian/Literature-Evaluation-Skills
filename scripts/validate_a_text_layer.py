#!/usr/bin/env python3
"""Check the real Chinese text layer in a v1.5 exact-frame A PDF."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    import pymupdf
except ImportError:  # pragma: no cover - dependency check
    pymupdf = None


@dataclass(frozen=True)
class TextLayerCheck:
    code: str
    passed: bool
    detail: str


def _cjk(text: str) -> str:
    return "".join(re.findall(r"[\u3400-\u9fff]", text))


def _search_keyword(text: str) -> str:
    """Choose text that is contiguous in the PDF, including punctuation/Latin boundaries."""
    runs = re.findall(r"[\u3400-\u9fff]+", text)
    if not runs:
        return ""
    run = next((value for value in runs if len(value) >= 2), runs[0])
    return run[:min(4, len(run))]


def _source_phrases(text: str, target: str) -> list[str]:
    words = re.findall(r"[A-Za-z]{4,}", text)
    target_folded = target.casefold()
    return [
        " ".join(words[index:index + 2]).casefold()
        for index in range(len(words) - 1)
        if any(word.casefold() not in target_folded for word in words[index:index + 2])
    ]


def validate(work_dir: Path, pdf_path: Path) -> list[TextLayerCheck]:
    if pymupdf is None:
        return [TextLayerCheck("A_TEXT_LAYER_DEPENDENCY_PASS", False, "PyMuPDF required")]
    try:
        inventory = json.loads((work_dir / "source_inventory.json").read_text(encoding="utf-8-sig"))
        frames = {
            row["frame_id"]: row
            for row in (json.loads(line) for line in (work_dir / "text_frame_inventory.jsonl").read_text(encoding="utf-8-sig").splitlines() if line.strip())
        }
        ledger = {
            row["frame_ids"][0]: row
            for row in (json.loads(line) for line in (work_dir / "translation_ledger.jsonl").read_text(encoding="utf-8-sig").splitlines() if line.strip())
            if len(row.get("frame_ids", [])) == 1
        }
        pdf = pymupdf.open(pdf_path)
    except (OSError, KeyError, ValueError, TypeError) as exc:
        return [TextLayerCheck("A_TEXT_LAYER_READ_PASS", False, str(exc))]
    failures = {name: [] for name in (
        "A_SELECTABLE_TEXT_PASS", "A_COPY_TEXT_FIDELITY_PASS", "A_CHINESE_SEARCH_PASS",
        "A_NO_STALE_ENGLISH_TEXT_LAYER_PASS", "A_READING_ORDER_PASS", "A_FONT_UNICODE_MAPPING_PASS",
    )}
    checked = 0
    try:
        for record in sorted(inventory["pages"], key=lambda row: row["output_page"]):
            page = pdf[record["output_page"] - 1]
            page_text = page.get_text("text", sort=False)
            prior_index = -1
            for frame_id in record["frame_ids"]:
                frame = frames[frame_id]
                if frame["translation_action"] != "TRANSLATE":
                    continue
                checked += 1
                row = ledger[frame_id]
                target = str(row["translated_text"])
                source = str(row["source_text"])
                rect = pymupdf.Rect(frame["bbox_pt"]) * page.transformation_matrix
                extracted = page.get_text("text", clip=rect, sort=False)
                wanted = _cjk(target)
                copied = _cjk(extracted)
                if wanted and (not copied or copied[:min(4, len(copied))] not in wanted):
                    failures["A_SELECTABLE_TEXT_PASS"].append(frame_id)
                if wanted and not (wanted in copied or (len(wanted) >= 6 and wanted[:6] in copied)):
                    failures["A_COPY_TEXT_FIDELITY_PASS"].append(frame_id)
                keyword = _search_keyword(target)
                if keyword and not any(rect.intersects(hit) for hit in page.search_for(keyword)):
                    failures["A_CHINESE_SEARCH_PASS"].append(frame_id)
                folded = " ".join(re.findall(r"[A-Za-z]{4,}", extracted)).casefold()
                if any(phrase in folded for phrase in _source_phrases(source, target)):
                    failures["A_NO_STALE_ENGLISH_TEXT_LAYER_PASS"].append(frame_id)
                if keyword:
                    index = _cjk(page_text).find(keyword, prior_index + 1)
                    if index < 0:
                        failures["A_READING_ORDER_PASS"].append(frame_id)
                    else:
                        prior_index = index
            # An embedded CJK font without ToUnicode cannot support reliable copy.
            for font in page.get_fonts(full=True):
                xref, _, font_type, base_font = font[:4]
                if "SimSun" in base_font or "SimHei" in base_font:
                    mapping_type, _ = pdf.xref_get_key(xref, "ToUnicode")
                    if mapping_type != "xref":
                        failures["A_FONT_UNICODE_MAPPING_PASS"].append(f"page-{record['output_page']}:{base_font}")
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        return [TextLayerCheck("A_TEXT_LAYER_READ_PASS", False, str(exc))]
    finally:
        pdf.close()
    if checked == 0:
        return [TextLayerCheck("A_TEXT_LAYER_READ_PASS", False, "no translated frames")]
    return [
        TextLayerCheck(name, not values, f"{checked} translated frames checked" if not values else f"failed: {sorted(set(values))}")
        for name, values in failures.items()
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    checks = validate(args.work_dir, args.pdf)
    payload = {"passed": all(check.passed for check in checks), "checks": [asdict(check) for check in checks]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
