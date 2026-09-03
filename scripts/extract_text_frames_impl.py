#!/usr/bin/env python3
"""Implementation for exact text-frame candidate extraction.

The public CLI lives in extract_text_frames.py. This module keeps the spatial
heuristics testable while allowing targeted hardening without broad relayout.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import pdfplumber
    from pdfplumber.utils import collate_line
except ImportError:  # pragma: no cover
    pdfplumber = None
    collate_line = None


class FrameExtractionError(ValueError):
    """Raised when a PDF cannot produce a defensible frame inventory."""


LIGATURES = {"ﬀ", "ﬁ", "ﬂ", "ﬃ", "ﬄ"}
LIGATURE_MAP = str.maketrans(
    {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl"}
)


def _require_pdfplumber() -> None:
    if pdfplumber is None or collate_line is None:
        raise FrameExtractionError(
            "pdfplumber is required. Run with the bundled Codex PDF Python runtime "
            "or install requirements-exact-mirror.txt."
        )


def _only_ligatures(chars: list[dict[str, Any]]) -> bool:
    values = [str(char.get("text", "")) for char in chars if str(char.get("text", "")).strip()]
    return bool(values) and all(value in LIGATURES for value in values)


def _merge_isolated_ligatures(
    lines: list[list[dict[str, Any]]], tolerance: float = 2.0
) -> list[list[dict[str, Any]]]:
    """Attach isolated ligature glyphs after full line extents are known.

    Journal PDFs can vertically shift a ligature by several points. On a two-
    column page, applying the expanded tolerance while streaming top-to-bottom
    can attach that glyph to a temporally adjacent line in the other column.
    We therefore keep the conservative first pass, split columns, then attach
    a ligature-only fragment to the unique nearest complete line whose vertical
    distance and horizontal extent are compatible.
    """

    isolated = [line for line in lines if _only_ligatures(line)]
    remaining = [line for line in lines if not _only_ligatures(line)]
    for ligature_line in isolated:
        ligature_top = statistics.median(float(char["top"]) for char in ligature_line)
        ligature_sizes = [float(char.get("size") or 0.0) for char in ligature_line]
        ligature_x0 = min(float(char["x0"]) for char in ligature_line)
        ligature_x1 = max(float(char["x1"]) for char in ligature_line)
        candidates: list[tuple[float, float, int]] = []
        for index, line in enumerate(remaining):
            line_top = statistics.median(float(char["top"]) for char in line)
            sizes = ligature_sizes + [float(char.get("size") or 0.0) for char in line]
            median_size = statistics.median(sizes) if sizes else 0.0
            maximum_delta = max(tolerance, median_size * 0.45)
            vertical_delta = abs(ligature_top - line_top)
            if vertical_delta > maximum_delta:
                continue
            line_x0 = min(float(char["x0"]) for char in line)
            line_x1 = max(float(char["x1"]) for char in line)
            horizontal_gap = max(
                line_x0 - ligature_x1,
                ligature_x0 - line_x1,
                0.0,
            )
            if horizontal_gap > max(12.0, median_size * 2.0):
                continue
            candidates.append((vertical_delta, horizontal_gap, index))
        if candidates:
            _, _, target = min(candidates)
            remaining[target].extend(ligature_line)
        else:
            remaining.append(ligature_line)
    return sorted(
        remaining,
        key=lambda line: (
            min(float(char["top"]) for char in line),
            min(float(char["x0"]) for char in line),
        ),
    )


def _line_groups(
    chars: list[dict[str, Any]], page_width: float, tolerance: float = 2.0
) -> list[list[dict[str, Any]]]:
    bands: list[list[dict[str, Any]]] = []
    for char in sorted(chars, key=lambda item: (float(item["top"]), float(item["x0"]))):
        if str(char.get("text", "")) == "":
            continue
        if not bands:
            bands.append([char])
            continue
        band = bands[-1]
        delta = abs(
            float(char["top"])
            - statistics.median(float(candidate["top"]) for candidate in band)
        )
        has_ligature = str(char.get("text", "")) in LIGATURES or any(
            str(candidate.get("text", "")) in LIGATURES for candidate in band
        )
        if has_ligature:
            sizes = [float(candidate.get("size") or 0.0) for candidate in band] + [
                float(char.get("size") or 0.0)
            ]
            effective_tolerance = max(tolerance, statistics.median(sizes) * 0.45)
        else:
            effective_tolerance = tolerance
        if delta > effective_tolerance:
            bands.append([char])
        else:
            bands[-1].append(char)

    lines: list[list[dict[str, Any]]] = []
    gap_threshold = max(12.0, page_width * 0.02)
    for band in bands:
        current: list[dict[str, Any]] = []
        previous_x1: float | None = None
        for char in sorted(band, key=lambda item: float(item["x0"])):
            x0 = float(char["x0"])
            x1 = float(char["x1"])
            if current and previous_x1 is not None and x0 - previous_x1 > gap_threshold:
                lines.append(current)
                current = []
            current.append(char)
            previous_x1 = x1 if previous_x1 is None else max(previous_x1, x1)
        if current:
            lines.append(current)
    return _merge_isolated_ligatures(lines, tolerance)


def _line_record(chars: list[dict[str, Any]]) -> dict[str, Any]:
    chars = sorted(chars, key=lambda item: float(item["x0"]))
    content_chars = [char for char in chars if str(char.get("text", "")).strip()]
    return {
        "text": collate_line(chars, tolerance=1.0).strip().translate(LIGATURE_MAP),
        "x0": min(float(char["x0"]) for char in chars),
        "x1": max(float(char["x1"]) for char in chars),
        "top": min(float(char["top"]) for char in chars),
        "bottom": max(float(char["bottom"]) for char in chars),
        "fontname": Counter(
            str(char.get("fontname") or "UNKNOWN") for char in content_chars
        ).most_common(1)[0][0],
        "size": statistics.median(float(char.get("size") or 0.0) for char in content_chars),
    }


def _table_candidates(page: Any) -> list[Any]:
    default_tables = list(page.find_tables())
    tables: list[Any] = []
    for table in default_tables:
        max_columns = max(
            (sum(cell is not None for cell in row.cells) for row in table.rows),
            default=0,
        )
        if len(table.rows) >= 2 and max_columns >= 2:
            tables.append(table)
    if tables:
        return tables
    text = page.extract_text() or ""
    if not re.search(r"(?mi)^\s*Table\s+[A-Z]?\d+", text):
        return []
    try:
        candidates = page.find_tables(
            table_settings={
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
                "intersection_tolerance": 5,
            }
        )
    except Exception:
        return []
    accepted: list[Any] = []
    for table in candidates:
        first_row = table.rows[0].cells if table.rows else []
        columns = sum(cell is not None for cell in first_row)
        width = float(table.bbox[2]) - float(table.bbox[0])
        if columns >= 3 and width >= float(page.width) * 0.35:
            accepted.append(table)
    return accepted


def _annotate_table_cells(lines: list[dict[str, Any]], tables: list[Any]) -> None:
    cells: list[tuple[tuple[int, int], tuple[float, float, float, float]]] = []
    for table_index, table in enumerate(tables, 1):
        for cell_index, cell in enumerate(table.cells, 1):
            if cell is not None:
                cells.append(((table_index, cell_index), tuple(float(value) for value in cell)))
    for line in lines:
        cx = (float(line["x0"]) + float(line["x1"])) / 2
        cy = (float(line["top"]) + float(line["bottom"])) / 2
        matches = []
        for cell_id, bbox in cells:
            if bbox[0] - 0.5 <= cx <= bbox[2] + 0.5 and bbox[1] - 0.5 <= cy <= bbox[3] + 0.5:
                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                matches.append((area, cell_id, bbox))
        if matches:
            _, cell_id, bbox = min(matches, key=lambda item: item[0])
            line["_table_cell_id"] = cell_id
            line["_table_cell_bbox"] = bbox


def _annotate_row_peers(lines: list[dict[str, Any]], tolerance: float = 2.0) -> None:
    bands: list[list[dict[str, Any]]] = []
    for line in sorted(lines, key=lambda item: (float(item["top"]), float(item["x0"]))):
        if not bands or abs(
            float(line["top"])
            - statistics.median(float(item["top"]) for item in bands[-1])
        ) > tolerance:
            bands.append([line])
        else:
            bands[-1].append(line)
    for band in bands:
        page_span = max(float(item["x1"]) for item in band) - min(float(item["x0"]) for item in band)
        minimum_segment = max(10.0, page_span * 0.02)
        count = sum(
            (float(item["x1"]) - float(item["x0"])) >= minimum_segment for item in band
        )
        for line in band:
            line["_row_peer_count"] = count


def _margin_identifier_frames(page: Any, source_id: str, page_number: int) -> list[dict[str, Any]]:
    width = float(page.width)
    height = float(page.height)
    rotated = [
        char
        for char in page.chars
        if not bool(char.get("upright", True))
        and (float(char["x0"]) < width * 0.05 or float(char["x1"]) > width * 0.95)
        and str(char.get("text", "")) != ""
    ]
    if not rotated:
        return []
    groups: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for char in rotated:
        side = "left" if float(char["x0"]) < width * 0.5 else "right"
        matrix = char.get("matrix") or (1, 0, 0, 1, 0, 0)
        rotation = 270 if float(matrix[1]) < 0 else 90
        groups.setdefault((side, rotation), []).append(char)
    rows: list[dict[str, Any]] = []
    for index, ((_, rotation), chars) in enumerate(sorted(groups.items()), 1):
        chars = sorted(chars, key=lambda item: (float(item["top"]), float(item["x0"])))
        text = "".join(str(char.get("text", "")) for char in chars).strip()
        content_chars = [char for char in chars if str(char.get("text", "")).strip()]
        if not text or not content_chars:
            continue
        x0 = min(float(char["x0"]) for char in chars)
        x1 = max(float(char["x1"]) for char in chars)
        top = min(float(char["top"]) for char in chars)
        bottom = max(float(char["bottom"]) for char in chars)
        font = Counter(str(char.get("fontname") or "UNKNOWN") for char in content_chars).most_common(1)[0][0]
        size = statistics.median(float(char.get("size") or 0.0) for char in content_chars)
        frame_id = f"TF-{source_id}-P{page_number:03d}-M{index:02d}"
        rows.append(
            {
                "frame_id": frame_id,
                "source_id": source_id,
                "source_page": page_number,
                "unit_id": frame_id.replace("TF-", "TU-", 1),
                "kind": "identifier",
                "bbox_pt": [x0, height - bottom, x1, height - top],
                "rotation": rotation,
                "reading_order": 1,
                "source_font": font,
                "source_font_size_pt": size,
                "source_leading_pt": max(size * 1.2, 0.1),
                "weight": "regular",
                "alignment": "left",
                "background": "UNREVIEWED",
                "translation_action": "RETAIN_SOURCE",
                "retain_reason": "IDENTIFIER",
                "source_text": text,
                "reviewed": False,
            }
        )
    return rows


def _line_number_identifier_frames(
    page: Any, source_id: str, page_number: int
) -> tuple[list[dict[str, Any]], set[int]]:
    width = float(page.width)
    height = float(page.height)
    gutter_chars = [
        char
        for char in page.chars
        if bool(char.get("upright", True))
        and str(char.get("text", "")) != ""
        and (float(char["x1"]) < width * 0.09 or float(char["x0"]) > width * 0.91)
    ]
    if not gutter_chars:
        return [], set()
    records: list[tuple[list[dict[str, Any]], dict[str, Any]]] = []
    for group in _line_groups(gutter_chars, width):
        if not any(str(char.get("text", "")).strip() for char in group):
            continue
        record = _line_record(group)
        if re.fullmatch(r"\d{1,4}", record["text"]):
            records.append((group, record))
    if len(records) < 3:
        return [], set()
    by_side: dict[str, list[tuple[list[dict[str, Any]], dict[str, Any]]]] = {}
    for group, record in records:
        midpoint = (float(record["x0"]) + float(record["x1"])) / 2
        side = "left" if midpoint < width / 2 else "right"
        by_side.setdefault(side, []).append((group, record))
    rows: list[dict[str, Any]] = []
    excluded: set[int] = set()
    for index, (_, items) in enumerate(sorted(by_side.items()), 1):
        if len(items) < 3:
            continue
        items.sort(key=lambda item: float(item[1]["top"]))
        values = [int(item[1]["text"]) for item in items]
        sequential_pairs = sum(
            1 for first, second in zip(values, values[1:]) if 0 < second - first <= 3
        )
        if sequential_pairs < max(2, len(values) // 2):
            continue
        all_chars = [char for group, _ in items for char in group]
        excluded.update(id(char) for char in all_chars)
        x0 = min(float(char["x0"]) for char in all_chars)
        x1 = max(float(char["x1"]) for char in all_chars)
        top = min(float(char["top"]) for char in all_chars)
        bottom = max(float(char["bottom"]) for char in all_chars)
        content_chars = [char for char in all_chars if str(char.get("text", "")).strip()]
        font = Counter(str(char.get("fontname") or "UNKNOWN") for char in content_chars).most_common(1)[0][0]
        size = statistics.median(float(char.get("size") or 0.0) for char in content_chars)
        frame_id = f"TF-{source_id}-P{page_number:03d}-L{index:02d}"
        rows.append(
            {
                "frame_id": frame_id,
                "source_id": source_id,
                "source_page": page_number,
                "unit_id": frame_id.replace("TF-", "TU-", 1),
                "kind": "identifier",
                "bbox_pt": [x0, height - bottom, x1, height - top],
                "rotation": 0,
                "reading_order": 1,
                "source_font": font,
                "source_font_size_pt": size,
                "source_leading_pt": max(size * 1.2, 0.1),
                "weight": "regular",
                "alignment": "left",
                "background": "UNREVIEWED",
                "translation_action": "RETAIN_SOURCE",
                "retain_reason": "IDENTIFIER",
                "source_text": "\n".join(str(value) for value in values),
                "reviewed": False,
            }
        )
    return rows, excluded


def _same_column(first: dict[str, Any], second: dict[str, Any], page_width: float) -> bool:
    overlap = min(first["x1"], second["x1"]) - max(first["x0"], second["x0"])
    minimum_width = min(first["x1"] - first["x0"], second["x1"] - second["x0"])
    if overlap >= minimum_width * 0.5:
        return True
    return abs(
        (first["x0"] + first["x1"]) / 2 - (second["x0"] + second["x1"]) / 2
    ) <= page_width * 0.08


def _blocks(lines: list[dict[str, Any]], page_width: float) -> list[list[dict[str, Any]]]:
    blocks: list[list[dict[str, Any]]] = []
    for line in sorted(lines, key=lambda item: (float(item["top"]), float(item["x0"]))):
        best_index = None
        best_gap = None
        line_cell = line.get("_table_cell_id")
        for index in range(len(blocks) - 1, -1, -1):
            previous = blocks[index][-1]
            previous_cell = previous.get("_table_cell_id")
            if line_cell is not None or previous_cell is not None:
                if line_cell != previous_cell:
                    continue
            elif int(line.get("_row_peer_count", 0)) >= 3 or int(previous.get("_row_peer_count", 0)) >= 3:
                continue
            gap = float(line["top"]) - float(previous["bottom"])
            if gap < -2:
                continue
            expected = max(float(previous["size"]), float(line["size"])) * 0.85
            if gap > expected:
                continue
            indent = abs(float(line["x0"]) - float(previous["x0"])) > max(12.0, page_width * 0.025)
            maximum_size = max(float(previous["size"]), float(line["size"]), 1.0)
            style_change = abs(float(line["size"]) - float(previous["size"])) > max(1.0, maximum_size * 0.12)
            if _same_column(previous, line, page_width) and not indent and not style_change:
                if best_gap is None or gap < best_gap:
                    best_index = index
                    best_gap = gap
        if best_index is None:
            blocks.append([line])
        else:
            blocks[best_index].append(line)
    return sorted(blocks, key=lambda block: (float(block[0]["top"]), float(block[0]["x0"])))


def _kind(block: list[dict[str, Any]], page_height: float, body_size: float) -> str:
    if any(line.get("_table_cell_id") is not None for line in block):
        return "table_cell"
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
    rows: list[dict[str, Any]] = []
    with pdfplumber.open(source_pdf) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            margin_rows = _margin_identifier_frames(page, source_id, page_number)
            line_number_rows, excluded_line_number_chars = _line_number_identifier_frames(
                page, source_id, page_number
            )
            chars = [
                char
                for char in page.chars
                if str(char.get("text", "")) != ""
                and bool(char.get("upright", True))
                and id(char) not in excluded_line_number_chars
            ]
            lines = [
                _line_record(group)
                for group in _line_groups(chars, float(page.width))
                if any(str(char.get("text", "")).strip() for char in group)
            ]
            _annotate_table_cells(lines, _table_candidates(page))
            _annotate_row_peers(lines)
            candidates = [
                round(float(char.get("size") or 0.0), 1)
                for char in chars
                if str(char.get("text", "")).strip()
                and 5.0 <= float(char.get("size") or 0.0) <= 14.0
            ]
            body_size = Counter(candidates).most_common(1)[0][0] if candidates else 10.0
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
            retained_rows = margin_rows + line_number_rows
            for retained_index, retained_row in enumerate(retained_rows, reading_order + 1):
                retained_row["reading_order"] = retained_index
                rows.append(retained_row)
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
