#!/usr/bin/env python3
"""Pure checks for the v1.5 Zotero parent and role-based attachment contract."""

from __future__ import annotations

from typing import Any
from pathlib import Path
from artifact_binding import fingerprint, same_content, resolve_path


ROLE_TITLES = {"MAIN": "pdf", "A": "A翻译", "B": "B精读"}


def role_title(role: str, si_number: int | None = None, *, data_si: bool = False) -> str:
    if role in ROLE_TITLES:
        return ROLE_TITLES[role]
    if role != "SI":
        raise ValueError(f"unsupported attachment role: {role}")
    if data_si:
        if not isinstance(si_number, int) or si_number < 1:
            raise ValueError("data SI requires a positive SI number")
        return f"SI-Data-{si_number}"
    if si_number is None:
        return "SI"
    if si_number < 1:
        raise ValueError("SI number must be positive")
    return f"SI-{si_number}"


def data(item: dict[str, Any]) -> dict[str, Any]:
    value = item.get("data")
    return value if isinstance(value, dict) else item


def key(item: dict[str, Any]) -> str:
    return str(item.get("key") or data(item).get("key") or "").strip()


def validate_archive(parent: dict[str, Any], children: list[dict[str, Any]], spec: dict[str, Any], *,
                     workspace_root: Path | None = None, allowed_roots: tuple[Path, ...] = ()) -> dict[str, Any]:
    parent_key = key(parent)
    parent_data = data(parent)
    failures: list[str] = []
    expected_doi = str(spec.get("doi") or "").strip().casefold().removeprefix("https://doi.org/")
    actual_doi = str(parent_data.get("DOI") or "").strip().casefold().removeprefix("https://doi.org/")
    if expected_doi and expected_doi != actual_doi:
        failures.append("parent DOI mismatch")
    if not parent_key or parent_key != spec.get("parent_key"):
        failures.append("parent key mismatch")
    if parent_data.get("itemType") in {"attachment", "note", "annotation"}:
        failures.append("parent is not bibliographic")
    rows = spec.get("attachments")
    if not isinstance(rows, list) or not rows:
        failures.append("attachment specification missing")
        rows = []
    seen_roles: set[tuple[str, int | None, bool]] = set()
    seen_keys: set[str] = set()
    matched: dict[str, str] = {}
    actual_by_key = {key(child): child for child in children}
    local_bindings = {}
    for row in rows:
        if not isinstance(row, dict):
            failures.append("invalid attachment specification")
            continue
        role = row.get("role")
        number = row.get("si_number")
        data_si = row.get("data_si") is True
        try:
            title = role_title(role, number, data_si=data_si)
        except (ValueError, TypeError) as exc:
            failures.append(str(exc))
            continue
        role_id = (role, number, data_si)
        if role_id in seen_roles:
            failures.append(f"duplicate expected role: {role_id}")
        seen_roles.add(role_id)
        attachment_key = str(row.get("key") or "").strip()
        if not attachment_key or attachment_key in seen_keys:
            failures.append(f"missing or duplicate attachment key: {title}")
        seen_keys.add(attachment_key)
        item = actual_by_key.get(attachment_key)
        if item is None:
            failures.append(f"missing child: {title}")
            continue
        child = data(item)
        expected_mime = str(row.get("mime") or ("application/pdf" if not data_si else "")).strip()
        if child.get("parentItem") != parent_key:
            failures.append(f"wrong parent: {title}")
        if child.get("itemType") != "attachment" or child.get("title") != title:
            failures.append(f"wrong role/title: {title}")
        if expected_mime and child.get("contentType") != expected_mime:
            failures.append(f"wrong MIME: {title}")
        filename = str(child.get("filename") or "")
        if not filename or not str(child.get("md5") or ""):
            failures.append(f"file not fully uploaded: {title}")
        if expected_mime == "application/pdf" and not filename.casefold().endswith(".pdf"):
            failures.append(f"not a PDF filename: {title}")
        matched[title] = attachment_key
        if spec.get("contract_version") == "1.5.0":
            try:
                if workspace_root is None:
                    raise ValueError("explicit workspace root required for local attachment binding")
                path = resolve_path(row.get("local_path", ""), workspace_root, allowed_roots=allowed_roots)
                actual = fingerprint(path)
                if not same_content(actual, row.get("local", {})):
                    raise ValueError("local attachment differs from upload specification")
                local_bindings[attachment_key] = {"local": actual, "api_md5": child.get("md5")}
            except (OSError, ValueError) as exc:
                failures.append(f"{title}: {exc}")
    for required in ("MAIN", "A", "B"):
        if (required, None, False) not in seen_roles:
            failures.append(f"missing required role: {required}")
    if not any(role == "SI" for role, _, _ in seen_roles) and spec.get("si_required"):
        failures.append("required SI missing")
    for row in rows:
        if isinstance(row, dict):
            try:
                title = role_title(row["role"], row.get("si_number"), data_si=row.get("data_si") is True)
            except (KeyError, ValueError, TypeError):
                continue
            same_title = [child for child in children if data(child).get("title") == title]
            if len(same_title) > 1:
                failures.append(f"duplicate Zotero title: {title}")
    result = {"passed": not failures, "failures": sorted(set(failures)), "attachment_keys": matched, "parent_key": parent_key}
    if spec.get("contract_version") == "1.5.0":
        result.update({k: spec.get(k) for k in ("paper_id", "workflow_id", "contract_version", "source_fingerprints", "collection_key")})
        if not all(result.get(k) for k in ("paper_id", "workflow_id", "source_fingerprints", "collection_key")):
            result["passed"] = False
            result["failures"].append("workflow/source/collection identity missing")
        if spec.get("collection_key") not in parent_data.get("collections", []):
            result["passed"] = False
            result["failures"].append("parent collection mismatch")
        result["content_bindings"] = local_bindings
    return result
