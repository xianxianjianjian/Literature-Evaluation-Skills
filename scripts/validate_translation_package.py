#!/usr/bin/env python3
"""Validate the evidence package behind a translated paper deliverable.

The validator checks source-to-output accountability. It deliberately does not
claim to automate semantic translation judgment or visual inspection; those
remain source-page comparisons recorded by the translation workflow.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mirror_pdf import MirrorPlanError, validate_plan_data

SCOPES = {"FULL_MIRROR", "MAIN_ONLY", "ABSTRACT_ONLY"}
INVENTORY_FILE = "source_inventory.json"
LEDGER_FILE = "translation_ledger.jsonl"
PLAN_FILE = "mirror_layout_plan.json"
ISSUES_FILE = "translation_issues.jsonl"


@dataclass(frozen=True)
class TranslationCheck:
    code: str
    passed: bool
    detail: str


class TranslationPackageError(ValueError):
    """Raised when a translation package cannot be parsed."""


def _load_json(path: Path, label: str) -> Any:
    if not path.is_file():
        raise TranslationPackageError(f"{label} missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise TranslationPackageError(f"{label} is invalid JSON: {exc}") from exc


def _load_jsonl(path: Path, label: str, *, required: bool = True) -> list[dict[str, Any]]:
    if not path.is_file():
        if required:
            raise TranslationPackageError(f"{label} missing: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TranslationPackageError(
                f"{label} line {line_number} is invalid JSON: {exc}"
            ) from exc
        if not isinstance(row, dict):
            raise TranslationPackageError(f"{label} line {line_number} must be an object")
        rows.append(row)
    return rows


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _identifier_map(
    rows: Any,
    field: str,
    label: str,
    checks: list[TranslationCheck],
    *,
    require_nonempty: bool = True,
) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        checks.append(TranslationCheck(f"inventory:{label}", False, f"{label} must be a list"))
        return {}
    result: dict[str, dict[str, Any]] = {}
    invalid = 0
    duplicates: list[str] = []
    for row in rows:
        if not isinstance(row, dict) or not _nonempty_text(row.get(field)):
            invalid += 1
            continue
        identifier = row[field].strip()
        if identifier in result:
            duplicates.append(identifier)
        else:
            result[identifier] = row
    passed = invalid == 0 and not duplicates and (bool(result) or not require_nonempty)
    detail = f"{len(result)} unique {label}"
    if invalid:
        detail += f"; {invalid} invalid record(s)"
    if duplicates:
        detail += f"; duplicate IDs: {', '.join(sorted(set(duplicates)))}"
    checks.append(TranslationCheck(f"inventory:{label}", passed, detail))
    return result


def _source_key(source_id: Any, source_page: Any) -> tuple[str, int] | None:
    if not _nonempty_text(source_id) or not _positive_int(source_page):
        return None
    return source_id.strip(), source_page


def _validate_inventory(data: Any, scope: str) -> tuple[list[TranslationCheck], dict[str, Any]]:
    checks: list[TranslationCheck] = []
    if not isinstance(data, dict):
        return [TranslationCheck("inventory:root", False, "inventory root must be an object")], {}
    checks.append(
        TranslationCheck(
            "inventory:schema",
            data.get("schema_version") == 1,
            f"schema_version={data.get('schema_version')!r}",
        )
    )
    checks.append(
        TranslationCheck(
            "inventory:scope",
            data.get("scope") == scope,
            f"inventory scope={data.get('scope')!r}; requested={scope}",
        )
    )
    sources = _identifier_map(data.get("sources"), "source_id", "sources", checks)
    units = _identifier_map(data.get("units"), "unit_id", "units", checks)
    objects = _identifier_map(
        data.get("objects"), "object_id", "objects", checks, require_nonempty=False
    )
    source_failures: list[str] = []
    for source_id, source in sources.items():
        if (
            source.get("role") not in {"MAIN", "SI"}
            or not _positive_int(source.get("page_count"))
            or not _nonempty_text(source.get("status"))
        ):
            source_failures.append(source_id)
    checks.append(
        TranslationCheck(
            "inventory:source-records",
            not source_failures,
            "all sources have role, page count and status"
            if not source_failures
            else f"invalid source records: {', '.join(source_failures)}",
        )
    )
    pages_raw = data.get("pages")
    pages: dict[tuple[str, int], dict[str, Any]] = {}
    invalid_pages = 0
    duplicate_pages: list[str] = []
    if isinstance(pages_raw, list):
        for page in pages_raw:
            if not isinstance(page, dict):
                invalid_pages += 1
                continue
            key = _source_key(page.get("source_id"), page.get("source_page"))
            if key is None or key[0] not in sources:
                invalid_pages += 1
                continue
            if key in pages:
                duplicate_pages.append(f"{key[0]}:p{key[1]}")
            else:
                pages[key] = page
    else:
        invalid_pages += 1
    checks.append(
        TranslationCheck(
            "inventory:pages",
            bool(pages) and invalid_pages == 0 and not duplicate_pages,
            f"{len(pages)} unique source pages; invalid={invalid_pages}; duplicates={len(duplicate_pages)}",
        )
    )
    expected_pages = {
        (source_id, page_number)
        for source_id, source in sources.items()
        if _positive_int(source.get("page_count"))
        for page_number in range(1, source["page_count"] + 1)
    }
    missing_inventory_pages = sorted(expected_pages - set(pages))
    unexpected_inventory_pages = sorted(set(pages) - expected_pages)
    checks.append(
        TranslationCheck(
            "inventory:page-count-coverage",
            not missing_inventory_pages and not unexpected_inventory_pages,
            "inventory enumerates every fixed-render source page"
            if not missing_inventory_pages and not unexpected_inventory_pages
            else f"missing={missing_inventory_pages}; unexpected={unexpected_inventory_pages}",
        )
    )

    unit_location_failures: list[str] = []
    for unit_id, unit in units.items():
        key = _source_key(unit.get("source_id"), unit.get("source_page"))
        if key not in pages or unit_id not in pages[key].get("unit_ids", []):
            unit_location_failures.append(unit_id)
    for key, page in pages.items():
        if not isinstance(page.get("unit_ids"), list) or any(
            unit_id not in units for unit_id in page.get("unit_ids", [])
        ):
            unit_location_failures.append(f"{key[0]}:p{key[1]}")
    checks.append(
        TranslationCheck(
            "inventory:unit-page-links",
            not unit_location_failures,
            "all units linked to source pages"
            if not unit_location_failures
            else f"units missing page links: {', '.join(unit_location_failures)}",
        )
    )

    object_failures: list[str] = []
    table_failures: list[str] = []
    for object_id, item in objects.items():
        key = _source_key(item.get("source_id"), item.get("source_page"))
        if (
            key not in pages
            or object_id not in pages[key].get("object_ids", [])
            or item.get("kind") not in {"figure", "table"}
        ):
            object_failures.append(object_id)
        if item.get("kind") == "table":
            shape = item.get("table_structure")
            if not isinstance(shape, dict) or not all(
                _positive_int(shape.get(field)) for field in ("rows", "columns", "header_rows")
            ):
                table_failures.append(object_id)
                continue
            if shape["header_rows"] > shape["rows"]:
                table_failures.append(object_id)
            for field in ("merged_cells", "footnotes"):
                value = shape.get(field)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    table_failures.append(object_id)
                    break
    for key, page in pages.items():
        if not isinstance(page.get("object_ids"), list) or any(
            object_id not in objects for object_id in page.get("object_ids", [])
        ):
            object_failures.append(f"{key[0]}:p{key[1]}")
    checks.append(
        TranslationCheck(
            "inventory:object-page-links",
            not object_failures,
            "all figure/table objects linked to source pages"
            if not object_failures
            else f"invalid object links: {', '.join(object_failures)}",
        )
    )
    checks.append(
        TranslationCheck(
            "inventory:table-structure",
            not table_failures,
            "all tables have source topology"
            if not table_failures
            else f"tables missing valid topology: {', '.join(sorted(set(table_failures)))}",
        )
    )
    return checks, {"sources": sources, "pages": pages, "units": units, "objects": objects}


def _validate_ledger(
    rows: list[dict[str, Any]],
    units: dict[str, dict[str, Any]] | None,
    issue_ids: set[str],
) -> tuple[list[TranslationCheck], dict[str, dict[str, Any]]]:
    checks: list[TranslationCheck] = []
    required = {
        "unit_id",
        "source_id",
        "source_page",
        "section",
        "unit_index",
        "kind",
        "source_status",
        "translation_status",
        "output_pages",
        "issue_ids",
    }
    ledger: dict[str, dict[str, Any]] = {}
    invalid_records: list[str] = []
    invalid_reasons: dict[str, int] = {}
    duplicate_ids: list[str] = []

    def record_invalid(label: str, reason: str) -> None:
        invalid_records.append(label)
        invalid_reasons[reason] = invalid_reasons.get(reason, 0) + 1

    for index, row in enumerate(rows, start=1):
        unit_id = row.get("unit_id")
        label = unit_id if _nonempty_text(unit_id) else f"line-{index}"
        if not required.issubset(row):
            for field in sorted(required - set(row)):
                invalid_reasons[f"missing {field}"] = invalid_reasons.get(
                    f"missing {field}", 0
                ) + 1
            invalid_records.append(str(label))
            continue
        if not _nonempty_text(unit_id) or unit_id in ledger:
            duplicate_ids.append(str(label))
            continue
        if (
            not _nonempty_text(row.get("source_id"))
            or not _positive_int(row.get("source_page"))
            or not _nonempty_text(row.get("section"))
            or not _positive_int(row.get("unit_index"))
            or not _nonempty_text(row.get("kind"))
            or not _nonempty_text(row.get("source_status"))
            or not isinstance(row.get("output_pages"), list)
            or not all(_positive_int(page) for page in row["output_pages"])
            or not isinstance(row.get("issue_ids"), list)
            or not all(_nonempty_text(issue_id) for issue_id in row["issue_ids"])
        ):
            record_invalid(str(label), "invalid field value or type")
            continue
        if row.get("translation_status") not in {"TRANSLATED", "SOURCE_GAP"}:
            record_invalid(str(label), "invalid translation_status")
            continue
        if row["translation_status"] == "TRANSLATED" and not row["output_pages"]:
            record_invalid(str(label), "translated unit has no output page")
            continue
        if row["translation_status"] == "SOURCE_GAP" and not row["issue_ids"]:
            record_invalid(str(label), "source gap has no issue")
            continue
        if any(issue_id not in issue_ids for issue_id in row["issue_ids"]):
            record_invalid(str(label), "unknown issue ID")
            continue
        ledger[unit_id] = row
    checks.append(
        TranslationCheck(
            "ledger:schema",
            not invalid_records and not duplicate_ids,
            f"{len(ledger)} valid records"
            + (
                "; invalid records="
                + str(len(invalid_records))
                + "; reasons="
                + ", ".join(
                    f"{reason} ({count})"
                    for reason, count in sorted(invalid_reasons.items())
                )
                + "; examples="
                + ", ".join(invalid_records[:10])
                if invalid_records
                else ""
            )
            + (f"; duplicates: {', '.join(duplicate_ids)}" if duplicate_ids else ""),
        )
    )
    if units is None:
        checks.append(
            TranslationCheck(
                "ledger:inventory-coverage",
                False,
                "source inventory unavailable; ledger coverage cannot be established",
            )
        )
        units = {}
    else:
        missing = sorted(set(units) - set(ledger))
        extra = sorted(set(ledger) - set(units))
        mismatched = sorted(
            unit_id
            for unit_id in set(units) & set(ledger)
            if (
                _source_key(units[unit_id].get("source_id"), units[unit_id].get("source_page"))
                != _source_key(ledger[unit_id].get("source_id"), ledger[unit_id].get("source_page"))
                or units[unit_id].get("kind") != ledger[unit_id].get("kind")
            )
        )
        checks.append(
            TranslationCheck(
                "ledger:inventory-coverage",
                not missing and not extra and not mismatched,
                "ledger exactly covers source units"
                if not missing and not extra and not mismatched
                else f"missing={missing}; extra={extra}; source-location-mismatch={mismatched}",
            )
        )
    gaps = sorted(
        unit_id for unit_id, row in ledger.items() if row.get("translation_status") == "SOURCE_GAP"
    )
    checks.append(
        TranslationCheck(
            "ledger:no-source-gaps",
            not gaps,
            "no unresolved source gaps" if not gaps else f"source gaps prevent COMPLETE: {', '.join(gaps)}",
        )
    )
    return checks, ledger


def _validate_issues(rows: list[dict[str, Any]]) -> tuple[list[TranslationCheck], set[str]]:
    issue_ids: set[str] = set()
    invalid: list[str] = []
    blocking: list[str] = []
    for index, row in enumerate(rows, start=1):
        issue_id = row.get("issue_id")
        if not _nonempty_text(issue_id) or issue_id in issue_ids:
            invalid.append(f"line-{index}")
            continue
        issue_ids.add(issue_id)
        if row.get("status") not in {"OPEN", "RESOLVED"}:
            invalid.append(issue_id)
        if row.get("completion_impact") not in {"NONE", "PROVISIONAL", "BLOCKED"}:
            invalid.append(issue_id)
        if row.get("status") == "OPEN" and row.get("completion_impact") in {"PROVISIONAL", "BLOCKED"}:
            blocking.append(issue_id)
    return [
        TranslationCheck(
            "issues:schema",
            not invalid,
            f"{len(issue_ids)} issues parsed"
            if not invalid
            else f"invalid issues: {', '.join(sorted(set(invalid)))}",
        ),
        TranslationCheck(
            "issues:no-completion-impact",
            not blocking,
            "no open consequential translation issues"
            if not blocking
            else f"open issues prevent COMPLETE: {', '.join(blocking)}",
        ),
    ], issue_ids


def _validate_layout(
    plan: Any,
    pages: dict[tuple[str, int], dict[str, Any]],
    objects: dict[str, dict[str, Any]],
    ledger: dict[str, dict[str, Any]],
    a_path: Path,
) -> list[TranslationCheck]:
    checks: list[TranslationCheck] = []
    try:
        validated = validate_plan_data(plan)
        checks.append(TranslationCheck("layout:plan-schema", True, "mirror plan schema valid"))
    except MirrorPlanError as exc:
        return [TranslationCheck("layout:plan-schema", False, str(exc))]

    planned_output = Path(str(validated.get("output_pdf", "")))
    try:
        same_output = planned_output.resolve() == a_path.resolve()
    except OSError:
        same_output = False
    checks.append(
        TranslationCheck(
            "layout:output-identity",
            same_output,
            "layout plan targets A" if same_output else f"plan output {planned_output} != A {a_path}",
        )
    )

    mapped_pages: set[tuple[str, int]] = set()
    placed_objects: set[str] = set()
    table_placements: dict[str, dict[str, Any]] = {}
    layout_field_failures: list[int] = []
    seen_output_pages: set[int] = set()
    duplicate_output_pages: list[int] = []
    for page in validated["pages"]:
        output_number = page.get("output_page_number")
        refs = page.get("source_page_refs")
        placed = page.get("placed_object_ids")
        placements = page.get("table_placements")
        if (
            not _positive_int(output_number)
            or not isinstance(refs, list)
            or not refs
            or not isinstance(placed, list)
            or not all(_nonempty_text(item) for item in placed)
            or not isinstance(placements, list)
        ):
            layout_field_failures.append(page.get("page_number"))
            continue
        if output_number in seen_output_pages:
            duplicate_output_pages.append(output_number)
        seen_output_pages.add(output_number)
        notes = page.get("render_notes")
        if page.get("render_checked") is True and not (
            isinstance(notes, list)
            and any(_nonempty_text(note) for note in notes)
        ):
            layout_field_failures.append(output_number)
        for ref in refs:
            if not isinstance(ref, dict):
                layout_field_failures.append(output_number)
                continue
            key = _source_key(ref.get("source_id"), ref.get("source_page"))
            if key is None:
                layout_field_failures.append(output_number)
            else:
                mapped_pages.add(key)
        placed_objects.update(item.strip() for item in placed)
        for placement in placements:
            if isinstance(placement, dict) and _nonempty_text(placement.get("object_id")):
                table_placements[placement["object_id"].strip()] = placement
            else:
                layout_field_failures.append(output_number)
    checks.append(
        TranslationCheck(
            "layout:page-fields",
            not layout_field_failures
            and not duplicate_output_pages
            and seen_output_pages == set(range(1, len(validated["pages"]) + 1)),
            "all output pages have source/object mappings"
            if (
                not layout_field_failures
                and not duplicate_output_pages
                and seen_output_pages == set(range(1, len(validated["pages"]) + 1))
            )
            else (
                f"invalid page fields={layout_field_failures}; "
                f"duplicate output pages={duplicate_output_pages}; "
                f"numbered output pages={sorted(seen_output_pages)}"
            ),
        )
    )
    ledger_page_failures = sorted(
        unit_id
        for unit_id, row in ledger.items()
        if any(page not in seen_output_pages for page in row.get("output_pages", []))
    )
    checks.append(
        TranslationCheck(
            "layout:ledger-output-pages",
            not ledger_page_failures,
            "every translated unit maps to a planned output page"
            if not ledger_page_failures
            else f"units reference unknown output pages: {', '.join(ledger_page_failures)}",
        )
    )
    missing_pages = sorted(set(pages) - mapped_pages)
    extra_pages = sorted(mapped_pages - set(pages))
    checks.append(
        TranslationCheck(
            "layout:source-page-coverage",
            not missing_pages and not extra_pages,
            "every source page maps to output"
            if not missing_pages and not extra_pages
            else f"unmapped={missing_pages}; unknown={extra_pages}",
        )
    )
    missing_objects = sorted(set(objects) - placed_objects)
    unknown_objects = sorted(placed_objects - set(objects))
    checks.append(
        TranslationCheck(
            "layout:object-coverage",
            not missing_objects and not unknown_objects,
            "every source figure/table is placed"
            if not missing_objects and not unknown_objects
            else f"missing={missing_objects}; unknown={unknown_objects}",
        )
    )

    topology_failures: list[str] = []
    for object_id, item in objects.items():
        if item.get("kind") != "table":
            continue
        placement = table_placements.get(object_id)
        shape = item.get("table_structure", {})
        if not placement:
            topology_failures.append(object_id)
            continue
        mode = placement.get("mode")
        if mode == "native-grid":
            if any(placement.get(field) != shape.get(field) for field in ("rows", "columns", "header_rows")):
                topology_failures.append(object_id)
                continue
            if shape.get("merged_cells", 0) and placement.get("merged_cells_preserved") is not True:
                topology_failures.append(object_id)
            if shape.get("footnotes", 0) and placement.get("footnotes_present") is not True:
                topology_failures.append(object_id)
        elif mode == "source-image-with-translation-map":
            if placement.get("translation_map_complete") is not True:
                topology_failures.append(object_id)
            if shape.get("footnotes", 0) and placement.get("footnotes_translated") is not True:
                topology_failures.append(object_id)
        else:
            topology_failures.append(object_id)
    checks.append(
        TranslationCheck(
            "layout:table-topology",
            not topology_failures,
            "table topology preserved or allowed image-map fallback documented"
            if not topology_failures
            else f"invalid table rendering: {', '.join(sorted(set(topology_failures)))}",
        )
    )
    all_checked = validated.get("layout_qc", {}).get("status") == "LAYOUT_QC_PASSED"
    checks.append(
        TranslationCheck(
            "layout:render-qc",
            all_checked,
            "all rendered pages inspected" if all_checked else "layout_qc must be LAYOUT_QC_PASSED",
        )
    )
    return checks


def validate_package(work_dir: Path, a_path: Path, scope: str) -> list[TranslationCheck]:
    work_dir = work_dir.resolve()
    a_path = a_path.resolve()
    checks: list[TranslationCheck] = []
    if scope not in SCOPES:
        return [TranslationCheck("scope", False, f"unsupported scope: {scope}")]
    pdf_ok = a_path.is_file() and a_path.stat().st_size > 0
    if pdf_ok:
        try:
            pdf_ok = a_path.read_bytes()[:5] == b"%PDF-"
        except OSError:
            pdf_ok = False
    checks.append(TranslationCheck("artifact:A", pdf_ok, "A PDF present" if pdf_ok else f"invalid A PDF: {a_path}"))
    parsed: dict[str, Any] = {}
    try:
        inventory = _load_json(work_dir / INVENTORY_FILE, "source inventory")
        inventory_checks, parsed = _validate_inventory(inventory, scope)
        checks.extend(inventory_checks)
    except (OSError, TranslationPackageError) as exc:
        checks.append(TranslationCheck("inventory:parse", False, str(exc)))

    issue_ids: set[str] = set()
    try:
        issue_checks, issue_ids = _validate_issues(
            _load_jsonl(work_dir / ISSUES_FILE, "translation issues", required=False)
        )
        checks.extend(issue_checks)
    except (OSError, TranslationPackageError) as exc:
        checks.append(TranslationCheck("issues:parse", False, str(exc)))

    parsed_ledger: dict[str, dict[str, Any]] = {}
    try:
        ledger = _load_jsonl(work_dir / LEDGER_FILE, "translation ledger")
        ledger_checks, parsed_ledger = _validate_ledger(
            ledger, parsed.get("units") if parsed else None, issue_ids
        )
        checks.extend(ledger_checks)
    except (OSError, TranslationPackageError) as exc:
        checks.append(TranslationCheck("ledger:parse", False, str(exc)))

    if scope == "FULL_MIRROR":
        try:
            plan = _load_json(work_dir / PLAN_FILE, "mirror layout plan")
            checks.extend(
                _validate_layout(
                    plan,
                    parsed.get("pages", {}),
                    parsed.get("objects", {}),
                    parsed_ledger,
                    a_path,
                )
            )
        except (OSError, TranslationPackageError) as exc:
            checks.append(TranslationCheck("layout:parse", False, str(exc)))
    return checks


def write_report(path: Path, work_dir: Path, a_path: Path, scope: str, checks: list[TranslationCheck]) -> None:
    payload = {
        "schema_version": 1,
        "validator": "validate_translation_package.py",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "work_dir": str(work_dir.resolve()),
        "a_path": str(a_path.resolve()),
        "passed": all(check.passed for check in checks),
        "checks": [asdict(check) for check in checks],
    }
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", delete=False, dir=path.parent
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--a-path", type=Path, required=True)
    parser.add_argument("--scope", choices=sorted(SCOPES), required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    checks = validate_package(args.work_dir, args.a_path, args.scope)
    write_report(args.report, args.work_dir, args.a_path, args.scope, checks)
    for check in checks:
        print(f"[{'PASS' if check.passed else 'FAIL'}] {check.code}: {check.detail}")
    failures = sum(not check.passed for check in checks)
    print(f"Summary: {len(checks) - failures} passed, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
