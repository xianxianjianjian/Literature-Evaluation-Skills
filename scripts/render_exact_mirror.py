#!/usr/bin/env python3
"""Render a FULL_MIRROR PDF by replacing reviewed source text frames in place."""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
except ImportError:  # pragma: no cover - CLI dependency check
    PdfReader = PdfWriter = pdfmetrics = TTFont = canvas = None

from exact_mirror import (
    FONT_SCALE_STEPS,
    EXPANDABLE_FRAME_KINDS,
    ExactMirrorError,
    load_json,
    load_jsonl,
    validate_exact_inventory,
    validate_exact_ledger,
    validate_font_map,
    validate_text_frames,
)
from mirror_pdf import MirrorPlanError, validate_plan_data
from normalize_chinese_typography import (
    SemanticToken,
    normalize_chinese_text,
    normalize_inline_citations,
    semantic_tokens,
)


class ExactMirrorRenderError(ValueError):
    """Raised when exact replacement cannot be rendered within the contract."""


def _require_dependencies() -> None:
    if any(item is None for item in (PdfReader, PdfWriter, pdfmetrics, TTFont, canvas)):
        raise ExactMirrorRenderError(
            "pypdf and reportlab are required. Use the bundled Codex PDF runtime "
            "or install requirements-exact-mirror.txt."
        )


def _resolve_source_pdf(work_dir: Path, source: dict[str, Any]) -> Path:
    """Resolve inventory pdf_path relative to the package work directory."""
    value = source.get("pdf_path")
    if not isinstance(value, str) or not value.strip():
        raise ExactMirrorRenderError(
            f"Source {source.get('source_id', '<unknown>')} requires pdf_path."
        )
    path = Path(value)
    if not path.is_absolute():
        path = work_dir / path
    if not path.is_file():
        raise ExactMirrorRenderError(f"Source PDF is missing: {path}")
    return path.resolve()


def _token_width(token: SemanticToken, font_name: str, font_size: float) -> float:
    size = font_size * 0.65 if token.kind == "CITATION" else font_size
    if token.kind in {"SCIENTIFIC", "STAT"}:
        match = re.fullmatch(r"(.+?10)([+−-]?\d+)", token.text)
        if match:
            return (
                pdfmetrics.stringWidth(match.group(1), font_name, font_size)
                + pdfmetrics.stringWidth(match.group(2), font_name, font_size * 0.65)
            )
    return pdfmetrics.stringWidth(token.text, font_name, size)


def _wrap_paragraph(text: str, font_name: str, font_size: float, width: float) -> list[list[SemanticToken]]:
    if not text:
        return [[]]
    lines: list[list[SemanticToken]] = []
    current: list[SemanticToken] = []
    current_width = 0.0
    for token in semantic_tokens(text):
        if token.kind == "BREAK":
            while current and current[-1].kind == "SPACE":
                current.pop()
            lines.append(current)
            current = []
            current_width = 0.0
            continue
        token_width = _token_width(token, font_name, font_size)
        if current and current_width + token_width > width:
            if token.kind == "PUNCTUATION" and token.text in "，。；：！？、）】》":
                carry: list[SemanticToken] = []
                while current and current[-1].kind == "SPACE":
                    current_width -= _token_width(current.pop(), font_name, font_size)
                if current:
                    carry.insert(0, current.pop())
                lines.append(current)
                current = carry + [token]
                current_width = sum(_token_width(item, font_name, font_size) for item in current)
                continue
            if current[-1].kind == "PUNCTUATION" and current[-1].text in "（【《":
                opener = current.pop()
                current_width -= _token_width(opener, font_name, font_size)
                lines.append(current)
                current = [opener, token]
                current_width = _token_width(opener, font_name, font_size) + token_width
                continue
            while current and current[-1].kind == "SPACE":
                current_width -= _token_width(current.pop(), font_name, font_size)
            lines.append(current)
            current = [] if token.kind == "SPACE" else [token]
            current_width = 0.0 if token.kind == "SPACE" else token_width
            continue
        if not current and token.kind == "SPACE":
            continue
        current.append(token)
        current_width += token_width
    if current or not lines:
        lines.append(current)
    return lines


def _used_height(lines: list[list[SemanticToken]], font_size: float, leading: float) -> float:
    return font_size + max(0, len(lines) - 1) * leading


