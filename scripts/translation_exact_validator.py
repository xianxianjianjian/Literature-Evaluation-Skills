#!/usr/bin/env python3
"""Exact-mirror PDF geometry, style, residual, and raster validation helpers."""

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
    EXPANDABLE_FRAME_KINDS,
    LEGACY_LAYOUT_FIDELITY,
    MINIMUM_FONT_SCALE,
    REQUIRED_CJK_FONT,
    STRUCTURAL_LAYOUT_FIDELITY,
    ExactMirrorError,
    bbox_contains,
    contains_cjk,
    frame_role,
    load_json as load_exact_json,
    load_jsonl as load_exact_jsonl,
    validate_exact_inventory,
    validate_exact_ledger,
    validate_font_map,
    validate_text_frames,
)
from mirror_pdf import MirrorPlanError, validate_plan_data
from translation_integrity import (
    NUMERIC_REPORT_FILE,
    TranslationIntegrityError,
    validate_figure_text_inventory,
    validate_numeric_integrity,
    validate_paper_terminology,
    validate_source_conflicts,
    write_json as write_integrity_json,
)
from audit_untranslated_residuals import (
    REPORT_FILE as RESIDUAL_REPORT_FILE,
    ResidualAuditError,
    audit_residuals,
    write_report as write_residual_report,
)
from style_fidelity import StyleFidelityError, validate_rendered_styles, audit_pdf_styles
import validate_a_text_layer
import validate_paragraph_styles

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
TYPOGRAPHY_FIT_FILE = "typography_fit.json"
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


def _resolve_cjk_owner(
    owners: list[tuple[str, dict[str, Any]]],
) -> tuple[str, dict[str, Any]] | None:
    """Assign a glyph to the innermost reviewed frame when patches are nested."""
    if len(owners) == 1:
        return owners[0]
    nested = [
        candidate
        for candidate in owners
        if all(
            candidate is other
            or bbox_contains(
                [float(value) for value in other[1]["bbox_pt"]],
                [float(value) for value in candidate[1]["bbox_pt"]],
                tolerance=0.25,
            )
            for other in owners
        )
    ]
    return nested[0] if len(nested) == 1 else None


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


def _write_jsonl_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", delete=False, dir=path.parent
    ) as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0



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


def _material_pixel_mask(
    source_array: Any, output_array: Any, *, antialias_tolerance: int = 64
) -> Any:
    """Ignore renderer-only edge-antialias variation while retaining real edits."""
    delta = np.abs(source_array.astype(np.int16) - output_array.astype(np.int16))
    return np.max(delta, axis=2) > antialias_tolerance


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
    changed = _material_pixel_mask(source_array, output_array) & ~mask
    changed_count = int(changed.sum())
    return changed_count == 0, changed_count


