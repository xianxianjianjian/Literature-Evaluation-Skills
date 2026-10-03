#!/usr/bin/env python3
"""Validate paragraph role mapping, Chinese typography, and APA reference layout."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from normalize_chinese_typography import normalize_chinese_text
from paragraph_styles import paragraph_style, style_name_for_role


@dataclass(frozen=True)
class ParagraphCheck:
    code: str
    passed: bool
    detail: str


def validate_records(records: list[dict[str, Any]]) -> list[ParagraphCheck]:
    mapping: list[str] = []
    alignment: list[str] = []
    indent: list[str] = []
    references: list[str] = []
    geometry: list[str] = []
    for index, row in enumerate(records, 1):
        frame_id = str(row.get("frame_id") or f"record-{index}")
        role = str(row.get("role") or "").upper()
        language = str(row.get("language") or "zh-CN")
        font_size = float(row.get("font_size_pt") or 0)
        if not role or font_size <= 0:
            mapping.append(frame_id)
            continue
        expected = paragraph_style(role, language, font_size)
        expected_name = style_name_for_role(role, language)
        exception = row.get("layout_exception")
        has_exception = isinstance(exception, dict) and exception.get("code") == "LAYOUT_EXCEPTION" and bool(exception.get("reason"))
        if row.get("style_name") != expected_name and not has_exception:
            mapping.append(frame_id)
        if row.get("overflow") is True or row.get("clipping") is True:
            geometry.append(frame_id)
        enforce_project_style = not row.get("exact_mirror") or (
            role == "BODY" and language.casefold().startswith("zh")
        )
        if enforce_project_style and not has_exception and row.get("alignment") != expected["alignment"]:
            alignment.append(frame_id)
        actual_indent = float(row.get("first_line_indent_pt") or 0)
        if enforce_project_style and not has_exception and abs(actual_indent - float(expected["first_line_indent_pt"])) > 0.25:
            indent.append(frame_id)
        if expected_name == "REFERENCE_APA" and not (
            row.get("alignment") == "left"
            and abs(float(row.get("hanging_indent_pt") or 0) - 36.0) <= 0.25
            and abs(float(row.get("left_indent_pt") or 0) - 36.0) <= 0.25
            and abs(actual_indent + 36.0) <= 0.25
        ):
            references.append(frame_id)
    return [
        ParagraphCheck("STYLE_ROLE_MAPPING_PASS", not mapping, "roles map to shared paragraph styles" if not mapping else f"failed: {mapping}"),
        ParagraphCheck("PARAGRAPH_ALIGNMENT_PASS", not alignment and not geometry, "alignment passes without overflow/clipping" if not alignment and not geometry else f"alignment={alignment}; geometry={geometry}"),
        ParagraphCheck("FIRST_LINE_INDENT_PASS", not indent and not geometry, "role-specific indentation passes" if not indent and not geometry else f"indent={indent}; geometry={geometry}"),
        ParagraphCheck("APA_REFERENCE_FORMAT_PASS", not references, "APA references use left alignment and 0.5-inch hanging indent" if not references else f"failed: {references}"),
    ]


def validate_bilingual_texts(records: list[dict[str, Any]]) -> ParagraphCheck:
    failures: list[str] = []
    for index, row in enumerate(records, 1):
        language = str(row.get("language") or "zh-CN").casefold()
        text = str(row.get("text") or "")
        if language.startswith("zh") and normalize_chinese_text(text) != text:
            failures.append(str(row.get("frame_id") or f"record-{index}"))
    return ParagraphCheck(
        "BILINGUAL_TYPOGRAPHY_PASS", not failures,
        "Chinese punctuation/spacing is normalized; statistics and protected tokens remain atomic"
        if not failures else f"normalization required: {failures}",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.records.read_text(encoding="utf-8-sig"))
        records = payload.get("records") if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            raise ValueError("records must be a list")
        checks = validate_records(records) + [validate_bilingual_texts(records)]
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        checks = [ParagraphCheck("STYLE_ROLE_MAPPING_PASS", False, str(exc))]
    result = {"passed": all(item.passed for item in checks), "checks": [asdict(item) for item in checks]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
