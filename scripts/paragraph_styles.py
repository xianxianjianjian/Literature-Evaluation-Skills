#!/usr/bin/env python3
"""Shared paragraph-style rules for generated Chinese and APA-oriented content."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ParagraphStyle:
    name: str
    alignment: str
    first_line_indent_em: float = 0.0
    first_line_indent_pt: float = 0.0
    left_indent_pt: float = 0.0
    hanging_indent_pt: float = 0.0
    paragraph_spacing_before_pt: float = 0.0
    paragraph_spacing_after_pt: float = 0.0
    line_spacing: str = "consistent"

    def resolved(self, font_size_pt: float) -> dict[str, Any]:
        value = asdict(self)
        if self.first_line_indent_em:
            value["first_line_indent_pt"] = round(self.first_line_indent_em * font_size_pt, 3)
        value["font_size_pt"] = round(font_size_pt, 3)
        return value


STYLES = {
    "BODY_ZH": ParagraphStyle("BODY_ZH", "justify", first_line_indent_em=2.0),
    "BODY_EN": ParagraphStyle("BODY_EN", "left", first_line_indent_pt=36.0),
    "ABSTRACT_ZH": ParagraphStyle("ABSTRACT_ZH", "justify"),
    "ABSTRACT_EN": ParagraphStyle("ABSTRACT_EN", "left"),
    "HEADING": ParagraphStyle("HEADING", "left"),
    "CAPTION": ParagraphStyle("CAPTION", "left"),
    "REFERENCE_APA": ParagraphStyle(
        "REFERENCE_APA", "left", first_line_indent_pt=-36.0,
        left_indent_pt=36.0, hanging_indent_pt=36.0,
    ),
    "TABLE_CELL": ParagraphStyle("TABLE_CELL", "left"),
    "FOOTNOTE": ParagraphStyle("FOOTNOTE", "left"),
}


ROLE_STYLE = {
    "TITLE": "HEADING", "H1": "HEADING", "H2": "HEADING", "H3": "HEADING",
    "CAPTION": "CAPTION", "TABLE_TEXT": "TABLE_CELL", "TABLE_NOTE": "TABLE_CELL",
    "REFERENCE": "REFERENCE_APA", "FOOTNOTE": "FOOTNOTE",
    # Front matter and miscellaneous publisher furniture are not normal body
    # paragraphs, so the Chinese BODY_ZH indentation rule must not be applied.
    "AUTHOR": "CAPTION", "AFFILIATION": "CAPTION",
    "ACKNOWLEDGEMENT": "CAPTION", "OTHER": "CAPTION",
}


def style_name_for_role(role: str, language: str) -> str:
    role = role.upper()
    language = language.casefold()
    if role == "BODY":
        return "BODY_ZH" if language.startswith("zh") else "BODY_EN"
    if role == "ABSTRACT":
        return "ABSTRACT_ZH" if language.startswith("zh") else "ABSTRACT_EN"
    return ROLE_STYLE.get(role, "BODY_ZH" if language.startswith("zh") else "BODY_EN")


def paragraph_style(role: str, language: str, font_size_pt: float) -> dict[str, Any]:
    name = style_name_for_role(role, language)
    return STYLES[name].resolved(font_size_pt)


def apply_docx_paragraph_style(paragraph: Any, style_name: str, font_size_pt: float) -> None:
    """Apply one shared style to generated B/C/Structural-Mirror DOCX paragraphs."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt

    if style_name not in STYLES:
        raise ValueError(f"Unknown paragraph style: {style_name}")
    style = STYLES[style_name].resolved(font_size_pt)
    paragraph.alignment = {
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
    }[style["alignment"]]
    fmt = paragraph.paragraph_format
    fmt.left_indent = Pt(style["left_indent_pt"])
    fmt.first_line_indent = Pt(style["first_line_indent_pt"])
    fmt.space_before = Pt(style["paragraph_spacing_before_pt"])
    fmt.space_after = Pt(style["paragraph_spacing_after_pt"])


def exact_mirror_body_preference(role: str, language: str, font_size_pt: float) -> dict[str, Any] | None:
    """Return optional frame-internal formatting; geometry remains authoritative."""
    if role.upper() not in {"BODY", "ABSTRACT"} or not language.casefold().startswith("zh"):
        return None
    return paragraph_style(role, language, font_size_pt)
