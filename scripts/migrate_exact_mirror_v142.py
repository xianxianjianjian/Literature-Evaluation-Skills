#!/usr/bin/env python3
"""Upgrade a reviewed v1.4.1 exact package to the generic v1.4.2 contracts."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from exact_mirror import DEFAULT_ROLE_BY_KIND, PRESERVE_ENGLISH_FRAME_ROLES
from style_fidelity import default_style_map


class MigrationError(ValueError):
    pass


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def infer_role(frame: dict) -> str:
    kind = str(frame.get("kind") or "other")
    text = str(frame.get("source_text") or "").strip().casefold()
    if frame.get("translation_action") == "RETAIN_SOURCE":
        reason = str(frame.get("retain_reason") or "")
        if reason == "FORMULA":
            return "FORMULA"
        if reason == "REFERENCE_ENTRY":
            return "REFERENCE"
        if reason == "FIGURE_INTERNAL":
            return "FIGURE_INTERNAL"
        if reason == "STATISTIC":
            return "STATISTIC"
        if reason == "IDENTIFIER":
            return "DOI_URL"
        return "OTHER"
    if kind == "body" and text.startswith("abstract"):
        return "ABSTRACT"
    if kind == "figure_label":
        return "CAPTION"
    return DEFAULT_ROLE_BY_KIND.get(kind, "OTHER")


def migrate(source_dir: Path, target_dir: Path, output_pdf: Path) -> dict:
    if not source_dir.is_dir():
        raise MigrationError(f"Source package does not exist: {source_dir}")
    if target_dir.exists():
        raise MigrationError(f"Refusing to overwrite target package: {target_dir}")
    shutil.copytree(source_dir, target_dir)
    frame_path = target_dir / "text_frame_inventory.jsonl"
    rows = read_jsonl(frame_path)
    for row in rows:
        role = infer_role(row)
        translatable = row.get("translation_action") == "TRANSLATE"
        if role in PRESERVE_ENGLISH_FRAME_ROLES:
            translatable = False
            row["translation_action"] = "RETAIN_SOURCE"
            row["retain_reason"] = "FIGURE_INTERNAL" if role == "FIGURE_INTERNAL" else (
                "FORMULA" if role in {"FORMULA", "STATISTIC"} else
                "REFERENCE_ENTRY" if role == "REFERENCE" else "IDENTIFIER"
            )
            row["replacement_status"] = "INTENTIONAL_PRESERVE"
            row["source_cleared"] = False
            row["target_rendered"] = False
            row["residual_checked"] = False
        row["role"] = role
        row["translatable"] = translatable
        row["preserve_english"] = not translatable
        row["italic"] = bool(row.get("italic", "italic" in str(row.get("weight", "")).casefold()))
        row["superscript"] = bool(row.get("superscript", False))
        row.pop("rendered_style", None)
    write_jsonl(frame_path, rows)

    translated_frame_ids = {row["frame_id"] for row in rows if row["translation_action"] == "TRANSLATE"}
    ledger_path = target_dir / "translation_ledger.jsonl"
    ledger = [
        row for row in read_jsonl(ledger_path)
        if set(row.get("frame_ids", [])) <= translated_frame_ids
    ]
    write_jsonl(ledger_path, ledger)

    plan_path = target_dir / "mirror_layout_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    plan["output_pdf"] = str(output_pdf.resolve())
    for page in plan.get("pages", []):
        page["replacement_regions"] = [
            row for row in page.get("replacement_regions", [])
            if row.get("frame_id") in translated_frame_ids
        ]
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    style_map = default_style_map(rows)
    (target_dir / "style_map.json").write_text(
        json.dumps(style_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for generated in (
        "style_fidelity.json", "translation_validation.json", "layout_diff.json",
        "untranslated_residual_audit.json", "numeric_integrity.json",
        "typography_fit.json", "exact_mirror_render.json",
    ):
        path = target_dir / generated
        if path.exists():
            path.unlink()
    return {"frames": len(rows), "translated_frames": len(translated_frame_ids), "ledger_units": len(ledger)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--target-dir", type=Path, required=True)
    parser.add_argument("--output-pdf", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = migrate(args.source_dir.resolve(), args.target_dir.resolve(), args.output_pdf.resolve())
    except (OSError, json.JSONDecodeError, MigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
