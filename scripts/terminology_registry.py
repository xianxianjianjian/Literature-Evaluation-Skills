#!/usr/bin/env python3
"""Query and maintain the evidence-tracked V1 terminology registry.

The helper manages explicit records and deterministic context matching. It never
chooses the academically "best" Chinese translation on its own.
"""

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
    seen_ids: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        if not TERM_ID_PATTERN.fullmatch(row["Term_ID"]):
            raise TerminologyError(
                f"Invalid Term_ID at line {line_number}: {row['Term_ID']}"
            )
        if row["Term_ID"] in seen_ids:
            raise TerminologyError(f"Duplicate Term_ID at line {line_number}.")
        seen_ids.add(row["Term_ID"])
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
    """Rewrite a registry using the frozen V1 schema."""
    path.parent.mkdir(parents=True, exist_ok=True)
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
    """Return the context-aware identity used for duplicate prevention."""
    return (
        normalized_component(record.get("English_Term")),
        normalized_component(record.get("Discipline")),
        normalized_component(record.get("Subfield")),
        normalized_component(record.get("Context")),
    )


def find_term(rows: list[dict[str, str]], term_id: str) -> dict[str, str]:
    matches = [row for row in rows if row["Term_ID"] == term_id]
    if not matches:
        raise TerminologyError(f"Unknown Term_ID: {term_id}")
    return matches[0]


def append_note(existing: str, note: str | None) -> str:
    note = (note or "").strip()
    if not note:
        return existing
    existing = existing.strip()
    return f"{existing} | {note}" if existing else note


def split_alternatives(value: str) -> list[str]:
    """Split the lightweight semicolon-delimited Alternative_Chinese field."""
    return [part.strip() for part in value.split(";") if part.strip()]


def merge_alternative(value: str, candidate: str) -> str:
    alternatives = split_alternatives(value)
    if candidate.strip() and candidate.strip() not in alternatives:
        alternatives.append(candidate.strip())
    return "; ".join(alternatives)


def ensure_unique_identity(
    rows: list[dict[str, str]], record: dict[str, str], *, exclude_term_id: str | None = None
) -> None:
    identity = terminology_identity(record)
    duplicate = next(
        (
            row
            for row in rows
            if row["Term_ID"] != exclude_term_id
            and terminology_identity(row) == identity
        ),
        None,
    )
    if duplicate is not None:
        raise TerminologyError(
            "Equivalent terminology context already exists: "
            f"{duplicate['Term_ID']} ({duplicate['English_Term']}; "
            f"discipline={duplicate['Discipline'] or '-'}, "
            f"subfield={duplicate['Subfield'] or '-'}, "
            f"context={duplicate['Context'] or '-'})"
        )