def _layout(text: str, source_text: str, frame: dict[str, Any]) -> tuple[float, float, list[list[SemanticToken]], dict[str, Any]] | None:
    x0, y0, x1, y1 = [float(value) for value in frame["bbox_pt"]]
    if frame.get("rotation") in {90, 270}:
        width = y1 - y0
        height = x1 - x0
    else:
        width = x1 - x0
        height = y1 - y0
    source_size = float(frame["source_font_size_pt"])
    source_leading = float(frame["source_leading_pt"])
    source_lines = _wrap_paragraph(source_text, "SimSun", source_size, width)
    source_used_height = _used_height(source_lines, source_size, source_leading)
    scales = FONT_SCALE_STEPS if frame.get("kind", "body") in EXPANDABLE_FRAME_KINDS else tuple(scale for scale in FONT_SCALE_STEPS if scale <= 1.0)
    candidates: list[tuple[float, float, list[list[SemanticToken]], float]] = []
    for scale in scales:
        font_size = source_size * scale
        for leading_ratio in (1.25, 1.20, 1.30, 1.15, 1.35, 1.40, 1.45):
            leading = font_size * leading_ratio
            lines = _wrap_paragraph(text, "SimSun", font_size, width)
            required_height = _used_height(lines, font_size, leading)
            if required_height <= height + 0.01:
                target_ratio = required_height / source_used_height if source_used_height else 1.0
                candidates.append((scale, leading, lines, target_ratio))
    if candidates:
        scale, leading, lines, ratio = min(
            candidates,
            key=lambda item: (
                0 if 0.90 <= item[3] <= 1.05 else abs(item[3] - 0.975),
                abs(item[0] - 1.0),
            ),
        )
        return scale, leading, lines, {
            "source_used_height_pt": round(source_used_height, 3),
            "target_used_height_pt": round(_used_height(lines, source_size * scale, leading), 3),
            "target_source_height_ratio": round(ratio, 4),
            "occupancy_status": "TARGET" if 0.90 <= ratio <= 1.05 else "WARNING",
        }
    return None


def _set_background(c: Any, frame: dict[str, Any], work_dir: Path) -> None:
    x0, y0, x1, y1 = [float(value) for value in frame["bbox_pt"]]
    background = frame["background"]
    if background == "uniform-white":
        c.setFillColorRGB(1, 1, 1)
        c.setStrokeColorRGB(1, 1, 1)
        c.rect(x0, y0, x1 - x0, y1 - y0, fill=1, stroke=0)
        return
    if background == "uniform-color":
        rgb = frame.get("background_rgb")
        if (
            not isinstance(rgb, list)
            or len(rgb) != 3
            or not all(isinstance(value, (int, float)) and 0 <= float(value) <= 1 for value in rgb)
        ):
            raise ExactMirrorRenderError(
                f"Frame {frame['frame_id']} requires background_rgb values in 0..1."
            )
        c.setFillColorRGB(*(float(value) for value in rgb))
        c.setStrokeColorRGB(*(float(value) for value in rgb))
        c.rect(x0, y0, x1 - x0, y1 - y0, fill=1, stroke=0)
        return
    patch_value = frame.get("background_patch_path")
    if not isinstance(patch_value, str) or not patch_value.strip():
        raise ExactMirrorRenderError(
            f"Frame {frame['frame_id']} has a non-uniform background but no reviewed clean patch."
        )
    patch = Path(patch_value)
    if not patch.is_absolute():
        patch = work_dir / patch
    if not patch.is_file():
        raise ExactMirrorRenderError(
            f"Frame {frame['frame_id']} background patch is missing: {patch}"
        )
    c.drawImage(str(patch), x0, y0, width=x1 - x0, height=y1 - y0, mask="auto")


def _draw_line(
    c: Any,
    line: list[SemanticToken],
    x: float,
    baseline: float,
    width: float,
    font_size: float,
    frame: dict[str, Any],
    is_last: bool,
) -> None:
    measured = sum(_token_width(token, "SimSun", font_size) for token in line)
    alignment = frame["alignment"]
    if alignment == "center":
        x += max(0.0, (width - measured) / 2)
    elif alignment == "right":
        x += max(0.0, width - measured)
    cursor = x
    for token in line:
        scientific = re.fullmatch(r"(.+?10)([+−-]?\d+)", token.text) if token.kind in {"SCIENTIFIC", "STAT"} else None
        pieces = (
            [(scientific.group(1), font_size, 0.0), (scientific.group(2), font_size * 0.65, font_size * 0.32)]
            if scientific else [(token.text, font_size * 0.65 if token.kind == "CITATION" else font_size,
                                  font_size * 0.32 if token.kind == "CITATION" else 0.0)]
        )
        for piece, token_size, rise in pieces:
            text = c.beginText()
            if "italic" in str(frame.get("weight", "")):
                text.setTextTransform(1, 0, 0.18, 1, cursor, baseline)
            else:
                text.setTextOrigin(cursor, baseline)
            text.setFont("SimSun", token_size)
            # Ts persists in the PDF text state across text objects; always reset
            # it so a citation cannot lift the following prose above its frame.
            text.setRise(rise)
            if str(frame.get("weight", "")).startswith("bold"):
                text.setTextRenderMode(2)
                c.setLineWidth(max(0.2, font_size * 0.035))
            text.textOut(piece)
            c.drawText(text)
            cursor += pdfmetrics.stringWidth(piece, "SimSun", token_size)


