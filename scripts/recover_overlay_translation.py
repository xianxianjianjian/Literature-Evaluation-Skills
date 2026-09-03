#!/usr/bin/env python3
"""Recover exact-frame translations from a previously reviewed mirror PDF.

This bridge is intentionally conservative. It only auto-recovers a translation
when overlay glyphs from the reviewed reference fall inside the corresponding
reviewed exact source frame. Legacy/structural mirrors can have reflowed Chinese
text, omitted legacy fields, or page-level overlays that do not correspond to
current v1.3 frames. Those cases are NOT force-mapped. Instead the tool writes a
partial ledger plus explicit review tasks and fails the strict gate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    import pdfplumber
    from pdfplumber.utils import collate_line
except ImportError:  # pragma: no cover
    pdfplumber = None
    collate_line = None


class OverlayRecoveryError(ValueError):
    """Raised when the reference overlay cannot be mapped exactly."""


PARTIAL_LEDGER_FILE = "translation_ledger.partial.jsonl"
RECOVERY_TASK_FILE = "translation_recovery_tasks.jsonl"
RECOVERY_REPORT_FILE = "overlay_recovery_report.json"


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
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


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
    source_counts = Counter(_char_signature(char) for char in source_page.chars)
    overlay: list[dict[str, Any]] = []
    for char in reference_page.chars:
        signature = _char_signature(char)
        if source_counts[signature] > 0:
            source_counts[signature] -= 1
        else:
            overlay.append(char)
    return overlay


def _frame_top_bbox(
    frame: dict[str, Any], page_height: float
) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = [float(value) for value in frame["bbox_pt"]]
    return x0, page_height - y1, x1, page_height - y0


def _contains_center(
    char: dict[str, Any], bbox: tuple[float, float, float, float]
) -> bool:
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
    chars = sorted(
        chars, key=lambda char: (float(char["top"]), float(char["x0"]))
    )
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


def _retained_english_tokens(text: str) -> list[dict[str, str]]:
    """Account validator-relevant English retained in the reviewed translation."""
    words = sorted(set(re.findall(r"[A-Za-z]{3,}(?:[-/][A-Za-z0-9]+)*", text)))
    return [
        {
            "text": word,
            "reason": "RETAINED_IN_REVIEWED_REFERENCE_TRANSLATION",
        }
        for word in words
    ]


def _box_values(value: Any) -> list[float] | None:
    """Normalize pypdf rectangles and pdfplumber tuple-style page boxes."""
    if value is None:
        return None
    if all(hasattr(value, name) for name in ("left", "bottom", "right", "top")):
        return [
            float(value.left),
            float(value.bottom),
            float(value.right),
            float(value.top),
        ]
    if isinstance(value, (tuple, list)) and len(value) == 4:
        return [float(item) for item in value]
    try:
        items = list(value)
    except (TypeError, ValueError):
        return None
    if len(items) != 4:
        return None
    return [float(item) for item in items]


def _boxes_match(
    source_page: Any, reference_page: Any, tolerance: float = 0.05
) -> bool:
    for field in ("mediabox", "cropbox", "trimbox", "bleedbox", "artbox"):
        left = _box_values(getattr(source_page, field, None))
        right = _box_values(getattr(reference_page, field, None))
        if left is None or right is None:
            continue
        if any(abs(a - b) > tolerance for a, b in zip(left, right)):
            return False
    return True


def _missing_frame_task(
    frame: dict[str, Any], output_page: int
) -> dict[str, Any]:
    return {
        "record_type": "MISSING_FRAME_TRANSLATION",
        "status": "REVIEW_REQUIRED",
        "reason": "NO_EXACT_GEOMETRIC_OVERLAY_MATCH",
        "frame_id": frame["frame_id"],
        "unit_id": frame["unit_id"],
        "source_id": frame["source_id"],
        "source_page": frame["source_page"],
        "output_page": output_page,
        "kind": frame.get("kind"),
        "bbox_pt": frame.get("bbox_pt"),
        "source_text": frame.get("source_text", ""),
        "translated_text": None,
        "review_note": (
            "Provide/review a real Chinese translation for this exact source frame. "
            "Do not copy text from an unrelated nearby legacy overlay."
        ),
    }


def recover(work_dir: Path, reference_pdf: Path, output: Path) -> dict[str, Any]:
    _require_dependencies()
    work_dir = work_dir.resolve()
    reference_pdf = reference_pdf.resolve()
    inventory = _load_json(work_dir / "source_inventory.json")
    frame_rows = _load_jsonl(work_dir / "text_frame_inventory.jsonl")
    frames = {row.get("frame_id"): row for row in frame_rows}
    if None in frames or len(frames) != len(frame_rows):
        raise OverlayRecoveryError(
            "Text-frame inventory has missing or duplicate frame IDs."
        )

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
    review_tasks: list[dict[str, Any]] = []
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
            page_unowned_chars: list[dict[str, Any]] = []
            for char in overlay:
                owners = [item for item in candidates if _contains_center(char, item[2])]
                if owners:
                    _, frame_id, _ = min(owners, key=lambda item: item[0])
                    owned[frame_id].append(char)
                elif str(char.get("text", "")).strip():
                    page_unowned_chars.append(char)

            if page_unowned_chars:
                unowned_text = _reconstruct_text(page_unowned_chars)
                unowned.append(
                    {
                        "output_page": output_page,
                        "character_count": len(page_unowned_chars),
                        "sample": unowned_text[:300],
                    }
                )
                review_tasks.append(
                    {
                        "record_type": "UNOWNED_LEGACY_OVERLAY",
                        "status": "REVIEW_REQUIRED",
                        "reason": "LEGACY_OR_REFLOWED_TEXT_OUTSIDE_CURRENT_EXACT_FRAMES",
                        "output_page": output_page,
                        "source_id": source_id,
                        "source_page": source_page_number,
                        "character_count": len(page_unowned_chars),
                        "legacy_overlay_text": unowned_text,
                        "review_note": (
                            "This reviewed legacy text is page-level evidence only. It must not be "
                            "force-assigned to a current exact frame without source/translation review."
                        ),
                    }
                )

            for fallback_index, frame_id in enumerate(page_record["frame_ids"], 1):
                frame = frames[frame_id]
                if frame.get("translation_action") != "TRANSLATE":
                    continue
                translated_text = _reconstruct_text(owned.get(frame_id, []))
                if not translated_text:
                    missing.append(frame_id)
                    review_tasks.append(_missing_frame_task(frame, output_page))
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
                        "untranslated_tokens": _retained_english_tokens(translated_text),
                        "recovery_evidence": "EXACT_GEOMETRIC_OVERLAY_MATCH",
                    }
                )
            page_diagnostics.append(
                {
                    "output_page": output_page,
                    "overlay_characters": len(overlay),
                    "owned_characters": sum(len(value) for value in owned.values()),
                    "unowned_nonspace_characters": len(page_unowned_chars),
                }
            )
    finally:
        reference.close()
        for document in source_documents.values():
            document.close()

    compatibility = (
        "EXACT_OVERLAY_COMPATIBLE"
        if not missing and not unowned
        else "LEGACY_OR_REFLOWED_REVIEW_REQUIRED"
    )
    report = {
        "schema_version": 2,
        "reference_pdf": str(reference_pdf),
        "reference_compatibility": compatibility,
        "ledger_rows_recovered": len(ledger),
        "missing_frame_ids": missing,
        "unowned_overlay": unowned,
        "review_task_count": len(review_tasks),
        "partial_ledger": str((work_dir / PARTIAL_LEDGER_FILE).resolve()),
        "recovery_tasks": str((work_dir / RECOVERY_TASK_FILE).resolve()),
        "pages": page_diagnostics,
        "passed": not missing and not unowned,
    }
    _write_json(work_dir / RECOVERY_REPORT_FILE, report)

    if missing or unowned:
        # Preserve evidence for migration/review, but never write the requested
        # production ledger path on a failed strict recovery.
        _write_jsonl(work_dir / PARTIAL_LEDGER_FILE, ledger)
        _write_jsonl(work_dir / RECOVERY_TASK_FILE, review_tasks)
        raise OverlayRecoveryError(
            "Reference mirror is not exact-frame compatible. "
            f"Recovered {len(ledger)} frame(s), but {len(missing)} frame(s) need translation review "
            f"and {len(unowned)} page(s) contain legacy/reflowed overlay text. "
            f"Review {RECOVERY_TASK_FILE}; do not force-map legacy text."
        )

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
        f"Recovered {report['ledger_rows_recovered']} translated frame(s) from the reviewed overlay PDF."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
