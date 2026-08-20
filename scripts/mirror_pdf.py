#!/usr/bin/env python3
"""Create and validate Phase 1 layout plans for a future mirror-PDF engine.

This module does not generate deliverable A. It freezes a deterministic layout
interface for page maps, text blocks, figure/table placeholders, adaptive font
sizing, overflow detection, extension pages, and the intended output path.
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


class MirrorPlanError(ValueError):
    """Raised when a layout plan request is incomplete or unsafe."""


def load_page_map(path: Path) -> dict[str, Any]:
    """Load the page-map JSON used by the Phase 1 planning interface."""
    if not path.is_file():
        raise MirrorPlanError(f"Page map does not exist: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MirrorPlanError(f"Invalid page-map JSON: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("pages"), list):
        raise MirrorPlanError("Page map must be an object containing a pages list.")
    for index, page in enumerate(data["pages"], start=1):
        if not isinstance(page, dict):
            raise MirrorPlanError(f"Page map entry {index} must be an object.")
        for field in ("text_blocks", "figure_placeholders", "table_placeholders"):
            if field in page and not isinstance(page[field], list):
                raise MirrorPlanError(f"Page {index} field {field} must be a list.")
    return data


def create_plan(args: argparse.Namespace) -> dict[str, Any]:
    """Build a layout plan without editing or generating a PDF."""
    if not args.source_pdf.is_file():
        raise MirrorPlanError(f"Source PDF does not exist: {args.source_pdf}")
    if args.source_pdf.suffix.lower() != ".pdf":
        raise MirrorPlanError("Source file must use a .pdf extension.")
    if args.output_pdf.suffix.lower() != ".pdf":
        raise MirrorPlanError("Future output path must use a .pdf extension.")
    if not 1.05 <= args.font_scale <= 1.15:
        raise MirrorPlanError("Initial font scale must be between 1.05 and 1.15.")
    page_map = load_page_map(args.page_map)
    pages = []
    for number, page in enumerate(page_map["pages"], start=1):
        pages.append(
            {
                "page_number": page.get("page_number", number),
                "text_blocks": page.get("text_blocks", []),
                "figure_placeholders": page.get("figure_placeholders", []),
                "table_placeholders": page.get("table_placeholders", []),
                "adaptive_font_sizing": {
                    "initial_scale": args.font_scale,
                    "minimum_font_pt": MINIMUM_FONT_PT,
                    "minimum_is_safety_floor_not_target": True,
                },
                "overflow_detected": None,
                "extension_page": None,
            }
        )
    return {
        "schema_version": 1,
        "phase": "PHASE_1_LAYOUT_PLAN_ONLY",
        "source_pdf": str(args.source_pdf.resolve()),
        "output_pdf": str(args.output_pdf.resolve()),
        # Future Chinese layout escalation order:
        # Strict Mirror -> Adaptive Mirror -> Readable Extension.
        "strategy_order": list(STRATEGIES),
        "requested_strategy": args.strategy,
        "pages": pages,
        "production_status": "NOT_IMPLEMENTED_IN_PHASE_1",
    }


def write_json(path: Path, data: dict[str, Any], overwrite: bool) -> None:
    """Write a plan atomically, refusing accidental overwrite by default."""
    if path.exists() and not overwrite:
        raise MirrorPlanError(f"Plan already exists: {path}. Use --force to replace it.")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", delete=False, dir=path.parent
    ) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    temporary.replace(path)


def command_create_plan(args: argparse.Namespace) -> None:
    """Create a future-engine layout plan."""
    plan = create_plan(args)
    write_json(args.plan_output, plan, args.force)
    print(f"Created Phase 1 layout plan: {args.plan_output}")
    print("PDF production: NOT_IMPLEMENTED_IN_PHASE_1")


def command_show_strategies(args: argparse.Namespace) -> None:
    """Show the frozen strategy escalation and font-size policy."""
    print(
        json.dumps(
            {
                "strategy_order": list(STRATEGIES),
                "initial_font_scale_range": [1.05, 1.15],
                "default_font_scale": DEFAULT_FONT_SCALE,
                "minimum_font_pt": MINIMUM_FONT_PT,
                "note": "8.5 pt is an extreme safety floor, not a target size.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("create-plan", help="Create a Phase 1 layout plan.")
    plan.add_argument("--source-pdf", type=Path, required=True)
    plan.add_argument("--page-map", type=Path, required=True)
    plan.add_argument("--plan-output", type=Path, required=True)
    plan.add_argument("--output-pdf", type=Path, required=True)
    plan.add_argument("--strategy", choices=STRATEGIES, default="strict-mirror")
    plan.add_argument("--font-scale", type=float, default=DEFAULT_FONT_SCALE)
    plan.add_argument("--force", action="store_true")
    plan.set_defaults(handler=command_create_plan)

    strategies = subparsers.add_parser(
        "show-strategies", help="Show the frozen future layout strategy."
    )
    strategies.set_defaults(handler=command_show_strategies)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the mirror-PDF planning CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.handler(args)
    except (MirrorPlanError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