def _draw_frame(c: Any, frame: dict[str, Any], text: str, scale: float, leading: float, lines: list[list[SemanticToken]], work_dir: Path) -> None:
    x0, y0, x1, y1 = [float(value) for value in frame["bbox_pt"]]
    rotation = int(frame.get("rotation", 0))
    c.saveState()
    clip = c.beginPath()
    clip.rect(x0, y0, x1 - x0, y1 - y0)
    c.clipPath(clip, stroke=0, fill=0)
    _set_background(c, frame, work_dir)
    if rotation == 90:
        c.translate(x1, y0)
        c.rotate(90)
        local_width, local_height = y1 - y0, x1 - x0
    elif rotation == 180:
        c.translate(x1, y1)
        c.rotate(180)
        local_width, local_height = x1 - x0, y1 - y0
    elif rotation == 270:
        c.translate(x0, y1)
        c.rotate(270)
        local_width, local_height = y1 - y0, x1 - x0
    else:
        c.translate(x0, y0)
        local_width, local_height = x1 - x0, y1 - y0
    font_size = float(frame["source_font_size_pt"]) * scale
    color = frame.get("text_rgb", [0, 0, 0])
    if not isinstance(color, list) or len(color) != 3:
        raise ExactMirrorRenderError(f"Frame {frame['frame_id']} has invalid text_rgb.")
    c.setFillColorRGB(*(float(value) for value in color))
    c.setStrokeColorRGB(*(float(value) for value in color))
    # SimSun's visual ascent is smaller than its nominal em square.  Using the
    # full em as the top offset can push the last baseline below the frame.
    baseline = local_height - font_size * 0.85
    for index, line in enumerate(lines):
        _draw_line(c, line, 0, baseline, local_width, font_size, frame, index == len(lines) - 1)
        baseline -= leading
    c.restoreState()


