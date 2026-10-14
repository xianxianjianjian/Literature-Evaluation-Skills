#!/usr/bin/env python3
"""Check the real Chinese text layer in a v1.5 exact-frame A PDF."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
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
    failed_frame_ids: tuple[str, ...] = ()
    frame_statistics: tuple[dict, ...] = ()


def _cjk(text: str) -> str:
    return "".join(re.findall(r"[\u3400-\u9fff]", text))


def _search_keyword(text: str) -> str:
    """Choose text that is contiguous in the PDF, including punctuation/Latin boundaries."""
    runs = re.findall(r"[\u3400-\u9fff]+", text)
    if not runs:
        return ""
    run = next((value for value in runs if len(value) >= 2), runs[0])
    return run[:min(4, len(run))]


def normalize_text(text: str) -> str:
    """Explicit extraction equivalences; never discard numbers or punctuation.

    NFC, fullwidth ASCII, ligatures and super/subscript digits are typography;
    U+2212 is painted as ASCII minus by the renderer. Whitespace and soft
    hyphens are layout only. Other compatibility characters remain significant.
    """
    equivalents = str.maketrans({
        **{chr(i): chr(i - 0xFEE0) for i in range(0xFF01, 0xFF5F)},
        **dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉", "01234567890123456789")),
        "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl",
        "−": "-", "⁻": "-", "₋": "-", "⁺": "+", "₊": "+", "\u00ad": "",
    })
    return "".join(c for c in unicodedata.normalize("NFC", text).translate(equivalents) if not c.isspace())


def _residual_tokens(source: str, target: str, extracted: str, row: dict, frame: dict) -> list[str]:
    if frame.get("role") in {"REFERENCE", "FIGURE_INTERNAL"} or frame.get("region_role") in {"REFERENCE", "FIGURE_INTERNAL"}:
        return []
    words = lambda value: set(re.findall(r"[A-Za-z]+", value.casefold()))
    # Target tokens themselves are evidence of intended retention (REM, PSG,
    # DOI, names, variables). Additional exceptions need a recorded reason.
    allowed = words(target)
    for entry in row.get("retained_source_tokens", []):
        if isinstance(entry, dict) and str(entry.get("reason") or "").strip():
            allowed.update(words(str(entry.get("token") or "")))
    candidates = words(source) - allowed
    return sorted(token for token in candidates if token in words(extracted) or re.search(
        r"\b" + r"\s*".join(re.escape(c) for c in token) + r"\b", extracted.casefold()))


def _geometric_text(lines: list[tuple]) -> str:
    """Join overlapping typographic baselines, including raised/lowered runs.

    PDF extractors may put an exponent in a separate line before its base.
    At least half of the smaller glyph-line height must overlap; distinct body
    lines remain separate. Horizontal glyph order, not object order, determines
    completeness. Object/copy order is independently checked below.
    """
    groups = []
    for bbox, chars in sorted(lines, key=lambda row: (row[0][1], row[0][0])):
        rect = pymupdf.Rect(bbox)
        group = next((item for item in groups if min(item[0].y1, rect.y1) - max(item[0].y0, rect.y0)
                      >= 0.5 * min(item[0].height, rect.height)), None)
        if group is None:
            groups.append([rect, list(chars)])
        else:
            group[0] |= rect
            group[1].extend(chars)
    return "\n".join("".join(c["c"] for c in sorted(chars, key=lambda c: c["bbox"][0]))
                     for _, chars in sorted(groups, key=lambda row: (row[0].y0, row[0].x0)))


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
    statistics = []
    try:
        for record in sorted(inventory["pages"], key=lambda row: row["output_page"]):
            page = pdf[record["output_page"] - 1]
            translated_ids = [fid for fid in record["frame_ids"] if frames[fid]["translation_action"] == "TRANSLATE"]
            rects = {fid: pymupdf.Rect(frames[fid]["bbox_pt"]) * page.transformation_matrix for fid in translated_ids}
            raw_lines = {fid: [] for fid in translated_ids}
            geometric_lines = {fid: [] for fid in translated_ids}
            cjk_fonts = set()
            frame_fonts = {fid: set() for fid in translated_ids}
            # Assign each glyph once by its centre. Overlapping frames cannot
            # borrow the same text layer to satisfy repeated ledger sentences.
            for block in page.get_text("rawdict")["blocks"]:
                for line in block.get("lines", []):
                    chars_by_frame = {fid: [] for fid in translated_ids}
                    for span in line["spans"]:
                        for char in span["chars"]:
                            box = pymupdf.Rect(char["bbox"])
                            point = (box.tl + box.br) / 2
                            owners = [fid for fid, rect in rects.items() if rect.contains(point)]
                            if len(owners) > 1:
                                for fid in owners:
                                    failures["A_COPY_TEXT_FIDELITY_PASS"].append(fid)
                            for fid in owners:
                                chars_by_frame[fid].append(char)
                                if _cjk(char["c"]):
                                    cjk_fonts.add(span["font"])
                                    frame_fonts[fid].add(span["font"])
                    for fid, chars in chars_by_frame.items():
                        if chars:
                            raw_lines[fid].append("".join(c["c"] for c in chars))
                            geometric_lines[fid].append((line["bbox"], chars))
            for frame_id in record["frame_ids"]:
                frame = frames[frame_id]
                if frame["translation_action"] != "TRANSLATE":
                    continue
                checked += 1
                row = ledger[frame_id]
                target = str(row["translated_text"])
                source = str(row["source_text"])
                rect = pymupdf.Rect(frame["bbox_pt"]) * page.transformation_matrix
                extracted = _geometric_text(geometric_lines[frame_id])
                wanted = normalize_text(target)
                copied = normalize_text(extracted)
                statistics.append({"frame_id": frame_id, "output_page": record["output_page"],
                                   "expected_characters": len(wanted), "extracted_characters": len(copied),
                                   "sequence_match": wanted == copied})
                if not copied or "\ufffd" in copied:
                    failures["A_SELECTABLE_TEXT_PASS"].append(frame_id)
                if not wanted or wanted != copied:
                    failures["A_COPY_TEXT_FIDELITY_PASS"].append(frame_id)
                keyword = _search_keyword(target)
                if keyword and not any(rect.intersects(hit) for hit in page.search_for(keyword)):
                    failures["A_CHINESE_SEARCH_PASS"].append(frame_id)
                if _residual_tokens(source, target, extracted, row, frame):
                    failures["A_NO_STALE_ENGLISH_TEXT_LAYER_PASS"].append(frame_id)
                # Do not assume global PDF object order traverses columns.
                # Within each frame, extracted copy order must match the target.
                if normalize_text("\n".join(raw_lines[frame_id])) != wanted:
                    failures["A_READING_ORDER_PASS"].append(frame_id)
            # An embedded CJK font without ToUnicode cannot support reliable copy.
            for font in page.get_fonts(full=True):
                xref, _, font_type, base_font = font[:4]
                if "SimSun" in base_font or "SimHei" in base_font or any(re.sub(r"[ -]|Regular$", "", name) in re.sub(r"[ -]", "", base_font) for name in cjk_fonts):
                    mapping_type, _ = pdf.xref_get_key(xref, "ToUnicode")
                    if mapping_type != "xref":
                        failures["A_FONT_UNICODE_MAPPING_PASS"].append(f"page-{record['output_page']}:{base_font}")
                        failures["A_FONT_UNICODE_MAPPING_PASS"].extend(
                            fid for fid, fonts in frame_fonts.items()
                            if any(re.sub(r"[ -]|Regular$", "", name) in re.sub(r"[ -]", "", base_font) for name in fonts))
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        return [TextLayerCheck("A_TEXT_LAYER_READ_PASS", False, str(exc))]
    finally:
        pdf.close()
    if checked == 0:
        return [TextLayerCheck("A_TEXT_LAYER_READ_PASS", False, "no translated frames")]
    return [
        TextLayerCheck(name, not values, f"{checked} translated frames checked" if not values else f"failed: {sorted(set(values))}",
                       tuple(sorted(set(values))), tuple(statistics) if name == "A_COPY_TEXT_FIDELITY_PASS" else ())
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
