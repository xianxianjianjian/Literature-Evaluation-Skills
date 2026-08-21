#!/usr/bin/env python3
"""Build and validate deterministic V1 mirror-PDF layout plans.

This helper does not translate text and is not a publisher-grade automatic
relayout engine. It freezes page/layout decisions for the required workflow:
Strict Mirror -> Adaptive Mirror -> Readable Extension. Actual A production
must still follow render -> inspect -> iterate -> re-render verification.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

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
        for field in ("text_blocks", "figure_placeholders", "table_placeholders"):
            if field in page and not isinstance(page[field], list):
                raise MirrorPlanError(f"Page {number} field {field} must be a list.")
    return data


def create_plan(args: argparse.Namespace) -> dict[str, Any]:
    validate_pdf_source(args.source_pdf)
    if args.output_pdf.suffix.lower() != ".pdf":
        raise MirrorPlanError("Output path must use a .pdf extension.")
    if not 1.05 <= args.font_scale <= 1.15:
        raise MirrorPlanError("Initial font scale must be between 1.05 and 1.15.")
    page_map = load_page_map(args.page_map)
    pages = []
    for index, page in enumerate(page_map["pages"], start=1):
        pages.append(
            {
                "page_number": page.get("page_number", index),
                "source_page_label": page.get("source_page_label"),
                "text_blocks": page.get("text_blocks", []),
                "figure_placeholders": page.get("figure_placeholders", []),
                "table_placeholders": page.get("table_placeholders", []),
                "adaptive_font_sizing": {
                    "initial_scale": args.font_scale,
                    "minimum_font_pt": MINIMUM_FONT_PT,
                    "minimum_is_safety_floor_not_target": True,
                },
                "layout_strategy_used": None,
                "overflow_detected": None,
                "extension_page": None,
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


def validate_plan_data(plan: object) -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise MirrorPlanError("Plan root must be an object.")
    if plan.get("schema_version") != 1:
        raise MirrorPlanError("Plan schema_version must be 1.")
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
    print(f"Created V1 mirror layout plan: {args.plan_output}")
    print(
        "Next gate: render every page, visually inspect, record QC, then re-render if needed."
    )


def command_validate_plan(args: argparse.Namespace) -> None:
    plan = load_json(args.plan, "layout plan")
    validate_plan_data(plan)
    print(f"Valid V1 mirror layout plan: {args.plan}")


def command_show_strategies(args: argparse.Namespace) -> None:
    print(
        json.dumps(
            {
                "strategy_order": list(STRATEGIES),
                "initial_font_scale_range": [1.05, 1.15],
                "default_font_scale": DEFAULT_FONT_SCALE,
                "minimum_font_pt": MINIMUM_FONT_PT,
                "note": "8.5 pt is an extreme safety floor, not a target size.",
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
        "create-plan", help="Create a deterministic V1 layout plan."
    )
    plan.add_argument("--source-pdf", type=Path, required=True)
    plan.add_argument("--page-map", type=Path, required=True)
    plan.add_argument("--plan-output", type=Path, required=True)
    plan.add_argument("--output-pdf", type=Path, required=True)
    plan.add_argument("--strategy", choices=STRATEGIES, default="strict-mirror")
    plan.add_argument("--font-scale", type=float, default=DEFAULT_FONT_SCALE)
    plan.add_argument("--force", action="store_true")
    plan.set_defaults(handler=command_create_plan)

    validate = subparsers.add_parser(
        "validate-plan", help="Validate a V1 layout/QC plan."
    )
    validate.add_argument("--plan", type=Path, required=True)
    validate.set_defaults(handler=command_validate_plan)

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
