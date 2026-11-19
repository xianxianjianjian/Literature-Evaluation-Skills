#!/usr/bin/env python3
"""Expose truthful V1 Zotero Desktop integration capabilities.

Reads use Zotero Desktop's Local API v3 under ``http://127.0.0.1:23119/api``.
Bibliographic-parent creation retains the verified Connector ``/saveItems``
route from Phase 7. On Zotero 10+, durable local-file attachment to an existing
parent uses the Local API write authorization and documented three-phase full
file-upload flow. A write is complete only after the created/attached object is
observable through the same Zotero-Server-ID identity partition.

This helper performs mechanical identity/archive operations only; it never
makes paper-selection or academic judgments.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import hashlib
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen, url2pathname

import zotero_local_archive as local_archive
import zotero_local_write as local_write
import zotero_attachment_contract as attachment_contract
from artifact_binding import fingerprint, same_content, resolve_path

SCHEMA_VERSION = 1
CAPABILITY_SET = "V1_ZOTERO_LOCAL_ARCHIVE"
DEFAULT_API_BASE_URL = "http://127.0.0.1:23119/api"
DEFAULT_CONNECTOR_BASE_URL = "http://127.0.0.1:23119"
DEFAULT_TIMEOUT = 3.0
DEFAULT_LIBRARY_PREFIX = "users/0"
DEFAULT_USER_AGENT = "Literature-Evaluation-Skills/1.0"
READ_INTERFACES = ["status", "selected-target", "find", "children", "verify"]
WRITE_INTERFACES = ["create", "attach"]
CREATE_ROUTE = "/connector/saveItems"
SELECTED_TARGET_ROUTE = "/connector/getSelectedCollection"
LOCAL_ATTACH_ROUTE = "ZOTERO_10_LOCAL_API_FULL_UPLOAD"
CONFIRMATION_REQUIRED = "WRITE_CONFIRMATION_REQUIRED"


from zotero_role_archive_ops import (
    ZoteroBridgeError,
    _parent_children,
    _parent_in_collection,
    build_connector_item,
    command_attach_role,
    command_ingest_pdf,
    command_normalize_titles,
    command_verify_archive,
    create_preview,
    emit,
    is_parent_bibliographic_item,
    item_data,
    item_key,
    load_metadata,
    normalize_doi,
    normalized_creators,
    pdf_ingest_preview,
)


def request_http(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float,
) -> tuple[int, str, dict[str, str]]:
    request_headers = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        request_headers.update(headers)
    request = Request(url, data=data, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            status = int(getattr(response, "status", response.getcode()))
            body = response.read().decode("utf-8", errors="replace")
            response_headers = {key: value for key, value in response.headers.items()}
            return status, body, response_headers
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ZoteroBridgeError(
            f"Zotero HTTP {exc.code} for {url}: {detail[:300]}"
        ) from exc
    except URLError as exc:
        raise ZoteroBridgeError(
            f"Cannot reach Zotero Desktop endpoint {url}: {exc.reason}"
        ) from exc
    except OSError as exc:
        raise ZoteroBridgeError(f"Zotero request failed for {url}: {exc}") from exc


def request_text(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float,
) -> str:
    _, body, _ = request_http(
        url,
        method=method,
        data=data,
        headers=headers,
        timeout=timeout,
    )
    return body


def api_get(
    base_url: str,
    path: str,
    *,
    query: dict[str, str] | None = None,
    timeout: float,
) -> Any:
    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    if query:
        url += "?" + urlencode(query)
    body = request_text(
        url,
        headers={"Accept": "application/json", "Zotero-API-Version": "3"},
        timeout=timeout,
    )
    if not body.strip():
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ZoteroBridgeError(
            f"Zotero Local API returned non-JSON content for {url}."
        ) from exc


def connector_post_json(
    base_url: str,
    path: str,
    payload: dict[str, Any],
    *,
    timeout: float,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    status, body, _ = request_http(
        url,
        method="POST",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Zotero-Connector-API-Version": "3",
        },
        timeout=timeout,
    )
    if status != 200:
        raise ZoteroBridgeError(
            f"Connector route {path} returned unexpected HTTP {status}: {body[:300]}"
        )
    try:
        value = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ZoteroBridgeError(
            f"Connector route {path} returned invalid JSON."
        ) from exc
    if not isinstance(value, dict):
        raise ZoteroBridgeError(f"Connector route {path} returned a non-object payload.")
    return value



def selected_target_payload(
    *,
    connector_base_url: str,
    timeout: float,
    ensure_writable: bool,
) -> dict[str, Any]:
    raw = connector_post_json(
        connector_base_url,
        SELECTED_TARGET_ROUTE,
        {"switchToReadableLibrary": bool(ensure_writable)},
        timeout=timeout,
    )
    target = {
        "library_id": raw.get("libraryID"),
        "library_name": raw.get("libraryName"),
        "library_editable": bool(raw.get("libraryEditable")),
        "files_editable": bool(raw.get("filesEditable")),
        "editable": bool(raw.get("editable")),
        "collection_id": raw.get("id"),
        "collection_name": raw.get("name"),
    }
    if ensure_writable and not target["editable"]:
        raise ZoteroBridgeError(
            "Connector did not resolve an editable save target for parent creation."
        )
    return target


def status_payload(
    *,
    api_available: bool,
    connector_available: bool,
    local_write_available: bool = False,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    create_enabled = bool(api_available and connector_available)
    return {
        "schema_version": SCHEMA_VERSION,
        "capability_set": CAPABILITY_SET,
        "local_api": {
            "available": api_available,
            "mode": (
                "READ_WRITE_ZOTERO_10_PLUS"
                if local_write_available
                else "READ_ONLY_OR_WRITE_UNVERIFIED"
            ),
            "implemented_reads": READ_INTERFACES,
            "durable_attachment_write_available": local_write_available,
        },
        "connector": {
            "available": connector_available,
            "mode": "WRITE_SERVER",
        },
        "writes": {
            "declared": WRITE_INTERFACES,
            "implemented": ["create", "attach"],
            "operations": {
                "create": {
                    "implemented": True,
                    "enabled": create_enabled,
                    "route": CREATE_ROUTE,
                    "target_resolution": SELECTED_TARGET_ROUTE,
                    "verification": "POST_WRITE_LOCAL_API_IDENTITY_CHECK",
                },
                "attach": {
                    "implemented": True,
                    "enabled": local_write_available,
                    "route": LOCAL_ATTACH_ROUTE,
                    "verification": "SERVER_BOUND_PARENT_FILENAME_MD5_CHECK",
                    "requires_user_authorization": True,
                },
            },
        },
        "errors": errors or [],
    }


def probe_api(args: argparse.Namespace) -> tuple[bool, Any | None, str | None]:
    try:
        # The API root is an HTML landing page on supported Zotero versions.
        # Probe the same library route used for parent identity verification.
        items = api_get(
            args.api_base_url, "/users/0/items",
            query={"limit": "1"}, timeout=args.timeout,
        )
        if not isinstance(items, list):
            raise ZoteroBridgeError("Zotero library probe expected a JSON item list.")
        return True, {"verified_endpoint": "/users/0/items"}, None
    except ZoteroBridgeError as exc:
        return False, None, str(exc)


def probe_local_write(args: argparse.Namespace) -> tuple[bool, dict[str, str] | None, str | None]:
    try:
        info = local_write.discover_server(args.api_base_url, timeout=args.timeout)
        return True, info, None
    except local_write.LocalAPIError as exc:
        return False, None, str(exc)


def probe_connector(args: argparse.Namespace) -> tuple[bool, str | None, str | None]:
    url = args.connector_base_url.rstrip("/") + "/connector/ping"
    try:
        body = request_text(url, timeout=args.timeout)
        return True, body.strip() or None, None
    except ZoteroBridgeError as exc:
        return False, None, str(exc)


def find_parent_matches(
    *,
    api_base_url: str,
    timeout: float,
    doi: str | None = None,
    title: str | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    if not doi and not title:
        raise ZoteroBridgeError("Identity lookup requires DOI or title.")
    query_text = doi if doi else title
    items = api_get(
        api_base_url,
        "/users/0/items",
        query={"q": str(query_text), "qmode": "everything", "limit": str(limit)},
        timeout=timeout,
    )
    if not isinstance(items, list):
        raise ZoteroBridgeError(
            "Unexpected Zotero search response; expected a list of items."
        )
    parents = [
        item
        for item in items
        if isinstance(item, dict) and is_parent_bibliographic_item(item)
    ]
    if doi:
        target = normalize_doi(doi)
        return [
            item
            for item in parents
            if normalize_doi(str(item_data(item).get("DOI", ""))) == target
        ]
    target_title = str(title).strip().casefold()
    return [
        item
        for item in parents
        if str(item_data(item).get("title", "")).strip().casefold() == target_title
    ]


def command_status(args: argparse.Namespace) -> int:
    api_ok, api_root, api_error = probe_api(args)
    local_write_ok, local_write_info, local_write_error = probe_local_write(args)
    connector_ok, connector_reply, connector_error = probe_connector(args)
    errors = [
        value
        for value in (api_error, local_write_error, connector_error)
        if value
    ]
    payload = status_payload(
        api_available=api_ok,
        connector_available=connector_ok,
        local_write_available=local_write_ok,
        errors=errors,
    )
    payload["api_root"] = api_root
    payload["local_write"] = {
        "available": local_write_ok,
        "api_version": local_write_info.get("api_version") if local_write_info else None,
        "server_identity_verified": bool(local_write_info and local_write_info.get("server_id")),
    }
    payload["connector_ping_reply"] = connector_reply
    return_code = 0 if api_ok else 2
    emit(payload)
    return return_code


def command_connector_status(args: argparse.Namespace) -> int:
    ok, reply, error = probe_connector(args)
    emit(
        {
            "schema_version": SCHEMA_VERSION,
            "connector_available": ok,
            "connector_base_url": args.connector_base_url,
            "ping_reply": reply,
            "connector_write_adapter": {"create": True, "generic_attach": False},
            "note": "Durable existing-parent attach uses Zotero 10+ Local API, not Connector saveAttachment.",
            "reason": None if ok else error,
        }
    )
    return 0 if ok else 2


def command_selected_target(args: argparse.Namespace) -> int:
    target = selected_target_payload(
        connector_base_url=args.connector_base_url,
        timeout=args.timeout,
        ensure_writable=args.writable,
    )
    emit(
        {
            "schema_version": SCHEMA_VERSION,
            "selected_target": target,
            "writable_resolution_requested": args.writable,
        }
    )
    return 0


def command_find(args: argparse.Namespace) -> int:
    matches = find_parent_matches(
        api_base_url=args.api_base_url,
        timeout=args.timeout,
        doi=args.doi,
        title=args.title,
        limit=args.limit,
    )
    emit(
        {
            "schema_version": SCHEMA_VERSION,
            "query": {"doi": args.doi, "title": args.title},
            "count": len(matches),
            "matches": matches,
        }
    )
    return 0 if matches else 4


def command_children(args: argparse.Namespace) -> int:
    prefix = getattr(args, "library_prefix", DEFAULT_LIBRARY_PREFIX).strip().strip("/")
    key = quote(args.parent_key.strip(), safe="")
    children = api_get(
        args.api_base_url,
        f"/{prefix}/items/{key}/children",
        timeout=args.timeout,
    )
    if not isinstance(children, list):
        raise ZoteroBridgeError(
            "Unexpected Zotero children response; expected a list."
        )
    emit(
        {
            "schema_version": SCHEMA_VERSION,
            "library_prefix": prefix,
            "parent_key": args.parent_key,
            "count": len(children),
            "children": children,
        }
    )
    return 0


def command_verify(args: argparse.Namespace) -> int:
    prefix = getattr(args, "library_prefix", DEFAULT_LIBRARY_PREFIX).strip().strip("/")
    key = quote(args.item_key.strip(), safe="")
    item = api_get(
        args.api_base_url,
        f"/{prefix}/items/{key}",
        timeout=args.timeout,
    )
    if not isinstance(item, dict):
        raise ZoteroBridgeError(
            "Unexpected Zotero item response; expected an object."
        )
    emit(
        {
            "schema_version": SCHEMA_VERSION,
            "library_prefix": prefix,
            "item_key": args.item_key,
            "verified": True,
            "item": item,
        }
    )
    return 0



def verify_created_parent(
    *,
    api_base_url: str,
    timeout: float,
    doi: str | None,
    title: str,
    attempts: int = 5,
    delay: float = 0.2,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for attempt in range(attempts):
        matches = find_parent_matches(
            api_base_url=api_base_url,
            timeout=timeout,
            doi=doi or None,
            title=None if doi else title,
        )
        if matches:
            return matches
        if attempt + 1 < attempts:
            time.sleep(delay)
    return matches


def command_create(args: argparse.Namespace) -> int:
    metadata = load_metadata(args.metadata)
    payload = create_preview(metadata)
    connector_item = payload["items"][0]
    doi = str(connector_item.get("DOI", "")).strip()
    title = str(connector_item["title"]).strip()

    if not args.yes:
        emit(
            {
                "schema_version": SCHEMA_VERSION,
                "command": "create",
                "status": CONFIRMATION_REQUIRED,
                "would_post_to": CREATE_ROUTE,
                "payload": payload,
                "note": (
                    "No Zotero write or target-resolution request was performed. "
                    "Use selected-target to inspect the destination, then re-run with --yes after authorization."
                ),
            }
        )
        return 3

    api_ok, _, api_error = probe_api(args)
    connector_ok, _, connector_error = probe_connector(args)
    if not api_ok:
        raise ZoteroBridgeError(
            "Refusing parent write because Local API verification is unavailable: "
            f"{api_error}"
        )
    if not connector_ok:
        raise ZoteroBridgeError(
            f"Refusing parent write because Connector server is unavailable: {connector_error}"
        )

    save_target = selected_target_payload(
        connector_base_url=args.connector_base_url,
        timeout=args.timeout,
        ensure_writable=True,
    )

    duplicates = find_parent_matches(
        api_base_url=args.api_base_url,
        timeout=args.timeout,
        doi=doi or None,
        title=None if doi else title,
    )
    if duplicates:
        emit(
            {
                "schema_version": SCHEMA_VERSION,
                "command": "create",
                "status": "DUPLICATE_PARENT_FOUND",
                "selected_target": save_target,
                "matches": duplicates,
                "note": "No Zotero write was performed.",
            }
        )
        return 6

    url = args.connector_base_url.rstrip("/") + CREATE_ROUTE
    status, body, _ = request_http(
        url,
        method="POST",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Zotero-Connector-API-Version": "3",
        },
        timeout=args.timeout,
    )
    if status != 201:
        raise ZoteroBridgeError(
            f"Connector create returned unexpected HTTP {status}: {body[:300]}"
        )

    matches = verify_created_parent(
        api_base_url=args.api_base_url,
        timeout=args.timeout,
        doi=doi or None,
        title=title,
    )
    if len(matches) == 1:
        key = item_key(matches[0])
        emit(
            {
                "schema_version": SCHEMA_VERSION,
                "command": "create",
                "status": "CREATED_AND_VERIFIED",
                "item_key": key,
                "selected_target": save_target,
                "identity": {"doi": doi or None, "title": title},
                "match": matches[0],
            }
        )
        return 0

    emit(
        {
            "schema_version": SCHEMA_VERSION,
            "command": "create",
            "status": (
                "WRITE_SUCCEEDED_VERIFICATION_AMBIGUOUS"
                if len(matches) > 1
                else "WRITE_SUCCEEDED_BUT_NOT_VERIFIED"
            ),
            "selected_target": save_target,
            "identity": {"doi": doi or None, "title": title},
            "matches": matches,
            "note": "Do not mark Zotero ingest COMPLETE until one parent identity is verified.",
        }
    )
    return 5


def command_attach(args: argparse.Namespace) -> int:
    try:
        descriptor = local_write.file_descriptor(args.file)
    except local_write.LocalAPIError as exc:
        raise ZoteroBridgeError(str(exc)) from exc
    public_descriptor = local_archive.public_descriptor(descriptor)

    if not args.yes:
        emit(
            {
                "schema_version": SCHEMA_VERSION,
                "command": "attach",
                "status": CONFIRMATION_REQUIRED,
                "library_prefix": args.library_prefix,
                "parent_key": args.parent_key,
                "attachment_name": args.name,
                "file": public_descriptor,
                "would_use": LOCAL_ATTACH_ROUTE,
                "note": (
                    "No Zotero probe, authorization, or write was performed. "
                    "Re-run with --yes to request Zotero Desktop write authorization."
                ),
            }
        )
        return 3

    try:
        client = local_write.LocalWriteClient.connect(
            args.api_base_url,
            timeout=args.timeout,
        )
        result = local_archive.attach_file(
            client,
            args.library_prefix,
            parent_key=args.parent_key,
            path=args.file,
            title=args.name,
        )
    except (local_write.LocalAPIError, local_archive.ArchiveError) as exc:
        raise ZoteroBridgeError(str(exc)) from exc

    payload = {
        "schema_version": SCHEMA_VERSION,
        "command": "attach",
        "library_prefix": args.library_prefix,
        "parent_key": args.parent_key,
        "attachment_name": args.name,
        "authorization_remembered": client.remembered,
        **result,
    }
    emit(payload)
    if result["status"] in {"ATTACHED_AND_VERIFIED", "ALREADY_ATTACHED_AND_VERIFIED"}:
        return 0
    if result["status"] == "ATTACHMENT_CONFLICT":
        return 6
    return 5


def command_pending_template(args: argparse.Namespace) -> int:
    record: dict[str, Any] = {
        "action": args.action,
        "paper_id": args.paper_id,
        "reason": args.reason,
    }
    if args.source_id:
        record["source_id"] = args.source_id
    if args.expected_attachment_name:
        record["expected_attachment_name"] = args.expected_attachment_name
    emit(
        {
            "schema_version": SCHEMA_VERSION,
            "pending_zotero_action": record,
            "note": "This command only prepares a manifest record; it does not modify Zotero.",
        }
    )
    return 0



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--api-base-url",
        default=DEFAULT_API_BASE_URL,
        help="Zotero Desktop Local API base URL.",
    )
    parser.add_argument(
        "--connector-base-url",
        default=DEFAULT_CONNECTOR_BASE_URL,
        help="Zotero Connector server base URL used for Phase-7 parent creation.",
    )
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT, help="Request timeout in seconds."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser(
        "status", help="Probe Local API, Zotero-10 write capability, and Connector readiness."
    )
    status.set_defaults(handler=command_status)

    connector = subparsers.add_parser(
        "connector-status", help="Probe only the Zotero Connector server."
    )
    connector.set_defaults(handler=command_connector_status)

    selected = subparsers.add_parser(
        "selected-target", help="Show the Connector library/collection save target."
    )
    selected.add_argument(
        "--writable",
        action="store_true",
        help="Resolve/switch to the writable target the Connector would use for saving.",
    )
    selected.set_defaults(handler=command_selected_target)

    find = subparsers.add_parser("find", help="Find a bibliographic parent item in My Library.")
    identity = find.add_mutually_exclusive_group(required=True)
    identity.add_argument("--doi")
    identity.add_argument("--title")
    find.add_argument("--limit", type=int, default=25)
    find.set_defaults(handler=command_find)

    children = subparsers.add_parser(
        "children", help="List child items/attachments for a parent key."
    )
    children.add_argument("--parent-key", required=True)
    children.add_argument("--library-prefix", default=DEFAULT_LIBRARY_PREFIX)
    children.set_defaults(handler=command_children)

    verify = subparsers.add_parser("verify", help="Verify one item/attachment key.")
    verify.add_argument("--item-key", required=True)
    verify.add_argument("--library-prefix", default=DEFAULT_LIBRARY_PREFIX)
    verify.set_defaults(handler=command_verify)

    create = subparsers.add_parser(
        "create",
        help="Create a bibliographic parent through /connector/saveItems and verify it via Local API.",
    )
    create.add_argument("--metadata", type=Path, required=True)
    create.add_argument(
        "--yes",
        action="store_true",
        help="Execute the Zotero write. Without --yes, only emit a preview.",
    )
    create.set_defaults(handler=command_create)

    attach = subparsers.add_parser(
        "attach",
        help="Attach a local file to an existing parent using Zotero 10+ Local API full upload.",
    )
    attach.add_argument("--parent-key", required=True)
    attach.add_argument("--file", type=Path, required=True)
    attach.add_argument("--name", required=True)
    attach.add_argument("--library-prefix", default=DEFAULT_LIBRARY_PREFIX)
    attach.add_argument(
        "--yes",
        action="store_true",
        help="Request Zotero Desktop authorization and execute the write. Without --yes, preview only.",
    )
    attach.set_defaults(handler=command_attach)

    attach_role = subparsers.add_parser("attach-role", help="Attach a file with its v1.5 role title.")
    attach_role.add_argument("--parent-key", required=True)
    attach_role.add_argument("--file", type=Path, required=True)
    attach_role.add_argument("--role", choices=("MAIN", "SI", "A", "B", "VIDEO", "DATA"), required=True)
    attach_role.add_argument("--si-number", type=int)
    attach_role.add_argument("--qc-report", type=Path)
    attach_role.add_argument("--data-si", action="store_true")
    attach_role.add_argument("--library-prefix", default=DEFAULT_LIBRARY_PREFIX)
    attach_role.add_argument("--yes", action="store_true")
    attach_role.set_defaults(handler=command_attach_role)

    archive_verify = subparsers.add_parser("verify-archive", help="Verify parent and all role attachments.")
    archive_verify.add_argument("--parent-key", required=True)
    archive_verify.add_argument("--spec", type=Path, required=True)
    archive_verify.add_argument("--workspace-root", type=Path)
    archive_verify.add_argument("--allow-external-root", type=Path, action="append", default=[])
    archive_verify.add_argument("--report", type=Path)
    archive_verify.add_argument("--library-prefix", default=DEFAULT_LIBRARY_PREFIX)
    archive_verify.set_defaults(handler=command_verify_archive)

    normalize = subparsers.add_parser("normalize-titles", help="Preview or apply title-only migration.")
    normalize.add_argument("--parent-key", required=True)
    normalize.add_argument("--spec", type=Path, required=True)
    normalize.add_argument("--report", type=Path)
    normalize.add_argument("--library-prefix", default=DEFAULT_LIBRARY_PREFIX)
    normalize.add_argument("--yes", action="store_true")
    normalize.set_defaults(handler=command_normalize_titles)

    ingest = subparsers.add_parser(
        "ingest-pdf",
        help="Plan and verify the default PDF-first Zotero recognition workflow.",
    )
    ingest.add_argument("--pdf", type=Path, required=True)
    ingest.add_argument("--metadata", type=Path, required=True)
    ingest.add_argument("--collection-key", required=True)
    ingest.add_argument("--recognized-parent-key")
    ingest.add_argument("--main-attachment-key", help="Confirmed Main key when parent has multiple PDFs")
    ingest.add_argument("--fallback-metadata", action="store_true")
    ingest.add_argument("--fallback-reason")
    ingest.add_argument("--yes", action="store_true")
    ingest.set_defaults(handler=command_ingest_pdf)

    pending = subparsers.add_parser(
        "pending", help="Prepare a pending_zotero_actions record without writing Zotero."
    )
    pending.add_argument("--action", required=True)
    pending.add_argument("--paper-id", required=True)
    pending.add_argument("--reason", required=True)
    pending.add_argument("--source-id")
    pending.add_argument("--expected-attachment-name")
    pending.set_defaults(handler=command_pending_template)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.exit(2, "error: --timeout must be positive\n")
    if getattr(args, "limit", 1) <= 0:
        parser.exit(2, "error: --limit must be positive\n")
    try:
        return args.handler(args)
    except ZoteroBridgeError as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())
