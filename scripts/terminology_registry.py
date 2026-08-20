#!/usr/bin/env python3
"""Query and maintain the evidence-tracked terminology registry."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path


FIELDS = [
    "Term_ID", "English_Term", "Abbreviation", "Preferred_Chinese",
    "Alternative_Chinese", "Discipline", "Subfield", "Definition", "Context",
    "Confidence", "Evidence_Level", "Evidence_IDs", "Status", "First_Verified",
    "Last_Verified", "Notes",
]
CONFIDENCE_VALUES = {"HIGH", "MEDIUM", "LOW"}
STATUS_VALUES = {"ACTIVE", "CONTEXTUAL", "DEPRECATED"}
TERM_ID_PATTERN = re.compile(r"^TERM-\d{4}$")
EVIDENCE_LEVEL_PATTERN = re.compile(r"^TE[1-7]$")


class TerminologyError(ValueError):
    """Raised when a registry or requested update is invalid."""


def validate_iso_date(value: str, field: str) -> None:
    """Require a canonical ISO 8601 calendar date when one is supplied."""
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise TerminologyError(f"{field} must use YYYY-MM-DD format.") from exc
    if parsed.isoformat() != value:
        raise TerminologyError(f"{field} must use canonical YYYY-MM-DD format.")


def read_registry(path: Path) -> list[dict[str, str]]:
    """Read and validate the registry header and row enums."""
    if not path.is_file():
        raise TerminologyError(f"Registry does not exist: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise TerminologyError(
                f"Unexpected registry header in {path}. Expected: {','.join(FIELDS)}"
            )
        rows = list(reader)
    for line_number, row in enumerate(rows, start=2):
        if not TERM_ID_PATTERN.fullmatch(row["Term_ID"]):
            raise TerminologyError(f"Invalid Term_ID at line {line_number}: {row['Term_ID']}")
        if row["Confidence"] not in CONFIDENCE_VALUES:
            raise TerminologyError(f"Invalid Confidence at line {line_number}.")
        if row["Status"] not in STATUS_VALUES:
            raise TerminologyError(f"Invalid Status at line {line_number}.")
        if row["Evidence_Level"] and not EVIDENCE_LEVEL_PATTERN.fullmatch(
            row["Evidence_Level"]
        ):
            raise TerminologyError(f"Invalid Evidence_Level at line {line_number}.")
        for field in ("First_Verified", "Last_Verified"):
            if row[field]:
                validate_iso_date(row[field], f"{field} at line {line_number}")
    return rows


def write_registry(path: Path, rows: list[dict[str, str]]) -> None:
    """Rewrite a validated registry without changing its schema."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def print_rows(rows: list[dict[str, str]]) -> None:
    """Print rows as readable JSON."""
    print(json.dumps(rows, ensure_ascii=False, indent=2))


def normalized_component(value: str | None) -> str:
    """Normalize one terminology identity component for comparison."""
    return (value or "").strip().casefold()


def terminology_identity(record: dict[str, str]) -> tuple[str, str, str, str]:
    """Return the context-aware identity used for duplicate prevention.

    The same English string may legitimately have different Chinese translations
    across disciplines/subfields/contexts, so English_Term alone is not unique.
    """
    return (
        normalized_component(record.get("English_Term")),
        normalized_component(record.get("Discipline")),
        normalized_component(record.get("Subfield")),
        normalized_component(record.get("Context")),
    )


def command_lookup(args: argparse.Namespace) -> None:
    """Find terms by ID, English term, abbreviation, or Chinese form."""
    rows = read_registry(args.registry)
    target = args.query.casefold().strip()
    searchable = (
        "Term_ID", "English_Term", "Abbreviation", "Preferred_Chinese", "Alternative_Chinese"
    )
    matches = [
        row
        for row in rows
        if any(target in row[field].casefold() for field in searchable if row[field])
    ]
    print_rows(matches)
    if not matches:
        raise TerminologyError(f"No terminology record matched {args.query!r}.")