def command_lookup(args: argparse.Namespace) -> None:
    """Find terms by ID, English term, abbreviation, or Chinese form."""
    rows = read_registry(args.registry)
    target = args.query.casefold().strip()
    searchable = (
        "Term_ID", "English_Term", "Abbreviation", "Preferred_Chinese",
        "Alternative_Chinese",
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
    """Add an explicitly chosen, evidence-traceable terminology record."""
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
            "English_Term": args.english_term.strip(),
            "Abbreviation": args.abbreviation or "",
            "Preferred_Chinese": args.preferred_chinese.strip(),
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
    if not record["English_Term"] or not record["Preferred_Chinese"]:
        raise TerminologyError("English_Term and Preferred_Chinese cannot be empty.")
    ensure_unique_identity(rows, record)
    rows.append(record)
    write_registry(args.registry, rows)
    print(f"Added terminology record: {args.term_id}")


def command_update(args: argparse.Namespace) -> None:
    """Explicitly update a term while preserving prior preferred wording/history."""
    rows = read_registry(args.registry)
    row = find_term(rows, args.term_id)
    validate_iso_date(args.verified_date, "verified_date")

    updates = {
        "Abbreviation": args.abbreviation,
        "Preferred_Chinese": args.preferred_chinese,
        "Alternative_Chinese": args.alternative_chinese,
        "Discipline": args.discipline,
        "Subfield": args.subfield,
        "Definition": args.definition,
        "Context": args.context,
        "Confidence": args.confidence,
        "Evidence_Level": args.evidence_level,
        "Evidence_IDs": args.evidence_ids,
    }
    if all(value is None for value in updates.values()) and not args.note:
        raise TerminologyError("No update fields were supplied.")
    if args.evidence_level and not EVIDENCE_LEVEL_PATTERN.fullmatch(args.evidence_level):
        raise TerminologyError("Evidence level must be TE1 through TE7.")

    old_preferred = row["Preferred_Chinese"]
    new_preferred = (args.preferred_chinese or "").strip()
    if new_preferred and new_preferred != old_preferred:
        if not args.note:
            raise TerminologyError(
                "Changing Preferred_Chinese requires --note explaining the evidence/context change."
            )
        row["Alternative_Chinese"] = merge_alternative(
            row["Alternative_Chinese"], old_preferred
        )

    for field, value in updates.items():
        if value is not None:
            row[field] = value.strip() if isinstance(value, str) else value

    if not row["Preferred_Chinese"].strip():
        raise TerminologyError("Preferred_Chinese cannot be empty.")
    ensure_unique_identity(rows, row, exclude_term_id=args.term_id)
    row["Last_Verified"] = args.verified_date
    row["Notes"] = append_note(row["Notes"], args.note)
    write_registry(args.registry, rows)
    print(f"Updated terminology record: {args.term_id}")


def command_update_status(args: argparse.Namespace) -> None:
    """Update only the lifecycle status of an existing term."""
    rows = read_registry(args.registry)
    row = find_term(rows, args.term_id)
    if args.verified_date:
        validate_iso_date(args.verified_date, "verified_date")
    row["Status"] = args.status
    if args.verified_date:
        row["Last_Verified"] = args.verified_date
    row["Notes"] = append_note(row["Notes"], args.note)
    write_registry(args.registry, rows)
    print(f"Updated {args.term_id} status to {args.status}.")


def context_candidates(
    rows: list[dict[str, str]],
    *,
    english_term: str,
    discipline: str | None,
    subfield: str | None,
    context: str | None,
) -> dict[str, object]:
    """Return context candidates without choosing a preferred record."""
    english = normalized_component(english_term)
    candidates = [
        row for row in rows if normalized_component(row["English_Term"]) == english
    ]
    exact: list[dict[str, str]] = []
    for row in candidates:
        requested = {
            "Discipline": discipline,
            "Subfield": subfield,
            "Context": context,
        }
        if all(
            value is None
            or normalized_component(row[field]) == normalized_component(value)
            for field, value in requested.items()
        ):
            exact.append(row)
    return {
        "query": {
            "English_Term": english_term,
            "Discipline": discipline,
            "Subfield": subfield,
            "Context": context,
        },
        "exact_or_filtered_matches": exact,
        "all_english_term_candidates": candidates,
        "auto_selected_term_id": None,
        "note": (
            "The helper reports candidates only. Reuse still requires conceptual/context "
            "agreement under the terminology policy."
        ),
    }


def command_context(args: argparse.Namespace) -> None:
    rows = read_registry(args.registry)
    payload = context_candidates(
        rows,
        english_term=args.english_term,
        discipline=args.discipline,
        subfield=args.subfield,
        context=args.context,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not payload["all_english_term_candidates"]:
        raise TerminologyError(
            f"No terminology records matched English_Term={args.english_term!r}."
        )


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


def command_export(args: argparse.Namespace) -> None:
    """Export registry rows deterministically without changing source records."""
    rows = read_registry(args.registry)
    if args.status:
        allowed = set(args.status)
        rows = [row for row in rows if row["Status"] in allowed]

    if args.format == "json":
        payload = json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
            print(f"Exported {len(rows)} terminology records to {args.output}")
        else:
            print(payload, end="")
        return

    if args.output is None:
        raise TerminologyError("CSV export requires --output.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Exported {len(rows)} terminology records to {args.output}")


def add_status_parser(
    subparsers: argparse._SubParsersAction, name: str, help_text: str
) -> None:
    parser = subparsers.add_parser(name, help=help_text)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--term-id", required=True)
    parser.add_argument("--status", choices=sorted(STATUS_VALUES), required=True)
    parser.add_argument("--verified-date")
    parser.add_argument("--note")
    parser.set_defaults(handler=command_update_status)


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

    update = subparsers.add_parser(
        "update", help="Explicitly update fields while preserving translation history."
    )
    update.add_argument("--registry", type=Path, required=True)
    update.add_argument("--term-id", required=True)
    update.add_argument("--abbreviation")
    update.add_argument("--preferred-chinese")
    update.add_argument("--alternative-chinese")
    update.add_argument("--discipline")
    update.add_argument("--subfield")
    update.add_argument("--definition")
    update.add_argument("--context")
    update.add_argument("--confidence", choices=sorted(CONFIDENCE_VALUES))
    update.add_argument("--evidence-level")
    update.add_argument("--evidence-ids")
    update.add_argument("--verified-date", required=True)
    update.add_argument("--note")
    update.set_defaults(handler=command_update)

    add_status_parser(subparsers, "status", "Update a term lifecycle status.")
    add_status_parser(
        subparsers, "update-status", "Backward-compatible alias for status."
    )

    context = subparsers.add_parser(
        "context", help="Return context-matched candidates without auto-selection."
    )
    context.add_argument("--registry", type=Path, required=True)
    context.add_argument("--english-term", required=True)
    context.add_argument("--discipline")
    context.add_argument("--subfield")
    context.add_argument("--context")
    context.set_defaults(handler=command_context)

    ambiguous = subparsers.add_parser(
        "list-ambiguous", help="List terms requiring contextual review."
    )
    ambiguous.add_argument("--registry", type=Path, required=True)
    ambiguous.set_defaults(handler=command_list_ambiguous)

    export = subparsers.add_parser(
        "export", help="Export terminology rows without modifying the registry."
    )
    export.add_argument("--registry", type=Path, required=True)
    export.add_argument("--format", choices=("json", "csv"), default="json")
    export.add_argument("--output", type=Path)
    export.add_argument(
        "--status", action="append", choices=sorted(STATUS_VALUES),
        help="Repeat to export selected lifecycle statuses only.",
    )
    export.set_defaults(handler=command_export)

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
