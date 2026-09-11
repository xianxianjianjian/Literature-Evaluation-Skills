#!/usr/bin/env python3
"""Discover and validate a Main/SI/correction/data/code source package."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from xml.etree import ElementTree as ET
import sys
from pathlib import Path
from typing import Any

SOURCE_TYPES = {"MAIN", "SI", "CORRECTION", "DATA", "CODE", "PROTOCOL", "OTHER"}
ARCHIVE_STATUSES = {"VERIFIED", "PENDING", "NOT_AVAILABLE"}
DISCOVERY_CATEGORIES = {'MAIN', 'SCIENTIFIC_SI', 'SUPPLEMENTARY_METHODS', 'SUPPLEMENTARY_RESULTS', 'SUPPLEMENTARY_TABLES', 'SUPPLEMENTARY_FIGURES', 'REPORTING_SUMMARY', 'CORRECTION_ERRATUM', 'PROTOCOL_PREREGISTRATION', 'CODE_DATA'}


class SourcePackageError(ValueError):
    pass


def discover_si_references(text: str) -> list[str]:
    """List explicit Main→SI citations for human source resolution."""
    return sorted(set(re.sub(r'\s+', ' ', match.group()).strip() for match in re.finditer(
        r'\bSupplementary\s+(?:Table|Figure|Fig\.?)(?:s)?\s*(?:S?\d+(?:\s*[–,\-]\s*S?\d+)*)|\bSupplementary\s+(?:Methods|Results|Materials?)\b', text, re.I)))


def _main_text(path: Path) -> str:
    if path.suffix.lower() == '.xml':
        return ' '.join(ET.parse(path).getroot().itertext())
    if path.suffix.lower() == '.pdf':
        from pypdf import PdfReader
        return '\n'.join(page.extract_text() or '' for page in PdfReader(path).pages)
    return path.read_text(encoding='utf-8-sig')


def validate_source_cross_reference(data: dict[str, Any], *, base_dir: Path | None = None) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise SourcePackageError("source_cross_reference.json schema_version must be 1.")
    records = data.get("sources")
    if not isinstance(records, list) or not records:
        raise SourcePackageError("Source package requires a non-empty sources list.")
    ids: set[str] = set()
    main_count = 0
    missing_required: list[str] = []
    for index, record in enumerate(records, 1):
        if not isinstance(record, dict):
            raise SourcePackageError(f"sources[{index}] must be an object.")
        source_id = str(record.get("source_id") or "").strip()
        source_type = record.get("source_type")
        if not source_id or source_id in ids:
            raise SourcePackageError(f"sources[{index}] has missing or duplicate source_id.")
        if source_type not in SOURCE_TYPES:
            raise SourcePackageError(f"{source_id} has invalid source_type.")
        if source_type == "MAIN":
            main_count += 1
        required = record.get("required")
        available = record.get("available")
        if not isinstance(required, bool) or not isinstance(available, bool):
            raise SourcePackageError(f"{source_id} requires boolean required/available.")
        path_value = str(record.get("local_path") or "").strip()
        if available:
            if not path_value:
                raise SourcePackageError(f"Available source {source_id} requires local_path.")
            path = Path(path_value)
            if base_dir and not path.is_absolute():
                path = base_dir / path
            if base_dir is not None and not path.is_file():
                raise SourcePackageError(f"Available source file is missing: {path}")
            if base_dir is not None:
                if path.suffix.lower() == '.pdf':
                    from pypdf import PdfReader
                    try:
                        if not PdfReader(path).pages:
                            raise ValueError('no pages')
                    except Exception as exc:
                        raise SourcePackageError(f'{source_id}: invalid source PDF: {exc}') from exc
                elif path.suffix.lower() in {'.docx','.xlsx'} and not zipfile.is_zipfile(path):
                    raise SourcePackageError(f'{source_id}: invalid Office source package')
        elif required:
            missing_required.append(source_id)
        if source_type == "SI" and required and not record.get("relation_to_main"):
            raise SourcePackageError(f"Required SI {source_id} requires relation_to_main.")
        ids.add(source_id)
    if main_count != 1:
        raise SourcePackageError("Source package requires exactly one MAIN source.")
    if base_dir is not None:
        discovery = data.get('discovery', {})
        missing = DISCOVERY_CATEGORIES - set(discovery)
        if missing or any(not isinstance(row, dict) or row.get('status') not in {'FOUND','NOT_FOUND','NOT_APPLICABLE'} or not row.get('evidence') for row in discovery.values()):
            raise SourcePackageError(f'Source discovery categories/evidence incomplete: {sorted(missing)}')
        main = next(row for row in records if row['source_type']=='MAIN')
        main_path = Path(main['local_path'])
        text_path = Path(data.get('main_reference_text_path') or main_path)
        if not text_path.is_absolute(): text_path=base_dir/text_path
        cited = {re.sub(r'\s+',' ', value).casefold() for value in discover_si_references(_main_text(text_path))}
        references = {re.sub(r'\s+',' ', row['reference']).casefold():row for row in data.get('references', [])}
        for citation in cited:
            resolved = references.get(citation)
            if not resolved or resolved.get('status')!='RESOLVED' or resolved.get('source_id') not in ids or not any(row['source_id']==resolved['source_id'] and row['available'] for row in records):
                missing_required.append(citation)
    archive = data.get("source_archive")
    if not isinstance(archive, dict) or archive.get("status") not in ARCHIVE_STATUSES:
        raise SourcePackageError("source_archive.status must be VERIFIED, PENDING, or NOT_AVAILABLE.")
    if archive["status"] == "VERIFIED":
        archived_ids = archive.get("archived_source_ids")
        if not isinstance(archived_ids, list) or not set(
            record["source_id"] for record in records if record["required"] and record["available"]
        ).issubset(set(archived_ids)):
            raise SourcePackageError("Verified Source Archive does not cover all required available sources.")
    status = "READY" if not missing_required else "READY_WITH_GAPS"
    if missing_required and data.get("missing_required_policy") == "BLOCK":
        status = "BLOCKED"
    return {
        "schema_version": 1,
        "passed": status == "READY" and archive["status"] in {"VERIFIED", "PENDING"},
        "status": status,
        "source_archive_status": archive["status"],
        "required_source_ids": [record["source_id"] for record in records if record["required"]],
        "missing_required_source_ids": missing_required,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cross-reference", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = json.loads(args.cross_reference.read_text(encoding="utf-8-sig"))
        report = validate_source_cross_reference(data, base_dir=args.cross_reference.parent)
        if args.report:
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, SourcePackageError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
