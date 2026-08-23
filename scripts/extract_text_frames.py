#!/usr/bin/env python3
"""Extract review-required source text-frame candidates from a paginated PDF."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import pdfplumber
except ImportError:  # pragma: no cover - exercised by CLI dependency check
    pdfplumber = None


class FrameExtractionError(ValueError):
    """Raised when a PDF cannot produce a defensible frame inventory."""


def _require_pdfplumber() -> None:
    if pdfplumber is None:
        raise FrameExtractionError(
            "pdfplumber is required. Run with the bundled Codex PDF Python runtime "
            "or install requirements-exact-mirror.txt."
        )


def _line_groups(chars: list[dict[str, Any]], tolerance: float = 2.0) -> list[list[dict[str, Any]]]:
    lines: list[list[dict[str, Any]]] = []
    for char in sorted(chars, key=lambda item: (float(item["top"]), float(item["x0"]))):
        if not str(char.get("text", "")).strip():
            continue
        if not lines or abs(float(char["top"]) - statistics.median(float(c["top"]) for c in lines[-1])) > tolerance:
            lines.append([char])
        else:
            lines[-1].append(char)
    return lines


def _line_record(chars: list[dict[str, Any]]) -> dict[str, Any]:
    chars = sorted(chars, key=lambda item: float(item["x0"]))
    return {
        "text": "".join(str(char.get("text", "")) for char in chars).strip(),
        "x0": min(float(char["x0"]) for char in chars),
        "x1": max(float(char["x1"]) for char in chars),
        "top": min(float(char["top"]) for char in chars),
        "bottom": max(float(char["bottom"]) for char in chars),
        "fontname": Counter(str(char.get("fontname") or "UNKNOWN") for char in chars).most_common(1)[0][0],
        "size": statistics.median(float(char.get("size") or 0.0) for char in chars),
    }


def _same_column(first: dict[str, Any], second: dict[str, Any], page_width: float) -> bool:
    overlap = min(first["x1"], second["x1"]) - max(first["x0"], second["x0"])
    minimum_width = min(first["x1"] - first["x0"], second["x1"] - second["x0"])
    if overlap >= minimum_width * 0.5:
        return True
    midpoint_first = (first["x0"] + first["x1"]) / 2
    midpoint_second = (second["x0"] + second["x1"]) / 2
    return abs(midpoint_first - midpoint_second) <= page_width * 0.08


def _blocks(lines: list[dict[str, Any]], page_width: float) -> list[list[dict[str, Any]]]:
    if not lines:
        return []
    blocks: list[list[dict[str, Any]]] = [[lines[0]]]
    for line in lines[1:]:
        previous = blocks[-1][-1]
        gap = line["top"] - previous["bottom"]
        expected = max(previous["size"], line["size"]) * 0.85
        paragraph_indent = abs(line["x0"] - previous["x0"]) > max(12.0, page_width * 0.025)
        if gap <= expected and _same_column(previous, line, page_width) and not paragraph_indent:
            blocks[-1].append(line)
        else:
            blocks.append([line])
    return blocks


def _kind(block: list[dict[str, Any]], page_height: float, body_size: float) -> str:
    top = min(line["top"] for line in block)
    bottom = max(line["bottom"] for line in block)
    size = statistics.median(line["size"] for line in block)
    if top < page_height * 0.06:
        return "page_header"
    if bottom > page_height * 0.94:
        return "page_footer"
    if size >= max(14.0, body_size * 1.7):
        return "title"
    if size >= body_size * 1.15:
        return "heading"
    return "body"


def extract_frames(source_pdf: Path, source_id: str) -> list[dict[str, Any]]:
    _require_pdfplumber()
    if not source_pdf.is_file() or source_pdf.suffix.lower() != ".pdf":
        raise FrameExtractionError(f"Source PDF is missing or invalid: {source_pdf}")
    rows: list[dict[str, Any]] = []
    with pdfplumber.open(source_pdf) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            chars = [char for char in page.chars if str(char.get("text", "")).strip()]
            lines = [_line_record(group) for group in _line_groups(chars)]
            positive_sizes = [line["size"] for line in lines if line["size"] > 0]
            body_size = statistics.median(positive_sizes) if positive_sizes else 10.0
            reading_order = 0
            for block in _blocks(lines, float(page.width)):
                if not any(line["text"] for line in block):
                    continue
                reading_order += 1
                x0 = min(line["x0"] for line in block)
                x1 = max(line["x1"] for line in block)
                top = min(line["top"] for line in block)
                bottom = max(line["bottom"] for line in block)
                baselines = [line["top"] for line in block]
                leading = (
                    statistics.median(
                        baselines[index] - baselines[index - 1]
                        for index in range(1, len(baselines))
                    )
                    if len(baselines) > 1
                    else statistics.median(line["size"] for line in block) * 1.2
                )
                font = Counter(line["fontname"] for line in block).most_common(1)[0][0]
                weight = "bold" if "bold" in font.lower() else "regular"
                if "italic" in font.lower() or "oblique" in font.lower():
                    weight = f"{weight}-italic"
                frame_id = f"TF-{source_id}-P{page_number:03d}-{reading_order:03d}"
                unit_id = f"TU-{source_id}-P{page_number:03d}-{reading_order:03d}"
                rows.append(
                    {
                        "frame_id": frame_id,
                        "source_id": source_id,
                        "source_page": page_number,
                        "unit_id": unit_id,
                        "kind": _kind(block, float(page.height), body_size),
                        "bbox_pt": [x0, float(page.height) - bottom, x1, float(page.height) - top],
                        "rotation": int(page.rotation or 0) % 360,
                        "reading_order": reading_order,
                        "source_font": font,
                        "source_font_size_pt": statistics.median(line["size"] for line in block),
                        "source_leading_pt": float(leading),
                        "weight": weight,
                        "alignment": "left",
                        "background": "UNREVIEWED",
                        "translation_action": "TRANSLATE",
                        "source_text": "\n".join(line["text"] for line in block),
                        "reviewed": False,
                    }
                )
    if not rows:
        raise FrameExtractionError("No extractable text frames were found.")
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]], force: bool) -> None:
    if path.exists() and not force:
        raise FrameExtractionError(f"Refusing to overwrite {path}; use --force if intended.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-pdf", type=Path, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rows = extract_frames(args.source_pdf, args.source_id.strip())
        write_jsonl(args.output, rows, args.force)
    except (FrameExtractionError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Extracted {len(rows)} review-required text-frame candidates to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
