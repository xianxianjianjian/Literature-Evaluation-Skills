#!/usr/bin/env python3
"""Create, inspect, and update V1 weekly workflow manifests.

The manifest is stored as JSON-compatible YAML 1.2 so the repository can keep a
`.yaml` contract while this helper remains Python-stdlib-only. Writes are
validated and replaced atomically. This helper manages state only; it never
makes academic decisions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from datetime import date
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
NON_GATE_STATUSES = ALLOWED_STATUSES - {"WAITING_USER"}
STAGE_NAMES = ("topic", "search", "translation", "deep_reading")
OUTPUT_NAMES = ("A", "B", "C")
GATE_STAGES = {"topic", "search"}
WEEK_PATTERN = re.compile(r"^\d{4}-W(?:0[1-9]|[1-4]\d|5[0-3])$")


class WorkflowStateError(ValueError):
    """Raised when a manifest or requested state update is invalid."""


def validate_iso_date(value: str, field: str) -> None:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise WorkflowStateError(f"{field} must use YYYY-MM-DD format.") from exc
    if parsed.isoformat() != value:
        raise WorkflowStateError(f"{field} must use canonical YYYY-MM-DD format.")


def _stage_record() -> dict[str, Any]:
    return {"status": "NOT_STARTED", "needs_update": False, "update_reason": []}


def initial_manifest(week: str, workflow_id: str | None = None) -> dict[str, Any]:
    if not WEEK_PATTERN.fullmatch(week):
        raise WorkflowStateError(
            f"Invalid week {week!r}; expected ISO week such as 2026-W34."
        )
    return {
        "schema_version": 1,
        "workflow_id": workflow_id or f"{week}-weekly-literature-evaluation",
        "week": week,
        "paper_id": None,
        "stages": {name: _stage_record() for name in STAGE_NAMES},
        "outputs": {
            "A": {"status": "NOT_STARTED", "zotero_attachment_key": None},
            "B": {"status": "NOT_STARTED", "zotero_attachment_key": None},
            "C": {"status": "NOT_STARTED", "git_path": None},
        },
        "pending_zotero_actions": [],
        "blocking_issues": [],
        "source_change": {"last_checked": None},
    }


def normalize_manifest(data: object) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise WorkflowStateError("Manifest root must be an object.")
    stages = data.get("stages")
    if isinstance(stages, dict):
        for name in STAGE_NAMES:
            stage = stages.get(name)
            if isinstance(stage, dict):
                stage.setdefault("needs_update", False)
                stage.setdefault("update_reason", [])
    data.setdefault("blocking_issues", [])
    return data


def validate_manifest(data: object) -> dict[str, Any]:
    """Validate V1 shape plus only deterministic workflow-state invariants."""
    data = normalize_manifest(data)
    if data.get("schema_version") != 1:
        raise WorkflowStateError("Manifest schema_version must be 1.")

    workflow_id = data.get("workflow_id")
    if not isinstance(workflow_id, str) or not workflow_id.strip():
        raise WorkflowStateError("workflow_id must be a non-empty string.")

    week = data.get("week")
    if not isinstance(week, str) or not WEEK_PATTERN.fullmatch(week):
        raise WorkflowStateError("Manifest week must use YYYY-Wxx ISO format.")

    paper_id = data.get("paper_id")
    if paper_id is not None and (not isinstance(paper_id, str) or not paper_id.strip()):
        raise WorkflowStateError("paper_id must be null or a non-empty string.")
    has_paper = isinstance(paper_id, str) and bool(paper_id.strip())

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
        if status == "WAITING_USER" and name not in GATE_STAGES:
            raise WorkflowStateError(
                f"WAITING_USER is reserved for the topic/paper Gates; stage {name} cannot use it."
            )
        if not isinstance(stage.get("needs_update"), bool):
            raise WorkflowStateError(f"{name}.needs_update must be true or false.")
        reasons = stage.get("update_reason")
        if not isinstance(reasons, list) or not all(
            isinstance(reason, str) and reason.strip() for reason in reasons
        ):
            raise WorkflowStateError(
                f"{name}.update_reason must be a list of non-empty strings."
            )
        if not stage["needs_update"] and reasons:
            raise WorkflowStateError(
                f"{name}.update_reason must be empty when needs_update is false."
            )

    if stages["search"]["status"] in {"PROVISIONAL", "COMPLETE"} and not has_paper:
        raise WorkflowStateError(
            "Search PROVISIONAL/COMPLETE requires a selected paper_id; use WAITING_USER for the final-paper Gate."
        )
    for name in ("translation", "deep_reading"):
        if stages[name]["status"] != "NOT_STARTED" and not has_paper:
            raise WorkflowStateError(
                f"Stage {name} cannot start before Minimal Intake establishes paper_id."
            )

    outputs = data.get("outputs")
    if not isinstance(outputs, dict):
        raise WorkflowStateError("Manifest must contain an outputs object.")
    for name in OUTPUT_NAMES:
        output = outputs.get(name)
        if not isinstance(output, dict):
            raise WorkflowStateError(f"Missing output object: {name}.")
        status = output.get("status")
        if status not in NON_GATE_STATUSES:
            raise WorkflowStateError(
                f"Invalid status for output {name}: {status!r}; outputs cannot WAITING_USER."
            )
        if status != "NOT_STARTED" and not has_paper:
            raise WorkflowStateError(
                f"Output {name} cannot start before paper_id is established."
            )

    for name in ("A", "B"):
        value = outputs[name].get("zotero_attachment_key")
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise WorkflowStateError(
                f"outputs.{name}.zotero_attachment_key must be null or text."
            )
    value = outputs["C"].get("git_path")
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise WorkflowStateError("outputs.C.git_path must be null or text.")

    pending = data.get("pending_zotero_actions")
    if not isinstance(pending, list) or not all(isinstance(item, dict) for item in pending):
        raise WorkflowStateError("pending_zotero_actions must be a list of objects.")

    blockers = data.get("blocking_issues")
    if not isinstance(blockers, list) or not all(isinstance(item, dict) for item in blockers):
        raise WorkflowStateError("blocking_issues must be a list of objects.")
    for index, blocker in enumerate(blockers):
        for key in ("stage", "type", "detail"):
            if not isinstance(blocker.get(key), str) or not blocker[key].strip():
                raise WorkflowStateError(
                    f"blocking_issues[{index}].{key} must be a non-empty string."
                )
        if blocker["stage"] not in STAGE_NAMES:
            raise WorkflowStateError(
                f"blocking_issues[{index}].stage must be one of {', '.join(STAGE_NAMES)}."
            )

    source_change = data.get("source_change")
    if not isinstance(source_change, dict) or "last_checked" not in source_change:
        raise WorkflowStateError("source_change.last_checked is required.")
    last_checked = source_change.get("last_checked")
    if last_checked is not None:
        if not isinstance(last_checked, str):
            raise WorkflowStateError("source_change.last_checked must be null or YYYY-MM-DD.")
        validate_iso_date(last_checked, "source_change.last_checked")
    return data


def load_manifest(path: Path) -> dict[str, Any]:
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
    data = validate_manifest(data)
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
    data = initial_manifest(args.week, args.workflow_id)
    write_manifest(args.manifest, data, overwrite=args.force)
    print(f"Initialized workflow manifest: {args.manifest}")


def command_show(args: argparse.Namespace) -> None:
    print(json.dumps(load_manifest(args.manifest), ensure_ascii=False, indent=2))


def command_set_paper(args: argparse.Namespace) -> None:
    data = load_manifest(args.manifest)
    value = args.paper_id.strip()
    if not value:
        raise WorkflowStateError("paper_id cannot be empty.")
    data["paper_id"] = value
    write_manifest(args.manifest, data)
    print(f"Set paper_id to {value}.")


def command_set_stage(args: argparse.Namespace) -> None:
    if args.status == "WAITING_USER" and args.stage not in GATE_STAGES:
        raise WorkflowStateError(
            "WAITING_USER is only valid for topic or search Gate stages."
        )
    data = load_manifest(args.manifest)
    data["stages"][args.stage]["status"] = args.status
    write_manifest(args.manifest, data)
    print(f"Set {args.stage} to {args.status}.")


def command_set_output(args: argparse.Namespace) -> None:
    data = load_manifest(args.manifest)
    output = data["outputs"][args.output]
    output["status"] = args.status
    if args.output in {"A", "B"} and args.zotero_attachment_key is not None:
        output["zotero_attachment_key"] = args.zotero_attachment_key or None
    if args.output == "C" and args.git_path is not None:
        output["git_path"] = args.git_path or None
    write_manifest(args.manifest, data)
    print(f"Set output {args.output} to {args.status}.")


def command_set_needs_update(args: argparse.Namespace) -> None:
    reason = args.reason.strip()
    if not reason:
        raise WorkflowStateError("Update reason cannot be empty.")
    data = load_manifest(args.manifest)
    stage = data["stages"][args.stage]
    stage["needs_update"] = True
    if reason not in stage["update_reason"]:
        stage["update_reason"].append(reason)
    write_manifest(args.manifest, data)
    print(f"Marked {args.stage} as needing update.")


def command_clear_needs_update(args: argparse.Namespace) -> None:
    data = load_manifest(args.manifest)
    stage = data["stages"][args.stage]
    stage["needs_update"] = False
    stage["update_reason"] = []
    write_manifest(args.manifest, data)
    print(f"Cleared update flag for {args.stage}.")


def command_add_blocker(args: argparse.Namespace) -> None:
    data = load_manifest(args.manifest)
    blocker: dict[str, Any] = {
        "stage": args.stage,
        "type": args.type.strip(),
        "detail": args.detail.strip(),
    }
    if args.source_id:
        blocker["source_id"] = args.source_id.strip()
    if not blocker["type"] or not blocker["detail"]:
        raise WorkflowStateError("Blocker type/detail cannot be empty.")
    if blocker not in data["blocking_issues"]:
        data["blocking_issues"].append(blocker)
    write_manifest(args.manifest, data)
    print(f"Added blocker for {args.stage}: {blocker['type']}")


def command_clear_blockers(args: argparse.Namespace) -> None:
    data = load_manifest(args.manifest)
    before = len(data["blocking_issues"])
    if args.all:
        data["blocking_issues"] = []
    else:
        def keep(item: dict[str, Any]) -> bool:
            if args.stage and item.get("stage") != args.stage:
                return True
            if args.type and item.get("type") != args.type:
                return True
            if args.source_id and item.get("source_id") != args.source_id:
                return True
            return False
        data["blocking_issues"] = [
            item for item in data["blocking_issues"] if keep(item)
        ]
    removed = before - len(data["blocking_issues"])
    write_manifest(args.manifest, data)
    print(f"Cleared {removed} blocker(s).")


def parse_json_object(raw: str, field: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WorkflowStateError(f"{field} is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise WorkflowStateError(f"{field} must be a JSON object.")
    return value


def command_add_pending_zotero(args: argparse.Namespace) -> None:
    data = load_manifest(args.manifest)
    record = parse_json_object(args.record_json, "--record-json")
    if not isinstance(record.get("action"), str) or not record["action"].strip():
        raise WorkflowStateError("Pending Zotero record requires non-empty action.")
    if record not in data["pending_zotero_actions"]:
        data["pending_zotero_actions"].append(record)
    write_manifest(args.manifest, data)
    print(f"Added pending Zotero action: {record['action']}")


def command_clear_pending_zotero(args: argparse.Namespace) -> None:
    data = load_manifest(args.manifest)
    before = len(data["pending_zotero_actions"])
    if args.all:
        data["pending_zotero_actions"] = []
    else:
        def keep(item: dict[str, Any]) -> bool:
            if args.action and item.get("action") != args.action:
                return True
            if args.source_id and item.get("source_id") != args.source_id:
                return True
            return False
        data["pending_zotero_actions"] = [
            item for item in data["pending_zotero_actions"] if keep(item)
        ]
    removed = before - len(data["pending_zotero_actions"])
    write_manifest(args.manifest, data)
    print(f"Cleared {removed} pending Zotero action(s).")


def command_set_source_checked(args: argparse.Namespace) -> None:
    validate_iso_date(args.date, "--date")
    data = load_manifest(args.manifest)
    data["source_change"]["last_checked"] = args.date
    write_manifest(args.manifest, data)
    print(f"Set source_change.last_checked to {args.date}.")


def command_summary(args: argparse.Namespace) -> None:
    data = load_manifest(args.manifest)
    payload = {
        "workflow_id": data["workflow_id"],
        "week": data["week"],
        "paper_id": data["paper_id"],
        "stages": {
            name: {
                "status": data["stages"][name]["status"],
                "needs_update": data["stages"][name]["needs_update"],
                "update_reason": data["stages"][name]["update_reason"],
            }
            for name in STAGE_NAMES
        },
        "outputs": {name: data["outputs"][name]["status"] for name in OUTPUT_NAMES},
        "blocking_issues": data["blocking_issues"],
        "pending_zotero_actions": data["pending_zotero_actions"],
        "source_change": data["source_change"],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
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

    summary = subparsers.add_parser(
        "summary", help="Show resume-relevant state without routing academically."
    )
    summary.add_argument("--manifest", type=Path, required=True)
    summary.set_defaults(handler=command_summary)

    paper = subparsers.add_parser("set-paper", help="Set the active stable paper_id.")
    paper.add_argument("--manifest", type=Path, required=True)
    paper.add_argument("--paper-id", required=True)
    paper.set_defaults(handler=command_set_paper)

    stage_parser = subparsers.add_parser("set-stage", help="Set a workflow stage status.")
    stage_parser.add_argument("--manifest", type=Path, required=True)
    stage_parser.add_argument("--stage", choices=STAGE_NAMES, required=True)
    stage_parser.add_argument("--status", choices=sorted(ALLOWED_STATUSES), required=True)
    stage_parser.set_defaults(handler=command_set_stage)

    output = subparsers.add_parser("set-output", help="Set A/B/C status and verified locator.")
    output.add_argument("--manifest", type=Path, required=True)
    output.add_argument("--output", choices=OUTPUT_NAMES, required=True)
    output.add_argument("--status", choices=sorted(NON_GATE_STATUSES), required=True)
    output.add_argument("--zotero-attachment-key")
    output.add_argument("--git-path")
    output.set_defaults(handler=command_set_output)

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

    blocker = subparsers.add_parser("add-blocker", help="Append a resumable blocking issue.")
    blocker.add_argument("--manifest", type=Path, required=True)
    blocker.add_argument("--stage", choices=STAGE_NAMES, required=True)
    blocker.add_argument("--type", required=True)
    blocker.add_argument("--detail", required=True)
    blocker.add_argument("--source-id")
    blocker.set_defaults(handler=command_add_blocker)

    clear_blocker = subparsers.add_parser("clear-blockers", help="Clear matching blockers.")
    clear_blocker.add_argument("--manifest", type=Path, required=True)
    clear_blocker.add_argument("--stage", choices=STAGE_NAMES)
    clear_blocker.add_argument("--type")
    clear_blocker.add_argument("--source-id")
    clear_blocker.add_argument("--all", action="store_true")
    clear_blocker.set_defaults(handler=command_clear_blockers)

    pending = subparsers.add_parser(
        "add-pending-zotero", help="Append one pending Zotero action JSON object."
    )
    pending.add_argument("--manifest", type=Path, required=True)
    pending.add_argument("--record-json", required=True)
    pending.set_defaults(handler=command_add_pending_zotero)

    clear_pending = subparsers.add_parser(
        "clear-pending-zotero", help="Clear matching pending Zotero actions."
    )
    clear_pending.add_argument("--manifest", type=Path, required=True)
    clear_pending.add_argument("--action")
    clear_pending.add_argument("--source-id")
    clear_pending.add_argument("--all", action="store_true")
    clear_pending.set_defaults(handler=command_clear_pending_zotero)

    checked = subparsers.add_parser(
        "set-source-checked", help="Record the last source-change check date."
    )
    checked.add_argument("--manifest", type=Path, required=True)
    checked.add_argument("--date", required=True)
    checked.set_defaults(handler=command_set_source_checked)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command in {"clear-blockers", "clear-pending-zotero"}:
            selectors = [
                getattr(args, name, None)
                for name in ("stage", "type", "source_id", "action")
            ]
            if not args.all and not any(selectors):
                raise WorkflowStateError(
                    "Specify a selector or --all when clearing records."
                )
        args.handler(args)
    except (WorkflowStateError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
