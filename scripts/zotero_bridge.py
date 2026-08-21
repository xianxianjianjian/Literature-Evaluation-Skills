#!/usr/bin/env python3
"""Expose truthful V1 Zotero Desktop integration capabilities.

Implemented reads use Zotero Desktop's read-only Local API v3 under
``http://127.0.0.1:23119/api``. Connector readiness can also be probed at the
shared desktop server root. Bibliographic/file writes are deliberately not
reported as supported until a verified Connector/plugin adapter exists for the
required operation.

This helper performs mechanical identity/archive operations only; it never
makes paper-selection or academic judgments.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

SCHEMA_VERSION = 1
CAPABILITY_SET = "V1_PARTIAL_ZOTERO_INTEGRATION"
UNSUPPORTED_WRITE = "WRITE_ROUTE_NOT_IMPLEMENTED_OR_VERIFIED"
DEFAULT_API_BASE_URL = "http://127.0.0.1:23119/api"
DEFAULT_CONNECTOR_BASE_URL = "http://127.0.0.1:23119"
DEFAULT_TIMEOUT = 3.0
READ_INTERFACES = ["status", "find", "children", "verify"]
WRITE_INTERFACES = ["create", "attach"]


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


def request_text(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float,
) -> str:
    request = Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
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


def item_data(item: dict[str, Any]) -> dict[str, Any]:
    data = item.get("data")
    return data if isinstance(data, dict) else {}


def is_parent_bibliographic_item(item: dict[str, Any]) -> bool:
    data = item_data(item)
    if data.get("parentItem"):
        return False
    return data.get("itemType") not in {"attachment", "note", "annotation"}


def status_payload(
    *, api_available: bool, connector_available: bool, errors: list[str] | None = None
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "capability_set": CAPABILITY_SET,
        "local_api": {
            "available": api_available,
            "mode": "READ_ONLY",
            "implemented": READ_INTERFACES,
        },
        "connector": {
            "available": connector_available,
            "mode": "WRITE_CAPABLE_SERVER_BUT_NO_VERIFIED_V1_ADAPTER",
        },
        "writes": {
            "declared": WRITE_INTERFACES,
            "implemented": [],
            "enabled": False,
            "reason": UNSUPPORTED_WRITE,
        },
        "errors": errors or [],
    }


def probe_api(args: argparse.Namespace) -> tuple[bool, Any | None, str | None]:
    try:
        root = api_get(args.api_base_url, "/", timeout=args.timeout)
        return True, root, None
    except ZoteroBridgeError as exc:
        return False, None, str(exc)


def probe_connector(args: argparse.Namespace) -> tuple[bool, str | None, str | None]:
    url = args.connector_base_url.rstrip("/") + "/connector/ping"
    try:
        body = request_text(url, timeout=args.timeout)
        return True, body.strip() or None, None
    except ZoteroBridgeError as exc:
        return False, None, str(exc)


def command_status(args: argparse.Namespace) -> int:
    api_ok, api_root, api_error = probe_api(args)
    connector_ok, connector_reply, connector_error = probe_connector(args)
    errors = [value for value in (api_error, connector_error) if value]
    payload = status_payload(
        api_available=api_ok,
        connector_available=connector_ok,
        errors=errors,
    )
    payload["api_root"] = api_root
    payload["connector_ping_reply"] = connector_reply
    emit(payload)
    return 0 if api_ok else 2


def command_connector_status(args: argparse.Namespace) -> int:
    ok, reply, error = probe_connector(args)
    emit(
        {
            "schema_version": SCHEMA_VERSION,
            "connector_available": ok,
            "connector_base_url": args.connector_base_url,
            "ping_reply": reply,
            "write_adapter_implemented": False,
            "reason": None if ok else error,
        }
    )
    return 0 if ok else 2


def command_find(args: argparse.Namespace) -> int:
    query_text = args.doi if args.doi else args.title
    items = api_get(
        args.api_base_url,
        "/users/0/items",
        query={"q": query_text, "qmode": "everything", "limit": str(args.limit)},
        timeout=args.timeout,
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
    if args.doi:
        target = normalize_doi(args.doi)
        matches = [
            item
            for item in parents
            if normalize_doi(str(item_data(item).get("DOI", ""))) == target
        ]
    else:
        target_title = args.title.strip().casefold()
        exact = [
            item
            for item in parents
            if str(item_data(item).get("title", "")).strip().casefold()
            == target_title
        ]
        matches = exact if exact else parents
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
    key = quote(args.parent_key.strip(), safe="")
    children = api_get(
        args.api_base_url,
        f"/users/0/items/{key}/children",
        timeout=args.timeout,
    )
    if not isinstance(children, list):
        raise ZoteroBridgeError(
            "Unexpected Zotero children response; expected a list."
        )
    emit(
        {
            "schema_version": SCHEMA_VERSION,
            "parent_key": args.parent_key,
            "count": len(children),
            "children": children,
        }
    )
    return 0


def command_verify(args: argparse.Namespace) -> int:
    key = quote(args.item_key.strip(), safe="")
    item = api_get(
        args.api_base_url,
        f"/users/0/items/{key}",
        timeout=args.timeout,
    )
    if not isinstance(item, dict):
        raise ZoteroBridgeError(
            "Unexpected Zotero item response; expected an object."
        )
    emit(
        {
            "schema_version": SCHEMA_VERSION,
            "item_key": args.item_key,
            "verified": True,
            "item": item,
        }
    )
    return 0


def command_write_unavailable(args: argparse.Namespace) -> int:
    parameters = {
        key: str(value) if isinstance(value, Path) else value
        for key, value in vars(args).items()
        if key
        not in {
            "handler",
            "command",
            "api_base_url",
            "connector_base_url",
            "timeout",
        }
        and value is not None
    }
    emit(
        {
            "schema_version": SCHEMA_VERSION,
            "capability_set": CAPABILITY_SET,
            "command": args.command,
            "status": UNSUPPORTED_WRITE,
            "parameters": parameters,
            "next_action": (
                "Record this operation in workflow_manifest.pending_zotero_actions "
                "or execute it through a separately verified Connector/plugin adapter."
            ),
        }
    )
    return 3


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
            "note": (
                "This command only prepares a manifest record; it does not modify Zotero."
            ),
        }
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--api-base-url",
        default=DEFAULT_API_BASE_URL,
        help="Zotero Desktop read-only Local API base URL.",
    )
    parser.add_argument(
        "--connector-base-url",
        default=DEFAULT_CONNECTOR_BASE_URL,
        help="Zotero Connector server base URL.",
    )
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT, help="Request timeout in seconds."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser(
        "status", help="Probe Local API and Connector readiness/capabilities."
    )
    status.set_defaults(handler=command_status)

    connector = subparsers.add_parser(
        "connector-status", help="Probe only the Zotero Connector server."
    )
    connector.set_defaults(handler=command_connector_status)

    find = subparsers.add_parser("find", help="Find a bibliographic parent item.")
    identity = find.add_mutually_exclusive_group(required=True)
    identity.add_argument("--doi")
    identity.add_argument("--title")
    find.add_argument("--limit", type=int, default=25)
    find.set_defaults(handler=command_find)

    children = subparsers.add_parser(
        "children", help="List child items/attachments for a parent key."
    )
    children.add_argument("--parent-key", required=True)
    children.set_defaults(handler=command_children)

    verify = subparsers.add_parser("verify", help="Verify one item/attachment key.")
    verify.add_argument("--item-key", required=True)
    verify.set_defaults(handler=command_verify)

    create = subparsers.add_parser(
        "create", help="Declared V1 parent-write interface; adapter not yet verified."
    )
    create.add_argument("--metadata", type=Path, required=True)
    create.set_defaults(handler=command_write_unavailable)

    attach = subparsers.add_parser(
        "attach", help="Declared V1 attachment-write interface; adapter not yet verified."
    )
    attach.add_argument("--parent-key", required=True)
    attach.add_argument("--file", type=Path, required=True)
    attach.add_argument("--name", required=True)
    attach.set_defaults(handler=command_write_unavailable)

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
