#!/usr/bin/env python3
"""Append and query selection and completed-reading CSV records safely.

Selection history is week-scoped. Completed-reading history is global by stable
paper identity and may only be appended after a workflow manifest verifies that
Deep Reading genuinely reached academic COMPLETE. Zotero archive keys are
optional metadata and may be reconciled later.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Iterable

from workflow_state import WorkflowStateError, load_manifest

SELECTION_FIELDS = [
    "Week", "Topic", "Paper_ID", "Title", "DOI", "Journal", "Year", "Role",
    "Quality_Gate", "Weighted_Score", "Selection_Decision", "Selection_Reason",
    "Zotero_Item_Key", "Logged_Date",
]
READING_FIELDS = [
    "Week", "Topic", "Paper_ID", "Title", "DOI", "Journal", "Year", "Study_Type",
    "Core_Finding", "Method_Value", "Transfer_Value", "Major_Limitation",
    "Open_Questions", "Next_Reading_Direction", "Zotero_Item_Key",
    "A_Attachment_Key", "B_Attachment_Key", "Git_Review_Path", "Completed_Date",
]
WEEK_PATTERN = re.compile(r"^\d{4}-W(?:0[1-9]|[1-4]\d|5[0-3])$")


class HistoryError(ValueError):
    """Raised when a history file or requested record is invalid."""


def validate_iso_date(value: str, field: str) -> None:
    """Require a calendar date in ISO 8601 YYYY-MM-DD form."""
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise HistoryError(f"{field} must be an ISO 8601 date (YYYY-MM-DD).") from exc
    if parsed.isoformat() != value:
        raise HistoryError(f"{field} must use canonical YYYY-MM-DD form.")


def normalize_doi(value: str) -> str:
    """Normalize a DOI for comparison without changing the stored value."""
    normalized = value.strip().lower()
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", normalized)


def read_rows(path: Path, expected_fields: list[str]) -> list[dict[str, str]]:
    """Read a CSV and verify its exact V1 header."""
    if not path.is_file():
        raise HistoryError(f"CSV file does not exist: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected_fields:
            raise HistoryError(
                f"Unexpected header in {path}. Expected: {','.join(expected_fields)}"
            )
        return list(reader)


def same_identity(left: dict[str, str], right: dict[str, str]) -> bool:
    """Match the same paper by Paper_ID or normalized DOI when either is available."""
    left_id = left.get("Paper_ID", "").strip().casefold()
    right_id = right.get("Paper_ID", "").strip().casefold()
    if left_id and right_id and left_id == right_id:
        return True
    left_doi = normalize_doi(left.get("DOI", ""))
    right_doi = normalize_doi(right.get("DOI", ""))
    return bool(left_doi and right_doi and left_doi == right_doi)


def duplicate_selection(
    rows: Iterable[dict[str, str]], record: dict[str, str]
) -> dict[str, str] | None:
    """Reject duplicate selection entries only within the same week."""
    week = record.get("Week", "").strip()
    for row in rows:
        if row.get("Week", "").strip() == week and same_identity(row, record):
            return row
    return None


def duplicate_reading(
    rows: Iterable[dict[str, str]], record: dict[str, str]
) -> dict[str, str] | None:
    """Reject a paper already recorded as a completed Deep Reading."""
    for row in rows:
        if same_identity(row, record):
            return row
    return None


def append_record(
    path: Path,
    fields: list[str],
    record: dict[str, str],
    *,
    record_type: str,
) -> None:
    """Append a schema-aligned record after record-type-specific duplicate checks."""
    rows = read_rows(path, fields)
    if record_type == "selection":
        duplicate = duplicate_selection(rows, record)
        duplicate_scope = f"week {record.get('Week', '').strip()}"
    elif record_type == "reading":
        duplicate = duplicate_reading(rows, record)
        duplicate_scope = "completed-reading history"
    else:
        raise HistoryError(f"Unknown record_type: {record_type}")
    if duplicate is not None:
        raise HistoryError(
            f"Duplicate {record_type} record detected in {duplicate_scope}: "
            f"{duplicate.get('Paper_ID') or duplicate.get('DOI')}"
        )
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writerow({field: record.get(field, "") for field in fields})


def record_from_args(args: argparse.Namespace, fields: list[str]) -> dict[str, str]:
    """Load a record object and validate required identity fields."""
    if args.record_json:
        try:
            value = json.loads(args.record_json)
        except json.JSONDecodeError as exc:
            raise HistoryError(f"--record-json is invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise HistoryError("--record-json must be a JSON object.")
        unknown = sorted(set(value) - set(fields))
        if unknown:
            raise HistoryError(f"Unknown record fields: {', '.join(unknown)}")
        record = {
            key: "" if value.get(key) is None else str(value.get(key, ""))
            for key in fields
        }
    else:
        record = {field: "" for field in fields}
        record.update(
            {
                "Week": args.week or "",
                "Topic": args.topic or "",
                "Paper_ID": args.paper_id or "",
                "Title": args.title or "",
                "DOI": args.doi or "",
                "Logged_Date": getattr(args, "logged_date", None) or "",
                "Completed_Date": getattr(args, "completed_date", None) or "",
            }
        )
    if not record["Paper_ID"].strip() and not record["DOI"].strip():
        raise HistoryError("A record requires Paper_ID or DOI.")
    if not record["Title"].strip():
        raise HistoryError("A record requires Title.")
    if not WEEK_PATTERN.fullmatch(record["Week"].strip()):
        raise HistoryError("A record requires Week in YYYY-Wxx ISO format.")
    return record


def verify_completed_reading_manifest(
    manifest_path: Path, record: dict[str, str]
) -> dict:
    """Mechanically verify that a reading-history row represents academic COMPLETE work.

    This does not judge academic quality. It enforces only the state contract:
    Deep Reading/B must be complete and free of unresolved academic blockers or
    update flags. Zotero parent/attachment keys are optional archive metadata and
    may remain pending after the reading itself is complete.
    """
    try:
        manifest = load_manifest(manifest_path)
    except (WorkflowStateError, OSError) as exc:
        raise HistoryError(f"Cannot verify completion manifest: {exc}") from exc

    if manifest["week"] != record["Week"].strip():
        raise HistoryError(
            f"Reading Week {record['Week']!r} does not match manifest week {manifest['week']!r}."
        )

    record_paper_id = record["Paper_ID"].strip()
    if not record_paper_id:
        raise HistoryError(
            "Completed reading records require Paper_ID so identity can be matched to the manifest."
        )
    manifest_paper_id = str(manifest.get("paper_id") or "").strip()
    if not manifest_paper_id or manifest_paper_id.casefold() != record_paper_id.casefold():
        raise HistoryError(
            "Reading Paper_ID does not match the active manifest paper_id."
        )

    deep = manifest["stages"]["deep_reading"]
    if deep["status"] != "COMPLETE":
        raise HistoryError(
            f"Deep Reading must be COMPLETE before history append; current={deep['status']}."
        )
    if deep["needs_update"]:
        raise HistoryError(
            "Deep Reading has unresolved needs_update and cannot enter completed history."
        )
    if any(
        blocker.get("stage") == "deep_reading"
        for blocker in manifest.get("blocking_issues", [])
    ):
        raise HistoryError(
            "Deep Reading still has a recorded academic blocker and cannot enter completed history."
        )

    b_output = manifest["outputs"]["B"]
    if b_output["status"] != "COMPLETE":
        raise HistoryError(
            "Completed reading history requires B academic status COMPLETE."
        )

    # Zotero identifiers are useful archive metadata but are not prerequisites
    # for recording that the paper was genuinely read and audited.
    manifest_b_key = str(b_output.get("zotero_attachment_key") or "").strip()
    record_b_key = record.get("B_Attachment_Key", "").strip()
    if manifest_b_key and record_b_key and manifest_b_key != record_b_key:
        raise HistoryError(
            "B_Attachment_Key in the reading record conflicts with the verified manifest key."
        )
    return manifest


def command_append_selection(args: argparse.Namespace) -> None:
    """Append one Search-stage selection record."""
    record = record_from_args(args, SELECTION_FIELDS)
    if not record["Logged_Date"].strip():
        raise HistoryError("Selection records require Logged_Date in ISO 8601 format.")
    validate_iso_date(record["Logged_Date"], "Logged_Date")
    append_record(args.file, SELECTION_FIELDS, record, record_type="selection")
    print(f"Appended selection record: {record['Paper_ID'] or record['DOI']}")


def command_append_reading(args: argparse.Namespace) -> None:
    """Append one manifest-verified academically completed Deep Reading record."""
    record = record_from_args(args, READING_FIELDS)
    if not record["Completed_Date"].strip():
        raise HistoryError("Reading records require Completed_Date in ISO 8601 format.")
    validate_iso_date(record["Completed_Date"], "Completed_Date")
    verify_completed_reading_manifest(args.manifest, record)
    append_record(args.file, READING_FIELDS, record, record_type="reading")
    print(f"Appended completed-reading record: {record['Paper_ID'] or record['DOI']}")


def find_records(path: Path, field: str, value: str) -> list[dict[str, str]]:
    """Find rows by normalized DOI or case-insensitive Paper_ID."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or field not in reader.fieldnames:
            raise HistoryError(f"CSV does not contain required field {field}: {path}")
        if field == "DOI":
            target = normalize_doi(value)
            return [row for row in reader if normalize_doi(row.get(field, "")) == target]
        target = value.strip().lower()
        return [row for row in reader if row.get(field, "").strip().lower() == target]


