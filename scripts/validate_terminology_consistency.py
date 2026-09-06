#!/usr/bin/env python3
"""Validate focal-paper terminology choices across A, B and C artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None

from terminology_registry import read_evidence_events, read_registry, validate_evidence_links


class TerminologyConsistencyError(ValueError):
    pass


def artifact_text(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix == ".pdf":
        if PdfReader is None:
            raise TerminologyConsistencyError("pypdf is required to inspect A")
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    if suffix == ".docx":
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
        return "\n".join(value for value in root.itertext() if value)
    return path.read_text(encoding="utf-8-sig")


def _value(row: dict[str, str], *names: str) -> str:
    return next((row.get(name, "").strip() for name in names if row.get(name, "").strip()), "")


def read_paper_terms(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise TerminologyConsistencyError("paper terminology is empty")
    normalized: list[dict[str, str]] = []
    for line, row in enumerate(rows, 2):
        item = {
            "term_id": _value(row, "Term_ID", "term_id", "TERM ID"),
            "english": _value(row, "English_Term", "english_term", "English term"),
            "preferred": _value(row, "Preferred_Chinese", "chosen_chinese", "Chinese_Term", "中文术语"),
            "alternatives": _value(row, "Alternative_Chinese", "alternative_chinese", "备选译法"),
            "evidence_ids": _value(row, "Evidence_IDs", "evidence_id", "Evidence_ID"),
        }
        if not item["english"] or not item["preferred"] or not item["evidence_ids"]:
            raise TerminologyConsistencyError(f"paper terminology line {line} lacks English/preferred/evidence")
        normalized.append(item)
    return normalized


def validate_consistency(
    paper_terms: Path,
    registry_path: Path,
    evidence_path: Path,
    artifacts: dict[str, Path],
) -> dict[str, Any]:
    terms = read_paper_terms(paper_terms)
    registry = {row["Term_ID"]: row for row in read_registry(registry_path)}
    evidence_failures = validate_evidence_links(list(registry.values()), read_evidence_events(evidence_path))
    texts = {name: artifact_text(path) for name, path in artifacts.items()}
    failures: list[dict[str, str]] = []
    for term in terms:
        registry_row = registry.get(term["term_id"])
        if term["term_id"] and registry_row is None:
            failures.append({"term": term["english"], "artifact": "registry", "reason": "unknown TERM ID"})
        elif registry_row is not None and registry_row["Preferred_Chinese"].strip() != term["preferred"]:
            failures.append({"term": term["english"], "artifact": "registry", "reason": "preferred Chinese mismatch"})
        alternatives = [item.strip() for item in re.split(r"[;；]", term["alternatives"]) if item.strip()]
        for artifact_name, text in texts.items():
            encountered = term["english"].casefold() in text.casefold() or term["preferred"] in text or any(
                alternative in text for alternative in alternatives
            )
            if encountered and term["preferred"] not in text:
                failures.append({"term": term["english"], "artifact": artifact_name, "reason": "preferred Chinese absent where term is used"})
            for alternative in alternatives:
                if alternative != term["preferred"] and alternative in text:
                    failures.append({"term": term["english"], "artifact": artifact_name, "reason": f"non-preferred translation used: {alternative}"})
    return {
        "schema_version": 1,
        "validator": "validate_terminology_consistency.py",
        "passed": not failures and not evidence_failures,
        "artifacts": {name: str(path.resolve()) for name, path in artifacts.items()},
        "failures": failures,
        "evidence_failures": evidence_failures,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-terminology", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--a-path", type=Path, required=True)
    parser.add_argument("--b-path", type=Path, required=True)
    parser.add_argument("--c-path", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = validate_consistency(
            args.paper_terminology,
            args.registry,
            args.evidence,
            {"A": args.a_path, "B": args.b_path, "C": args.c_path},
        )
    except (OSError, csv.Error, zipfile.BadZipFile, ET.ParseError, TerminologyConsistencyError) as exc:
        payload = {"schema_version": 1, "passed": False, "error": str(exc)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("passed") else 2


if __name__ == "__main__":
    sys.exit(main())
