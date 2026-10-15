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

LEGACY_FIELDS = [
    "Term_ID", "English_Term", "Abbreviation", "Preferred_Chinese",
    "Alternative_Chinese", "Discipline", "Subfield", "Definition", "Context",
    "Confidence", "Evidence_Level", "Evidence_IDs", "Status", "First_Verified",
    "Last_Verified", "Notes",
]
FIELDS = [
    "Term_ID", "English_Term", "Preferred_Chinese", "Alternative_Chinese",
    "Abbreviation", "Domain", "Subdomain", "Definition", "Context",
    "Operational_Use", "Source_Type", "Source_Citation", "Confidence",
    "Evidence_ID", "Evidence_IDs", "Evidence_Level", "Paper_ID", "First_Seen",
    "First_Verified", "Last_Used", "Last_Verified", "Usage_Count", "Status",
    "Notes",
]
CONFIDENCE_VALUES = {"HIGH", "MEDIUM", "LOW"}
STATUS_VALUES = {"ACTIVE", "CONTEXTUAL", "DEPRECATED"}
EVIDENCE_ROLES = {"Translation Evidence", "Definition Evidence", "Methodological Evidence"}
EVIDENCE_ID_PATTERN = re.compile(r"^TERMEV-\d{4,}$")
TERM_ID_PATTERN = re.compile(r"^TERM-\d{4}$")
EVIDENCE_LEVEL_PATTERN = re.compile(r"^TE[1-7]$")
MODEL_SOURCE_PATTERN = re.compile(r"\b(?:chatgpt|openai|codex|ai\s+(?:recommended|suggested))\b", re.I)


class TerminologyError(ValueError):
    """Raised when a registry or requested update is invalid."""


def validate_iso_date(value: str, field: str) -> None:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise TerminologyError(f"{field} must use YYYY-MM-DD format.") from exc
    if parsed.isoformat() != value:
        raise TerminologyError(f"{field} must use canonical YYYY-MM-DD format.")


