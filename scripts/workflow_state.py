#!/usr/bin/env python3
"""Create, inspect, and update weekly workflow manifests.

Phase 1 stores machine-maintained ``.yaml`` files as JSON-compatible YAML 1.2,
which keeps the public file contract while requiring only Python's standard
library. Writes are validated and replaced atomically.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


ALLOWED_STATUSES = {
    "NOT_STARTED",
    "IN_PROGRESS",
    "WAITING_USER",
    "BLOCKED",
    "PROVISIONAL",
    "COMPLETE",
}
STAGE_NAMES = ("topic", "search", "translation", "deep_reading")
WEEK_PATTERN = re.compile(r"^\d{4}-W(?:0[1-9]|[1-4]\d|5[0-3])$")


class WorkflowStateError(ValueError):
    """Raised when a manifest or requested transition is invalid."""


def initial_manifest(week: str, workflow_id: str | None = None) -> dict[str, Any]:
    """Return a validated initial manifest for an ISO week."""
    if not WEEK_PATTERN.fullmatch(week):
        raise WorkflowStateError(
            f"Invalid week {week!r}; expected ISO week such as 2026-W34."
        )
    return {
        "schema_version": 1,
        "workflow_id": workflow_id,
        "week": week,
        "paper_id": None,
        "stages": {
            "topic": {"status": "NOT_STARTED"},
            "search": {"status": "NOT_STARTED"},
            "translation": {
                "status": "NOT_STARTED",
                "needs_update": False,
                "update_reason": [],
            },
            "deep_reading": {
                "status": "NOT_STARTED",
                "needs_update": False,
                "update_reason": [],
            },
        },
        "outputs": {
            "A": {"status": "NOT_STARTED", "zotero_attachment_key": None},
            "B": {"status": "NOT_STARTED", "zotero_attachment_key": None},
            "C": {"status": "NOT_STARTED", "git_path": None},
        },
        "pending_zotero_actions": [],
        "source_change": {"last_checked": None},
    }


def validate_manifest(data: object) -> dict[str, Any]:
    """Validate the Phase 1 manifest shape and state enums."""
    if not isinstance(data, dict):
        raise WorkflowStateError("Manifest root must be an object.")
    if data.get("schema_version") != 1:
        raise WorkflowStateError("Manifest schema_version must be 1.")
    week = data.get("week")
    if not isinstance(week, str) or not WEEK_PATTERN.fullmatch(week):
        raise WorkflowStateError("Manifest week must use YYYY-Wxx ISO format.")

    stages = data.get("stages")
    if not isinstance(stages, dict):
        raise WorkflowStateError("Manifest must contain a stages object.")
    for name in STAGE_NAMES:
        stage = stages.get(name)
        if not isinstance(stage, dict):
            raise WorkflowStateError(f"Missing stage object: {name}.")
        status = stage.get("status")
        if status not in ALLOWED_STATUSES:
            raise WorkflowStateError(
                f"Invalid status for stage {name}: {status!r}. "
                f"Allowed: {', '.join(sorted(ALLOWED_STATUSES))}."
            )
        if "needs_update" in stage and not isinstance(stage["needs_update"], bool):
            raise WorkflowStateError(f"{name}.needs_update must be true or false.")
        if "update_reason" in stage:
            reasons = stage["update_reason"]
            if not isinstance(reasons, list) or not all(
                isinstance(reason, str) and reason.strip() for reason in reasons
            ):
                raise WorkflowStateError(
                    f"{name}.update_reason must be a list of non-empty strings."
                )

    outputs = data.get("outputs")
    if not isinstance(outputs, dict):
        raise WorkflowStateError("Manifest must contain an outputs object.")
    for name in ("A", "B", "C"):
        output = outputs.get(name)
        if not isinstance(output, dict):
            raise WorkflowStateError(f"Missing output object: {name}.")
        if output.get("status") not in ALLOWED_STATUSES:
            raise WorkflowStateError(f"Invalid status for output {name}.")

    if not isinstance(data.get("pending_zotero_actions"), list):
        raise WorkflowStateError("pending_zotero_actions must be a list.")
    source_change = data.get("source_change")
    if not isinstance(source_change, dict) or "last_checked" not in source_change:
        raise WorkflowStateError("source_change.last_checked is required.")
    return data


def load_manifest(path: Path) -> dict[str, Any]:
    """Load and validate a JSON-compatible YAML manifest."""
    if not path.is_file():
        raise WorkflowStateError(f"Manifest does not exist: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowStateError(
            f"Manifest is not valid JSON-compatible YAML: {path}: {exc}"
        ) from exc
    return validate_manifest(data)


def write_manifest(path: Path, data: dict[str, Any], *, overwrite: bool = True) -> None:
    """Validate and atomically write a manifest."""
    validate_manifest(data)
    if path.exists() and not overwrite:
        raise WorkflowStateError(
            f"Refusing to overwrite existing manifest: {path}. Use --force if intended."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", delete=False, dir=path.parent
    ) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    temporary.replace(path)


def command_init(args: argparse.Namespace) -> None:
    """Create a new manifest."""
    data = initial_manifest(args.week, args.workflow_id)
    write_manifest(args.manifest, data, overwrite=args.force)
    print(f"Initialized workflow manifest: {args.manifest}")


def command_show(args: argparse.Namespace) -> None:
    """Print a validated manifest."""
    data = load_manifest(args.manifest)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def command_set_stage(args: argparse.Namespace) -> None:
    """Set one stage to an allowed state."""
    data = load_manifest(args.manifest)
    data["stages"][args.stage]["status"] = args.status
    write_manifest(args.manifest, data)
    print(f"Set {args.stage} to {args.status}.")


def command_set_needs_update(args: argparse.Namespace) -> None:
    """Mark a stage as requiring an update and append a reason."""
    reason = args.reason.strip()
    if not reason:
        raise WorkflowStateError("Update reason cannot be empty.")
    data = load_manifest(args.manifest)
    stage = data["stages"][args.stage]
    stage["needs_update"] = True
    reasons = stage.setdefault("update_reason", [])
    if reason not in reasons:
        reasons.append(reason)
    write_manifest(args.manifest, data)
    print(f"Marked {args.stage} as needing update.")


def command_clear_needs_update(args: argparse.Namespace) -> None:
    """Clear a stage's update flag and reasons."""
    data = load_manifest(args.manifest)
    stage = data["stages"][args.stage]
    stage["needs_update"] = False
    stage["update_reason"] = []
    write_manifest(args.manifest, data)
    print(f"Cleared update flag for {args.stage}.")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a workflow manifest.")
    init_parser.add_argument("--manifest", type=Path, required=True)
    init_parser.add_argument("--week", required=True)
    init_parser.add_argument("--workflow-id")
    init_parser.add_argument("--force", action="store_true")
    init_parser.set_defaults(handler=command_init)

    show_parser = subparsers.add_parser("show", help="Validate and display a manifest.")
    show_parser.add_argument("--manifest", type=Path, required=True)
    show_parser.set_defaults(handler=command_show)

    stage_parser = subparsers.add_parser("set-stage", help="Set a workflow stage status.")
    stage_parser.add_argument("--manifest", type=Path, required=True)
    stage_parser.add_argument("--stage", choices=STAGE_NAMES, required=True)
    stage_parser.add_argument("--status", choices=sorted(ALLOWED_STATUSES), required=True)
    stage_parser.set_defaults(handler=command_set_stage)

    update_parser = subparsers.add_parser(
        "set-needs-update", help="Mark a stage for source-driven update."
    )
    update_parser.add_argument("--manifest", type=Path, required=True)
    update_parser.add_argument("--stage", choices=STAGE_NAMES, required=True)
    update_parser.add_argument("--reason", required=True)
    update_parser.set_defaults(handler=command_set_needs_update)

    clear_parser = subparsers.add_parser(
        "clear-needs-update", help="Clear a stage update flag and reasons."
    )
    clear_parser.add_argument("--manifest", type=Path, required=True)
    clear_parser.add_argument("--stage", choices=STAGE_NAMES, required=True)
    clear_parser.set_defaults(handler=command_clear_needs_update)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the workflow-state CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.handler(args)
    except (WorkflowStateError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