def command_find(args: argparse.Namespace) -> None:
    """Print matching rows as JSON."""
    field = "DOI" if args.command == "find-by-doi" else "Paper_ID"
    value = args.doi if field == "DOI" else args.paper_id
    matches = find_records(args.file, field, value)
    print(json.dumps(matches, ensure_ascii=False, indent=2))
    if not matches:
        raise HistoryError(f"No record found for {field}={value!r}.")


def add_common_record_arguments(parser: argparse.ArgumentParser) -> None:
    """Add concise append arguments; JSON supports the complete schema."""
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--record-json", help="Complete record as a JSON object.")
    parser.add_argument("--week")
    parser.add_argument("--topic")
    parser.add_argument("--paper-id")
    parser.add_argument("--title")
    parser.add_argument("--doi")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    selection = subparsers.add_parser("append-selection", help="Append a Search selection.")
    add_common_record_arguments(selection)
    selection.add_argument("--logged-date")
    selection.set_defaults(handler=command_append_selection)

    reading = subparsers.add_parser(
        "append-reading",
        help="Append a completed reading after verifying academic Deep Reading completion.",
    )
    add_common_record_arguments(reading)
    reading.add_argument("--completed-date")
    reading.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Workflow manifest proving academic Deep Reading COMPLETE for this paper/week.",
    )
    reading.set_defaults(handler=command_append_reading)

    by_doi = subparsers.add_parser("find-by-doi", help="Find records by DOI.")
    by_doi.add_argument("--file", type=Path, required=True)
    by_doi.add_argument("--doi", required=True)
    by_doi.set_defaults(handler=command_find)

    by_id = subparsers.add_parser("find-by-paper-id", help="Find records by Paper_ID.")
    by_id.add_argument("--file", type=Path, required=True)
    by_id.add_argument("--paper-id", required=True)
    by_id.set_defaults(handler=command_find)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the history manager CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.handler(args)
    except (HistoryError, OSError, csv.Error) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