def _validate_exact_package(
    work_dir: Path, a_path: Path, *, contract_version: str = "1.4.1"
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
        frame_rows = load_exact_jsonl(work_dir / FRAMES_FILE, "text frame inventory")
        frames = validate_text_frames(
            frame_rows, inventory
        )
        checks.append(TranslationCheck("layout:text-frame-schema", True, f"{len(frames)} reviewed frames"))
        if contract_version in {"1.4.2", "1.5.0"}:
            missing_roles = sorted(row["frame_id"] for row in frame_rows if "role" not in row or "preserve_english" not in row)
            checks.append(TranslationCheck(
                "layout:role-contract", not missing_roles,
                "all frames have explicit v1.4.2 role/translatable/preserve-English semantics"
                if not missing_roles else f"frames missing role contract: {missing_roles}",
            ))
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
    if contract_version in {"1.4.2", "1.5.0"}:
        try:
            style_map = _load_json(work_dir / "style_map.json", "style map")
            style_report = validate_rendered_styles(frame_rows, style_map)
            measured = audit_pdf_styles(a_path, inventory, frame_rows, style_map, work_dir)
            style_report['independent_pdf_audit'] = measured
            style_report['passed'] = style_report['passed'] and measured['passed']
            style_report['failures'].extend(measured['failures'])
            (work_dir / "style_fidelity.json").write_text(
                json.dumps(style_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            checks.append(TranslationCheck(
                "style:fidelity", style_report["passed"],
                "role-aware size/leading/weight/italic/color/alignment/superscript evidence passed"
                if style_report["passed"] else str(style_report["failures"]),
            ))
        except (OSError, TranslationPackageError, StyleFidelityError, ValueError) as exc:
            checks.append(TranslationCheck("style:fidelity", False, str(exc)))
    try:
        plan = validate_plan_data(_load_json(work_dir / PLAN_FILE, "mirror layout plan"))
        if plan.get("schema_version") != 2 or plan.get("layout_fidelity") != EXACT_LAYOUT_FIDELITY:
            raise MirrorPlanError("FULL_MIRROR exact completion requires a V2 EXACT_TEXT_FRAME plan.")
        checks.append(TranslationCheck("layout:exact-plan", True, "V2 exact plan valid"))
    except (MirrorPlanError, TranslationPackageError, OSError) as exc:
        return checks + [TranslationCheck("layout:exact-plan", False, str(exc))], diff

    # These content gates are deliberately downstream of the renderer schemas.
    # They independently compare evidence rather than trusting generator flags.
    try:
        numeric_result, numeric_report = validate_numeric_integrity(work_dir, ledger)
        write_integrity_json(work_dir / NUMERIC_REPORT_FILE, numeric_report)
        checks.append(TranslationCheck(numeric_result.code, numeric_result.passed, numeric_result.detail))
        for result in (
            validate_figure_text_inventory(work_dir, inventory, frames, ledger),
            validate_source_conflicts(work_dir, ledger),
            validate_paper_terminology(work_dir),
        ):
            checks.append(TranslationCheck(result.code, result.passed, result.detail))
    except (TranslationIntegrityError, OSError) as exc:
        checks.append(TranslationCheck("content:integrity-evidence", False, str(exc)))

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
        if not MINIMUM_FONT_SCALE <= float(row.get("font_scale_used", 0)) <= (
            1.10 if frames[row["frame_ids"][0]]["kind"] in EXPANDABLE_FRAME_KINDS else 1.0
        )
    )
    checks.append(
        TranslationCheck(
            "layout:frame-fit",
            not fit_failures and not scale_failures,
            "all translated frames fit within role-specific 95%-110% limits"
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
        residual_passed, residual_report = audit_residuals(
            work_dir, a_path, inventory, frames, ledger_rows,
            contract_version=contract_version,
        )
        write_residual_report(work_dir / RESIDUAL_REPORT_FILE, residual_report)
        audited_ids = {row["frame_id"] for row in residual_report["frames"]}
        for frame in frame_rows:
            if frame["translation_action"] == "TRANSLATE":
                checked = residual_passed and frame["frame_id"] in audited_ids
                frame["residual_checked"] = checked
                frames[frame["frame_id"]]["residual_checked"] = checked
        _write_jsonl_atomic(work_dir / FRAMES_FILE, frame_rows)
        checks.append(TranslationCheck(
            "semantic:visible-english-residual",
            residual_passed,
            "independent role-aware OCR found no unapproved source-matched English residual"
            if residual_passed else f"visible English remains in: {residual_report['failed_frame_ids']}",
        ))
    except (ResidualAuditError, OSError, subprocess.SubprocessError) as exc:
        checks.append(TranslationCheck("semantic:visible-english-residual", False, str(exc)))
    closure_failures = sorted(
        frame_id for frame_id, frame in frames.items()
        if frame["translation_action"] == "TRANSLATE"
        and not all(frame.get(field) is True for field in (
            "source_cleared", "target_rendered", "residual_checked"
        ))
    )
    checks.append(TranslationCheck(
        "layout:frame-closure",
        not closure_failures,
        "every translated frame closes source clearing, target rendering and residual audit"
        if not closure_failures else f"open translated frames: {closure_failures}",
    ))
    typography: dict[str, Any] = {}
    try:
        typography = _load_json(work_dir / TYPOGRAPHY_FIT_FILE, "typography fit")
        records = typography.get("frames") if isinstance(typography, dict) else None
        typography_ok = (
            isinstance(records, list)
            and {item.get("frame_id") for item in records} == set(expected_regions)
            and all(
                isinstance(item.get("target_source_height_ratio"), (int, float))
                and item.get("occupancy_status") in {"TARGET", "WARNING"}
                and 1.15 - 1e-6 <= float(item.get("leading_pt", 0)) / (
                    float(frames[item["frame_id"]]["source_font_size_pt"]) * float(item["font_scale_used"])
                ) <= 1.45 + 1e-6
                for item in records
            )
        )
        checks.append(TranslationCheck(
            "layout:typography-fit",
            typography_ok,
            "typography fit evidence covers every translated frame"
            if typography_ok else "typography fit evidence is missing or incomplete",
        ))
        if contract_version == "1.5.0" and isinstance(records, list):
            target_by_frame = {
                frame_id: str(row.get("translated_text") or "")
                for row in ledger.values()
                for frame_id in row.get("frame_ids", [])
            }
            paragraph_records = [
                {**item, "text": target_by_frame.get(str(item.get("frame_id")), "")}
                for item in records
            ]
            paragraph_checks = validate_paragraph_styles.validate_records(paragraph_records)
            paragraph_checks.append(validate_paragraph_styles.validate_bilingual_texts(paragraph_records))
            checks.extend(
                TranslationCheck(item.code, item.passed, item.detail)
                for item in paragraph_checks
            )
    except (TranslationPackageError, OSError, KeyError, TypeError, ZeroDivisionError) as exc:
        checks.append(TranslationCheck("layout:typography-fit", False, str(exc)))
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
                            # Synthetic bold strokes are clipped to the reviewed frame,
                            # but pdfplumber reports the unclipped glyph box.  Account for
                            # at most the renderer's stroke-scale envelope when assigning
                            # an owner; raster comparison still rejects visible spill.
                            if bbox_contains(
                                [float(value) for value in frame["bbox_pt"]], bbox,
                                tolerance=max(0.25, float(char.get("size") or 0.0) * 0.04),
                            )
                        ]
                        owner = _resolve_cjk_owner(owners)
                        if owner is None:
                            cjk_position_failures.append(output_number)
                            continue
                        frame_id, frame = owner
                        cjk_frame_counts[frame_id] += 1
                        if frame.get("rotation") not in {90, 270}:
                            frame_line_positions[frame_id].append(float(char["top"]))
                        font_name = str(char.get("fontname") or "")
                        expected_families = {
                            style_map.get('roles', {}).get(frame_role(frame), {}).get('cjk_font_family', 'SimSun')
                            if contract_version in {'1.4.2', '1.5.0'} else 'SimSun'
                        }
                        if contract_version in {'1.4.2', '1.5.0'}:
                            expected_families.update(
                                str(run.get('font_family') or '')
                                for run in frame.get('style_runs', [])
                            )
                        if not any(family and family.lower() in font_name.lower() for family in expected_families):
                            cjk_font_failures.append(frame_id)
                        ratio = float(char.get("size") or 0.0) / float(frame["source_font_size_pt"])
                        maximum = 1.10 if frame["kind"] in EXPANDABLE_FRAME_KINDS else 1.0
                        if ratio < MINIMUM_FONT_SCALE - 0.005 or ratio > maximum + 0.005:
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
                "every rendered CJK glyph uses its approved CJK font mapping"
                if not cjk_font_failures
                else f"CJK font mapping mismatches: {sorted(set(cjk_font_failures))}",
            )
        )
        checks.append(
            TranslationCheck(
                "layout:actual-font-scale",
                not actual_scale_failures,
                "rendered CJK sizes remain within role-specific 95%-110% limits"
                if not actual_scale_failures
                else f"out-of-range rendered sizes: {sorted(set(actual_scale_failures))}",
            )
        )
        typography_records = {
            item["frame_id"]: item
            for item in (typography.get("frames", []) if isinstance(typography, dict) else [])
            if isinstance(item, dict) and isinstance(item.get("frame_id"), str)
        }
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
            expected = float(typography_records.get(frame_id, {}).get("leading_pt", frames[frame_id]["source_leading_pt"]))
            plausible = [gap for gap in gaps if expected * 0.75 <= gap <= expected * 1.6]
            if not plausible:
                leading_failures.append(frame_id)
                continue
            plausible.sort()
            observed = plausible[len(plausible) // 2]
            if abs(observed - expected) > 0.75:
                leading_failures.append(frame_id)
        checks.append(
            TranslationCheck(
                "layout:leading",
                not leading_failures,
                "multi-line translated frames match recorded typography leading"
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

