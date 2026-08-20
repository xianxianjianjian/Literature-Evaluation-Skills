#!/usr/bin/env python3
"""Safe Zotero Desktop Local API read bridge with Phase 1 write stubs.

Read operations use Zotero Desktop's local Web API v3 at 127.0.0.1:23119.
Local reads require no API key. Phase 1 deliberately leaves create/attach as
explicit NOT_IMPLEMENTED_IN_PHASE_1 operations rather than pretending writes
succeeded.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


PHASE = "PHASE_1"
NOT_IMPLEMENTED = "NOT_IMPLEMENTED_IN_PHASE_1"
DEFAULT_BASE_URL = "http://127.0.0.1:23119/api"
DEFAULT_TIMEOUT = 3.0


class ZoteroBridgeError(RuntimeError):
    """Raised when the local Zotero API cannot satisfy a read request."""


def emit(payload: Any) -> None:
    """Print a machine-readable response."""
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def normalize_doi(value: str) -> str:
    """Normalize DOI strings for exact comparison."""
    normalized = value.strip().casefold()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
            break
    return normalized


def api_get(base_url: str, path: str, *, query: dict[str, str] | None = None, timeout: float) -> Any:
    """GET and decode one Zotero local API JSON response."""
    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    if query:
        url += "?" + urlencode(query)
    request = Request(
        url,
        headers={"Accept": "application/json", "Zotero-API-Version": "3"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ZoteroBridgeError(f"Zotero API HTTP {exc.code} for {url}: {detail[:300]}") from exc
    except URLError as exc:
        raise ZoteroBridgeError(
            f"Cannot reach Zotero Local API at {base_url}. Is Zotero running and the local API enabled? {exc.reason}"
        ) from exc
    except OSError as exc:
        raise ZoteroBridgeError(f"Zotero Local API request failed: {exc}") from exc
    if not body.strip():
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ZoteroBridgeError(f"Zotero API returned non-JSON content for {url}.") from exc


def item_data(item: dict[str, Any]) -> dict[str, Any]:
    """Return the Web API data object from a Zotero item."""
    data = item.get("data")
    return data if isinstance(data, dict) else {}


def is_parent_bibliographic_item(item: dict[str, Any]) -> bool:
    """Exclude obvious children/attachments when resolving a bibliographic parent."""
    data = item_data(item)
    if data.get("parentItem"):
        return False
    return data.get("itemType") not in {"attachment", "note", "annotation"}


def command_status(args: argparse.Namespace) -> int:
    """Probe Zotero Desktop's local API readiness."""
    try:
        payload = api_get(args.base_url, "/", timeout=args.timeout)
    except ZoteroBridgeError as exc:
        emit(
            {
                "schema_version": 1,
                "phase": PHASE,
                "bridge_status": "UNAVAILABLE",
                "implemented_read_interfaces": ["status", "find", "children", "verify"],
                "declared_write_interfaces": ["create", "attach"],
                "write_enabled": False,
                "error": str(exc),
            }
        )
        return 2
    emit(
        {
            "schema_version": 1,
            "phase": PHASE,
            "bridge_status": "AVAILABLE",
            "implemented_read_interfaces": ["status", "find", "children", "verify"],
            "declared_write_interfaces": ["create", "attach"],
            "write_enabled": False,
            "api_root": payload,
        }
    )
    return 0


def command_find(args: argparse.Namespace) -> int:
    """Find likely bibliographic parent items by DOI or title."""
    query_text = args.doi if args.doi else args.title
    items = api_get(
        args.base_url,
        "/users/0/items",
        query={"q": query_text, "qmode": "everything", "limit": str(args.limit)},
        timeout=args.timeout,
    )
    if not isinstance(items, list):
        raise ZoteroBridgeError("Unexpected Zotero search response; expected a list of items.")
    parents = [item for item in items if isinstance(item, dict) and is_parent_bibliographic_item(item)]

    if args.doi:
        target = normalize_doi(args.doi)
        matches = [
            item for item in parents
            if normalize_doi(str(item_data(item).get("DOI", ""))) == target
        ]
    else:
        target_title = args.title.strip().casefold()
        exact = [
            item for item in parents
            if str(item_data(item).get("title", "")).strip().casefold() == target_title
        ]
        matches = exact if exact else parents

    emit(
        {
            "schema_version": 1,
            "query": {"doi": args.doi, "title": args.title},
            "count": len(matches),
            "matches": matches,
        }
    )
    return 0 if matches else 4


def command_children(args: argparse.Namespace) -> int:
    """List child items/attachments for one parent item key."""
    key = quote(args.parent_key.strip(), safe="")
    children = api_get(
        args.base_url,
        f"/users/0/items/{key}/children",
        timeout=args.timeout,
    )
    if not isinstance(children, list):
        raise ZoteroBridgeError("Unexpected Zotero children response; expected a list.")
    emit({"schema_version": 1, "parent_key": args.parent_key, "count": len(children), "children": children})
    return 0


def command_verify(args: argparse.Namespace) -> int:
    """Verify that one Zotero item or attachment key exists and return its record."""
    key = quote(args.item_key.strip(), safe="")
    item = api_get(
        args.base_url,
        f"/users/0/items/{key}",
        timeout=args.timeout,
    )
    if not isinstance(item, dict):
        raise ZoteroBridgeError("Unexpected Zotero item response; expected an object.")
    emit({"schema_version": 1, "item_key": args.item_key, "verified": True, "item": item})
    return 0


def command_not_implemented(args: argparse.Namespace) -> int:
    """Return an explicit Phase 1 boundary for unavailable write operations."""
    parameters = {
        key: value
        for key, value in vars(args).items()
        if key not in {"handler", "command", "base_url", "timeout"} and value is not None
    }
    emit(
        {
            "schema_version": 1,
            "phase": PHASE,
            "command": args.command,
            "status": NOT_IMPLEMENTED,
            "parameters": parameters,
        }
    )
    return 3


def build_parser() -> argparse.ArgumentParser:
    """Build the stable Phase 1 command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Zotero local API base URL.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Local API timeout in seconds.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Probe local Zotero API readiness.")
    status.set_defaults(handler=command_status)

    find = subparsers.add_parser("find", help="Find a bibliographic parent item.")
    identity = find.add_mutually_exclusive_group(required=True)
    identity.add_argument("--doi")
    identity.add_argument("--title")
    find.add_argument("--limit", type=int, default=25)
    find.set_defaults(handler=command_find)

    children = subparsers.add_parser("children", help="List child items for a parent key.")
    children.add_argument("--parent-key", required=True)
    children.set_defaults(handler=command_children)

    verify = subparsers.add_parser("verify", help="Verify an item or attachment key.")
    verify.add_argument("--item-key", required=True)
    verify.set_defaults(handler=command_verify)

    create = subparsers.add_parser(
        "create", help="Create a parent item (not implemented in Phase 1)."
    )
    create.add_argument("--metadata", required=True, help="Path to metadata payload.")
    create.set_defaults(handler=command_not_implemented)

    attach = subparsers.add_parser(
        "attach", help="Attach a file (not implemented in Phase 1)."
    )
    attach.add_argument("--parent-key", required=True)
    attach.add_argument("--file", required=True)
    attach.add_argument("--name", required=True)
    attach.set_defaults(handler=command_not_implemented)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Zotero bridge CLI."""
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
