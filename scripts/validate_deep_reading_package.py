#!/usr/bin/env python3
"""Independently validate the B deep-reading DOCX and its rendered visual evidence."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - explicit dependency result
    PdfReader = None

from sanitize_docx_metadata import validate_docx_metadata


class DeepReadingValidationError(ValueError):
    """Raised when B evidence cannot be parsed."""


@dataclass(frozen=True)
class DeepReadingCheck:
    code: str
    passed: bool
    detail: str


TOP_LEVEL_HEADINGS = (
    "0 文献定位与研究审计",
    "1 Abstract 精读",
    "2 Introduction：理论框架与研究问题",
    "3 Methods",
    "4 Results",
    "5 Discussion",
    "6 Innovation",
    "7 Limitations",
    "8 Redesign",
    "9 Research Transfer",
    "10 Terminology & Evidence Index",
)
METHOD_MARKERS = (
    "研究架构",
    "样本台账",
    "时间线",
    "参与者视角",
    "研究者视角",
    "测量链",
    "采集",
    "预处理",
    "统计分析",
    "适用方法规范",
    "可复现性缺口",
)
RESULT_MARKERS = ("分析路线图", "结果矩阵", "假设—结果", "零结果", "内部一致性")
DISCUSSION_MARKERS = ("原文直接内容", "作者解释", "评译者分析", "外部依据")
VISUAL_FLAGS = (
    "blank",
    "overflow",
    "table_clipping",
    "orphan_heading",
    "missing_glyph",
)


def _docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    return "\n".join(value.strip() for value in root.itertext() if value and value.strip())


def _check_heading_schema(text: str) -> list[DeepReadingCheck]:
    positions: list[int] = []
    missing: list[str] = []
    for heading in TOP_LEVEL_HEADINGS:
        position = text.find(heading)
        if position < 0:
            missing.append(heading)
        positions.append(position)
    ordered = not missing and positions == sorted(positions)
    return [
        DeepReadingCheck(
            "B:heading-schema",
            not missing and ordered,
            "required 0-10 headings present in order"
            if not missing and ordered
            else f"missing={missing}; ordered={ordered}",
        ),
        DeepReadingCheck(
            "B:methods-schema",
            all(marker in text for marker in METHOD_MARKERS),
            "Methods dynamic subsections present"
            if all(marker in text for marker in METHOD_MARKERS)
            else f"missing={[marker for marker in METHOD_MARKERS if marker not in text]}",
        ),
        DeepReadingCheck(
            "B:results-schema",
            all(marker in text for marker in RESULT_MARKERS),
            "Results audit subsections present"
            if all(marker in text for marker in RESULT_MARKERS)
            else f"missing={[marker for marker in RESULT_MARKERS if marker not in text]}",
        ),
        DeepReadingCheck(
            "B:discussion-provenance",
            all(marker in text for marker in DISCUSSION_MARKERS),
            "Discussion separates data, author, evaluator and external evidence"
            if all(marker in text for marker in DISCUSSION_MARKERS)
            else f"missing={[marker for marker in DISCUSSION_MARKERS if marker not in text]}",
        ),
    ]


def _relationship_checks(path: Path) -> list[str]:
    failures: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        for name in sorted(item for item in names if item.endswith(".rels")):
            try:
                root = ET.fromstring(archive.read(name))
            except ET.ParseError as exc:
                failures.append(f"{name}: invalid XML ({exc})")
                continue
            base = Path(name).parent.parent if Path(name).parent.name == "_rels" else Path(name).parent
            for relation in root:
                target = relation.attrib.get("Target", "")
                if relation.attrib.get("TargetMode") == "External" or not target:
                    continue
                resolved = (base / target).as_posix()
                normalized: list[str] = []
                for part in resolved.split("/"):
                    if part == "..":
                        if normalized:
                            normalized.pop()
                    elif part not in ("", "."):
                        normalized.append(part)
                candidate = "/".join(normalized)
                if candidate not in names:
                    failures.append(f"{name}: dangling relationship {target}")

        for name in sorted(item for item in names if item.endswith(".xml")):
            raw = archive.read(name).decode("utf-8", errors="replace")
            root_tag = raw.split(">", 1)[0]
            match = re.search(r"mc:Ignorable\s*=\s*['\"]([^'\"]+)['\"]", root_tag)
            if match:
                for prefix in match.group(1).split():
                    if not re.search(rf"xmlns:{re.escape(prefix)}\s*=", root_tag):
                        failures.append(f"{name}: mc:Ignorable prefix {prefix} is undeclared")
        if any(name.startswith("word/comments") for name in names):
            failures.append("Word comments remain in package")
    return failures


def _python_docx_readable(path: Path) -> tuple[bool, str]:
    try:
        from docx import Document
    except ImportError:
        return False, "python-docx is unavailable"
    try:
        document = Document(str(path))
        _ = len(document.paragraphs)
    except Exception as exc:  # python-docx exposes multiple parser exceptions
        return False, f"python-docx cannot read B: {exc}"
    return True, "python-docx opened B"


def _find_soffice(explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit if explicit.is_file() else None
    located = shutil.which("soffice") or shutil.which("libreoffice")
    if located:
        return Path(located)
    candidates = (
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
    )
    return next((path for path in candidates if path.is_file()), None)


def render_docx(path: Path, output_dir: Path, soffice: Path | None) -> Path:
    executable = _find_soffice(soffice)
    if executable is None:
        raise DeepReadingValidationError("LibreOffice/compatible independent renderer is unavailable")
    output_dir.mkdir(parents=True, exist_ok=True)
    process = subprocess.run(
        [str(executable), "--headless", "--convert-to", "pdf", "--outdir", str(output_dir), str(path)],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    rendered = output_dir / f"{path.stem}.pdf"
    if process.returncode != 0 or not rendered.is_file():
        detail = (process.stderr or process.stdout or "no renderer output").strip()
        raise DeepReadingValidationError(f"independent DOCX render failed: {detail}")
    return rendered


def _validate_visual_qa(
    qa_path: Path, rendered_pdf: Path, png_dir: Path
) -> list[DeepReadingCheck]:
    if not qa_path.is_file():
        return [DeepReadingCheck("B:visual-qa", False, f"visual QA missing: {qa_path}")]
    try:
        data = json.loads(qa_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return [DeepReadingCheck("B:visual-qa", False, f"invalid visual QA: {exc}")]
    pages = data.get("pages") if isinstance(data, dict) else None
    if PdfReader is None:
        return [DeepReadingCheck("B:rendered-pdf", False, "pypdf is unavailable")]
    try:
        page_count = len(PdfReader(str(rendered_pdf)).pages)
    except Exception as exc:
        return [DeepReadingCheck("B:rendered-pdf", False, f"cannot read rendered PDF: {exc}")]
    pngs = sorted(png_dir.glob("*.png")) if png_dir.is_dir() else []
    invalid: list[int | str] = []
    renderer = str(data.get("renderer") or "") if isinstance(data, dict) else ""
    if not re.search(r"libreoffice|microsoft\s+word|onlyoffice|openoffice", renderer, re.IGNORECASE):
        invalid.append("renderer-provenance")
    if not isinstance(pages, list) or len(pages) != page_count or len(pngs) != page_count:
        invalid.append("page-count")
    else:
        for expected, row in enumerate(pages, 1):
            if (
                not isinstance(row, dict)
                or row.get("page") != expected
                or row.get("reviewed") is not True
                or any(row.get(flag) is not False for flag in VISUAL_FLAGS)
            ):
                invalid.append(expected)
    if isinstance(data, dict) and data.get("wrong_page_count") is not False:
        invalid.append("wrong-page-count")
    return [
        DeepReadingCheck(
            "B:rendered-pdf",
            rendered_pdf.is_file() and page_count > 0,
            f"independent render has {page_count} page(s)",
        ),
        DeepReadingCheck(
            "B:all-page-png",
            len(pngs) == page_count,
            f"{len(pngs)}/{page_count} rendered page PNG(s)",
        ),
        DeepReadingCheck(
            "B:visual-qa",
            not invalid,
            "all pages reviewed: no blank/overflow/table clipping/orphan heading/missing glyph/page-count issue"
            if not invalid
            else f"invalid visual QA pages/flags: {invalid}",
        ),
    ]


def validate_package(
    b_path: Path,
    work_dir: Path,
    *,
    expected_author: str | None = None,
    soffice: Path | None = None,
    rendered_pdf: Path | None = None,
    png_dir: Path | None = None,
    visual_qa: Path | None = None,
) -> list[DeepReadingCheck]:
    checks: list[DeepReadingCheck] = []
    if not b_path.is_file() or b_path.suffix.casefold() != ".docx":
        return [DeepReadingCheck("B:artifact", False, f"missing or invalid DOCX: {b_path}")]
    try:
        text = _docx_text(b_path)
        checks.append(DeepReadingCheck("B:ooxml", True, "DOCX package XML readable"))
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        return [DeepReadingCheck("B:ooxml", False, f"invalid DOCX package: {exc}")]
    checks.extend(_check_heading_schema(text))

    metadata_failures = validate_docx_metadata(b_path, expected_author=expected_author)
    checks.append(
        DeepReadingCheck(
            "B:metadata",
            not metadata_failures,
            "metadata and comments sanitized"
            if not metadata_failures
            else "; ".join(metadata_failures),
        )
    )
    relationship_failures = _relationship_checks(b_path)
    checks.append(
        DeepReadingCheck(
            "B:ooxml-relationships",
            not relationship_failures,
            "namespaces and relationships valid"
            if not relationship_failures
            else "; ".join(relationship_failures),
        )
    )
    readable, detail = _python_docx_readable(b_path)
    checks.append(DeepReadingCheck("B:python-docx", readable, detail))

    evidence_map = work_dir / "claim_evidence_map.csv"
    audit_log = work_dir / "audit_log.jsonl"
    checks.append(DeepReadingCheck("B:evidence-map", evidence_map.is_file(), str(evidence_map)))
    checks.append(DeepReadingCheck("B:main-si-audit", audit_log.is_file(), str(audit_log)))

    render_dir = work_dir / "deep_reading_render"
    try:
        active_pdf = rendered_pdf or render_docx(b_path, render_dir, soffice)
    except (DeepReadingValidationError, OSError, subprocess.SubprocessError) as exc:
        checks.append(DeepReadingCheck("B:independent-render", False, str(exc)))
        return checks
    checks.append(DeepReadingCheck("B:independent-render", True, f"rendered by independent office engine: {active_pdf}"))
    checks.extend(
        _validate_visual_qa(
            visual_qa or work_dir / "b_visual_qa.json",
            active_pdf,
            png_dir or work_dir / "deep_reading_render" / "pages",
        )
    )
    return checks


def write_report(path: Path, checks: list[DeepReadingCheck], b_path: Path) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "validator": "validate_deep_reading_package.py",
        "artifact": str(b_path.resolve()),
        "passed": all(check.passed for check in checks),
        "checks": [asdict(check) for check in checks],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--b-path", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-author")
    parser.add_argument("--soffice", type=Path)
    parser.add_argument("--rendered-pdf", type=Path)
    parser.add_argument("--png-dir", type=Path)
    parser.add_argument("--visual-qa", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    checks = validate_package(
        args.b_path,
        args.work_dir,
        expected_author=args.expected_author,
        soffice=args.soffice,
        rendered_pdf=args.rendered_pdf,
        png_dir=args.png_dir,
        visual_qa=args.visual_qa,
    )
    payload = write_report(args.report, checks, args.b_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
