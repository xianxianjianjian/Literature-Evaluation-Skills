#!/usr/bin/env python3
"""Independent content-integrity gates for translation packages.

The exact renderer never imports this module.  It is intentionally validator-side
so generator assertions cannot certify their own output.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable


class TranslationIntegrityError(ValueError):
    """Raised when integrity evidence is missing or malformed."""


@dataclass(frozen=True)
class IntegrityResult:
    code: str
    passed: bool
    detail: str


FIGURE_TEXT_FILE = "figure_text_inventory.jsonl"
SOURCE_CONFLICT_FILE = "source_conflicts.jsonl"
NUMERIC_REPORT_FILE = "numeric_integrity.json"
NUMERIC_WHITELIST_FILE = "numeric_integrity_whitelist.jsonl"
PAPER_TERMINOLOGY_FILE = "paper_terminology.csv"

_SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-")
_NUMBER = r"[+\-−–]?(?:\d+(?:[.,]\d+)?|[.,]\d+)"
_SCI = re.compile(
    rf"(?<![A-Za-z0-9_.])({_NUMBER}\s*(?:×|x|X|\*)\s*10\s*(?:\^|\*\*)?\s*[+\-−–⁺⁻]?\s*[0-9⁰¹²³⁴⁵⁶⁷⁸⁹]+)",
    re.IGNORECASE,
)
_STAT = re.compile(
    rf"(?<![A-Za-z0-9_])(p|t|f|z|χ\s*[²2]|chi\s*[- ]?square|β|beta|r\s*[s²2]?|r\s*\^\s*2|df|ci|icc|or|hr)\s*(?:\([^)]*\))?\s*(=|<|>|≤|≥|~=|≈)?\s*({_NUMBER})",
    re.IGNORECASE,
)
_STAT_SCI = re.compile(
    rf"(?<![A-Za-z0-9_])(p|t|f|z|χ\s*[²2]|chi\s*[- ]?square|β|beta|r\s*[s²2]?|r\s*\^\s*2|df|ci|icc|or|hr)\s*(=|<|>|≤|≥|~=|≈)?\s*({_NUMBER}\s*(?:×|x|X|\*)\s*10\s*(?:\^|\*\*)?\s*[+\-−–⁺⁻]?\s*[0-9⁰¹²³⁴⁵⁶⁷⁸⁹]+)",
    re.IGNORECASE,
)
_UNIT = re.compile(
    rf"(?<![A-Za-z0-9_])({_NUMBER})\s*(%|hz|khz|mhz|ms|s|sec|secs|second|seconds|min|mins|minute|minutes|h|hr|hrs|hour|hours|day|days|night|nights|db|mv|μv|uv|mm|cm|m|kg|g)(?![A-Za-z])",
    re.IGNORECASE,
)
_DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:a-z0-9]+", re.IGNORECASE)
_VERSION = re.compile(r"\bv(?:ersion\s*)?\d+(?:\.\d+){1,4}\b", re.IGNORECASE)
_TIMEPOINT = re.compile(r"(?<![A-Za-z0-9_])T\d+(?![A-Za-z0-9_])", re.IGNORECASE)
_BRACKET_CITATION = re.compile(r"\[\s*\d+(?:\s*[,;–—-]\s*\d+)*\s*\]")
_SUPERSCRIPT_CITATION = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+(?:[˒,，–—-][⁰¹²³⁴⁵⁶⁷⁸⁹]+)*")
_PLAIN = re.compile(rf"(?<![A-Za-z0-9_.–—-]){_NUMBER}(?![A-Za-z0-9_.])")


def _canon(value: str) -> str:
    value = value.translate(_SUPERSCRIPT)
    value = re.sub(
        r"((?:×|x|X|\*)\s*10)\s*(?!\^)([+\-−–]?\s*\d+)",
        r"\1^\2",
        value,
    )
    value = value.replace("−", "-").replace("–", "-")
    value = value.replace("×", "x").replace("*", "x")
    value = value.replace("χ²", "chi2").replace("χ2", "chi2")
    value = value.replace("β", "beta").replace("²", "2")
    value = re.sub(r"\br\s*\^\s*2\b", "r2", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", "", value.casefold())
    value = value.replace(",", "")
    return value


def extract_numeric_tokens(text: str) -> list[str]:
    """Extract normalized numeric/statistical tokens without losing signs or exponents."""
    if not isinstance(text, str):
        return []
    spans: list[tuple[int, int]] = []
    tokens: list[str] = []
    for pattern in (_DOI, _STAT_SCI, _SCI, _STAT, _UNIT, _VERSION, _TIMEPOINT):
        for match in pattern.finditer(text):
            if any(match.start() < end and match.end() > start for start, end in spans):
                continue
            tokens.append(_canon(match.group(0)))
            spans.append(match.span())
    masked = list(text)
    for start, end in spans:
        masked[start:end] = " " * (end - start)
    remaining = "".join(masked)
    for pattern in (_BRACKET_CITATION, _SUPERSCRIPT_CITATION):
        for match in pattern.finditer(remaining):
            masked[match.start():match.end()] = " " * (match.end() - match.start())
    tokens.extend(_canon(match.group(0)) for match in _PLAIN.finditer("".join(masked)))
    return tokens


def _read_jsonl(path: Path, *, required: bool) -> list[dict[str, Any]]:
    if not path.is_file():
        if required:
            raise TranslationIntegrityError(f"required evidence file missing: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TranslationIntegrityError(f"{path.name}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise TranslationIntegrityError(f"{path.name}:{line_number}: row must be an object")
        rows.append(value)
    return rows


def validate_numeric_integrity(
    work_dir: Path, ledger: dict[str, dict[str, Any]]
) -> tuple[IntegrityResult, dict[str, Any]]:
    whitelist_rows = _read_jsonl(work_dir / NUMERIC_WHITELIST_FILE, required=False)
    whitelist: set[tuple[str, str, str]] = set()
    invalid_whitelist: list[str] = []
    for index, row in enumerate(whitelist_rows, 1):
        fields = ("unit_id", "source_token", "translated_token", "reason", "reviewer", "reviewed_date")
        if not all(isinstance(row.get(field), str) and row[field].strip() for field in fields):
            invalid_whitelist.append(f"line-{index}")
            continue
        try:
            date.fromisoformat(row["reviewed_date"])
        except ValueError:
            invalid_whitelist.append(f"line-{index}")
            continue
        whitelist.add(
            (row["unit_id"].strip(), _canon(row["source_token"]), _canon(row["translated_token"]))
        )

    discrepancies: list[dict[str, Any]] = []
    unit_reports: list[dict[str, Any]] = []
    for unit_id, row in sorted(ledger.items()):
        source = Counter(extract_numeric_tokens(str(row.get("source_text", ""))))
        translated = Counter(extract_numeric_tokens(str(row.get("translated_text", ""))))
        missing = list((source - translated).elements())
        added = list((translated - source).elements())
        unmatched_missing = list(missing)
        unmatched_added = list(added)
        for source_token in missing[:]:
            for translated_token in added[:]:
                key = (unit_id, source_token, translated_token)
                if key in whitelist:
                    unmatched_missing.remove(source_token)
                    unmatched_added.remove(translated_token)
                    added.remove(translated_token)
                    break
        for token in unmatched_missing:
            discrepancies.append({"unit_id": unit_id, "kind": "MISSING", "token": token})
        for token in unmatched_added:
            discrepancies.append({"unit_id": unit_id, "kind": "ADDED", "token": token})
        unit_reports.append(
            {
                "unit_id": unit_id,
                "source_tokens": list(source.elements()),
                "translated_tokens": list(translated.elements()),
                "discrepancies": [item for item in discrepancies if item["unit_id"] == unit_id],
            }
        )
    report = {
        "schema_version": 1,
        "validator": "translation_integrity.py",
        "passed": not discrepancies and not invalid_whitelist,
        "whitelist_count": len(whitelist),
        "invalid_whitelist_rows": invalid_whitelist,
        "discrepancies": discrepancies,
        "units": unit_reports,
    }
    detail = (
        f"{len(ledger)} units preserve numeric/statistical tokens"
        if report["passed"]
        else f"{len(discrepancies)} unapproved discrepancy(s); invalid whitelist={invalid_whitelist}"
    )
    return IntegrityResult("numeric:integrity", report["passed"], detail), report


def validate_figure_text_inventory(
    work_dir: Path,
    inventory: dict[str, Any],
    frames: dict[str, dict[str, Any]],
    ledger: dict[str, dict[str, Any]],
) -> IntegrityResult:
    rows = _read_jsonl(work_dir / FIGURE_TEXT_FILE, required=True)
    expected: dict[str, str] = {}
    for obj in inventory.get("objects", []):
        if obj.get("kind") != "figure":
            continue
        for frame_id in obj.get("label_frame_ids", []):
            expected[str(frame_id)] = str(obj.get("object_id", ""))
    found: dict[str, dict[str, Any]] = {}
    invalid: list[str] = []
    for index, row in enumerate(rows, 1):
        frame_id = str(row.get("frame_id", "")).strip()
        label = frame_id or f"line-{index}"
        if not frame_id or frame_id in found:
            invalid.append(label)
            continue
        required_text = ("figure_id", "source_id", "source_text", "translated_text")
        bbox = row.get("bbox_pt")
        if (
            any(not isinstance(row.get(field), str) or not row[field].strip() for field in required_text)
            or not isinstance(row.get("source_page"), int)
            or not isinstance(bbox, list)
            or len(bbox) != 4
            or any(not isinstance(value, (int, float)) for value in bbox)
            or any(row.get(flag) is not True for flag in ("reviewed", "rendered", "validated"))
        ):
            invalid.append(label)
            continue
        frame = frames.get(frame_id)
        if (
            frame is None
            or frame.get("kind") != "figure_label"
            or expected.get(frame_id) != row.get("figure_id")
            or list(frame.get("bbox_pt", [])) != bbox
        ):
            invalid.append(label)
            continue
        unit_id = str(frame.get("unit_id", ""))
        ledger_row = ledger.get(unit_id)
        if ledger_row is None or ledger_row.get("translated_text") != row.get("translated_text"):
            invalid.append(label)
            continue
        found[frame_id] = row
    missing = sorted(set(expected) - set(found))
    extra = sorted(set(found) - set(expected))
    passed = not invalid and not missing and not extra
    detail = (
        f"{len(found)} figure label(s) reviewed, rendered and validated"
        if passed
        else f"invalid={sorted(set(invalid))}; missing={missing}; extra={extra}"
    )
    return IntegrityResult("figure:text-inventory", passed, detail)


def validate_source_conflicts(work_dir: Path, ledger: dict[str, dict[str, Any]]) -> IntegrityResult:
    rows = _read_jsonl(work_dir / SOURCE_CONFLICT_FILE, required=True)
    invalid: list[str] = []
    for index, row in enumerate(rows, 1):
        conflict_id = str(row.get("conflict_id", "")).strip() or f"line-{index}"
        source_values = row.get("source_values")
        unit_ids = row.get("unit_ids")
        audit_ids = row.get("audit_ids")
        if (
            not re.fullmatch(r"CONFLICT-\d{3,}", conflict_id)
            or not isinstance(source_values, list)
            or len(source_values) < 2
            or len({_canon(str(value)) for value in source_values}) < 2
            or not isinstance(unit_ids, list)
            or len(unit_ids) < 2
            or any(str(unit_id) not in ledger for unit_id in unit_ids)
            or not isinstance(audit_ids, list)
            or not audit_ids
            or any(not re.fullmatch(r"AUD-\d{3,}", str(item)) for item in audit_ids)
            or row.get("preserved_separately") is not True
        ):
            invalid.append(conflict_id)
            continue
        translated_values = [str(ledger[str(unit_id)].get("translated_text", "")) for unit_id in unit_ids]
        if len({_canon(value) for value in translated_values}) < 2:
            invalid.append(conflict_id)
    return IntegrityResult(
        "source:main-si-conflicts",
        not invalid,
        f"{len(rows)} conflict record(s) preserve source-specific values"
        if not invalid
        else f"conflicts normalized or malformed: {sorted(set(invalid))}",
    )


def read_paper_terminology(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise TranslationIntegrityError(f"paper terminology missing: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if not rows:
        raise TranslationIntegrityError("paper terminology must contain at least one term")
    aliases = {
        "english": ("English_Term", "english_term", "English term"),
        "chinese": ("Preferred_Chinese", "chosen_chinese", "Chinese_Term", "中文术语"),
        "confidence": ("Confidence", "confidence"),
        "evidence": ("Evidence_IDs", "evidence_id", "Evidence_ID"),
    }
    for index, row in enumerate(rows, 2):
        for label, candidates in aliases.items():
            if not any(str(row.get(field, "")).strip() for field in candidates):
                raise TranslationIntegrityError(f"paper terminology line {index} missing {label}")
    return rows


def validate_paper_terminology(work_dir: Path) -> IntegrityResult:
    try:
        rows = read_paper_terminology(work_dir / PAPER_TERMINOLOGY_FILE)
    except (TranslationIntegrityError, OSError, csv.Error) as exc:
        return IntegrityResult("terminology:paper-sheet", False, str(exc))
    return IntegrityResult("terminology:paper-sheet", True, f"{len(rows)} evidence-linked paper term(s)")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
