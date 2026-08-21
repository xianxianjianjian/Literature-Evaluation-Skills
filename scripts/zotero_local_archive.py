#!/usr/bin/env python3
"""Resumable archive operations built on Zotero 10+ Local API primitives.

This module contains only deterministic archive mechanics. It never decides
which paper/source should be selected and never overwrites a conflicting child
attachment silently.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

import zotero_local_write as local


class ArchiveError(RuntimeError):
    """Raised when a durable Zotero archive operation cannot proceed safely."""


def public_descriptor(descriptor: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON-safe descriptor without leaking opaque Python objects."""
    return {
        key: str(value) if isinstance(value, Path) else value
        for key, value in descriptor.items()
    }


def optional_text(value: Any) -> str:
    """Normalize Zotero null/empty optional string fields to one representation."""
    return "" if value is None else str(value)


def server_bound_get(
    client: local.LocalWriteClient,
    path: str,
) -> Any:
    """Read from the same Zotero database identified when the client connected."""
    url = client.api_base_url.rstrip("/") + "/" + path.lstrip("/")
    status, body, _ = local.http_result(
        url,
        headers={
            "Accept": "application/json",
            "Zotero-API-Version": "3",
            "Zotero-Server-ID": client.server_id,
        },
        timeout=client.timeout,
    )
    if status == 412:
        raise ArchiveError(
            "Zotero-Server-ID changed during archive operation; stop and reconnect before retrying."
        )
    if status != 200:
        raise ArchiveError(
            f"Local API GET {path} returned HTTP {status}: {local.decode_body(body)[:300]}"
        )
    try:
        return json.loads(local.decode_body(body))
    except json.JSONDecodeError as exc:
        raise ArchiveError(f"Local API GET {path} returned invalid JSON.") from exc


def item_data(item: dict[str, Any]) -> dict[str, Any]:
    data = item.get("data")
    return data if isinstance(data, dict) else {}


def item_key(item: dict[str, Any]) -> str | None:
    key = item.get("key")
    if isinstance(key, str) and key.strip():
        return key.strip()
    data = item_data(item)
    key = data.get("key")
    return key.strip() if isinstance(key, str) and key.strip() else None


def read_parent(
    client: local.LocalWriteClient,
    library_prefix: str,
    parent_key: str,
) -> dict[str, Any]:
    prefix = local.normalize_library_prefix(library_prefix)
    key = quote(parent_key.strip(), safe="")
    value = server_bound_get(client, f"/{prefix}/items/{key}")
    if not isinstance(value, dict):
        raise ArchiveError("Parent lookup returned a non-object payload.")
    data = item_data(value)
    if data.get("parentItem") or data.get("itemType") in {"attachment", "note", "annotation"}:
        raise ArchiveError(f"{parent_key} is not a top-level bibliographic parent item.")
    return value


def read_children(
    client: local.LocalWriteClient,
    library_prefix: str,
    parent_key: str,
) -> list[dict[str, Any]]:
    prefix = local.normalize_library_prefix(library_prefix)
    key = quote(parent_key.strip(), safe="")
    value = server_bound_get(client, f"/{prefix}/items/{key}/children")
    if not isinstance(value, list):
        raise ArchiveError("Parent children lookup returned a non-list payload.")
    return [item for item in value if isinstance(item, dict)]


def create_attachment_child(
    client: local.LocalWriteClient,
    library_prefix: str,
    *,
    parent_key: str,
    title: str,
    descriptor: dict[str, Any],
) -> str:
    """Create a child from the Zotero v3 imported-file attachment template shape."""
    parent_key = parent_key.strip()
    title = title.strip()
    if not parent_key or not title:
        raise ArchiveError("parent_key and attachment title are required.")
    item = {
        "itemType": "attachment",
        "parentItem": parent_key,
        "linkMode": "imported_file",
        "title": title,
        "accessDate": "",
        "url": "",
        "note": "",
        "tags": [],
        "relations": {},
        "contentType": str(descriptor["content_type"]),
        "charset": "",
        "filename": str(descriptor["filename"]),
        "md5": None,
        "mtime": None,
    }
    try:
        return local.create_item(client, library_prefix, item)
    except local.LocalAPIError as exc:
        raise ArchiveError(str(exc)) from exc