def command_add(args: argparse.Namespace) -> None:
    """Add an explicit, evidence-traceable terminology record."""
    rows = read_registry(args.registry)
    if not TERM_ID_PATTERN.fullmatch(args.term_id):
        raise TerminologyError("Term_ID must use TERM-0001 format.")
    if any(row["Term_ID"] == args.term_id for row in rows):
        raise TerminologyError(f"Term_ID already exists: {args.term_id}")
    if args.evidence_level and not EVIDENCE_LEVEL_PATTERN.fullmatch(args.evidence_level):
        raise TerminologyError("Evidence level must be TE1 through TE7.")
    if args.verified_date:
        validate_iso_date(args.verified_date, "verified_date")

    record = {field: "" for field in FIELDS}
    record.update(
        {
            "Term_ID": args.term_id,
            "English_Term": args.english_term,
            "Abbreviation": args.abbreviation or "",
            "Preferred_Chinese": args.preferred_chinese,
            "Alternative_Chinese": args.alternative_chinese or "",
            "Discipline": args.discipline or "",
            "Subfield": args.subfield or "",
            "Definition": args.definition or "",
            "Context": args.context or "",
            "Confidence": args.confidence,
            "Evidence_Level": args.evidence_level or "",
            "Evidence_IDs": args.evidence_ids or "",
            "Status": args.status,
            "First_Verified": args.verified_date or "",
            "Last_Verified": args.verified_date or "",
            "Notes": args.notes or "",
        }
    )

    identity = terminology_identity(record)
    duplicate = next((row for row in rows if terminology_identity(row) == identity), None)
    if duplicate is not None:
        raise TerminologyError(
            "Equivalent terminology context already exists: "
            f"{duplicate['Term_ID']} ({duplicate['English_Term']}; "
            f"discipline={duplicate['Discipline'] or '-'}, "
            f"subfield={duplicate['Subfield'] or '-'}, "
            f"context={duplicate['Context'] or '-'})"
        )

    rows.append(record)
    write_registry(args.registry, rows)
    print(f"Added terminology record: {args.term_id}")


def command_update_status(args: argparse.Namespace) -> None:
    """Update only the lifecycle status of an existing term."""
    rows = read_registry(args.registry)
    matches = [row for row in rows if row["Term_ID"] == args.term_id]
    if not matches:
        raise TerminologyError(f"Unknown Term_ID: {args.term_id}")
    if args.verified_date:
        validate_iso_date(args.verified_date, "verified_date")
    matches[0]["Status"] = args.status
    if args.verified_date:
        matches[0]["Last_Verified"] = args.verified_date
    if args.note:
        existing = matches[0]["Notes"].strip()
        matches[0]["Notes"] = f"{existing} | {args.note}" if existing else args.note
    write_registry(args.registry, rows)
    print(f"Updated {args.term_id} status to {args.status}.")


def command_list_ambiguous(args: argparse.Namespace) -> None:
    """List records that still require contextual or evidence review."""
    rows = read_registry(args.registry)
    ambiguous = [
        row
        for row in rows
        if row["Confidence"] in {"LOW", "MEDIUM"}
        or row["Status"] == "CONTEXTUAL"
        or bool(row["Alternative_Chinese"].strip())
        or not row["Evidence_IDs"].strip()
    ]
    print_rows(ambiguous)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    lookup = subparsers.add_parser("lookup", help="Look up a term or identifier.")
    lookup.add_argument("--registry", type=Path, required=True)
    lookup.add_argument("--query", required=True)
    lookup.set_defaults(handler=command_lookup)

    add = subparsers.add_parser("add", help="Add an explicitly chosen term record.")
    add.add_argument("--registry", type=Path, required=True)
    add.add_argument("--term-id", required=True)
    add.add_argument("--english-term", required=True)
    add.add_argument("--preferred-chinese", required=True)
    add.add_argument("--abbreviation")
    add.add_argument("--alternative-chinese")
    add.add_argument("--discipline")
    add.add_argument("--subfield")
    add.add_argument("--definition")
    add.add_argument("--context")
    add.add_argument("--confidence", choices=sorted(CONFIDENCE_VALUES), required=True)
    add.add_argument("--evidence-level")
    add.add_argument("--evidence-ids")
    add.add_argument("--status", choices=sorted(STATUS_VALUES), default="ACTIVE")
    add.add_argument("--verified-date")
    add.add_argument("--notes")
    add.set_defaults(handler=command_add)

    update = subparsers.add_parser("update-status", help="Update a term lifecycle status.")
    update.add_argument("--registry", type=Path, required=True)
    update.add_argument("--term-id", required=True)
    update.add_argument("--status", choices=sorted(STATUS_VALUES), required=True)
    update.add_argument("--verified-date")
    update.add_argument("--note")
    update.set_defaults(handler=command_update_status)

    ambiguous = subparsers.add_parser(
        "list-ambiguous", help="List terms requiring contextual review."
    )
    ambiguous.add_argument("--registry", type=Path, required=True)
    ambiguous.set_defaults(handler=command_list_ambiguous)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the terminology-registry CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.handler(args)
    except (TerminologyError, OSError, csv.Error) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
