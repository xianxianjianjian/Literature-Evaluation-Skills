#!/usr/bin/env python3
"""Shared schema and geometry helpers for exact text-frame mirror PDFs."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

EXACT_LAYOUT_FIDELITY = "EXACT_TEXT_FRAME"
STRUCTURAL_LAYOUT_FIDELITY = "STRUCTURAL_MIRROR"
LEGACY_LAYOUT_FIDELITY = "LEGACY_STRUCTURAL"
REQUIRED_CJK_FONT = "SimSun"
MINIMUM_FONT_SCALE = 0.95
MAXIMUM_FONT_SCALE = 1.0
FONT_SCALE_STEPS = (1.0, 0.99, 0.98, 0.97, 0.96, 0.95)
FRAME_ACTIONS = {"TRANSLATE", "RETAIN_SOURCE"}
FRAME_KINDS = {
    "title",
    "author",
    "affiliation",
    "heading",
    "abstract",
    "body",
    "caption",
    "footnote",
    "page_header",
    "page_footer",
    "table_cell",
    "figure_label",
    "reference",
    "formula",
    "identifier",
    "logo",
    "other",
}
RETAIN_REASONS = {
    "AUTHOR_NAME",
    "REFERENCE_ENTRY",
    "FORMULA",
    "IDENTIFIER",
    "JOURNAL_LOGO",
    "TRADEMARK",
    "SOURCE_GAP",
}
FIT_STATUSES = {"FIT", "OVERFLOW", "SOURCE_GAP", "RETAINED"}
PAGE_BOX_FIELDS = ("media_box", "crop_box", "trim_box", "bleed_box", "art_box")
CJK_PATTERN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


class ExactMirrorError(ValueError):
    """Raised when exact-mirror evidence is incomplete or inconsistent."""


def load_json(path: Path, label: str) -> Any:
    if not path.is_file():
        raise ExactMirrorError(f"{label} does not exist: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExactMirrorError(f"Invalid {label} JSON: {exc}") from exc


def load_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ExactMirrorError(f"{label} does not exist: {path}")
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ExactMirrorError(
                f"Invalid {label} JSONL at line {line_number}: {exc}"
            ) from exc
        if not isinstance(row, dict):
            raise ExactMirrorError(f"{label} line {line_number} must be an object.")
        rows.append(row)
    return rows


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_bbox(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 4 or not all(finite_number(v) for v in value):
        raise ExactMirrorError(f"{label} must be four finite numbers.")
    bbox = [float(item) for item in value]
    if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
        raise ExactMirrorError(f"{label} must have positive width and height.")
    return bbox


def validate_page_box(value: Any, label: str) -> list[float]:
    return validate_bbox(value, label)


def source_key(source_id: Any, source_page: Any) -> tuple[str, int] | None:
    if not nonempty_text(source_id) or not positive_int(source_page):
        return None
    return source_id.strip(), source_page


def validate_exact_inventory(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ExactMirrorError("source inventory root must be an object.")
    if data.get("schema_version") != 2:
        raise ExactMirrorError("EXACT_TEXT_FRAME requires source_inventory schema_version 2.")
    if data.get("scope") != "FULL_MIRROR":
        raise ExactMirrorError("Exact mirror inventory scope must be FULL_MIRROR.")
    if data.get("layout_fidelity") != EXACT_LAYOUT_FIDELITY:
        raise ExactMirrorError("Exact mirror inventory must declare layout_fidelity=EXACT_TEXT_FRAME.")
    sources = data.get("sources")
    pages = data.get("pages")
    objects = data.get("objects")
    if not isinstance(sources, list) or not sources:
        raise ExactMirrorError("Exact source inventory requires sources.")
    if not isinstance(pages, list) or not pages:
        raise ExactMirrorError("Exact source inventory requires pages.")
    if not isinstance(objects, list):
        raise ExactMirrorError("Exact source inventory requires an objects list.")

    source_counts: dict[str, int] = {}
    for index, source in enumerate(sources, 1):
        if not isinstance(source, dict):
            raise ExactMirrorError(f"sources[{index}] must be an object.")
        source_id = source.get("source_id")
        if not nonempty_text(source_id) or source_id in source_counts:
            raise ExactMirrorError(f"sources[{index}] has invalid or duplicate source_id.")
        if source.get("role") not in {"MAIN", "SI"}:
            raise ExactMirrorError(f"sources[{index}] role must be MAIN or SI.")
        if not positive_int(source.get("page_count")):
            raise ExactMirrorError(f"sources[{index}] page_count must be positive.")
        if not nonempty_text(source.get("pdf_path")):
            raise ExactMirrorError(f"sources[{index}] pdf_path is required.")
        source_counts[source_id] = source["page_count"]

    seen_pages: set[tuple[str, int]] = set()
    seen_outputs: set[int] = set()
    for index, page in enumerate(pages, 1):
        if not isinstance(page, dict):
            raise ExactMirrorError(f"pages[{index}] must be an object.")
        key = source_key(page.get("source_id"), page.get("source_page"))
        if key is None or key in seen_pages:
            raise ExactMirrorError(f"pages[{index}] has invalid or duplicate source page.")
        if key[0] not in source_counts or key[1] > source_counts[key[0]]:
            raise ExactMirrorError(f"pages[{index}] references an unknown source page.")
        output_page = page.get("output_page")
        if not positive_int(output_page) or output_page in seen_outputs:
            raise ExactMirrorError(f"pages[{index}] has invalid or duplicate output_page.")
        for field in PAGE_BOX_FIELDS:
            validate_page_box(page.get(field), f"pages[{index}].{field}")
        rotation = page.get("rotation")
        if rotation not in {0, 90, 180, 270}:
            raise ExactMirrorError(f"pages[{index}].rotation must be 0/90/180/270.")
        for list_field in ("unit_ids", "object_ids", "frame_ids"):
            value = page.get(list_field)
            if not isinstance(value, list) or not all(nonempty_text(item) for item in value):
                raise ExactMirrorError(f"pages[{index}].{list_field} must be a list of IDs.")
        seen_pages.add(key)
        seen_outputs.add(output_page)
    expected_pages = {
        (source_id, page)
        for source_id, count in source_counts.items()
        for page in range(1, count + 1)
    }
    if seen_pages != expected_pages:
        raise ExactMirrorError(
            f"Inventory page coverage mismatch: missing={sorted(expected_pages-seen_pages)}; "
            f"extra={sorted(seen_pages-expected_pages)}"
        )
    if seen_outputs != set(range(1, len(pages) + 1)):
        raise ExactMirrorError("Inventory output_page values must be contiguous from 1.")
    page_frame_ids = {frame_id for page in pages for frame_id in page["frame_ids"]}
    page_object_ids = {object_id for page in pages for object_id in page["object_ids"]}
    seen_objects: set[str] = set()
    for index, item in enumerate(objects, 1):
        if not isinstance(item, dict):
            raise ExactMirrorError(f"objects[{index}] must be an object.")
        object_id = item.get("object_id")
        if not nonempty_text(object_id) or object_id in seen_objects:
            raise ExactMirrorError(f"objects[{index}] has invalid or duplicate object_id.")
        if item.get("kind") not in {"figure", "table"}:
            raise ExactMirrorError(f"object {object_id} kind must be figure or table.")
        key = source_key(item.get("source_id"), item.get("source_page"))
        if key not in seen_pages:
            raise ExactMirrorError(f"object {object_id} references an unknown source page.")
        validate_bbox(item.get("bbox_pt"), f"object {object_id}.bbox_pt")
        label_frames = item.get("label_frame_ids", [])
        if not isinstance(label_frames, list) or not all(
            nonempty_text(frame_id) and frame_id in page_frame_ids for frame_id in label_frames
        ):
            raise ExactMirrorError(f"object {object_id} has invalid label_frame_ids.")
        if item["kind"] == "table":
            structure = item.get("table_structure")
            cells = item.get("cells")
            if not isinstance(structure, dict) or not all(
                isinstance(structure.get(field), int) and structure[field] >= 0
                for field in ("rows", "columns", "header_rows", "merged_cells", "footnotes")
            ):
                raise ExactMirrorError(f"table {object_id} requires table_structure.")
            if structure["rows"] <= 0 or structure["columns"] <= 0:
                raise ExactMirrorError(f"table {object_id} rows/columns must be positive.")
            if not isinstance(cells, list) or not cells:
                raise ExactMirrorError(f"table {object_id} requires cell evidence.")
            for cell_index, cell in enumerate(cells, 1):
                if not isinstance(cell, dict):
                    raise ExactMirrorError(f"table {object_id} cell {cell_index} must be an object.")
                for field in ("row", "column", "row_span", "column_span"):
                    if not positive_int(cell.get(field)):
                        raise ExactMirrorError(f"table {object_id} cell {cell_index} requires {field}.")
                validate_bbox(cell.get("bbox_pt"), f"table {object_id} cell {cell_index}.bbox_pt")
                if not nonempty_text(cell.get("frame_id")) or cell["frame_id"] not in page_frame_ids:
                    raise ExactMirrorError(f"table {object_id} cell {cell_index} requires a known frame_id.")
        seen_objects.add(object_id)
    if seen_objects != page_object_ids:
        raise ExactMirrorError(
            f"Object coverage mismatch: missing={sorted(page_object_ids-seen_objects)}; "
            f"extra={sorted(seen_objects-page_object_ids)}"
        )
    return data


def validate_text_frames(
    rows: list[dict[str, Any]], inventory: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    page_keys = {
        (page["source_id"], page["source_page"]): page for page in inventory["pages"]
    }
    frames: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows, 1):
        frame_id = row.get("frame_id")
        if not nonempty_text(frame_id) or frame_id in frames:
            raise ExactMirrorError(f"text frame {index} has invalid or duplicate frame_id.")
        key = source_key(row.get("source_id"), row.get("source_page"))
        if key not in page_keys:
            raise ExactMirrorError(f"text frame {frame_id} references an unknown source page.")
        if not nonempty_text(row.get("unit_id")):
            raise ExactMirrorError(f"text frame {frame_id} requires unit_id.")
        if row.get("kind") not in FRAME_KINDS:
            raise ExactMirrorError(f"text frame {frame_id} has invalid kind.")
        validate_bbox(row.get("bbox_pt"), f"text frame {frame_id}.bbox_pt")
        if row.get("rotation") not in {0, 90, 180, 270}:
            raise ExactMirrorError(f"text frame {frame_id} has invalid rotation.")
        if not positive_int(row.get("reading_order")):
            raise ExactMirrorError(f"text frame {frame_id} requires positive reading_order.")
        for field in ("source_font", "alignment", "background"):
            if not nonempty_text(row.get(field)):
                raise ExactMirrorError(f"text frame {frame_id} requires {field}.")
        for field in ("source_font_size_pt", "source_leading_pt"):
            if not finite_number(row.get(field)) or float(row[field]) <= 0:
                raise ExactMirrorError(f"text frame {frame_id} requires positive {field}.")
        action = row.get("translation_action")
        if action not in FRAME_ACTIONS:
            raise ExactMirrorError(f"text frame {frame_id} has invalid translation_action.")
        if action == "RETAIN_SOURCE" and row.get("retain_reason") not in RETAIN_REASONS:
            raise ExactMirrorError(f"retained text frame {frame_id} requires retain_reason.")
        if row.get("reviewed") is not True:
            raise ExactMirrorError(f"text frame {frame_id} must be visually reviewed.")
        frames[frame_id] = row

    inventory_ids = {
        frame_id for page in inventory["pages"] for frame_id in page.get("frame_ids", [])
    }
    if set(frames) != inventory_ids:
        raise ExactMirrorError(
            f"Frame coverage mismatch: missing={sorted(inventory_ids-set(frames))}; "
            f"extra={sorted(set(frames)-inventory_ids)}"
        )
    return frames


def validate_font_map(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ExactMirrorError("font_map.json schema_version must be 1.")
    if data.get("cjk_font_family") != REQUIRED_CJK_FONT:
        raise ExactMirrorError("Exact mirror requires cjk_font_family=SimSun.")
    if not nonempty_text(data.get("font_path")):
        raise ExactMirrorError("font_map.json requires font_path.")
    if data.get("ttc_face_index") != 0:
        raise ExactMirrorError("SimSun ttc_face_index must be 0.")
    if data.get("fallback_allowed") is not False:
        raise ExactMirrorError("Exact mirror font fallback must be disabled.")
    if data.get("bold_mode") != "synthetic-stroke" or data.get("italic_mode") != "synthetic-shear":
        raise ExactMirrorError("font_map.json must declare the SimSun synthetic style modes.")
    return data


def validate_exact_ledger(
    rows: Iterable[dict[str, Any]], frames: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    ledger: dict[str, dict[str, Any]] = {}
    translated_frames = {
        frame_id for frame_id, frame in frames.items() if frame["translation_action"] == "TRANSLATE"
    }
    covered_frames: set[str] = set()
    for index, row in enumerate(rows, 1):
        unit_id = row.get("unit_id")
        if not nonempty_text(unit_id) or unit_id in ledger:
            raise ExactMirrorError(f"ledger row {index} has invalid or duplicate unit_id.")
        if source_key(row.get("source_id"), row.get("source_page")) is None:
            raise ExactMirrorError(f"ledger unit {unit_id} requires source_id/source_page.")
        if not nonempty_text(row.get("section")) or not positive_int(row.get("unit_index")):
            raise ExactMirrorError(f"ledger unit {unit_id} requires section/unit_index.")
        if not nonempty_text(row.get("kind")) or not nonempty_text(row.get("source_status")):
            raise ExactMirrorError(f"ledger unit {unit_id} requires kind/source_status.")
        if row.get("translation_status") != "TRANSLATED":
            raise ExactMirrorError(f"ledger unit {unit_id} must be TRANSLATED for exact rendering.")
        output_pages = row.get("output_pages")
        issue_ids = row.get("issue_ids")
        if not isinstance(output_pages, list) or not output_pages or not all(positive_int(page) for page in output_pages):
            raise ExactMirrorError(f"ledger unit {unit_id} requires output_pages.")
        if not isinstance(issue_ids, list) or not all(nonempty_text(issue) for issue in issue_ids):
            raise ExactMirrorError(f"ledger unit {unit_id} issue_ids must be a list of IDs.")
        frame_ids = row.get("frame_ids")
        if (
            not isinstance(frame_ids, list)
            or len(frame_ids) != 1
            or not all(nonempty_text(item) for item in frame_ids)
        ):
            raise ExactMirrorError(
                f"ledger unit {unit_id} must map to exactly one source text frame."
            )
        if any(frame_id not in translated_frames for frame_id in frame_ids):
            raise ExactMirrorError(f"ledger unit {unit_id} references a non-translated or unknown frame.")
        if not nonempty_text(row.get("source_text")) or not nonempty_text(row.get("translated_text")):
            raise ExactMirrorError(f"ledger unit {unit_id} requires source_text and translated_text.")
        scale = row.get("font_scale_used")
        if not finite_number(scale) or not MINIMUM_FONT_SCALE <= float(scale) <= MAXIMUM_FONT_SCALE:
            raise ExactMirrorError(f"ledger unit {unit_id} font_scale_used must be 0.95-1.00.")
        if row.get("fit_status") not in FIT_STATUSES:
            raise ExactMirrorError(f"ledger unit {unit_id} has invalid fit_status.")
        tokens = row.get("untranslated_tokens")
        if not isinstance(tokens, list) or not all(
            isinstance(token, dict)
            and nonempty_text(token.get("text"))
            and nonempty_text(token.get("reason"))
            for token in tokens
        ):
            raise ExactMirrorError(f"ledger unit {unit_id} untranslated_tokens is invalid.")
        covered_frames.update(frame_ids)
        ledger[unit_id] = row
    if covered_frames != translated_frames:
        raise ExactMirrorError(
            f"Translated-frame ledger coverage mismatch: missing={sorted(translated_frames-covered_frames)}; "
            f"extra={sorted(covered_frames-translated_frames)}"
        )
    return ledger


def contains_cjk(text: str) -> bool:
    return bool(CJK_PATTERN.search(text))


def bbox_contains(outer: list[float], inner: list[float], tolerance: float = 0.25) -> bool:
    return (
        inner[0] >= outer[0] - tolerance
        and inner[1] >= outer[1] - tolerance
        and inner[2] <= outer[2] + tolerance
        and inner[3] <= outer[3] + tolerance
    )


def bbox_intersects(first: list[float], second: list[float]) -> bool:
    return not (
        first[2] <= second[0]
        or second[2] <= first[0]
        or first[3] <= second[1]
        or second[3] <= first[1]
    )