def attachment_identity(item: dict[str, Any]) -> dict[str, Any]:
    data = item_data(item)
    return {
        "key": item_key(item),
        "title": optional_text(data.get("title")),
        "item_type": data.get("itemType"),
        "parent": optional_text(data.get("parentItem")),
        "link_mode": data.get("linkMode"),
        "filename": optional_text(data.get("filename")),
        "md5": optional_text(data.get("md5")).casefold(),
    }


def plan_attachment(
    children: list[dict[str, Any]],
    *,
    parent_key: str,
    title: str,
    descriptor: dict[str, Any],
) -> dict[str, Any]:
    """Choose NEW, REUSE_PARTIAL, ALREADY_VERIFIED, or CONFLICT deterministically."""
    target_title = title.strip()
    candidates = [
        attachment_identity(item)
        for item in children
        if item_data(item).get("itemType") == "attachment"
        and optional_text(item_data(item).get("title")).strip() == target_title
    ]
    if not candidates:
        return {"action": "NEW", "candidate": None}
    if len(candidates) > 1:
        return {
            "action": "CONFLICT",
            "reason": "MULTIPLE_SAME_TITLE_ATTACHMENTS",
            "candidates": candidates,
        }

    candidate = candidates[0]
    expected_md5 = str(descriptor["md5"]).casefold()
    expected_filename = str(descriptor["filename"])
    structural_ok = (
        candidate["parent"] == parent_key
        and candidate["item_type"] == "attachment"
        and candidate["link_mode"] in {"imported_file", "imported_url"}
        and bool(candidate["key"])
    )
    if not structural_ok:
        return {
            "action": "CONFLICT",
            "reason": "SAME_TITLE_CHILD_HAS_UNEXPECTED_IDENTITY",
            "candidate": candidate,
        }

    filename = candidate["filename"]
    md5 = candidate["md5"]
    if filename == expected_filename and md5 == expected_md5:
        return {"action": "ALREADY_VERIFIED", "candidate": candidate}

    # A correctly created attachment-template child already contains filename,
    # contentType, etc. before file registration. The resumable signal is an
    # empty MD5 with no conflicting filename.
    if not md5 and filename in {"", expected_filename}:
        return {"action": "REUSE_PARTIAL", "candidate": candidate}

    return {
        "action": "CONFLICT",
        "reason": "SAME_TITLE_ATTACHMENT_HAS_DIFFERENT_FILE",
        "candidate": candidate,
        "expected": {"filename": expected_filename, "md5": expected_md5},
    }


def attach_file(
    client: local.LocalWriteClient,
    library_prefix: str,
    *,
    parent_key: str,
    path: Path,
    title: str,
) -> dict[str, Any]:
    """Attach one local file to an existing parent with idempotent resume semantics."""
    descriptor = local.file_descriptor(path)
    public = public_descriptor(descriptor)
    read_parent(client, library_prefix, parent_key)
    children = read_children(client, library_prefix, parent_key)
    plan = plan_attachment(
        children,
        parent_key=parent_key,
        title=title,
        descriptor=descriptor,
    )

    if plan["action"] == "CONFLICT":
        return {
            "status": "ATTACHMENT_CONFLICT",
            "plan": plan,
            "descriptor": public,
            "attachment_key": None,
        }
    if plan["action"] == "ALREADY_VERIFIED":
        return {
            "status": "ALREADY_ATTACHED_AND_VERIFIED",
            "plan": plan,
            "descriptor": public,
            "attachment_key": plan["candidate"]["key"],
        }

    reused = plan["action"] == "REUSE_PARTIAL"
    if reused:
        attachment_key = str(plan["candidate"]["key"])
    else:
        attachment_key = create_attachment_child(
            client,
            library_prefix,
            parent_key=parent_key,
            title=title,
            descriptor=descriptor,
        )

    try:
        _, verified = local.upload_file_to_attachment(
            client,
            library_prefix,
            attachment_key,
            path,
            parent_key=parent_key,
        )
    except local.LocalAPIError as exc:
        return {
            "status": "ATTACHMENT_FILE_UPLOAD_INCOMPLETE",
            "plan": plan,
            "descriptor": public,
            "attachment_key": attachment_key,
            "reused_partial_child": reused,
            "error": str(exc),
        }

    return {
        "status": "ATTACHED_AND_VERIFIED",
        "plan": plan,
        "descriptor": public,
        "attachment_key": attachment_key,
        "reused_partial_child": reused,
        "verified_item": verified,
    }
