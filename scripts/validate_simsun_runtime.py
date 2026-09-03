#!/usr/bin/env python3
"""Validate a real Windows SimSun TTC for production exact-mirror rendering."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from fontTools.ttLib import TTCollection
from pypdf import PdfReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

REQUIRED_TEXT = "中文正文 睡眠记忆 情绪 表格图，。；：（）"


def _font_names(font: Any) -> set[str]:
    names: set[str] = set()
    for record in font["name"].names:
        if record.nameID not in {1, 4, 6}:
            continue
        try:
            value = record.toUnicode().strip()
        except Exception:
            continue
        if value:
            names.add(value)
    return names


def _font_descriptor(font_object: Any) -> Any | None:
    font_object = font_object.get_object()
    descriptor = font_object.get("/FontDescriptor")
    if descriptor is not None:
        return descriptor.get_object()
    descendants = font_object.get("/DescendantFonts")
    if descendants:
        descendant = descendants[0].get_object()
        descriptor = descendant.get("/FontDescriptor")
        if descriptor is not None:
            return descriptor.get_object()
    return None


def validate(font_path: Path) -> dict[str, Any]:
    if not font_path.is_file():
        raise RuntimeError(f"Required production SimSun is missing: {font_path}")
    if font_path.name.lower() != "simsun.ttc":
        raise RuntimeError(f"Production font must be simsun.ttc, got: {font_path.name}")

    collection = TTCollection(str(font_path), lazy=False)
    if not collection.fonts:
        raise RuntimeError("simsun.ttc has no font faces")
    face = collection.fonts[0]
    names = _font_names(face)
    if not any("simsun" in name.lower() or "宋体" in name for name in names):
        raise RuntimeError(f"TTC face 0 is not identifiable as SimSun/宋体: {sorted(names)}")
    cmap = face.getBestCmap() or {}
    missing = sorted({char for char in REQUIRED_TEXT if not char.isspace() and ord(char) not in cmap})
    if missing:
        raise RuntimeError(f"SimSun face 0 lacks required glyphs: {missing}")

    with tempfile.TemporaryDirectory() as temporary:
        output = Path(temporary) / "simsun-production-gate.pdf"
        pdfmetrics.registerFont(TTFont("SimSun", str(font_path), subfontIndex=0))
        c = canvas.Canvas(str(output), pagesize=(360, 180), pageCompression=1)
        c.setFont("SimSun", 12)
        c.drawString(24, 135, REQUIRED_TEXT)

        bold = c.beginText()
        bold.setTextOrigin(24, 100)
        bold.setFont("SimSun", 12)
        bold.setTextRenderMode(2)
        c.setLineWidth(0.42)
        bold.textOut("中文粗体")
        c.drawText(bold)

        italic = c.beginText()
        italic.setTextTransform(1, 0, 0.18, 1, 24, 65)
        italic.setFont("SimSun", 12)
        italic.textOut("中文斜体")
        c.drawText(italic)
        c.showPage()
        c.save()

        reader = PdfReader(str(output))
        if len(reader.pages) != 1:
            raise RuntimeError("SimSun production gate output has an unexpected page count")
        resources = reader.pages[0]["/Resources"].get_object()
        fonts = resources.get("/Font")
        if fonts is None:
            raise RuntimeError("Rendered PDF has no font resources")
        fonts = fonts.get_object()

        embedded = False
        base_fonts: list[str] = []
        for reference in fonts.values():
            font_object = reference.get_object()
            base_fonts.append(str(font_object.get("/BaseFont", "")))
            descriptor = _font_descriptor(font_object)
            if descriptor is not None and any(
                descriptor.get(key) is not None for key in ("/FontFile", "/FontFile2", "/FontFile3")
            ):
                embedded = True
        if not embedded:
            raise RuntimeError(f"SimSun is not embedded in the generated PDF; BaseFont={base_fonts}")

        extracted = reader.pages[0].extract_text() or ""
        for token in ("中文正文", "睡眠记忆", "情绪", "表格图"):
            if token not in extracted:
                raise RuntimeError(f"Embedded SimSun text cannot be round-tripped: missing {token!r}")

    return {
        "passed": True,
        "font_path": str(font_path),
        "face_index": 0,
        "font_names": sorted(names),
        "required_glyphs": REQUIRED_TEXT,
        "embedded": True,
        "synthetic_bold": "PASS",
        "synthetic_italic": "PASS",
    }


def main() -> int:
    font_path = Path(os.environ.get("SIMSUN_PATH", r"C:\Windows\Fonts\simsun.ttc"))
    try:
        report = validate(font_path)
    except Exception as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=True, indent=2))
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
