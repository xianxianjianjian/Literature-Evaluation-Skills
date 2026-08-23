#!/usr/bin/env python3
"""Build and validate deterministic mirror-PDF layout plans.

This helper does not translate text and is not a publisher-grade automatic
relayout engine. It freezes page/layout decisions for the required workflow:
V1 structural plans remain readable for explicit legacy use. V2 exact plans
freeze one-to-one source pages, reviewed text frames, SimSun, and a 95% font
floor. Actual A production still requires rendering and independent validation.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from exact_mirror import (
    EXACT_LAYOUT_FIDELITY,
    MINIMUM_FONT_SCALE as EXACT_MINIMUM_FONT_SCALE,
    REQUIRED_CJK_FONT,
    ExactMirrorError,
    load_jsonl,
    validate_exact_inventory,
    validate_font_map,
    validate_text_frames,
)

STRATEGIES = ("strict-mirror", "adaptive-mirror", "readable-extension")
DEFAULT_FONT_SCALE = 1.10
MINIMUM_FONT_PT = 8.5
PLAN_STATUS_VALUES = {"PLANNED", "LAYOUT_QC_IN_PROGRESS", "LAYOUT_QC_PASSED"}


class MirrorPlanError(ValueError):
    """Raised when a mirror-layout plan is incomplete or unsafe."""


def validate_pdf_source(path: Path) -> None:
    if not path.is_file():
        raise MirrorPlanError(f"Source PDF does not exist: {path}")
    if path.suffix.lower() != ".pdf":
        raise MirrorPlanError("Source file must use a .pdf extension.")
    try:
        header = path.read_bytes()[:5]
    except OSError as exc:
        raise MirrorPlanError(f"Cannot read source PDF: {exc}") from exc
    if header != b"%PDF-":
        raise MirrorPlanError("Source file does not have a valid PDF signature.")


def load_json(path: Path, label: str) -> Any:
    if not path.is_file():
        raise MirrorPlanError(f"{label} does not exist: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MirrorPlanError(f"Invalid {label} JSON: {exc}") from exc


def load_page_map(path: Path) -> dict[str, Any]:
    data = load_json(path, "page map")
    if not isinstance(data, dict) or not isinstance(data.get("pages"), list):
        raise MirrorPlanError("Page map must be an object containing a pages list.")
    if not data["pages"]:
        raise MirrorPlanError("Page map pages list cannot be empty.")
    seen: set[int] = set()
    for index, page in enumerate(data["pages"], start=1):
        if not isinstance(page, dict):
            raise MirrorPlanError(f"Page map entry {index} must be an object.")
        number = page.get("page_number", index)
        if not isinstance(number, int) or number <= 0:
            raise MirrorPlanError(f"Page {index} page_number must be a positive integer.")
        if number in seen:
            raise MirrorPlanError(f"Duplicate page_number in page map: {number}")
        seen.add(number)
        source_id = page.get("source_id", "SRC-M1")
        source_page = page.get("source_page", number)
        if not isinstance(source_id, str) or not source_id.strip():
            raise MirrorPlanError(f"Page {number} source_id must be non-empty text.")
        if not isinstance(source_page, int) or source_page <= 0:
            raise MirrorPlanError(f"Page {number} source_page must be a positive integer.")
        for field in ("text_blocks", "figure_placeholders", "table_placeholders"):
            if field in page and not isinstance(page[field], list):
                raise MirrorPlanError(f"Page {number} field {field} must be a list.")
        if "table_placements" in page and not isinstance(page["table_placements"], list):
            raise MirrorPlanError(f"Page {number} table_placements must be a list.")
    return data


def _placeholder_ids(items: list[Any]) -> list[str]:
    identifiers: list[str] = []
    for item in items:
        if isinstance(item, str) and item.strip():
            identifiers.append(item.strip())
        elif isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"].strip():
            identifiers.append(item["id"].strip())
    return identifiers


def create_plan(args: argparse.Namespace) -> dict[str, Any]:
    if getattr(args, "source_inventory", None):
        return create_exact_plan(args)
    if args.source_pdf is None or args.page_map is None or args.output_pdf is None:
        raise MirrorPlanError(
            "Legacy structural create-plan requires --source-pdf, --page-map, and --output-pdf."
        )
    validate_pdf_source(args.source_pdf)
    if args.output_pdf.suffix.lower() != ".pdf":
        raise MirrorPlanError("Output path must use a .pdf extension.")
    if not 1.05 <= args.font_scale <= 1.15:
        raise MirrorPlanError("Initial font scale must be between 1.05 and 1.15.")
    page_map = load_page_map(args.page_map)
    pages = []
    for index, page in enumerate(page_map["pages"], start=1):
        page_number = page.get("page_number", index)
        figures = page.get("figure_placeholders", [])
        tables = page.get("table_placeholders", [])
        pages.append(
            {
                "page_number": page_number,
                "output_page_number": page_number,
                "source_page_label": page.get("source_page_label"),
                "source_page_refs": [
                    {
                        "source_id": page.get("source_id", "SRC-M1"),
                        "source_page": page.get("source_page", page_number),
                    }
                ],
                "text_blocks": page.get("text_blocks", []),
                "figure_placeholders": figures,
                "table_placeholders": tables,
                "placed_object_ids": _placeholder_ids(figures + tables),
                "table_placements": page.get("table_placements", []),
                "adaptive_font_sizing": {
                    "initial_scale": args.font_scale,
                    "minimum_font_pt": MINIMUM_FONT_PT,
                    "minimum_is_safety_floor_not_target": True,
                },
                "layout_strategy_used": None,
                "overflow_detected": None,
                "extension_page": None,
                "extension_of": None,
                "render_checked": False,
                "render_notes": [],
            }
        )
    return {
        "schema_version": 1,
        "helper_scope": "V1_LAYOUT_HELPER_NOT_FULL_AUTOMATIC_RELAYOUT",
        "source_pdf": str(args.source_pdf.resolve()),
        "output_pdf": str(args.output_pdf.resolve()),
        "strategy_order": list(STRATEGIES),
        "requested_strategy": args.strategy,
        "page_count_planned": len(pages),
        "pages": pages,
        "layout_qc": {
            "render_required": True,
            "visual_inspection_required": True,
            "all_pages_checked": False,
            "status": "PLANNED",
        },
    }


def create_exact_plan(args: argparse.Namespace) -> dict[str, Any]:
    if args.layout_fidelity != EXACT_LAYOUT_FIDELITY:
        raise MirrorPlanError("Exact create-plan requires --layout-fidelity EXACT_TEXT_FRAME.")
    if args.cjk_font_family != REQUIRED_CJK_FONT:
        raise MirrorPlanError("Exact create-plan requires --cjk-font-family SimSun.")
    if float(args.minimum_font_scale) != EXACT_MINIMUM_FONT_SCALE:
        raise MirrorPlanError("Exact create-plan requires --minimum-font-scale 0.95.")
    try:
        inventory = validate_exact_inventory(load_json(args.source_inventory, "source inventory"))
        frame_path = args.text_frame_inventory or args.source_inventory.with_name(
            "text_frame_inventory.jsonl"
        )
        frames = validate_text_frames(
            load_jsonl(frame_path, "text frame inventory"), inventory
        )
        font_path = args.font_map or args.source_inventory.with_name("font_map.json")
        font_map = validate_font_map(load_json(font_path, "font map"))
    except ExactMirrorError as exc:
        raise MirrorPlanError(str(exc)) from exc

    output_pdf = args.output_pdf
    if output_pdf is None:
        output_pdf = args.source_inventory.with_name("A_EXACT_TEXT_FRAME_zh.pdf")
    if output_pdf.suffix.lower() != ".pdf":
        raise MirrorPlanError("Output path must use a .pdf extension.")
    pages: list[dict[str, Any]] = []
    objects = {item["object_id"]: item for item in inventory["objects"]}
    for source_page in sorted(inventory["pages"], key=lambda item: item["output_page"]):
        page_frame_ids = source_page["frame_ids"]
        replacement_regions = [
            {
                "frame_id": frame_id,
                "bbox_pt": frames[frame_id]["bbox_pt"],
                "kind": frames[frame_id]["kind"],
                "background": frames[frame_id]["background"],
                "font_scale_used": None,
                "fit_status": None,
                "background_patch_path": frames[frame_id].get("background_patch_path"),
            }
            for frame_id in page_frame_ids
            if frames[frame_id]["translation_action"] == "TRANSLATE"
        ]
        pages.append(
            {
                "page_number": source_page["output_page"],
                "output_page_number": source_page["output_page"],
                "source_page_refs": [
                    {
                        "source_id": source_page["source_id"],
                        "source_page": source_page["source_page"],
                    }
                ],
                "page_boxes": {
                    field: source_page[field]
                    for field in ("media_box", "crop_box", "trim_box", "bleed_box", "art_box")
                },
                "rotation": source_page["rotation"],
                "frame_ids": page_frame_ids,
                "replacement_regions": replacement_regions,
                "placed_object_ids": source_page["object_ids"],
                "table_placements": [
                    {
                        "object_id": object_id,
                        "mode": "exact-cells",
                        "rows": objects[object_id]["table_structure"]["rows"],
                        "columns": objects[object_id]["table_structure"]["columns"],
                        "header_rows": objects[object_id]["table_structure"]["header_rows"],
                        "merged_cells": objects[object_id]["table_structure"]["merged_cells"],
                        "footnotes": objects[object_id]["table_structure"]["footnotes"],
                        "cell_frame_ids": [cell["frame_id"] for cell in objects[object_id]["cells"]],
                    }
                    for object_id in source_page["object_ids"]
                    if objects[object_id]["kind"] == "table"
                ],
                "layout_strategy_used": "exact-text-frame",
                "extension_page": False,
                "render_checked": False,
                "render_notes": [],
            }
        )
    return {
        "schema_version": 2,
        "layout_fidelity": EXACT_LAYOUT_FIDELITY,
        "scope": "FULL_MIRROR",
        "source_inventory": str(args.source_inventory.resolve()),
        "text_frame_inventory": str(frame_path.resolve()),
        "font_map": str(font_path.resolve()),
        "output_pdf": str(output_pdf.resolve()),
        "cjk_font_family": font_map["cjk_font_family"],
        "minimum_font_scale": EXACT_MINIMUM_FONT_SCALE,
        "page_count_planned": len(pages),
        "pages": pages,
        "layout_qc": {
            "render_required": True,
            "visual_inspection_required": True,
            "all_pages_checked": False,
            "status": "PLANNED",
        },
    }


def validate_plan_data(plan: object) -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise MirrorPlanError("Plan root must be an object.")
    if plan.get("schema_version") == 2:
        return validate_exact_plan_data(plan)
    if plan.get("schema_version") != 1:
        raise MirrorPlanError("Plan schema_version must be 1 or 2.")
    if plan.get("strategy_order") != list(STRATEGIES):
        raise MirrorPlanError("Plan strategy_order does not match the frozen V1 escalation.")
    if plan.get("requested_strategy") not in STRATEGIES:
        raise MirrorPlanError("Plan requested_strategy is invalid.")
    pages = plan.get("pages")
    if not isinstance(pages, list) or not pages:
        raise MirrorPlanError("Plan pages must be a non-empty list.")
    if plan.get("page_count_planned") != len(pages):
        raise MirrorPlanError("page_count_planned does not equal the number of plan pages.")
    seen: set[int] = set()
    for page in pages:
        if not isinstance(page, dict):
            raise MirrorPlanError("Every plan page must be an object.")
        number = page.get("page_number")
        if not isinstance(number, int) or number <= 0 or number in seen:
            raise MirrorPlanError(f"Invalid or duplicate plan page number: {number!r}")
        seen.add(number)
        sizing = page.get("adaptive_font_sizing")
        if not isinstance(sizing, dict):
            raise MirrorPlanError(f"Page {number} is missing adaptive_font_sizing.")
        scale = sizing.get("initial_scale")
        if not isinstance(scale, (int, float)) or not 1.05 <= float(scale) <= 1.15:
            raise MirrorPlanError(f"Page {number} initial font scale is outside 1.05-1.15.")
        if sizing.get("minimum_font_pt") != MINIMUM_FONT_PT:
            raise MirrorPlanError(
                f"Page {number} minimum font floor must remain {MINIMUM_FONT_PT} pt."
            )
        strategy = page.get("layout_strategy_used")
        if strategy is not None and strategy not in STRATEGIES:
            raise MirrorPlanError(f"Page {number} has invalid layout_strategy_used.")
        if not isinstance(page.get("render_checked"), bool):
            raise MirrorPlanError(f"Page {number} render_checked must be boolean.")
        notes = page.get("render_notes")
        if not isinstance(notes, list) or not all(isinstance(note, str) for note in notes):
            raise MirrorPlanError(f"Page {number} render_notes must be a list of strings.")
        output_number = page.get("output_page_number")
        if not isinstance(output_number, int) or output_number <= 0:
            raise MirrorPlanError(f"Page {number} output_page_number must be a positive integer.")
        refs = page.get("source_page_refs")
        if not isinstance(refs, list) or not refs:
            raise MirrorPlanError(f"Page {number} source_page_refs must be a non-empty list.")
        for ref in refs:
            if (
                not isinstance(ref, dict)
                or not isinstance(ref.get("source_id"), str)
                or not ref["source_id"].strip()
                or not isinstance(ref.get("source_page"), int)
                or ref["source_page"] <= 0
            ):
                raise MirrorPlanError(f"Page {number} has an invalid source_page_refs entry.")
        placed = page.get("placed_object_ids")
        if not isinstance(placed, list) or not all(
            isinstance(item, str) and item.strip() for item in placed
        ):
            raise MirrorPlanError(f"Page {number} placed_object_ids must be a list of IDs.")
        placements = page.get("table_placements")
        if not isinstance(placements, list):
            raise MirrorPlanError(f"Page {number} table_placements must be a list.")
    qc = plan.get("layout_qc")
    if not isinstance(qc, dict):
        raise MirrorPlanError("layout_qc object is required.")
    if qc.get("status") not in PLAN_STATUS_VALUES:
        raise MirrorPlanError("layout_qc.status is invalid.")
    all_checked = all(page["render_checked"] for page in pages)
    if qc.get("status") == "LAYOUT_QC_PASSED" and not all_checked:
        raise MirrorPlanError(
            "LAYOUT_QC_PASSED requires render_checked=true for every page."
        )
    if bool(qc.get("all_pages_checked")) != all_checked:
        raise MirrorPlanError(
            "layout_qc.all_pages_checked must match per-page render_checked values."
        )
    return plan


def validate_exact_plan_data(plan: dict[str, Any]) -> dict[str, Any]:
    if plan.get("layout_fidelity") != EXACT_LAYOUT_FIDELITY:
        raise MirrorPlanError("V2 plan requires layout_fidelity=EXACT_TEXT_FRAME.")
    if plan.get("scope") != "FULL_MIRROR":
        raise MirrorPlanError("V2 exact plan scope must be FULL_MIRROR.")
    if plan.get("cjk_font_family") != REQUIRED_CJK_FONT:
        raise MirrorPlanError("V2 exact plan requires SimSun.")
    if plan.get("minimum_font_scale") != EXACT_MINIMUM_FONT_SCALE:
        raise MirrorPlanError("V2 exact plan minimum_font_scale must be 0.95.")
    for field in ("source_inventory", "text_frame_inventory", "font_map", "output_pdf"):
        if not isinstance(plan.get(field), str) or not plan[field].strip():
            raise MirrorPlanError(f"V2 exact plan requires {field}.")
    pages = plan.get("pages")
    if not isinstance(pages, list) or not pages:
        raise MirrorPlanError("V2 exact plan requires pages.")
    if plan.get("page_count_planned") != len(pages):
        raise MirrorPlanError("V2 exact page_count_planned does not match pages.")
    seen_outputs: set[int] = set()
    seen_sources: set[tuple[str, int]] = set()
    for page in pages:
        if not isinstance(page, dict):
            raise MirrorPlanError("Every V2 exact page must be an object.")
        output_page = page.get("output_page_number")
        if not isinstance(output_page, int) or output_page <= 0 or output_page in seen_outputs:
            raise MirrorPlanError(f"Invalid or duplicate V2 output page: {output_page!r}")
        refs = page.get("source_page_refs")
        if not isinstance(refs, list) or len(refs) != 1:
            raise MirrorPlanError(f"V2 page {output_page} must map to exactly one source page.")
        ref = refs[0]
        if (
            not isinstance(ref, dict)
            or not isinstance(ref.get("source_id"), str)
            or not ref["source_id"].strip()
            or not isinstance(ref.get("source_page"), int)
            or ref["source_page"] <= 0
        ):
            raise MirrorPlanError(f"V2 page {output_page} has invalid source_page_refs.")
        source_ref = (ref["source_id"], ref["source_page"])
        if source_ref in seen_sources:
            raise MirrorPlanError(f"V2 source page is mapped more than once: {source_ref}")
        if page.get("layout_strategy_used") != "exact-text-frame":
            raise MirrorPlanError(f"V2 page {output_page} cannot use adaptive/extension layout.")
        if page.get("extension_page") is not False:
            raise MirrorPlanError(f"V2 page {output_page} cannot be an extension page.")
        if page.get("rotation") not in {0, 90, 180, 270}:
            raise MirrorPlanError(f"V2 page {output_page} has invalid rotation.")
        boxes = page.get("page_boxes")
        if not isinstance(boxes, dict) or set(boxes) != {
            "media_box", "crop_box", "trim_box", "bleed_box", "art_box"
        }:
            raise MirrorPlanError(f"V2 page {output_page} has incomplete page_boxes.")
        for box in boxes.values():
            if (
                not isinstance(box, list)
                or len(box) != 4
                or not all(isinstance(value, (int, float)) for value in box)
            ):
                raise MirrorPlanError(f"V2 page {output_page} has invalid page box.")
        frame_ids = page.get("frame_ids")
        regions = page.get("replacement_regions")
        if not isinstance(frame_ids, list) or not all(isinstance(item, str) and item for item in frame_ids):
            raise MirrorPlanError(f"V2 page {output_page} has invalid frame_ids.")
        if not isinstance(regions, list):
            raise MirrorPlanError(f"V2 page {output_page} has invalid replacement_regions.")
        region_ids: set[str] = set()
        for region in regions:
            if not isinstance(region, dict) or region.get("frame_id") not in frame_ids:
                raise MirrorPlanError(f"V2 page {output_page} has an unowned replacement region.")
            if region["frame_id"] in region_ids:
                raise MirrorPlanError(f"V2 page {output_page} has duplicate replacement regions.")
            bbox = region.get("bbox_pt")
            if (
                not isinstance(bbox, list)
                or len(bbox) != 4
                or not all(isinstance(value, (int, float)) for value in bbox)
                or bbox[2] <= bbox[0]
                or bbox[3] <= bbox[1]
            ):
                raise MirrorPlanError(f"V2 page {output_page} has an invalid replacement bbox.")
            scale = region.get("font_scale_used")
            if scale is not None and not EXACT_MINIMUM_FONT_SCALE <= float(scale) <= 1.0:
                raise MirrorPlanError(f"V2 page {output_page} has font scale outside 0.95-1.00.")
            region_ids.add(region["frame_id"])
        for field in ("placed_object_ids", "table_placements", "render_notes"):
            if not isinstance(page.get(field), list):
                raise MirrorPlanError(f"V2 page {output_page} requires {field} list.")
        if not isinstance(page.get("render_checked"), bool):
            raise MirrorPlanError(f"V2 page {output_page} render_checked must be boolean.")
        seen_outputs.add(output_page)
        seen_sources.add(source_ref)
    if seen_outputs != set(range(1, len(pages) + 1)):
        raise MirrorPlanError("V2 output pages must be contiguous from 1.")
    qc = plan.get("layout_qc")
    if not isinstance(qc, dict) or qc.get("status") not in PLAN_STATUS_VALUES:
        raise MirrorPlanError("V2 exact plan requires valid layout_qc.")
    return plan


def write_json(path: Path, data: dict[str, Any], overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise MirrorPlanError(f"Output already exists: {path}. Use --force to replace it.")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", delete=False, dir=path.parent
    ) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    temporary.replace(path)


def command_create_plan(args: argparse.Namespace) -> None:
    plan = create_plan(args)
    validate_plan_data(plan)
    write_json(args.plan_output, plan, args.force)
    print(f"Created mirror layout plan: {args.plan_output}")
    print(
        "Next gate: render every page, visually inspect, record QC, then re-render if needed."
    )


def command_validate_plan(args: argparse.Namespace) -> None:
    plan = load_json(args.plan, "layout plan")
    validate_plan_data(plan)
    print(f"Valid mirror layout plan: {args.plan}")


def command_create_font_map(args: argparse.Namespace) -> None:
    font_path = args.font_path.resolve()
    if not font_path.is_file() or font_path.name.lower() != "simsun.ttc":
        raise MirrorPlanError(f"Required SimSun font is missing: {font_path}")
    data = {
        "schema_version": 1,
        "cjk_font_family": REQUIRED_CJK_FONT,
        "font_path": str(font_path),
        "ttc_face_index": 0,
        "fallback_allowed": False,
        "regular_mode": "embedded-subset",
        "bold_mode": "synthetic-stroke",
        "italic_mode": "synthetic-shear",
        "expected_pdf_font_name": "SimSun",
    }
    validate_font_map(data)
    write_json(args.output, data, args.force)
    print(f"Created strict SimSun font map: {args.output}")


def command_show_strategies(args: argparse.Namespace) -> None:
    print(
        json.dumps(
            {
                "default_full_mirror": {
                    "layout_fidelity": EXACT_LAYOUT_FIDELITY,
                    "strategy": "exact-text-frame",
                    "cjk_font_family": REQUIRED_CJK_FONT,
                    "font_scale_steps": [1.0, 0.99, 0.98, 0.97, 0.96, 0.95],
                    "automatic_fallback": False,
                },
                "explicit_structural_mirror": {
                    "strategy_order": list(STRATEGIES),
                    "initial_font_scale_range": [1.05, 1.15],
                    "default_font_scale": DEFAULT_FONT_SCALE,
                    "minimum_font_pt": MINIMUM_FONT_PT,
                },
                "qa_loop": "render -> inspect -> iterate -> re-render",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser(
        "create-plan", help="Create an exact V2 or explicit structural V1 plan."
    )
    plan.add_argument("--source-pdf", type=Path)
    plan.add_argument("--page-map", type=Path)
    plan.add_argument("--source-inventory", type=Path)
    plan.add_argument("--text-frame-inventory", type=Path)
    plan.add_argument("--font-map", type=Path)
    plan.add_argument(
        "--plan-output", "--output", dest="plan_output", type=Path, required=True
    )
    plan.add_argument("--output-pdf", type=Path)
    plan.add_argument("--strategy", choices=STRATEGIES, default="strict-mirror")
    plan.add_argument("--font-scale", type=float, default=DEFAULT_FONT_SCALE)
    plan.add_argument(
        "--layout-fidelity",
        choices=(EXACT_LAYOUT_FIDELITY, "STRUCTURAL_MIRROR"),
        default=EXACT_LAYOUT_FIDELITY,
    )
    plan.add_argument("--cjk-font-family", default=REQUIRED_CJK_FONT)
    plan.add_argument(
        "--minimum-font-scale", type=float, default=EXACT_MINIMUM_FONT_SCALE
    )
    plan.add_argument("--force", action="store_true")
    plan.set_defaults(handler=command_create_plan)

    validate = subparsers.add_parser(
        "validate-plan", help="Validate a V1 layout/QC plan."
    )
    validate.add_argument("--plan", type=Path, required=True)
    validate.set_defaults(handler=command_validate_plan)

    font_map = subparsers.add_parser(
        "create-font-map", help="Create the no-fallback SimSun font map."
    )
    font_map.add_argument(
        "--font-path", type=Path, default=Path(r"C:\Windows\Fonts\simsun.ttc")
    )
    font_map.add_argument("--output", type=Path, required=True)
    font_map.add_argument("--force", action="store_true")
    font_map.set_defaults(handler=command_create_font_map)

    strategies = subparsers.add_parser(
        "show-strategies", help="Show frozen layout strategy and QA rules."
    )
    strategies.set_defaults(handler=command_show_strategies)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.handler(args)
    except (MirrorPlanError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