def read_registry(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise TerminologyError(f"Registry does not exist: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        if fieldnames not in (FIELDS, LEGACY_FIELDS):
            raise TerminologyError(
                f"Unexpected registry header in {path}. Expected: {','.join(FIELDS)}"
            )
        raw_rows = list(reader)
    rows: list[dict[str, str]] = []
    for raw in raw_rows:
        row = {field: "" for field in FIELDS}
        if fieldnames == LEGACY_FIELDS:
            row.update({field: str(raw.get(field) or "") for field in LEGACY_FIELDS if field in row})
            row["Domain"] = str(raw.get("Discipline") or "")
            row["Subdomain"] = str(raw.get("Subfield") or "")
            row["Evidence_ID"] = next(
                (item.strip() for item in re.split(r"[;,]", str(raw.get("Evidence_IDs") or "")) if item.strip()),
                "",
            )
            row["First_Seen"] = str(raw.get("First_Verified") or "")
            row["Last_Used"] = str(raw.get("Last_Verified") or "")
            row["Usage_Count"] = "0"
        else:
            row.update({field: str(raw.get(field) or "") for field in FIELDS})
        rows.append(row)
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
        if row["Evidence_Level"] and not (
            row["Source_Citation"].strip() or row["Evidence_IDs"].strip() or row["Evidence_ID"].strip()
        ):
            raise TerminologyError(f"Evidence-backed term lacks a traceable citation/ID at line {line_number}.")
        if MODEL_SOURCE_PATTERN.search(row["Source_Citation"]):
            raise TerminologyError(f"Model recommendation is not terminology evidence at line {line_number}.")
        for field in ("First_Verified", "Last_Verified"):
            if row[field]:
                validate_iso_date(row[field], f"{field} at line {line_number}")
        for field in ("First_Seen", "Last_Used"):
            if row[field]:
                validate_iso_date(row[field], f"{field} at line {line_number}")
        try:
            usage_count = int(row["Usage_Count"] or "0")
        except ValueError as exc:
            raise TerminologyError(f"Invalid Usage_Count at line {line_number}.") from exc
        if usage_count < 0:
            raise TerminologyError(f"Invalid Usage_Count at line {line_number}.")
    return rows


def write_registry(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def print_rows(rows: list[dict[str, str]]) -> None:
    print(json.dumps(rows, ensure_ascii=False, indent=2))


def normalized_component(value: str | None) -> str:
    return (value or "").strip().casefold()


def terminology_identity(record: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        normalized_component(record.get("English_Term")),
        normalized_component(record.get("Domain")),
        normalized_component(record.get("Subdomain")),
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
    return [part.strip() for part in value.split(";") if part.strip()]


def evidence_ids_for_row(row: dict[str, str]) -> list[str]:
    values = f"{row.get('Evidence_ID', '')};{row.get('Evidence_IDs', '')}"
    return list(dict.fromkeys(
        item.strip() for item in re.split(r"[;,]", values) if item.strip()
    ))


def merge_alternative(value: str, candidate: str) -> str:
    alternatives = split_alternatives(value)
    candidate = candidate.strip()
    if candidate and candidate not in alternatives:
        alternatives.append(candidate)
    return "; ".join(alternatives)


def merge_alternative_values(existing: str, supplied: str | None, *required: str) -> str:
    """Merge alternatives without ever erasing required historical wordings."""
    merged = existing
    if supplied is not None:
        for candidate in split_alternatives(supplied):
            merged = merge_alternative(merged, candidate)
    for candidate in required:
        merged = merge_alternative(merged, candidate)
    return merged


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
            f"domain={duplicate['Domain'] or '-'}, "
            f"subdomain={duplicate['Subdomain'] or '-'}, "
            f"context={duplicate['Context'] or '-'})"
        )


def command_lookup(args: argparse.Namespace) -> None:
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
    rows = read_registry(args.registry)
    if not TERM_ID_PATTERN.fullmatch(args.term_id):
        raise TerminologyError("Term_ID must use TERM-0001 format.")
    if any(row["Term_ID"] == args.term_id for row in rows):
        raise TerminologyError(f"Term_ID already exists: {args.term_id}")
    if args.evidence_level and not EVIDENCE_LEVEL_PATTERN.fullmatch(args.evidence_level):
        raise TerminologyError("Evidence level must be TE1 through TE7.")
    if args.verified_date:
        validate_iso_date(args.verified_date, "verified_date")
    for field in ("first_seen", "last_used"):
        value = getattr(args, field, None)
        if value:
            validate_iso_date(value, field)
    if getattr(args, "usage_count", None) is not None and args.usage_count < 0:
        raise TerminologyError("usage_count cannot be negative.")
    if MODEL_SOURCE_PATTERN.search(getattr(args, "source_citation", None) or ""):
        raise TerminologyError("Source_Citation cannot cite a model recommendation.")
    record = {field: "" for field in FIELDS}
    domain = getattr(args, "domain", None) or getattr(args, "discipline", None) or ""
    subdomain = getattr(args, "subdomain", None) or getattr(args, "subfield", None) or ""
    verified_date = args.verified_date or ""
    evidence_ids = getattr(args, "evidence_ids", None) or ""
    primary_evidence_id = getattr(args, "evidence_id", None) or next(
        (item.strip() for item in re.split(r"[;,]", evidence_ids) if item.strip()), ""
    )
    record.update(
        {
            "Term_ID": args.term_id,
            "English_Term": args.english_term.strip(),
            "Abbreviation": args.abbreviation or "",
            "Preferred_Chinese": args.preferred_chinese.strip(),
            "Alternative_Chinese": args.alternative_chinese or "",
            "Domain": domain,
            "Subdomain": subdomain,
            "Definition": args.definition or "",
            "Context": args.context or "",
            "Operational_Use": getattr(args, "operational_use", None) or "",
            "Source_Type": getattr(args, "source_type", None) or "",
            "Source_Citation": getattr(args, "source_citation", None) or "",
            "Confidence": args.confidence,
            "Evidence_Level": args.evidence_level or "",
            "Evidence_ID": primary_evidence_id,
            "Evidence_IDs": evidence_ids or primary_evidence_id,
            "Paper_ID": getattr(args, "paper_id", None) or "",
            "First_Seen": getattr(args, "first_seen", None) or verified_date,
            "Status": args.status,
            "First_Verified": verified_date,
            "Last_Used": getattr(args, "last_used", None) or verified_date,
            "Last_Verified": verified_date,
            "Usage_Count": str(getattr(args, "usage_count", None) or 0),
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
        "Domain": getattr(args, "domain", None) or getattr(args, "discipline", None),
        "Subdomain": getattr(args, "subdomain", None) or getattr(args, "subfield", None),
        "Definition": args.definition,
        "Context": args.context,
        "Operational_Use": getattr(args, "operational_use", None),
        "Source_Type": getattr(args, "source_type", None),
        "Source_Citation": getattr(args, "source_citation", None),
        "Confidence": args.confidence,
        "Evidence_Level": args.evidence_level,
        "Evidence_IDs": args.evidence_ids,
        "Paper_ID": getattr(args, "paper_id", None),
    }
    if (
        all(value is None for value in updates.values())
        and args.alternative_chinese is None
        and not args.note
    ):
        raise TerminologyError("No update fields were supplied.")
    if args.evidence_level and not EVIDENCE_LEVEL_PATTERN.fullmatch(args.evidence_level):
        raise TerminologyError("Evidence level must be TE1 through TE7.")

    old_preferred = row["Preferred_Chinese"]
    new_preferred = (args.preferred_chinese or "").strip()
    preferred_changed = bool(new_preferred and new_preferred != old_preferred)
    if preferred_changed and not args.note:
        raise TerminologyError(
            "Changing Preferred_Chinese requires --note explaining the evidence/context change."
        )

    for field, value in updates.items():
        if value is not None:
            row[field] = value.strip() if isinstance(value, str) else value
    if args.evidence_ids is not None:
        row["Evidence_ID"] = next(
            (item.strip() for item in re.split(r"[;,]", args.evidence_ids) if item.strip()), ""
        )

    required_history = (old_preferred,) if preferred_changed else ()
    row["Alternative_Chinese"] = merge_alternative_values(
        row["Alternative_Chinese"], args.alternative_chinese, *required_history
    )

    if not row["Preferred_Chinese"].strip():
        raise TerminologyError("Preferred_Chinese cannot be empty.")
    ensure_unique_identity(rows, row, exclude_term_id=args.term_id)
    row["Last_Verified"] = args.verified_date
    row["Notes"] = append_note(row["Notes"], args.note)
    write_registry(args.registry, rows)
    if preferred_changed:
        corrections = getattr(args, "corrections", None) or args.registry.with_name(
            "terminology_corrections.jsonl"
        )
        append_evidence_event(
            corrections,
            {
                "schema_version": 1,
                "event_type": "TERM_CORRECTION",
                "term_id": args.term_id,
                "old_preferred_chinese": old_preferred,
                "new_preferred_chinese": row["Preferred_Chinese"],
                "reason": args.note.strip(),
                "evidence_ids": [
                    item.strip() for item in re.split(r"[;,]", row["Evidence_IDs"]) if item.strip()
                ],
                "corrected_date": args.verified_date,
            },
        )
    print(f"Updated terminology record: {args.term_id}")


def command_update_status(args: argparse.Namespace) -> None:
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
    discipline: str | None = None,
    subfield: str | None = None,
    context: str | None = None,
    domain: str | None = None,
    subdomain: str | None = None,
) -> dict[str, object]:
    english = normalized_component(english_term)
    candidates = [
        row for row in rows if normalized_component(row["English_Term"]) == english
    ]
    exact: list[dict[str, str]] = []
    for row in candidates:
        requested = {
            "Domain": domain or discipline,
            "Subdomain": subdomain or subfield,
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
            "Domain": domain or discipline,
            "Subdomain": subdomain or subfield,
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


def resolve_context_candidate(
    rows: list[dict[str, str]], *, english_term: str, domain: str,
    context: str, subdomain: str = "",
) -> dict[str, object]:
    """Reuse one verified exact-context record or require external verification."""
    payload = context_candidates(
        rows, english_term=english_term, domain=domain,
        subdomain=subdomain or None, context=context,
    )
    exact = [
        row for row in payload["exact_or_filtered_matches"]
        if row["Status"] in {"ACTIVE", "CONTEXTUAL"}
        and row["Confidence"] == "HIGH"
        and bool(row["Evidence_IDs"].strip() or row["Evidence_ID"].strip())
    ]
    selected = exact[0] if len(exact) == 1 else None
    payload["auto_selected_term_id"] = selected["Term_ID"] if selected else None
    payload["decision"] = "REUSE_VERIFIED" if selected else "EXTERNAL_VERIFICATION_REQUIRED"
    return payload


def command_resolve(args: argparse.Namespace) -> None:
    payload = resolve_context_candidate(
        read_registry(args.registry), english_term=args.english_term,
        domain=args.domain, subdomain=args.subdomain or "", context=args.context,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def command_record_usage(args: argparse.Namespace) -> None:
    """Accumulate one use per focal paper without erasing earlier paper IDs."""
    validate_iso_date(args.used_date, "used_date")
    rows = read_registry(args.registry)
    requested = [item.strip() for item in re.split(r"[;,]", args.term_ids) if item.strip()]
    if not requested:
        raise TerminologyError("record-usage requires at least one TERM ID.")
    unknown = sorted(set(requested) - {row["Term_ID"] for row in rows})
    if unknown:
        raise TerminologyError(f"Unknown TERM IDs: {unknown}")
    for term_id in dict.fromkeys(requested):
        row = find_term(rows, term_id)
        paper_ids = [item.strip() for item in row["Paper_ID"].split(";") if item.strip()]
        if args.paper_id not in paper_ids:
            paper_ids.append(args.paper_id)
            row["Usage_Count"] = str(int(row["Usage_Count"] or "0") + 1)
        row["Paper_ID"] = "; ".join(paper_ids)
        row["Last_Used"] = args.used_date
        if not row["First_Seen"]:
            row["First_Seen"] = args.used_date
    write_registry(args.registry, rows)
    print(f"Recorded terminology usage for {len(set(requested))} term(s).")


def command_record_paper_usage(args: argparse.Namespace) -> None:
    """Accumulate every TERM ID from one reviewed paper terminology sheet."""
    with args.paper_terminology.open("r", encoding="utf-8-sig", newline="") as handle:
        paper_rows = list(csv.DictReader(handle))
    term_ids = list(dict.fromkeys(
        str(row.get("Term_ID") or row.get("term_id") or "").strip()
        for row in paper_rows
        if str(row.get("Term_ID") or row.get("term_id") or "").strip()
    ))
    if not term_ids:
        raise TerminologyError("paper terminology sheet contains no TERM IDs.")
    command_record_usage(argparse.Namespace(
        registry=args.registry, term_ids=";".join(term_ids),
        paper_id=args.paper_id, used_date=args.used_date,
    ))


def command_context(args: argparse.Namespace) -> None:
    rows = read_registry(args.registry)
    payload = context_candidates(
        rows,
        english_term=args.english_term,
        discipline=args.discipline,
        subfield=args.subfield,
        context=args.context,
        domain=getattr(args, "domain", None),
        subdomain=getattr(args, "subdomain", None),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not payload["all_english_term_candidates"]:
        raise TerminologyError(
            f"No terminology records matched English_Term={args.english_term!r}."
        )


def command_list_ambiguous(args: argparse.Namespace) -> None:
    rows = read_registry(args.registry)
    ambiguous = [
        row
        for row in rows
        if row["Confidence"] in {"LOW", "MEDIUM"}
        or row["Status"] == "CONTEXTUAL"
        or bool(row["Alternative_Chinese"].strip())
        or not evidence_ids_for_row(row)
    ]
    print_rows(ambiguous)


def command_export(args: argparse.Namespace) -> None:
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


def read_evidence_events(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        raise TerminologyError(f"Evidence registry does not exist: {path}")
    events: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TerminologyError(f"Invalid evidence JSONL line {line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise TerminologyError(f"Evidence JSONL line {line_number} must be an object.")
        events.append(value)
    return events


def evidence_state(events: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    state: dict[str, dict[str, object]] = {}
    for event in events:
        event_type = event.get("event_type")
        if event_type in {"DEPRECATE", "UNLINK", "UPDATE_SUPPORTS"}:
            target = str(event.get("target_evidence_id") or "")
            if event_type == "DEPRECATE" and target in state:
                state[target]["status"] = "DEPRECATED"
            elif event_type == "UPDATE_SUPPORTS" and target in state:
                replacement = event.get("new_supports")
                if isinstance(replacement, list):
                    state[target]["supports"] = list(replacement)
                    reported = event.get("reported_terms")
                    if isinstance(reported, list):
                        state[target]["reported_terms"] = list(reported)
                    roles = event.get("roles")
                    if isinstance(roles, list):
                        state[target]["roles"] = list(roles)
            continue
        evidence_id = str(event.get("evidence_id") or "")
        if evidence_id:
            record = dict(event)
            record.setdefault("status", "ACTIVE")
            state[evidence_id] = record
    return state


def append_evidence_event(path: Path, event: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def _parse_roles(value: str) -> list[str]:
    roles = [item.strip() for item in re.split(r"[;,]", value) if item.strip()]
    unknown = sorted(set(roles) - EVIDENCE_ROLES)
    if not roles or unknown:
        raise TerminologyError(
            "Evidence role must be one or more of: " + ", ".join(sorted(EVIDENCE_ROLES))
        )
    return roles


def command_add_evidence(args: argparse.Namespace) -> None:
    events = read_evidence_events(args.evidence)
    if not EVIDENCE_ID_PATTERN.fullmatch(args.evidence_id):
        raise TerminologyError("Evidence_ID must use TERMEV-0001 format.")
    if args.evidence_id in evidence_state(events):
        raise TerminologyError(f"Evidence_ID already exists: {args.evidence_id}")
    validate_iso_date(args.verified_date, "verified_date")
    supports = [item.strip() for item in args.supports.split(";") if item.strip()]
    if not supports:
        raise TerminologyError("Evidence must support at least one explicit term.")
    event = {
        "schema_version": 2,
        "event_type": "ADD",
        "evidence_id": args.evidence_id,
        "roles": _parse_roles(args.roles),
        "type": args.type,
        "source": args.source.strip(),
        "url": args.url,
        "supports": supports,
        "reported_terms": [item.strip() for item in (args.reported_terms or "").split(";") if item.strip()],
        "paper_id": args.paper_id,
        "verified_date": args.verified_date,
        "status": "ACTIVE",
    }
    append_evidence_event(args.evidence, event)
    print(f"Added terminology evidence: {args.evidence_id}")


def command_deprecate_evidence(args: argparse.Namespace) -> None:
    state = evidence_state(read_evidence_events(args.evidence))
    if args.evidence_id not in state:
        raise TerminologyError(f"Unknown evidence ID: {args.evidence_id}")
    validate_iso_date(args.verified_date, "verified_date")
    append_evidence_event(
        args.evidence,
        {
            "schema_version": 2,
            "event_type": "DEPRECATE",
            "target_evidence_id": args.evidence_id,
            "reason": args.reason.strip(),
            "verified_date": args.verified_date,
        },
    )
    print(f"Deprecated terminology evidence: {args.evidence_id}")


def command_unlink_evidence(args: argparse.Namespace) -> None:
    rows = read_registry(args.registry)
    row = find_term(rows, args.term_id)
    ids = evidence_ids_for_row(row)
    if args.evidence_id not in ids:
        raise TerminologyError(f"{args.term_id} is not linked to {args.evidence_id}.")
    validate_iso_date(args.verified_date, "verified_date")
    remaining = [item for item in ids if item != args.evidence_id]
    row["Evidence_ID"] = remaining[0] if remaining else ""
    row["Evidence_IDs"] = "; ".join(remaining)
    row["Last_Verified"] = args.verified_date
    row["Notes"] = append_note(row["Notes"], f"Unlinked {args.evidence_id}: {args.reason.strip()}")
    write_registry(args.registry, rows)
    append_evidence_event(
        args.evidence,
        {
            "schema_version": 2,
            "event_type": "UNLINK",
            "target_evidence_id": args.evidence_id,
            "term_id": args.term_id,
            "reason": args.reason.strip(),
            "verified_date": args.verified_date,
        },
    )
    print(f"Unlinked {args.evidence_id} from {args.term_id}.")


def validate_evidence_links(
    rows: list[dict[str, str]], events: list[dict[str, object]]
) -> list[str]:
    failures: list[str] = []
    state = evidence_state(events)
    for evidence_id, record in state.items():
        if not EVIDENCE_ID_PATTERN.fullmatch(evidence_id):
            failures.append(f"invalid evidence id: {evidence_id}")
        if not re.fullmatch(r"TE[1-7]", str(record.get("type") or "")):
            failures.append(f"{evidence_id}: invalid evidence type")
        roles = record.get("roles")
        if roles is None and isinstance(record.get("role"), str):
            roles = [item.strip() for item in re.split(r"\band\b|[;,]", str(record["role"])) if item.strip()]
        if not isinstance(roles, list) or not roles or not set(map(str, roles)).issubset(EVIDENCE_ROLES):
            failures.append(f"{evidence_id}: invalid evidence role")
        supports = record.get("supports")
        if not isinstance(supports, list) or not supports or not all(str(item).strip() for item in supports):
            failures.append(f"{evidence_id}: supports must be a non-empty list")
        if str(record.get("type")) == "TE7" and "focal paper" in str(record.get("source", "")).casefold():
            reported = record.get("reported_terms")
            if not record.get("paper_id") or not isinstance(reported, list) or not set(map(str, supports or [])).issubset(set(map(str, reported or []))):
                failures.append(f"{evidence_id}: focal-paper TE7 supports exceed reported_terms")
    for row in rows:
        for evidence_id in evidence_ids_for_row(row):
            record = state.get(evidence_id)
            if record is None:
                failures.append(f"{row['Term_ID']}: unknown evidence {evidence_id}")
            elif record.get("status") == "DEPRECATED":
                failures.append(f"{row['Term_ID']}: deprecated evidence {evidence_id}")
            elif row["English_Term"] not in [str(item) for item in record.get("supports", [])]:
                failures.append(f"{row['Term_ID']}: {evidence_id} does not support English_Term")
    return failures


def command_validate_evidence(args: argparse.Namespace) -> None:
    failures = validate_evidence_links(read_registry(args.registry), read_evidence_events(args.evidence))
    payload = {"schema_version": 1, "passed": not failures, "failures": failures}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if failures:
        raise TerminologyError(f"Terminology evidence validation failed ({len(failures)} issue(s)).")


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
    add.add_argument("--domain")
    add.add_argument("--subdomain")
    add.add_argument("--discipline")
    add.add_argument("--subfield")
    add.add_argument("--definition")
    add.add_argument("--context")
    add.add_argument("--operational-use")
    add.add_argument("--source-type")
    add.add_argument("--source-citation")
    add.add_argument("--confidence", choices=sorted(CONFIDENCE_VALUES), required=True)
    add.add_argument("--evidence-id")
    add.add_argument("--evidence-level")
    add.add_argument("--evidence-ids")
    add.add_argument("--paper-id")
    add.add_argument("--first-seen")
    add.add_argument("--last-used")
    add.add_argument("--usage-count", type=int)
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
    update.add_argument("--domain")
    update.add_argument("--subdomain")
    update.add_argument("--discipline")
    update.add_argument("--subfield")
    update.add_argument("--definition")
    update.add_argument("--context")
    update.add_argument("--operational-use")
    update.add_argument("--source-type")
    update.add_argument("--source-citation")
    update.add_argument("--confidence", choices=sorted(CONFIDENCE_VALUES))
    update.add_argument("--evidence-level")
    update.add_argument("--evidence-ids")
    update.add_argument("--paper-id")
    update.add_argument("--corrections", type=Path)
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
    context.add_argument("--domain")
    context.add_argument("--subdomain")
    context.add_argument("--discipline")
    context.add_argument("--subfield")
    context.add_argument("--context")
    context.set_defaults(handler=command_context)

    resolve = subparsers.add_parser(
        "resolve", help="Reuse one high-confidence exact-context term or require verification."
    )
    resolve.add_argument("--registry", type=Path, required=True)
    resolve.add_argument("--english-term", required=True)
    resolve.add_argument("--domain", required=True)
    resolve.add_argument("--subdomain")
    resolve.add_argument("--context", required=True)
    resolve.set_defaults(handler=command_resolve)

    usage = subparsers.add_parser(
        "record-usage", help="Increment cross-paper usage once per paper and term."
    )
    usage.add_argument("--registry", type=Path, required=True)
    usage.add_argument("--term-ids", required=True, help="Semicolon-separated TERM IDs.")
    usage.add_argument("--paper-id", required=True)
    usage.add_argument("--used-date", required=True)
    usage.set_defaults(handler=command_record_usage)

    paper_usage = subparsers.add_parser(
        "record-paper-usage", help="Accumulate all reviewed TERM IDs from one paper sheet."
    )
    paper_usage.add_argument("--registry", type=Path, required=True)
    paper_usage.add_argument("--paper-terminology", type=Path, required=True)
    paper_usage.add_argument("--paper-id", required=True)
    paper_usage.add_argument("--used-date", required=True)
    paper_usage.set_defaults(handler=command_record_paper_usage)

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

    add_evidence = subparsers.add_parser("add-evidence", help="Append a terminology evidence record.")
    add_evidence.add_argument("--evidence", type=Path, required=True)
    add_evidence.add_argument("--evidence-id", required=True)
    add_evidence.add_argument("--roles", required=True)
    add_evidence.add_argument("--type", choices=[f"TE{i}" for i in range(1, 8)], required=True)
    add_evidence.add_argument("--source", required=True)
    add_evidence.add_argument("--url")
    add_evidence.add_argument("--supports", required=True, help="Semicolon-separated English terms.")
    add_evidence.add_argument("--reported-terms", help="Semicolon-separated terms actually reported by a focal paper.")
    add_evidence.add_argument("--paper-id")
    add_evidence.add_argument("--verified-date", required=True)
    add_evidence.set_defaults(handler=command_add_evidence)

    deprecate_evidence = subparsers.add_parser("deprecate-evidence", help="Append a deprecation event.")
    deprecate_evidence.add_argument("--evidence", type=Path, required=True)
    deprecate_evidence.add_argument("--evidence-id", required=True)
    deprecate_evidence.add_argument("--reason", required=True)
    deprecate_evidence.add_argument("--verified-date", required=True)
    deprecate_evidence.set_defaults(handler=command_deprecate_evidence)

    unlink_evidence = subparsers.add_parser("unlink-evidence", help="Traceably unlink evidence from one term.")
    unlink_evidence.add_argument("--registry", type=Path, required=True)
    unlink_evidence.add_argument("--evidence", type=Path, required=True)
    unlink_evidence.add_argument("--term-id", required=True)
    unlink_evidence.add_argument("--evidence-id", required=True)
    unlink_evidence.add_argument("--reason", required=True)
    unlink_evidence.add_argument("--verified-date", required=True)
    unlink_evidence.set_defaults(handler=command_unlink_evidence)

    validate_evidence = subparsers.add_parser("validate-evidence", help="Validate term/evidence links and TE7 scope.")
    validate_evidence.add_argument("--registry", type=Path, required=True)
    validate_evidence.add_argument("--evidence", type=Path, required=True)
    validate_evidence.set_defaults(handler=command_validate_evidence)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.handler(args)
    except (TerminologyError, OSError, csv.Error) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
