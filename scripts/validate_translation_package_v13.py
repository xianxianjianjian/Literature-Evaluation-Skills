#!/usr/bin/env python3
"""v1.3 exact validator hardening for overlapping reviewed source frames."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import validate_translation_package as core
from exact_mirror import (
    EXACT_LAYOUT_FIDELITY,
    contains_cjk,
    load_json as load_exact_json,
    load_jsonl as load_exact_jsonl,
    validate_exact_inventory,
    validate_exact_ledger,
    validate_text_frames,
)


def _frame_area(frame: dict[str, Any]) -> float:
    x0, y0, x1, y1 = [float(value) for value in frame["bbox_pt"]]
    return max(0.0, (x1 - x0) * (y1 - y0))


def _glyph_center(glyph_bbox: list[float]) -> tuple[float, float]:
    return (
        (float(glyph_bbox[0]) + float(glyph_bbox[2])) / 2.0,
        (float(glyph_bbox[1]) + float(glyph_bbox[3])) / 2.0,
    )


def _center_in_frame(
    frame: dict[str, Any], glyph_bbox: list[float], tolerance: float = 0.25
) -> bool:
    x0, y0, x1, y1 = [float(value) for value in frame["bbox_pt"]]
    cx, cy = _glyph_center(glyph_bbox)
    return (
        x0 - tolerance <= cx <= x1 + tolerance
        and y0 - tolerance <= cy <= y1 + tolerance
    )


def _select_owner(
    owners: list[tuple[str, dict[str, Any]]], area_tolerance: float = 0.01
) -> tuple[str, dict[str, Any]] | None:
    """Choose the unique smallest reviewed frame among center-containing owners.

    Real journal frames can overlap at headings, superscripts and adjacent table
    cells. A glyph center can therefore lie in more than one reviewed bbox even
    though the renderer painted it from exactly one frame. The immutable raster
    gate separately proves that painting never escapes the union of reviewed
    regions; this function only assigns deterministic semantic ownership.
    """
    if not owners:
        return None
    ranked = sorted(owners, key=lambda item: (_frame_area(item[1]), item[0]))
    smallest_area = _frame_area(ranked[0][1])
    tied = [
        item
        for item in ranked
        if abs(_frame_area(item[1]) - smallest_area) <= area_tolerance
    ]
    if len(tied) != 1:
        return None
    return ranked[0]


def _recompute_text_frame_geometry(
    work_dir: Path, a_path: Path
) -> tuple[core.TranslationCheck, dict[str, int]]:
    if core.pdfplumber is None:
        return (
            core.TranslationCheck(
                "layout:text-frame-geometry",
                False,
                "pdfplumber is required",
            ),
            {},
        )

    inventory = validate_exact_inventory(
        load_exact_json(work_dir / core.INVENTORY_FILE, "source inventory")
    )
    frames = validate_text_frames(
        load_exact_jsonl(work_dir / core.FRAMES_FILE, "text frame inventory"),
        inventory,
    )
    ledger = validate_exact_ledger(
        load_exact_jsonl(work_dir / core.LEDGER_FILE, "translation ledger"),
        frames,
    )

    page_frames: dict[int, list[tuple[str, dict[str, Any]]]] = {}
    expected: dict[str, int] = {}
    for page_record in inventory["pages"]:
        translated = [
            (frame_id, frames[frame_id])
            for frame_id in page_record["frame_ids"]
            if frames[frame_id]["translation_action"] == "TRANSLATE"
        ]
        page_frames[page_record["output_page"]] = translated
        for frame_id, _ in translated:
            expected[frame_id] = 0

    ambiguous_pages: list[int] = []
    with core.pdfplumber.open(a_path) as pdf:
        for output_number, page in enumerate(pdf.pages, 1):
            for char in page.chars:
                text_value = str(char.get("text", ""))
                if not contains_cjk(text_value):
                    continue
                glyph_bbox = [
                    float(char["x0"]),
                    float(page.height) - float(char["bottom"]),
                    float(char["x1"]),
                    float(page.height) - float(char["top"]),
                ]
                owners = [
                    (frame_id, frame)
                    for frame_id, frame in page_frames.get(output_number, [])
                    if _center_in_frame(frame, glyph_bbox)
                ]
                owner = _select_owner(owners)
                if owner is None:
                    ambiguous_pages.append(output_number)
                    continue
                expected[owner[0]] += 1

    missing = sorted(
        frame_id
        for frame_id, count in expected.items()
        if count == 0 and contains_cjk(core.frame_to_text(frame_id, ledger))
    )
    passed = not ambiguous_pages and not missing
    detail = (
        "every rendered Chinese glyph has one deterministic reviewed-frame owner"
        if passed
        else f"ambiguous-pages={sorted(set(ambiguous_pages))}; missing-frame-glyphs={missing}"
    )
    return core.TranslationCheck("layout:text-frame-geometry", passed, detail), expected


def validate_package_detailed(
    work_dir: Path,
    a_path: Path,
    scope: str,
    layout_fidelity: str | None = None,
):
    checks, diff, resolved = core.validate_package_detailed(
        work_dir, a_path, scope, layout_fidelity
    )
    if (
        resolved == EXACT_LAYOUT_FIDELITY
        and a_path.is_file()
        and any(check.code == "layout:text-frame-geometry" for check in checks)
    ):
        replacement, counts = _recompute_text_frame_geometry(
            work_dir.resolve(), a_path.resolve()
        )
        checks = [
            replacement if check.code == "layout:text-frame-geometry" else check
            for check in checks
        ]
        if diff is not None:
            for frame in diff.get("frames", []):
                frame_id = frame.get("frame_id")
                if frame_id in counts:
                    frame["cjk_glyph_count"] = counts[frame_id]
            diff["passed"] = all(check.passed for check in checks)
            diff["checks"] = [core.asdict(check) for check in checks]
    return checks, diff, resolved


def main(argv: list[str] | None = None) -> int:
    args = core.build_parser().parse_args(argv)
    checks, layout_diff, resolved_fidelity = validate_package_detailed(
        args.work_dir, args.a_path, args.scope, args.layout_fidelity
    )
    if layout_diff is not None:
        core.write_layout_diff(
            args.work_dir.resolve() / core.LAYOUT_DIFF_FILE,
            layout_diff,
        )
    core.write_report(
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
