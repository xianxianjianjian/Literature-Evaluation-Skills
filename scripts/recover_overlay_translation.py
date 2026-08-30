#!/usr/bin/env python3
"""Recover translated overlay text from an earlier mirror PDF without storing it in Git.

This release-acceptance bridge is intentionally read-only with respect to the
reference PDF. It subtracts the original source text layer from the reference
PDF, assigns the remaining overlay glyphs to the already-reviewed exact source
frames, and writes a frame-linked translation ledger. It never marks frames as
reviewed and never changes source/background evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    import pdfplumber
    from pdfplumber.utils import collate_line
except ImportError:  # pragma: no cover - CLI dependency check
    pdfplumber = None
    collate_line = None


class OverlayRecoveryError(ValueError):
    """Raised when the reference overlay cannot be mapped exactly."""


def _require_dependencies() -> None:
    if pdfplumber is None or collate_line is None:
        raise OverlayRecoveryError(
            "pdfplumber is required. Install requirements-exact-mirror.txt."
        )


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise OverlayRecoveryError(f"Missing JSON file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OverlayRecoveryError(f"Invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise OverlayRecoveryError(f"JSON root must be an object: {path}")
    return value


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise OverlayRecoveryError(f"Missing JSONL file: {path}")
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise OverlayRecoveryError(
                f"Invalid JSONL {path} line {line_number}: {exc}"
            ) from exc
        if not isinstance(value, dict):
            raise OverlayRecoveryError(f"JSONL line {line_number} must be an object.")
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _rounded(value: Any, quantum: float = 0.25) -> float:
    return round(float(value) / quantum) * quantum


def _char_signature(char: dict[str, Any]) -> tuple[str, float, float, float, float]:
    return (
        str(char.get("text", "")),
        _rounded(char["x0"]),
        _rounded(char["x1"]),
        _rounded(char["top"]),
        _rounded(char["bottom"]),
    )


def _overlay_chars(source_page: Any, reference_page: Any) -> list[dict[str, Any]]:
    """Remove the unchanged original source text layer as a multiset."""

    source_counts = Counter(_char_signature(char) for char in source_page.chars)
    overlay: list[dict[str, Any]] = []
    for char in reference_page.chars:
        signature = _char_signature(char)
        if source_counts[signature] > 0:
            source_counts[signature] -= 1
        else:
            overlay.append(char)
    return overlay


def _frame_top_bbox(frame: dict[str, Any], page_height: float) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = [float(value) for value in frame["bbox_pt"]]
    return x0, page_height - y1, x1, page_height - y0


def _contains_center(char: dict[str, Any], bbox: tuple[float, float, float, float]) -> bool:
    cx = (float(char["x0"]) + float(char["x1"])) / 2
    cy = (float(char["top"]) + float(char["bottom"])) / 2
    tolerance = 0.75
    return (
        bbox[0] - tolerance <= cx <= bbox[2] + tolerance
        and bbox[1] - tolerance <= cy <= bbox[3] + tolerance
    )


def _reconstruct_text(chars: list[dict[str, Any]]) -> str:
    if not chars:
        return ""
    chars = sorted(chars, key=lambda char: (float(char["top"]), float(char["x0"])))
    bands: list[list[dict[str, Any]]] = []
    for char in chars:
        if not bands:
            bands.append([char])
            continue
        top_values = sorted(float(item["top"]) for item in bands[-1])
        median_top = top_values[len(top_values) // 2]
        tolerance = max(1.5, float(char.get("size") or 0.0) * 0.25)
        if abs(float(char["top"]) - median_top) > tolerance:
            bands.append([char])
        else:
            bands[-1].append(char)

    lines: list[str] = []
    for band in bands:
        ordered = sorted(band, key=lambda char: float(char["x0"]))
        text = collate_line(ordered, tolerance=1.0).strip()
        if text:
            lines.append(text)
    return "\n".join(lines).strip()


def _boxes_match(source_page: Any, reference_page: Any, tolerance: float = 0.05) -> bool:
    for field in ("mediabox", "cropbox", "trimbox", "bleedbox", "artbox"):
        left = getattr(source_page, field, None)
        right = getattr(reference_page, field, None)
        if left is None or right is None:
            continue
        left_values = [float(left.left), float(left.bottom), float(left.right), float(left.top)]
        right_values = [float(right.left), float(right.bottom), float(right.right), float(right.top)]
        if any(abs(a - b) > tolerance for a, b in zip(left_values, right_values)):
            return False
    return True


def recover(work_dir: Path, reference_pdf: Path, output: Path) -> dict[str, Any]:
    _require_dependencies()
    work_dir = work_dir.resolve()
    reference_pdf = reference_pdf.resolve()
    inventory = _load_json(work_dir / "source_inventory.json")
    frame_rows = _load_jsonl(work_dir / "text_frame_inventory.jsonl")
    frames = {row.get("frame_id"): row for row in frame_rows}
    if None in frames or len(frames) != len(frame_rows):
        raise OverlayRecoveryError("Text-frame inventory has missing or duplicate frame IDs.")

    sources = {source["source_id"]: source for source in inventory.get("sources", [])}
    pages = sorted(inventory.get("pages", []), key=lambda page: page["output_page"])
    if not pages:
        raise OverlayRecoveryError("Source inventory has no pages.")

    source_documents: dict[str, Any] = {}
    for source_id, source in sources.items():
        source_path = Path(source["pdf_path"])
        if not source_path.is_absolute():
            source_path = work_dir / source_path
        if not source_path.is_file():
            raise OverlayRecoveryError(f"Source PDF is missing: {source_path}")
        source_documents[source_id] = pdfplumber.open(source_path)

    reference = pdfplumber.open(reference_pdf)
    if len(reference.pages) != len(pages):
        for document in source_documents.values():
            document.close()
        reference.close()
        raise OverlayRecoveryError(
            f"Reference page count {len(reference.pages)} does not equal inventory {len(pages)}."
        )

    ledger: list[dict[str, Any]] = []
    missing: list[str] = []
    unowned: list[dict[str, Any]] = []
    page_diagnostics: list[dict[str, Any]] = []
    try:
        for page_record in pages:
            output_page = int(page_record["output_page"])
            source_id = page_record["source_id"]
            source_page_number = int(page_record["source_page"])
            source_page = source_documents[source_id].pages[source_page_number - 1]
            reference_page = reference.pages[output_page - 1]
            if not _boxes_match(source_page, reference_page):
                raise OverlayRecoveryError(
                    f"Reference/source page boxes differ at output page {output_page}."
                )

            overlay = _overlay_chars(source_page, reference_page)
            candidates: list[tuple[float, str, tuple[float, float, float, float]]] = []
            for frame_id in page_record["frame_ids"]:
                frame = frames[frame_id]
                if frame.get("translation_action") != "TRANSLATE":
                    continue
                bbox = _frame_top_bbox(frame, float(reference_page.height))
                area = max(1e-9, (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]))
                candidates.append((area, frame_id, bbox))

            owned: dict[str, list[dict[str, Any]]] = defaultdict(list)
            page_unowned: list[str] = []
            for char in overlay:
                owners = [item for item in candidates if _contains_center(char, item[2])]
                if owners:
                    _, frame_id, _ = min(owners, key=lambda item: item[0])
                    owned[frame_id].append(char)
                elif str(char.get("text", "")).strip():
                    page_unowned.append(str(char.get("text", "")))

            if page_unowned:
                unowned.append(
                    {
                        "output_page": output_page,
                        "character_count": len(page_unowned),
                        "sample": "".join(page_unowned[:80]),
                    }
                )

            for fallback_index, frame_id in enumerate(page_record["frame_ids"], 1):
                frame = frames[frame_id]
                if frame.get("translation_action") != "TRANSLATE":
                    continue
                translated_text = _reconstruct_text(owned.get(frame_id, []))
                if not translated_text:
                    missing.append(frame_id)
                    continue
                ledger.append(
                    {
                        "unit_id": frame["unit_id"],
                        "source_id": source_id,
                        "source_page": source_page_number,
                        "section": str(frame.get("kind") or "Body"),
                        "unit_index": int(frame.get("reading_order") or fallback_index),
                        "kind": frame["kind"],
                        "source_status": "READABLE",
                        "translation_status": "TRANSLATED",
                        "output_pages": [output_page],
                        "issue_ids": [],
                        "frame_ids": [frame_id],
                        "source_text": frame.get("source_text", ""),
                        "translated_text": translated_text,
                        "font_scale_used": 1.0,
                        "fit_status": "FIT",
                        "untranslated_tokens": [],
                    }
                )
            page_diagnostics.append(
                {
                    "output_page": output_page,
                    "overlay_characters": len(overlay),
                    "owned_characters": sum(len(value) for value in owned.values()),
                    "unowned_nonspace_characters": len(page_unowned),
                }
            )
    finally:
        reference.close()
        for document in source_documents.values():
            document.close()

    report = {
        "schema_version": 1,
        "reference_pdf": str(reference_pdf),
        "ledger_rows": len(ledger),
        "missing_frame_ids": missing,
        "unowned_overlay": unowned,
        "pages": page_diagnostics,
        "passed": not missing and not unowned,
    }
    _write_json(work_dir / "overlay_recovery_report.json", report)
    if missing or unowned:
        details: list[str] = []
        if missing:
            details.append(
                "missing translated overlay text: "
                + ", ".join(missing[:30])
                + (" ..." if len(missing) > 30 else "")
            )
        if unowned:
            details.append(
                "unowned overlay glyphs on output pages: "
                + ", ".join(str(item["output_page"]) for item in unowned[:30])
            )
        raise OverlayRecoveryError("; ".join(details))

    _write_jsonl(output, ledger)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--reference-pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = recover(args.work_dir, args.reference_pdf, args.output)
    except (OverlayRecoveryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(
        f"Recovered {report['ledger_rows']} translated frame(s) from the reviewed overlay PDF."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