def _atomic_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", delete=False, dir=path.parent
    ) as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def _atomic_json(path: Path, data: dict[str, Any]) -> None:
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", delete=False, dir=path.parent
    ) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def render(work_dir: Path, output: Path) -> dict[str, Any]:
    _require_dependencies()
    work_dir = work_dir.resolve()
    inventory = validate_exact_inventory(load_json(work_dir / "source_inventory.json", "source inventory"))
    frame_rows = load_jsonl(work_dir / "text_frame_inventory.jsonl", "text frame inventory")
    frames = validate_text_frames(frame_rows, inventory)
    ledger_path = work_dir / "translation_ledger.jsonl"
    ledger_rows = load_jsonl(ledger_path, "translation ledger")
    ledger = validate_exact_ledger(ledger_rows, frames)
    font_map = validate_font_map(load_json(work_dir / "font_map.json", "font map"))
    plan_path = work_dir / "mirror_layout_plan.json"
    try:
        plan = validate_plan_data(load_json(plan_path, "mirror layout plan"))
    except MirrorPlanError as exc:
        raise ExactMirrorRenderError(str(exc)) from exc
    planned_output = Path(plan["output_pdf"]).resolve()
    if planned_output != output.resolve():
        raise ExactMirrorRenderError(f"Plan output {planned_output} does not match requested output {output.resolve()}.")

    font_path = Path(font_map["font_path"])
    if not font_path.is_file() or font_path.name.lower() != "simsun.ttc":
        raise ExactMirrorRenderError(
            f"Required SimSun file is missing or not simsun.ttc: {font_path}"
        )
    try:
        pdfmetrics.registerFont(TTFont("SimSun", str(font_path), subfontIndex=0))
    except Exception as exc:  # reportlab exposes several font-parser exception types
        raise ExactMirrorRenderError(f"Cannot register/embed SimSun: {exc}") from exc

    sources = {source["source_id"]: source for source in inventory["sources"]}
    readers = {
        source_id: PdfReader(str(_resolve_source_pdf(work_dir, source)))
        for source_id, source in sources.items()
    }
    frame_to_ledger = {
        row["frame_ids"][0]: row for row in ledger.values()
    }
    page_plan = {page["output_page_number"]: page for page in plan["pages"]}
    inventory_pages = sorted(inventory["pages"], key=lambda item: item["output_page"])
    writer = PdfWriter()
    overflows: list[str] = []
    rendered_frames: list[dict[str, Any]] = []

    for inventory_page in inventory_pages:
        output_page = inventory_page["output_page"]
        source_id = inventory_page["source_id"]
        source_page_number = inventory_page["source_page"]
        source_page = readers[source_id].pages[source_page_number - 1]
        media = inventory_page["media_box"]
        width = float(media[2]) - float(media[0])
        height = float(media[3]) - float(media[1])
        page_render_start = len(rendered_frames)
        overlay_buffer = io.BytesIO()
        overlay_canvas = canvas.Canvas(overlay_buffer, pagesize=(width, height), pageCompression=1)
        for frame_id in inventory_page["frame_ids"]:
            frame = frames[frame_id]
            if frame["translation_action"] != "TRANSLATE":
                continue
            row = frame_to_ledger[frame_id]
            row["translated_text"] = normalize_chinese_text(
                normalize_inline_citations(row["translated_text"], row["source_text"])
            )
            fitted = _layout(row["translated_text"], row["source_text"], frame)
            if fitted is None:
                row["fit_status"] = "OVERFLOW"
                overflows.append(frame_id)
                continue
            scale, leading, lines, typography = fitted
            _draw_frame(overlay_canvas, frame, row["translated_text"], scale, leading, lines, work_dir)
            row["font_scale_used"] = scale
            row["fit_status"] = "FIT"
            frame["source_cleared"] = True
            frame["target_rendered"] = True
            frame["residual_checked"] = False
            rendered_frames.append(
                {
                    "frame_id": frame_id,
                    "output_page": output_page,
                    "bbox_pt": frame["bbox_pt"],
                    "font_scale_used": scale,
                    "leading_pt": leading,
                    "line_count": len(lines),
                    **typography,
                }
            )
            for region in page_plan[output_page]["replacement_regions"]:
                if region["frame_id"] == frame_id:
                    region["font_scale_used"] = scale
                    region["fit_status"] = "FIT"
        overlay_canvas.save()
        if overflows:
            break
        writer.add_page(source_page)
        if len(rendered_frames) == page_render_start:
            # A page containing only RETAIN_SOURCE frames needs no overlay. ReportLab
            # serializes an untouched canvas as a zero-page PDF, so attempting pages[0]
            # would fail. Preserve the source page byte-for-byte at the page-content level.
            continue
        overlay_buffer.seek(0)
        overlay_reader = PdfReader(overlay_buffer)
        if len(overlay_reader.pages) != 1:
            raise ExactMirrorRenderError(
                f"Expected one overlay page for output page {output_page}; got {len(overlay_reader.pages)}."
            )
        writer.pages[-1].merge_page(overlay_reader.pages[0], over=True)

    _atomic_jsonl(ledger_path, ledger_rows)
    _atomic_jsonl(work_dir / "text_frame_inventory.jsonl", frame_rows)
    figure_path = work_dir / "figure_text_inventory.jsonl"
    if figure_path.is_file():
        figure_rows = load_jsonl(figure_path, "figure text inventory")
        for figure_row in figure_rows:
            figure_row["translated_text"] = normalize_chinese_text(
                normalize_inline_citations(
                    str(figure_row.get("translated_text", "")),
                    str(figure_row.get("source_text", "")),
                )
            )
        _atomic_jsonl(figure_path, figure_rows)
    if overflows:
        report = {
            "schema_version": 1,
            "renderer": "render_exact_mirror.py",
            "passed": False,
            "status": "PROVISIONAL",
            "overflow_frame_ids": overflows,
            "rendered_frames": rendered_frames,
        }
        _atomic_json(work_dir / "exact_mirror_render.json", report)
        raise ExactMirrorRenderError(
            "Translation does not fit at the 0.95 floor; keep A PROVISIONAL: "
            + ", ".join(overflows)
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=output.parent) as handle:
        writer.write(handle)
        temporary_output = Path(handle.name)
    temporary_output.replace(output)
    _atomic_json(plan_path, plan)
    typography_report = {
        "schema_version": 1,
        "renderer": "render_exact_mirror.py",
        "passed": all(item["occupancy_status"] in {"TARGET", "WARNING"} for item in rendered_frames),
        "target_ratio_range": [0.90, 1.05],
        "warning_below_ratio": 0.80,
        "frames": rendered_frames,
    }
    _atomic_json(work_dir / "typography_fit.json", typography_report)
    report = {
        "schema_version": 1,
        "renderer": "render_exact_mirror.py",
        "passed": True,
        "status": "IN_PROGRESS",
        "output": str(output.resolve()),
        "rendered_frames": rendered_frames,
    }
    _atomic_json(work_dir / "exact_mirror_render.json", report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = render(args.work_dir, args.output)
    except (ExactMirrorError, ExactMirrorRenderError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Rendered {len(report['rendered_frames'])} exact SimSun text frames to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
