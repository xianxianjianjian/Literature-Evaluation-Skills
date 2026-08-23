#!/usr/bin/env python3
"""Independently validate evidence and exact layout behind a translated PDF."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from exact_mirror import (
    EXACT_LAYOUT_FIDELITY,
    LEGACY_LAYOUT_FIDELITY,
    MINIMUM_FONT_SCALE,
    REQUIRED_CJK_FONT,
    STRUCTURAL_LAYOUT_FIDELITY,
    ExactMirrorError,
    bbox_contains,
    contains_cjk,
    load_json as load_exact_json,
    load_jsonl as load_exact_jsonl,
    validate_exact_inventory,
    validate_exact_ledger,
    validate_font_map,
    validate_text_frames,
)
from mirror_pdf import MirrorPlanError, validate_plan_data

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - dependency check
    PdfReader = None

try:
    import pdfplumber
except ImportError:  # pragma: no cover - dependency check
    pdfplumber = None

try:
    import numpy as np
    from PIL import Image
except ImportError:  # pragma: no cover - dependency check
    np = Image = None

SCOPES = {"FULL_MIRROR", "MAIN_ONLY", "ABSTRACT_ONLY"}
INVENTORY_FILE = "source_inventory.json"
LEDGER_FILE = "translation_ledger.jsonl"
PLAN_FILE = "mirror_layout_plan.json"
ISSUES_FILE = "translation_issues.jsonl"
FRAMES_FILE = "text_frame_inventory.jsonl"
FONT_MAP_FILE = "font_map.json"
LAYOUT_DIFF_FILE = "layout_diff.json"
LAYOUT_FIDELITIES = {
    EXACT_LAYOUT_FIDELITY,
    STRUCTURAL_LAYOUT_FIDELITY,
    LEGACY_LAYOUT_FIDELITY,
}


@dataclass(frozen=True)
class TranslationCheck:
    code: str
    passed: bool
    detail: str


class TranslationPackageError(ValueError):
    """Raised when a translation package cannot be parsed."""


def _load_json(path: Path, label: str) -> Any:
    if not path.is_file():
        raise TranslationPackageError(f"{label} missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise TranslationPackageError(f"{label} is invalid JSON: {exc}") from exc


def _load_jsonl(path: Path, label: str, *, required: bool = True) -> list[dict[str, Any]]:
    if not path.is_file():
        if required:
            raise TranslationPackageError(f"{label} missing: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TranslationPackageError(
                f"{label} line {line_number} is invalid JSON: {exc}"
            ) from exc
        if not isinstance(row, dict):
            raise TranslationPackageError(f"{label} line {line_number} must be an object")
        rows.append(row)
    return rows


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _identifier_map(
    rows: Any,
    field: str,
    label: str,
    checks: list[TranslationCheck],
    *,
    require_nonempty: bool = True,
) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        checks.append(TranslationCheck(f"inventory:{label}", False, f"{label} must be a list"))
        return {}
    result: dict[str, dict[str, Any]] = {}
    invalid = 0
    duplicates: list[str] = []
    for row in rows:
        if not isinstance(row, dict) or not _nonempty_text(row.get(field)):
            invalid += 1
            continue
        identifier = row[field].strip()
        if identifier in result:
            duplicates.append(identifier)
        else:
            result[identifier] = row
    passed = invalid == 0 and not duplicates and (bool(result) or not require_nonempty)
    detail = f"{len(result)} unique {label}"
    if invalid:
        detail += f"; {invalid} invalid record(s)"
    if duplicates:
        detail += f"; duplicate IDs: {', '.join(sorted(set(duplicates)))}"
    checks.append(TranslationCheck(f"inventory:{label}", passed, detail))
    return result


def _source_key(source_id: Any, source_page: Any) -> tuple[str, int] | None:
    if not _nonempty_text(source_id) or not _positive_int(source_page):
        return None
    return source_id.strip(), source_page


def _validate_inventory(data: Any, scope: str) -> tuple[list[TranslationCheck], dict[str, Any]]:
    checks: list[TranslationCheck] = []
    if not isinstance(data, dict):
        return [TranslationCheck("inventory:root", False, "inventory root must be an object")], {}
    checks.append(
        TranslationCheck(
            "inventory:schema",
            data.get("schema_version") == 1,
            f"schema_version={data.get('schema_version')!r}",
        )
    )
    checks.append(
        TranslationCheck(
            "inventory:scope",
            data.get("scope") == scope,
            f"inventory scope={data.get('scope')!r}; requested={scope}",
        )
    )
    sources = _identifier_map(data.get("sources"), "source_id", "sources", checks)
    units = _identifier_map(data.get("units"), "unit_id", "units", checks)
    objects = _identifier_map(
        data.get("objects"), "object_id", "objects", checks, require_nonempty=False
    )
    source_failures: list[str] = []
    for source_id, source in sources.items():
        if (
            source.get("role") not in {"MAIN", "SI"}
            or not _positive_int(source.get("page_count"))
            or not _nonempty_text(source.get("status"))
        ):
            source_failures.append(source_id)
    checks.append(
        TranslationCheck(
            "inventory:source-records",
            not source_failures,
            "all sources have role, page count and status"
            if not source_failures
            else f"invalid source records: {', '.join(source_failures)}",
        )
    )
    pages_raw = data.get("pages")
    pages: dict[tuple[str, int], dict[str, Any]] = {}
    invalid_pages = 0
    duplicate_pages: list[str] = []
    if isinstance(pages_raw, list):
        for page in pages_raw:
            if not isinstance(page, dict):
                invalid_pages += 1
                continue
            key = _source_key(page.get("source_id"), page.get("source_page"))
            if key is None or key[0] not in sources:
                invalid_pages += 1
                continue
            if key in pages:
                duplicate_pages.append(f"{key[0]}:p{key[1]}")
            else:
                pages[key] = page
    else:
        invalid_pages += 1
    checks.append(
        TranslationCheck(
            "inventory:pages",
            bool(pages) and invalid_pages == 0 and not duplicate_pages,
            f"{len(pages)} unique source pages; invalid={invalid_pages}; duplicates={len(duplicate_pages)}",
        )
    )
    expected_pages = {
        (source_id, page_number)
        for source_id, source in sources.items()
        if _positive_int(source.get("page_count"))
        for page_number in range(1, source["page_count"] + 1)
    }
    missing_inventory_pages = sorted(expected_pages - set(pages))
    unexpected_inventory_pages = sorted(set(pages) - expected_pages)
    checks.append(
        TranslationCheck(
            "inventory:page-count-coverage",
            not missing_inventory_pages and not unexpected_inventory_pages,
            "inventory enumerates every fixed-render source page"
            if not missing_inventory_pages and not unexpected_inventory_pages
            else f"missing={missing_inventory_pages}; unexpected={unexpected_inventory_pages}",
        )
    )

    unit_location_failures: list[str] = []
    for unit_id, unit in units.items():
        key = _source_key(unit.get("source_id"), unit.get("source_page"))
        if key not in pages or unit_id not in pages[key].get("unit_ids", []):
            unit_location_failures.append(unit_id)
    for key, page in pages.items():
        if not isinstance(page.get("unit_ids"), list) or any(
            unit_id not in units for unit_id in page.get("unit_ids", [])
        ):
            unit_location_failures.append(f"{key[0]}:p{key[1]}")
    checks.append(
        TranslationCheck(
            "inventory:unit-page-links",
            not unit_location_failures,
            "all units linked to source pages"
            if not unit_location_failures
            else f"units missing page links: {', '.join(unit_location_failures)}",
        )
    )

    object_failures: list[str] = []
    table_failures: list[str] = []
    for object_id, item in objects.items():
        key = _source_key(item.get("source_id"), item.get("source_page"))
        if (
            key not in pages
            or object_id not in pages[key].get("object_ids", [])
            or item.get("kind") not in {"figure", "table"}
        ):
            object_failures.append(object_id)
        if item.get("kind") == "table":
            shape = item.get("table_structure")
            if not isinstance(shape, dict) or not all(
                _positive_int(shape.get(field)) for field in ("rows", "columns", "header_rows")
            ):
                table_failures.append(object_id)
                continue
            if shape["header_rows"] > shape["rows"]:
                table_failures.append(object_id)
            for field in ("merged_cells", "footnotes"):
                value = shape.get(field)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    table_failures.append(object_id)
                    break
    for key, page in pages.items():
        if not isinstance(page.get("object_ids"), list) or any(
            object_id not in objects for object_id in page.get("object_ids", [])
        ):
            object_failures.append(f"{key[0]}:p{key[1]}")
    checks.append(
        TranslationCheck(
            "inventory:object-page-links",
            not object_failures,
            "all figure/table objects linked to source pages"
            if not object_failures
            else f"invalid object links: {', '.join(object_failures)}",
        )
    )
    checks.append(
        TranslationCheck(
            "inventory:table-structure",
            not table_failures,
            "all tables have source topology"
            if not table_failures
            else f"tables missing valid topology: {', '.join(sorted(set(table_failures)))}",
        )
    )
    return checks, {"sources": sources, "pages": pages, "units": units, "objects": objects}


def _validate_ledger(
    rows: list[dict[str, Any]],
    units: dict[str, dict[str, Any]] | None,
    issue_ids: set[str],
) -> tuple[list[TranslationCheck], dict[str, dict[str, Any]]]:
    checks: list[TranslationCheck] = []
    required = {
        "unit_id",
        "source_id",
        "source_page",
        "section",
        "unit_index",
        "kind",
        "source_status",
        "translation_status",
        "output_pages",
        "issue_ids",
    }
    ledger: dict[str, dict[str, Any]] = {}
    invalid_records: list[str] = []
    invalid_reasons: dict[str, int] = {}
    duplicate_ids: list[str] = []

    def record_invalid(label: str, reason: str) -> None:
        invalid_records.append(label)
        invalid_reasons[reason] = invalid_reasons.get(reason, 0) + 1

    for index, row in enumerate(rows, start=1):
        unit_id = row.get("unit_id")
        label = unit_id if _nonempty_text(unit_id) else f"line-{index}"
        if not required.issubset(row):
            for field in sorted(required - set(row)):
                invalid_reasons[f"missing {field}"] = invalid_reasons.get(
                    f"missing {field}", 0
                ) + 1
            invalid_records.append(str(label))
            continue
        if not _nonempty_text(unit_id) or unit_id in ledger:
            duplicate_ids.append(str(label))
            continue
        if (
            not _nonempty_text(row.get("source_id"))
            or not _positive_int(row.get("source_page"))
            or not _nonempty_text(row.get("section"))
            or not _positive_int(row.get("unit_index"))
            or not _nonempty_text(row.get("kind"))
            or not _nonempty_text(row.get("source_status"))
            or not isinstance(row.get("output_pages"), list)
            or not all(_positive_int(page) for page in row["output_pages"])
            or not isinstance(row.get("issue_ids"), list)
            or not all(_nonempty_text(issue_id) for issue_id in row["issue_ids"])
        ):
            record_invalid(str(label), "invalid field value or type")
            continue
        if row.get("translation_status") not in {"TRANSLATED", "SOURCE_GAP"}:
            record_invalid(str(label), "invalid translation_status")
            continue
        if row["translation_status"] == "TRANSLATED" and not row["output_pages"]:
            record_invalid(str(label), "translated unit has no output page")
            continue
        if row["translation_status"] == "SOURCE_GAP" and not row["issue_ids"]:
            record_invalid(str(label), "source gap has no issue")
            continue
        if any(issue_id not in issue_ids for issue_id in row["issue_ids"]):
            record_invalid(str(label), "unknown issue ID")
            continue
        ledger[unit_id] = row
    checks.append(
        TranslationCheck(
            "ledger:schema",
            not invalid_records and not duplicate_ids,
            f"{len(ledger)} valid records"
            + (
                "; invalid records="
                + str(len(invalid_records))
                + "; reasons="
                + ", ".join(
                    f"{reason} ({count})"
                    for reason, count in sorted(invalid_reasons.items())
                )
                + "; examples="
                + ", ".join(invalid_records[:10])
                if invalid_records
                else ""
            )
            + (f"; duplicates: {', '.join(duplicate_ids)}" if duplicate_ids else ""),
        )
    )
    if units is None:
        checks.append(
            TranslationCheck(
                "ledger:inventory-coverage",
                False,
                "source inventory unavailable; ledger coverage cannot be established",
            )
        )
        units = {}
    else:
        missing = sorted(set(units) - set(ledger))
        extra = sorted(set(ledger) - set(units))
        mismatched = sorted(
            unit_id
            for unit_id in set(units) & set(ledger)
            if (
                _source_key(units[unit_id].get("source_id"), units[unit_id].get("source_page"))
                != _source_key(ledger[unit_id].get("source_id"), ledger[unit_id].get("source_page"))
                or units[unit_id].get("kind") != ledger[unit_id].get("kind")
            )
        )
        checks.append(
            TranslationCheck(
                "ledger:inventory-coverage",
                not missing and not extra and not mismatched,
                "ledger exactly covers source units"
                if not missing and not extra and not mismatched
                else f"missing={missing}; extra={extra}; source-location-mismatch={mismatched}",
            )
        )
    gaps = sorted(
        unit_id for unit_id, row in ledger.items() if row.get("translation_status") == "SOURCE_GAP"
    )
    checks.append(
        TranslationCheck(
            "ledger:no-source-gaps",
            not gaps,
            "no unresolved source gaps" if not gaps else f"source gaps prevent COMPLETE: {', '.join(gaps)}",
        )
    )
    return checks, ledger


def _validate_issues(rows: list[dict[str, Any]]) -> tuple[list[TranslationCheck], set[str]]:
    issue_ids: set[str] = set()
    invalid: list[str] = []
    blocking: list[str] = []
    for index, row in enumerate(rows, start=1):
        issue_id = row.get("issue_id")
        if not _nonempty_text(issue_id) or issue_id in issue_ids:
            invalid.append(f"line-{index}")
            continue
        issue_ids.add(issue_id)
        if row.get("status") not in {"OPEN", "RESOLVED"}:
            invalid.append(issue_id)
        if row.get("completion_impact") not in {"NONE", "PROVISIONAL", "BLOCKED"}:
            invalid.append(issue_id)
        if row.get("status") == "OPEN" and row.get("completion_impact") in {"PROVISIONAL", "BLOCKED"}:
            blocking.append(issue_id)
    return [
        TranslationCheck(
            "issues:schema",
            not invalid,
            f"{len(issue_ids)} issues parsed"
            if not invalid
            else f"invalid issues: {', '.join(sorted(set(invalid)))}",
        ),
        TranslationCheck(
            "issues:no-completion-impact",
            not blocking,
            "no open consequential translation issues"
            if not blocking
            else f"open issues prevent COMPLETE: {', '.join(blocking)}",
        ),
    ], issue_ids


def _validate_layout(
    plan: Any,
    pages: dict[tuple[str, int], dict[str, Any]],
    objects: dict[str, dict[str, Any]],
    ledger: dict[str, dict[str, Any]],
    a_path: Path,
) -> list[TranslationCheck]:
    checks: list[TranslationCheck] = []
    try:
        validated = validate_plan_data(plan)
        checks.append(TranslationCheck("layout:plan-schema", True, "mirror plan schema valid"))
    except MirrorPlanError as exc:
        return [TranslationCheck("layout:plan-schema", False, str(exc))]

    planned_output = Path(str(validated.get("output_pdf", "")))
    try:
        same_output = planned_output.resolve() == a_path.resolve()
    except OSError:
        same_output = False
    checks.append(
        TranslationCheck(
            "layout:output-identity",
            same_output,
            "layout plan targets A" if same_output else f"plan output {planned_output} != A {a_path}",
        )
    )

    mapped_pages: set[tuple[str, int]] = set()
    placed_objects: set[str] = set()
    table_placements: dict[str, dict[str, Any]] = {}
    layout_field_failures: list[int] = []
    seen_output_pages: set[int] = set()
    duplicate_output_pages: list[int] = []
    for page in validated["pages"]:
        output_number = page.get("output_page_number")
        refs = page.get("source_page_refs")
        placed = page.get("placed_object_ids")
        placements = page.get("table_placements")
        if (
            not _positive_int(output_number)
            or not isinstance(refs, list)
            or not refs
            or not isinstance(placed, list)
            or not all(_nonempty_text(item) for item in placed)
            or not isinstance(placements, list)
        ):
            layout_field_failures.append(page.get("page_number"))
            continue
        if output_number in seen_output_pages:
            duplicate_output_pages.append(output_number)
        seen_output_pages.add(output_number)
        notes = page.get("render_notes")
        if page.get("render_checked") is True and not (
            isinstance(notes, list)
            and any(_nonempty_text(note) for note in notes)
        ):
            layout_field_failures.append(output_number)
        for ref in refs:
            if not isinstance(ref, dict):
                layout_field_failures.append(output_number)
                continue
            key = _source_key(ref.get("source_id"), ref.get("source_page"))
            if key is None:
                layout_field_failures.append(output_number)
            else:
                mapped_pages.add(key)
        placed_objects.update(item.strip() for item in placed)
        for placement in placements:
            if isinstance(placement, dict) and _nonempty_text(placement.get("object_id")):
                table_placements[placement["object_id"].strip()] = placement
            else:
                layout_field_failures.append(output_number)
    checks.append(
        TranslationCheck(
            "layout:page-fields",
            not layout_field_failures
            and not duplicate_output_pages
            and seen_output_pages == set(range(1, len(validated["pages"]) + 1)),
            "all output pages have source/object mappings"
            if (
                not layout_field_failures
                and not duplicate_output_pages
                and seen_output_pages == set(range(1, len(validated["pages"]) + 1))
            )
            else (
                f"invalid page fields={layout_field_failures}; "
                f"duplicate output pages={duplicate_output_pages}; "
                f"numbered output pages={sorted(seen_output_pages)}"
            ),
        )
    )
    ledger_page_failures = sorted(
        unit_id
        for unit_id, row in ledger.items()
        if any(page not in seen_output_pages for page in row.get("output_pages", []))
    )
    checks.append(
        TranslationCheck(
            "layout:ledger-output-pages",
            not ledger_page_failures,
            "every translated unit maps to a planned output page"
            if not ledger_page_failures
            else f"units reference unknown output pages: {', '.join(ledger_page_failures)}",
        )
    )
    missing_pages = sorted(set(pages) - mapped_pages)
    extra_pages = sorted(mapped_pages - set(pages))
    checks.append(
        TranslationCheck(
            "layout:source-page-coverage",
            not missing_pages and not extra_pages,
            "every source page maps to output"
            if not missing_pages and not extra_pages
            else f"unmapped={missing_pages}; unknown={extra_pages}",
        )
    )
    missing_objects = sorted(set(objects) - placed_objects)
    unknown_objects = sorted(placed_objects - set(objects))
    checks.append(
        TranslationCheck(
            "layout:object-coverage",
            not missing_objects and not unknown_objects,
            "every source figure/table is placed"
            if not missing_objects and not unknown_objects
            else f"missing={missing_objects}; unknown={unknown_objects}",
        )
    )

    topology_failures: list[str] = []
    for object_id, item in objects.items():
        if item.get("kind") != "table":
            continue
        placement = table_placements.get(object_id)
        shape = item.get("table_structure", {})
        if not placement:
            topology_failures.append(object_id)
            continue
        mode = placement.get("mode")
        if mode == "native-grid":
            if any(placement.get(field) != shape.get(field) for field in ("rows", "columns", "header_rows")):
                topology_failures.append(object_id)
                continue
            if shape.get("merged_cells", 0) and placement.get("merged_cells_preserved") is not True:
                topology_failures.append(object_id)
            if shape.get("footnotes", 0) and placement.get("footnotes_present") is not True:
                topology_failures.append(object_id)
        elif mode == "source-image-with-translation-map":
            if placement.get("translation_map_complete") is not True:
                topology_failures.append(object_id)
            if shape.get("footnotes", 0) and placement.get("footnotes_translated") is not True:
                topology_failures.append(object_id)
        else:
            topology_failures.append(object_id)
    checks.append(
        TranslationCheck(
            "layout:table-topology",
            not topology_failures,
            "table topology preserved or allowed image-map fallback documented"
            if not topology_failures
            else f"invalid table rendering: {', '.join(sorted(set(topology_failures)))}",
        )
    )
    all_checked = validated.get("layout_qc", {}).get("status") == "LAYOUT_QC_PASSED"
    checks.append(
        TranslationCheck(
            "layout:render-qc",
            all_checked,
            "all rendered pages inspected" if all_checked else "layout_qc must be LAYOUT_QC_PASSED",
        )
    )
    return checks


def _box_values(page: Any, field: str) -> list[float]:
    box = getattr(page, field)
    return [float(box.left), float(box.bottom), float(box.right), float(box.top)]


def _box_matches(actual: list[float], expected: list[float], tolerance: float = 0.01) -> bool:
    return all(abs(left - right) <= tolerance for left, right in zip(actual, expected))


def _font_descriptor(font: Any) -> Any | None:
    font = font.get_object()
    descriptor = font.get("/FontDescriptor")
    if descriptor is not None:
        return descriptor.get_object()
    descendants = font.get("/DescendantFonts")
    if descendants:
        descendant = descendants[0].get_object()
        descriptor = descendant.get("/FontDescriptor")
        if descriptor is not None:
            return descriptor.get_object()
    return None


def _embedded_simsun(reader: Any) -> tuple[bool, list[str]]:
    names: set[str] = set()
    embedded = False
    for page in reader.pages:
        resources = page.get("/Resources")
        if resources is None:
            continue
        fonts = resources.get_object().get("/Font")
        if fonts is None:
            continue
        for reference in fonts.get_object().values():
            font = reference.get_object()
            base_name = str(font.get("/BaseFont") or "")
            if "simsun" not in base_name.lower():
                continue
            names.add(base_name)
            descriptor = _font_descriptor(font)
            if descriptor is not None and any(
                descriptor.get(key) is not None for key in ("/FontFile", "/FontFile2", "/FontFile3")
            ):
                embedded = True
    return embedded, sorted(names)


def _find_pdftoppm() -> Path | None:
    located = shutil.which("pdftoppm")
    if located:
        return Path(located)
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        candidate = Path(user_profile) / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "native" / "poppler" / "Library" / "bin" / "pdftoppm.exe"
        if candidate.is_file():
            return candidate
    return None


def _render_pdf_page(pdftoppm: Path, pdf: Path, page_number: int, output_prefix: Path) -> Path:
    command = [
        str(pdftoppm),
        "-f",
        str(page_number),
        "-l",
        str(page_number),
        "-r",
        "144",
        "-png",
        "-singlefile",
        str(pdf),
        str(output_prefix),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode:
        raise TranslationPackageError(
            f"pdftoppm failed for {pdf} page {page_number}: {completed.stderr.strip()}"
        )
    output = output_prefix.with_suffix(".png")
    if not output.is_file():
        raise TranslationPackageError(f"pdftoppm did not create {output}")
    return output


def _raster_outside_frames_unchanged(
    source_pdf: Path,
    source_page: int,
    output_pdf: Path,
    output_page: int,
    media_box: list[float],
    frame_boxes: list[list[float]],
    temporary: Path,
    pdftoppm: Path,
) -> tuple[bool, int]:
    source_png = _render_pdf_page(
        pdftoppm, source_pdf, source_page, temporary / f"src-{output_page}"
    )
    output_png = _render_pdf_page(
        pdftoppm, output_pdf, output_page, temporary / f"out-{output_page}"
    )
    source_array = np.asarray(Image.open(source_png).convert("RGB"))
    output_array = np.asarray(Image.open(output_png).convert("RGB"))
    if source_array.shape != output_array.shape:
        return False, max(source_array.size, output_array.size)
    height, width, _ = source_array.shape
    mask = np.zeros((height, width), dtype=bool)
    page_width = media_box[2] - media_box[0]
    page_height = media_box[3] - media_box[1]
    x_scale = width / page_width
    y_scale = height / page_height
    for bbox in frame_boxes:
        left = max(0, int((bbox[0] - media_box[0]) * x_scale) - 2)
        right = min(width, int((bbox[2] - media_box[0]) * x_scale) + 3)
        top = max(0, int((media_box[3] - bbox[3]) * y_scale) - 2)
        bottom = min(height, int((media_box[3] - bbox[1]) * y_scale) + 3)
        mask[top:bottom, left:right] = True
    changed = np.any(source_array != output_array, axis=2) & ~mask
    changed_count = int(changed.sum())
    return changed_count == 0, changed_count


def _validate_exact_package(
    work_dir: Path, a_path: Path
) -> tuple[list[TranslationCheck], dict[str, Any]]:
    checks: list[TranslationCheck] = []
    diff: dict[str, Any] = {
        "schema_version": 1,
        "validator": "validate_translation_package.py",
        "layout_fidelity": EXACT_LAYOUT_FIDELITY,
        "pages": [],
        "fonts": {},
        "frames": [],
    }
    try:
        inventory = validate_exact_inventory(
            load_exact_json(work_dir / INVENTORY_FILE, "source inventory")
        )
        checks.append(TranslationCheck("inventory:exact-schema", True, "exact inventory schema valid"))
    except (ExactMirrorError, OSError) as exc:
        return [TranslationCheck("inventory:exact-schema", False, str(exc))], diff
    try:
        frames = validate_text_frames(
            load_exact_jsonl(work_dir / FRAMES_FILE, "text frame inventory"), inventory
        )
        checks.append(TranslationCheck("layout:text-frame-schema", True, f"{len(frames)} reviewed frames"))
    except (ExactMirrorError, OSError) as exc:
        return checks + [TranslationCheck("layout:text-frame-schema", False, str(exc))], diff
    try:
        font_map = validate_font_map(load_exact_json(work_dir / FONT_MAP_FILE, "font map"))
        font_path = Path(font_map["font_path"])
        font_available = font_path.is_file() and font_path.name.lower() == "simsun.ttc"
        checks.append(
            TranslationCheck(
                "font:simsun-source",
                font_available,
                f"SimSun source available: {font_path}" if font_available else f"required simsun.ttc unavailable: {font_path}",
            )
        )
    except (ExactMirrorError, OSError) as exc:
        return checks + [TranslationCheck("font:map", False, str(exc))], diff
    try:
        ledger_rows = load_exact_jsonl(work_dir / LEDGER_FILE, "translation ledger")
        ledger = validate_exact_ledger(ledger_rows, frames)
        checks.append(TranslationCheck("ledger:exact-schema", True, f"{len(ledger)} frame-level units"))
    except (ExactMirrorError, OSError) as exc:
        return checks + [TranslationCheck("ledger:exact-schema", False, str(exc))], diff
    try:
        plan = validate_plan_data(_load_json(work_dir / PLAN_FILE, "mirror layout plan"))
        if plan.get("schema_version") != 2 or plan.get("layout_fidelity") != EXACT_LAYOUT_FIDELITY:
            raise MirrorPlanError("FULL_MIRROR exact completion requires a V2 EXACT_TEXT_FRAME plan.")
        checks.append(TranslationCheck("layout:exact-plan", True, "V2 exact plan valid"))
    except (MirrorPlanError, TranslationPackageError, OSError) as exc:
        return checks + [TranslationCheck("layout:exact-plan", False, str(exc))], diff

    output_identity = Path(plan["output_pdf"]).resolve() == a_path.resolve()
    checks.append(
        TranslationCheck(
            "layout:output-identity",
            output_identity,
            "exact plan targets A" if output_identity else "exact plan output does not match A",
        )
    )
    issues_rows = _load_jsonl(work_dir / ISSUES_FILE, "translation issues", required=False)
    issue_checks, _ = _validate_issues(issues_rows)
    checks.extend(issue_checks)

    fit_failures = sorted(
        row["unit_id"] for row in ledger.values() if row.get("fit_status") != "FIT"
    )
    scale_failures = sorted(
        row["unit_id"]
        for row in ledger.values()
        if not MINIMUM_FONT_SCALE <= float(row.get("font_scale_used", 0)) <= 1.0
    )
    checks.append(
        TranslationCheck(
            "layout:frame-fit",
            not fit_failures and not scale_failures,
            "all translated frames fit at 95%-100%"
            if not fit_failures and not scale_failures
            else f"non-fitting={fit_failures}; invalid-scale={scale_failures}",
        )
    )
    residual_units: list[str] = []
    for row in ledger.values():
        recorded = {
            word.lower()
            for token in row["untranslated_tokens"]
            for word in re.findall(r"[A-Za-z]{3,}", str(token["text"]))
        }
        words = {word.lower() for word in re.findall(r"[A-Za-z]{3,}", row["translated_text"])}
        if any(word not in recorded for word in words):
            residual_units.append(row["unit_id"])
    checks.append(
        TranslationCheck(
            "semantic:english-accounting",
            not residual_units,
            "English tokens in translated units are explicitly accounted for"
            if not residual_units
            else f"unaccounted English remains in: {', '.join(sorted(residual_units))}",
        )
    )

    expected_regions = {
        frame_id: frame["bbox_pt"]
        for frame_id, frame in frames.items()
        if frame["translation_action"] == "TRANSLATE"
    }
    plan_regions: dict[str, list[float]] = {}
    mapped_sources: set[tuple[str, int]] = set()
    placed_objects: set[str] = set()
    table_placements: dict[str, dict[str, Any]] = {}
    for page in plan["pages"]:
        ref = page["source_page_refs"][0]
        mapped_sources.add((ref["source_id"], ref["source_page"]))
        placed_objects.update(page["placed_object_ids"])
        for region in page["replacement_regions"]:
            plan_regions[region["frame_id"]] = [float(value) for value in region["bbox_pt"]]
        for placement in page["table_placements"]:
            if isinstance(placement, dict) and _nonempty_text(placement.get("object_id")):
                table_placements[placement["object_id"]] = placement
    region_failures = sorted(
        frame_id
        for frame_id in set(expected_regions) | set(plan_regions)
        if frame_id not in expected_regions
        or frame_id not in plan_regions
        or not _box_matches(plan_regions[frame_id], expected_regions[frame_id], 0.25)
    )
    checks.append(
        TranslationCheck(
            "layout:replacement-regions",
            not region_failures,
            "every mask is owned by one reviewed source frame"
            if not region_failures
            else f"invalid replacement regions: {', '.join(region_failures)}",
        )
    )
    inventory_source_pages = {
        (page["source_id"], page["source_page"]) for page in inventory["pages"]
    }
    checks.append(
        TranslationCheck(
            "layout:one-to-one-pages",
            mapped_sources == inventory_source_pages and len(plan["pages"]) == len(inventory["pages"]),
            "every source page has exactly one output page"
            if mapped_sources == inventory_source_pages and len(plan["pages"]) == len(inventory["pages"])
            else "source/output page mapping is not one-to-one",
        )
    )
    objects = {item["object_id"]: item for item in inventory["objects"]}
    checks.append(
        TranslationCheck(
            "layout:object-coverage",
            placed_objects == set(objects),
            "all source figures/tables remain on their source pages"
            if placed_objects == set(objects)
            else f"missing={sorted(set(objects)-placed_objects)}; extra={sorted(placed_objects-set(objects))}",
        )
    )
    table_failures: list[str] = []
    for object_id, item in objects.items():
        if item["kind"] != "table":
            continue
        placement = table_placements.get(object_id)
        structure = item["table_structure"]
        expected_cells = {cell["frame_id"] for cell in item["cells"]}
        if (
            not placement
            or placement.get("mode") != "exact-cells"
            or any(placement.get(field) != structure[field] for field in ("rows", "columns", "header_rows", "merged_cells", "footnotes"))
            or set(placement.get("cell_frame_ids", [])) != expected_cells
        ):
            table_failures.append(object_id)
    checks.append(
        TranslationCheck(
            "layout:table-exact-cells",
            not table_failures,
            "tables preserve exact cell topology" if not table_failures else f"invalid tables: {', '.join(table_failures)}",
        )
    )

    if PdfReader is None:
        checks.append(TranslationCheck("layout:pdf-dependency", False, "pypdf is required"))
        return checks, diff
    if not a_path.is_file():
        checks.append(TranslationCheck("layout:a-pdf", False, f"A does not exist: {a_path}"))
        return checks, diff
    try:
        output_reader = PdfReader(str(a_path))
    except Exception as exc:
        checks.append(TranslationCheck("layout:a-pdf", False, f"Cannot read A: {exc}"))
        return checks, diff
    page_count_ok = len(output_reader.pages) == len(inventory["pages"])
    checks.append(
        TranslationCheck(
            "layout:page-count",
            page_count_ok,
            f"output pages={len(output_reader.pages)}, expected={len(inventory['pages'])}",
        )
    )
    geometry_failures: list[int] = []
    source_readers: dict[str, Any] = {}
    source_paths: dict[str, Path] = {}
    for source in inventory["sources"]:
        path = Path(source["pdf_path"])
        if not path.is_absolute():
            path = work_dir / path
        source_paths[source["source_id"]] = path
        if path.is_file():
            try:
                source_readers[source["source_id"]] = PdfReader(str(path))
            except Exception:
                pass
    if page_count_ok:
        field_map = {
            "media_box": "mediabox",
            "crop_box": "cropbox",
            "trim_box": "trimbox",
            "bleed_box": "bleedbox",
            "art_box": "artbox",
        }
        for page_record in inventory["pages"]:
            output_number = page_record["output_page"]
            source_reader = source_readers.get(page_record["source_id"])
            if source_reader is None or page_record["source_page"] > len(source_reader.pages):
                geometry_failures.append(output_number)
                continue
            source_page = source_reader.pages[page_record["source_page"] - 1]
            output_page = output_reader.pages[output_number - 1]
            page_ok = int(source_page.get("/Rotate", 0) or 0) % 360 == int(output_page.get("/Rotate", 0) or 0) % 360
            for evidence_field, pdf_field in field_map.items():
                source_box = _box_values(source_page, pdf_field)
                output_box = _box_values(output_page, pdf_field)
                expected_box = [float(value) for value in page_record[evidence_field]]
                page_ok = page_ok and _box_matches(source_box, expected_box) and _box_matches(output_box, expected_box)
            if not page_ok:
                geometry_failures.append(output_number)
            diff["pages"].append({"output_page": output_number, "geometry_passed": page_ok})
    checks.append(
        TranslationCheck(
            "layout:page-geometry",
            page_count_ok and not geometry_failures,
            "all page boxes and rotations match within 0.01 pt"
            if page_count_ok and not geometry_failures
            else f"geometry failures on output pages: {geometry_failures}",
        )
    )
    embedded, font_names = _embedded_simsun(output_reader)
    diff["fonts"] = {"embedded_simsun": embedded, "font_names": font_names}
    checks.append(
        TranslationCheck(
            "font:simsun-embedded",
            embedded,
            f"embedded SimSun resources: {font_names}" if embedded else f"no embedded SimSun resource; observed={font_names}",
        )
    )

    cjk_frame_counts = {frame_id: 0 for frame_id in expected_regions}
    frame_line_positions: dict[str, list[float]] = {
        frame_id: [] for frame_id in expected_regions
    }
    cjk_font_failures: list[str] = []
    cjk_position_failures: list[int] = []
    actual_scale_failures: list[str] = []
    if pdfplumber is None:
        checks.append(TranslationCheck("layout:text-geometry-dependency", False, "pdfplumber is required"))
    else:
        page_frames: dict[int, list[tuple[str, dict[str, Any]]]] = {}
        for page_record in inventory["pages"]:
            page_frames[page_record["output_page"]] = [
                (frame_id, frames[frame_id])
                for frame_id in page_record["frame_ids"]
                if frames[frame_id]["translation_action"] == "TRANSLATE"
            ]
        try:
            with pdfplumber.open(a_path) as pdf:
                for output_number, page in enumerate(pdf.pages, 1):
                    for char in page.chars:
                        text_value = str(char.get("text", ""))
                        if not contains_cjk(text_value):
                            continue
                        bbox = [
                            float(char["x0"]),
                            float(page.height) - float(char["bottom"]),
                            float(char["x1"]),
                            float(page.height) - float(char["top"]),
                        ]
                        owners = [
                            (frame_id, frame)
                            for frame_id, frame in page_frames.get(output_number, [])
                            if bbox_contains([float(value) for value in frame["bbox_pt"]], bbox)
                        ]
                        if len(owners) != 1:
                            cjk_position_failures.append(output_number)
                            continue
                        frame_id, frame = owners[0]
                        cjk_frame_counts[frame_id] += 1
                        if frame.get("rotation") not in {90, 270}:
                            frame_line_positions[frame_id].append(float(char["top"]))
                        font_name = str(char.get("fontname") or "")
                        if "simsun" not in font_name.lower():
                            cjk_font_failures.append(frame_id)
                        ratio = float(char.get("size") or 0.0) / float(frame["source_font_size_pt"])
                        if ratio < MINIMUM_FONT_SCALE - 0.005 or ratio > 1.005:
                            actual_scale_failures.append(frame_id)
        except Exception as exc:
            checks.append(TranslationCheck("layout:text-geometry-read", False, str(exc)))
        missing_cjk = sorted(
            frame_id
            for frame_id, count in cjk_frame_counts.items()
            if count == 0 and contains_cjk(frame_to_text(frame_id, ledger))
        )
        checks.append(
            TranslationCheck(
                "layout:text-frame-geometry",
                not cjk_position_failures and not missing_cjk,
                "all rendered Chinese glyphs stay inside their source frame"
                if not cjk_position_failures and not missing_cjk
                else f"position-pages={sorted(set(cjk_position_failures))}; missing-frame-glyphs={missing_cjk}",
            )
        )
        checks.append(
            TranslationCheck(
                "font:simsun-cjk",
                not cjk_font_failures,
                "every rendered CJK glyph uses SimSun"
                if not cjk_font_failures
                else f"non-SimSun CJK frames: {sorted(set(cjk_font_failures))}",
            )
        )
        checks.append(
            TranslationCheck(
                "layout:actual-font-scale",
                not actual_scale_failures,
                "rendered CJK sizes remain within 95%-100%"
                if not actual_scale_failures
                else f"out-of-range rendered sizes: {sorted(set(actual_scale_failures))}",
            )
        )
        leading_failures: list[str] = []
        for frame_id, positions in frame_line_positions.items():
            clustered = sorted({round(position * 2) / 2 for position in positions})
            if len(clustered) < 2:
                continue
            gaps = [
                clustered[index] - clustered[index - 1]
                for index in range(1, len(clustered))
                if clustered[index] - clustered[index - 1] > 1.0
            ]
            if not gaps:
                continue
            observed = min(gaps)
            expected = float(frames[frame_id]["source_leading_pt"])
            if abs(observed - expected) > 0.5:
                leading_failures.append(frame_id)
        checks.append(
            TranslationCheck(
                "layout:leading",
                not leading_failures,
                "multi-line translated frames preserve source leading"
                if not leading_failures
                else f"leading mismatch: {sorted(set(leading_failures))}",
            )
        )
    for frame_id, count in cjk_frame_counts.items():
        diff["frames"].append({"frame_id": frame_id, "cjk_glyph_count": count})

    pdftoppm = _find_pdftoppm()
    raster_failures: list[dict[str, Any]] = []
    if np is None or Image is None or pdftoppm is None:
        checks.append(
            TranslationCheck(
                "layout:raster-dependency",
                False,
                "NumPy, Pillow, and pdftoppm are required for exact non-text comparison",
            )
        )
    elif page_count_ok and not geometry_failures:
        with tempfile.TemporaryDirectory() as temporary_name:
            temporary = Path(temporary_name)
            for page_record in inventory["pages"]:
                frame_boxes = [
                    [float(value) for value in frames[frame_id]["bbox_pt"]]
                    for frame_id in page_record["frame_ids"]
                    if frames[frame_id]["translation_action"] == "TRANSLATE"
                ]
                try:
                    passed, changed_pixels = _raster_outside_frames_unchanged(
                        source_paths[page_record["source_id"]],
                        page_record["source_page"],
                        a_path,
                        page_record["output_page"],
                        [float(value) for value in page_record["media_box"]],
                        frame_boxes,
                        temporary,
                        pdftoppm,
                    )
                except TranslationPackageError as exc:
                    passed, changed_pixels = False, -1
                    raster_failures.append({"output_page": page_record["output_page"], "error": str(exc)})
                if not passed and changed_pixels >= 0:
                    raster_failures.append(
                        {"output_page": page_record["output_page"], "changed_pixels": changed_pixels}
                    )
                for page_diff in diff["pages"]:
                    if page_diff["output_page"] == page_record["output_page"]:
                        page_diff["outside_frame_changed_pixels"] = changed_pixels
        checks.append(
            TranslationCheck(
                "layout:non-text-raster",
                not raster_failures,
                "no rendered pixels changed outside reviewed text frames"
                if not raster_failures
                else f"outside-frame changes: {raster_failures}",
            )
        )
    return checks, diff


def frame_to_text(frame_id: str, ledger: dict[str, dict[str, Any]]) -> str:
    for row in ledger.values():
        if row.get("frame_ids") == [frame_id]:
            return str(row.get("translated_text") or "")
    return ""


def validate_package_detailed(
    work_dir: Path,
    a_path: Path,
    scope: str,
    layout_fidelity: str | None = None,
) -> tuple[list[TranslationCheck], dict[str, Any] | None, str]:
    work_dir = work_dir.resolve()
    a_path = a_path.resolve()
    checks: list[TranslationCheck] = []
    if scope not in SCOPES:
        return [TranslationCheck("scope", False, f"unsupported scope: {scope}")], None, layout_fidelity or "NONE"
    if layout_fidelity is None:
        if scope == "FULL_MIRROR":
            try:
                candidate_plan = _load_json(work_dir / PLAN_FILE, "mirror layout plan")
                layout_fidelity = (
                    EXACT_LAYOUT_FIDELITY
                    if candidate_plan.get("schema_version") == 2
                    else LEGACY_LAYOUT_FIDELITY
                )
            except TranslationPackageError:
                layout_fidelity = EXACT_LAYOUT_FIDELITY
        else:
            layout_fidelity = "NONE"
    if layout_fidelity not in LAYOUT_FIDELITIES and layout_fidelity != "NONE":
        return [TranslationCheck("layout:fidelity", False, f"unsupported layout fidelity: {layout_fidelity}")], None, layout_fidelity
    if scope == "FULL_MIRROR" and layout_fidelity == EXACT_LAYOUT_FIDELITY:
        exact_checks, diff = _validate_exact_package(work_dir, a_path)
        pdf_ok = a_path.is_file() and a_path.stat().st_size > 0
        combined = [
            TranslationCheck(
                "artifact:A",
                pdf_ok,
                "A PDF present" if pdf_ok else f"invalid A PDF: {a_path}",
            )
        ] + exact_checks
        diff["passed"] = all(check.passed for check in combined)
        diff["checks"] = [asdict(check) for check in combined]
        return combined, diff, layout_fidelity
    pdf_ok = a_path.is_file() and a_path.stat().st_size > 0
    if pdf_ok:
        try:
            pdf_ok = a_path.read_bytes()[:5] == b"%PDF-"
        except OSError:
            pdf_ok = False
    checks.append(TranslationCheck("artifact:A", pdf_ok, "A PDF present" if pdf_ok else f"invalid A PDF: {a_path}"))
    parsed: dict[str, Any] = {}
    try:
        inventory = _load_json(work_dir / INVENTORY_FILE, "source inventory")
        inventory_checks, parsed = _validate_inventory(inventory, scope)
        checks.extend(inventory_checks)
    except (OSError, TranslationPackageError) as exc:
        checks.append(TranslationCheck("inventory:parse", False, str(exc)))

    issue_ids: set[str] = set()
    try:
        issue_checks, issue_ids = _validate_issues(
            _load_jsonl(work_dir / ISSUES_FILE, "translation issues", required=False)
        )
        checks.extend(issue_checks)
    except (OSError, TranslationPackageError) as exc:
        checks.append(TranslationCheck("issues:parse", False, str(exc)))

    parsed_ledger: dict[str, dict[str, Any]] = {}
    try:
        ledger = _load_jsonl(work_dir / LEDGER_FILE, "translation ledger")
        ledger_checks, parsed_ledger = _validate_ledger(
            ledger, parsed.get("units") if parsed else None, issue_ids
        )
        checks.extend(ledger_checks)
    except (OSError, TranslationPackageError) as exc:
        checks.append(TranslationCheck("ledger:parse", False, str(exc)))

    if scope == "FULL_MIRROR":
        try:
            plan = _load_json(work_dir / PLAN_FILE, "mirror layout plan")
            checks.extend(
                _validate_layout(
                    plan,
                    parsed.get("pages", {}),
                    parsed.get("objects", {}),
                    parsed_ledger,
                    a_path,
                )
            )
        except (OSError, TranslationPackageError) as exc:
            checks.append(TranslationCheck("layout:parse", False, str(exc)))
    return checks, None, layout_fidelity


def validate_package(
    work_dir: Path,
    a_path: Path,
    scope: str,
    layout_fidelity: str | None = None,
) -> list[TranslationCheck]:
    checks, _, _ = validate_package_detailed(
        work_dir, a_path, scope, layout_fidelity
    )
    return checks


def write_report(
    path: Path,
    work_dir: Path,
    a_path: Path,
    scope: str,
    checks: list[TranslationCheck],
    layout_fidelity: str | None = None,
) -> None:
    payload = {
        "schema_version": 2 if layout_fidelity == EXACT_LAYOUT_FIDELITY else 1,
        "validator": "validate_translation_package.py",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "layout_fidelity": layout_fidelity,
        "work_dir": str(work_dir.resolve()),
        "a_path": str(a_path.resolve()),
        "passed": all(check.passed for check in checks),
        "checks": [asdict(check) for check in checks],
    }
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", delete=False, dir=path.parent
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def write_layout_diff(path: Path, payload: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", delete=False, dir=path.parent
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--a-path", type=Path, required=True)
    parser.add_argument("--scope", choices=sorted(SCOPES), required=True)
    parser.add_argument(
        "--layout-fidelity",
        choices=sorted(LAYOUT_FIDELITIES),
    )
    parser.add_argument("--report", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    checks, layout_diff, resolved_fidelity = validate_package_detailed(
        args.work_dir, args.a_path, args.scope, args.layout_fidelity
    )
    if layout_diff is not None:
        write_layout_diff(args.work_dir.resolve() / LAYOUT_DIFF_FILE, layout_diff)
    write_report(
        args.report,
        args.work_dir,
        args.a_path,
        args.scope,
        checks,
        resolved_fidelity,
    )
    for check in checks:
        print(f"[{'PASS' if check.passed else 'FAIL'}] {check.code}: {check.detail}")
    failures = sum(not check.passed for check in checks)
    print(f"Summary: {len(checks) - failures} passed, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
