#!/usr/bin/env python3
"""Expose a stable, non-deceptive Phase 1 Zotero bridge interface.

Phase 1 defines read and write command contracts but does not perform Zotero
API operations. Unsupported commands return ``NOT_IMPLEMENTED_IN_PHASE_1`` and
a non-zero status instead of pretending that a lookup or mutation succeeded.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


PHASE = "PHASE_1"
NOT_IMPLEMENTED = "NOT_IMPLEMENTED_IN_PHASE_1"


def emit(payload: dict[str, Any]) -> None:
    """Print a machine-readable response."""
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def command_status(args: argparse.Namespace) -> int:
    """Report the bridge capability state without probing credentials."""
    emit(
        {
            "schema_version": 1,
            "phase": PHASE,
            "bridge_status": "INTERFACE_ONLY",
            "implemented": ["status"],
            "declared_read_interfaces": ["find", "children", "verify"],
            "declared_write_interfaces": ["create", "attach"],
            "write_enabled": False,
            "message": NOT_IMPLEMENTED,
        }
    )
    return 0


def command_not_implemented(args: argparse.Namespace) -> int:
    """Return an explicit Phase 1 boundary for unavailable operations."""
    parameters = {
        key: value
        for key, value in vars(args).items()
        if key not in {"handler", "command"} and value is not None
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
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Show bridge capability status.")
    status.set_defaults(handler=command_status)

    find = subparsers.add_parser("find", help="Find a parent item (Phase 1 interface).")
    identity = find.add_mutually_exclusive_group(required=True)
    identity.add_argument("--doi")
    identity.add_argument("--title")
    find.set_defaults(handler=command_not_implemented)

    children = subparsers.add_parser(
        "children", help="List child attachments (Phase 1 interface)."
    )
    children.add_argument("--parent-key", required=True)
    children.set_defaults(handler=command_not_implemented)

    verify = subparsers.add_parser(
        "verify", help="Verify an item or attachment (Phase 1 interface)."
    )
    verify.add_argument("--item-key", required=True)
    verify.set_defaults(handler=command_not_implemented)

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
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
