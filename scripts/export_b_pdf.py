#!/usr/bin/env python3
"""Promote an independently rendered, academically validated B PDF for archive."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from pypdf import PdfReader

from validate_deep_reading_package import TOP_LEVEL_HEADINGS


def export(b_path: Path, academic_report: Path, rendered_pdf: Path, output: Path) -> dict:
    report = json.loads(academic_report.read_text(encoding="utf-8-sig"))
    if report.get("passed") is not True or Path(str(report.get("artifact", ""))).resolve() != b_path.resolve():
        raise ValueError("B academic report has not passed for this DOCX")
    required = {"B:independent-render", "B:rendered-pdf", "B:all-page-png", "B:visual-qa"}
    passed = {item.get("code") for item in report.get("checks", []) if item.get("passed") is True}
    if not required.issubset(passed):
        raise ValueError(f"B academic report lacks rendered visual gates: {sorted(required - passed)}")
    render_evidence = next(
        (str(item.get("detail") or "") for item in report.get("checks", [])
         if item.get("code") == "B:independent-render"), ""
    )
    if not render_evidence.endswith(str(rendered_pdf)):
        raise ValueError("requested B PDF is not the academic report's independent render")
    if not rendered_pdf.is_file() or rendered_pdf.stat().st_size == 0:
        raise ValueError("independent B PDF is missing or empty")
    reader = PdfReader(str(rendered_pdf))
    if not reader.pages:
        raise ValueError("B PDF has no pages")
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    missing = [heading for heading in TOP_LEVEL_HEADINGS if heading not in text]
    if missing:
        raise ValueError(f"B PDF headings not extractable: {missing}")
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(rendered_pdf, output)
    return {
        "B_PDF_EXPORT_PASS": True,
        "source_docx": str(b_path.resolve()),
        "pdf_path": str(output.resolve()),
        "pages": len(reader.pages),
        "academic_report": str(academic_report.resolve()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--b-path", type=Path, required=True)
    parser.add_argument("--academic-report", type=Path, required=True)
    parser.add_argument("--rendered-pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        payload = export(args.b_path, args.academic_report, args.rendered_pdf, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
