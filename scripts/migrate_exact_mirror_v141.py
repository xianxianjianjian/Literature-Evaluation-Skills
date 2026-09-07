#!/usr/bin/env python3
"""Migrate exact-mirror evidence to frame-closure and typography v1.4.1."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from normalize_chinese_typography import normalize_chinese_text


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def migrate(work_dir: Path, split: dict[str, Any] | None = None) -> None:
    inventory_path = work_dir / "source_inventory.json"
    frames_path = work_dir / "text_frame_inventory.jsonl"
    ledger_path = work_dir / "translation_ledger.jsonl"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8-sig"))
    frames = _read_jsonl(frames_path)
    ledger = _read_jsonl(ledger_path)

    for frame in frames:
        translated = frame.get("translation_action") == "TRANSLATE"
        frame.update({
            "translatable": translated,
            "replacement_status": "TRANSLATED" if translated else "INTENTIONAL_PRESERVE",
            "source_cleared": False,
            "target_rendered": False,
            "residual_checked": False,
        })
    for row in ledger:
        row["translated_text"] = normalize_chinese_text(str(row["translated_text"]))

    if split:
        old_frame_id = split["frame_id"]
        old_unit_id = next(frame["unit_id"] for frame in frames if frame["frame_id"] == old_frame_id)
        frame_index = next(index for index, frame in enumerate(frames) if frame["frame_id"] == old_frame_id)
        ledger_index = next(index for index, row in enumerate(ledger) if row["unit_id"] == old_unit_id)
        old_frame = frames[frame_index]
        old_row = ledger[ledger_index]
        source_marker = split["source_right_marker"]
        target_marker = split["target_right_marker"]
        source_offset = old_row["source_text"].index(source_marker)
        target_offset = old_row["translated_text"].index(target_marker)

        left_frame = deepcopy(old_frame)
        left_frame.update({
            "frame_id": split["new_frame_id"],
            "unit_id": split["new_unit_id"],
            "bbox_pt": split["new_bbox_pt"],
            "source_text": old_row["source_text"][:source_offset].strip(),
        })
        old_frame["source_text"] = old_row["source_text"][source_offset:].strip()
        left_row = deepcopy(old_row)
        left_row.update({
            "unit_id": split["new_unit_id"],
            "frame_ids": [split["new_frame_id"]],
            "source_text": old_row["source_text"][:source_offset].strip(),
            "translated_text": old_row["translated_text"][:target_offset].strip(),
        })
        old_row["source_text"] = old_row["source_text"][source_offset:].strip()
        old_row["translated_text"] = old_row["translated_text"][target_offset:].strip()
        frames.insert(frame_index, left_frame)
        ledger.insert(ledger_index, left_row)

        page = next(page for page in inventory["pages"] if old_frame_id in page["frame_ids"])
        position = page["frame_ids"].index(old_frame_id)
        page["frame_ids"].insert(position, split["new_frame_id"])
        unit_position = page["unit_ids"].index(old_unit_id)
        page["unit_ids"].insert(unit_position, split["new_unit_id"])
        if isinstance(inventory.get("units"), list):
            unit_index = next(index for index, unit in enumerate(inventory["units"]) if unit.get("unit_id") == old_unit_id)
            new_unit = deepcopy(inventory["units"][unit_index])
            new_unit["unit_id"] = split["new_unit_id"]
            inventory["units"].insert(unit_index, new_unit)

    for page in inventory["pages"]:
        page_frames = [frame for frame in frames if frame["frame_id"] in page["frame_ids"]]
        page_frames.sort(key=lambda frame: page["frame_ids"].index(frame["frame_id"]))
        for order, frame in enumerate(page_frames, 1):
            frame["reading_order"] = order
    for page in inventory["pages"]:
        page_units = [row for row in ledger if row["unit_id"] in page["unit_ids"]]
        page_units.sort(key=lambda row: page["unit_ids"].index(row["unit_id"]))
        for order, row in enumerate(page_units, 1):
            row["unit_index"] = order

    inventory_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_jsonl(frames_path, frames)
    _write_jsonl(ledger_path, ledger)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--split-spec", type=Path)
    args = parser.parse_args()
    split = json.loads(args.split_spec.read_text(encoding="utf-8")) if args.split_spec else None
    migrate(args.work_dir.resolve(), split)


if __name__ == "__main__":
    main()
