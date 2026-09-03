#!/usr/bin/env python3
"""Harden the v1.3 exact renderer by clipping every replacement to its source frame."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import render_exact_mirror as core


def _clip_to_frame(c: Any, frame: dict[str, Any]) -> None:
    """Install a vector clip equal to the immutable reviewed source bbox."""
    x0, y0, x1, y1 = [float(value) for value in frame["bbox_pt"]]
    path = c.beginPath()
    path.rect(x0, y0, x1 - x0, y1 - y0)
    c.clipPath(path, stroke=0, fill=0)


def _draw_frame(
    c: Any,
    frame: dict[str, Any],
    text: str,
    scale: float,
    lines: list[str],
    work_dir: Path,
) -> None:
    """Draw one replacement under an exact bbox clip.

    The clip is applied before background cleanup and before synthetic bold/
    italic text. This prevents glyph outlines, shearing and raster antialiasing
    from altering pixels outside the reviewed replacement region.
    """
    x0, y0, x1, y1 = [float(value) for value in frame["bbox_pt"]]
    rotation = int(frame.get("rotation", 0))

    c.saveState()
    _clip_to_frame(c, frame)
    core._set_background(c, frame, work_dir)

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
    leading = float(frame["source_leading_pt"])
    color = frame.get("text_rgb", [0, 0, 0])
    if not isinstance(color, list) or len(color) != 3:
        raise core.ExactMirrorRenderError(
            f"Frame {frame['frame_id']} has invalid text_rgb."
        )
    c.setFillColorRGB(*(float(value) for value in color))
    c.setStrokeColorRGB(*(float(value) for value in color))
    baseline = local_height - font_size
    for index, line in enumerate(lines):
        core._draw_line(
            c,
            line,
            0,
            baseline,
            local_width,
            font_size,
            frame,
            index == len(lines) - 1,
        )
        baseline -= leading
    c.restoreState()


# render() resolves this global at runtime, so patching the implementation keeps
# all source-path, retain-only-page, fitting and reporting behavior unchanged.
core._draw_frame = _draw_frame


def main(argv: list[str] | None = None) -> int:
    return core.main(argv)


if __name__ == "__main__":
    sys.exit(main())
