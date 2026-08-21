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
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import zotero_local_archive as local_archive
import zotero_local_write as local_write

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


class ZoteroBridgeError(RuntimeError):
    """Raised when Zotero cannot satisfy a requested bridge operation."""


def emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def normalize_doi(value: str) -> str:
    normalized = value.strip().casefold()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if normalized.startswith(prefix):
            return normalized[len(prefix):].strip()
    return normalized


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


def item_data(item: dict[str, Any]) -> dict[str, Any]:
    data = item.get("data")
    return data if isinstance(data, dict) else {}


def is_parent_bibliographic_item(item: dict[str, Any]) -> bool:
    data = item_data(item)
    if data.get("parentItem"):
        return False
    return data.get("itemType") not in {"attachment", "note", "annotation"}


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
        root = api_get(args.api_base_url, "/", timeout=args.timeout)
        return True, root, None
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


def load_metadata(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ZoteroBridgeError(f"Metadata file does not exist: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ZoteroBridgeError(f"Metadata file is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ZoteroBridgeError("Metadata root must be a JSON object.")
    return value


def normalized_creators(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize personal/institutional creators to Zotero translator-item fields."""
    creators = metadata.get("creators")
    if creators is None:
        creators = metadata.get("authors", [])
    if creators is None:
        return []
    if not isinstance(creators, list):
        raise ZoteroBridgeError("creators/authors must be a list of structured objects.")

    normalized: list[dict[str, Any]] = []
    for index, creator in enumerate(creators):
        if not isinstance(creator, dict):
            raise ZoteroBridgeError(
                "Author names are not parsed from free-text strings. "
                f"creators/authors[{index}] must be an object."
            )
        first = str(creator.get("firstName", "")).strip()
        last = str(creator.get("lastName", "")).strip()
        single_name = str(creator.get("name", "")).strip()
        creator_type = str(creator.get("creatorType", "author")).strip() or "author"

        if single_name and not (first or last):
            normalized.append(
                {
                    "lastName": single_name,
                    "fieldMode": 1,
                    "creatorType": creator_type,
                }
            )
            continue
        if not last:
            raise ZoteroBridgeError(
                f"creators/authors[{index}] requires lastName or a single-field name."
            )
        record: dict[str, Any] = {
            "firstName": first,
            "lastName": last,
            "creatorType": creator_type,
        }
        if creator.get("fieldMode") == 1:
            if first:
                raise ZoteroBridgeError(
                    f"creators/authors[{index}] fieldMode=1 cannot include firstName."
                )
            record.pop("firstName", None)
            record["fieldMode"] = 1
        normalized.append(record)
    return normalized


def build_connector_item(metadata: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if metadata.get("attachments"):
        raise ZoteroBridgeError(
            "Parent create does not accept attachment payloads. Use attach/pending separately."
        )
    title = str(metadata.get("title", "")).strip()
    if not title:
        raise ZoteroBridgeError("Metadata requires a non-empty title.")

    item: dict[str, Any] = {
        "itemType": str(metadata.get("itemType", "journalArticle")).strip()
        or "journalArticle",
        "title": title,
        "creators": normalized_creators(metadata),
        "attachments": [],
    }
    mapping = {
        "publicationTitle": ("publicationTitle", "journal"),
        "date": ("date", "year"),
        "volume": ("volume",),
        "issue": ("issue",),
        "pages": ("pages",),
        "url": ("url",),
        "abstractNote": ("abstractNote", "abstract"),
        "language": ("language",),
    }
    for target, sources in mapping.items():
        for source in sources:
            value = metadata.get(source)
            if value is not None and str(value).strip():
                item[target] = str(value).strip()
                break

    doi_raw = str(metadata.get("DOI", metadata.get("doi", ""))).strip()
    doi = normalize_doi(doi_raw) if doi_raw else ""
    if doi:
        item["DOI"] = doi

    source_uri = str(metadata.get("source_uri", "")).strip()
    if not source_uri:
        source_uri = str(item.get("url", "")).strip()
    if not source_uri and doi:
        source_uri = f"https://doi.org/{doi}"
    if not source_uri:
        raise ZoteroBridgeError(
            "Metadata requires source_uri, url, or DOI so Connector save provenance is explicit."
        )
    return item, source_uri


def create_preview(metadata: dict[str, Any]) -> dict[str, Any]:
    item, source_uri = build_connector_item(metadata)
    return {"items": [item], "uri": source_uri}


def item_key(item: dict[str, Any]) -> str | None:
    key = item.get("key")
    if isinstance(key, str) and key.strip():
        return key.strip()
    data = item_data(item)
    key = data.get("key")
    return key.strip() if isinstance(key, str) and key.strip() else None


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