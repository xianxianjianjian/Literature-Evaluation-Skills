#!/usr/bin/env python3
"""Independent OCR audit for visible untranslated English in exact-mirror frames."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image


REPORT_FILE = "untranslated_residual_audit.json"
_DEFAULT_WHITELIST = {
    "rem", "nrem", "sws", "tmr", "eeg", "psg", "fmri", "anova", "lmm", "ci",
    "cb", "nap", "error", "doi", "url", "figure", "table", "references", "nature",
    "e-rem", "e-sws", "n-sws", "e-nap",
}
_LATIN_RUN = re.compile(r"\b[A-Za-z][A-Za-z'’-]*\b(?:\s+\b[A-Za-z][A-Za-z'’-]*\b){3,}")


class ResidualAuditError(ValueError):
    pass


def _find_program(name: str, candidates: list[Path]) -> Path | None:
    found = shutil.which(name)
    if found:
        return Path(found)
    return next((path for path in candidates if path.is_file()), None)


def _allowed_words(ledger_rows: list[dict[str, Any]]) -> set[str]:
    words = set(_DEFAULT_WHITELIST)
    for row in ledger_rows:
        for token in row.get("untranslated_tokens", []):
            words.update(word.casefold() for word in re.findall(r"[A-Za-z]{2,}", str(token.get("text", ""))))
    return words


def _latin_failures(text: str, allowed: set[str]) -> list[str]:
    failures: list[str] = []
    for match in _LATIN_RUN.finditer(text):
        words = re.findall(r"[A-Za-z][A-Za-z'’-]*", match.group(0))
        if sum(word.casefold() not in allowed for word in words) >= 4:
            failures.append(match.group(0).strip())
    return failures


def _shared_source_runs(output_text: str, source_text: str, allowed: set[str]) -> list[str]:
    """Find source English sequences that visibly survive in the output OCR."""
    def residual_words(value: str) -> list[str]:
        value = "\n".join(
            line for line in value.splitlines()
            if not re.search(r"https?|doi\b|www\.", line, re.IGNORECASE)
        )
        return [
            word for word in re.findall(r"[A-Za-z][A-Za-z'’-]*", value)
            if len(re.sub(r"[^A-Za-z]", "", word)) >= 3
        ]

    output_words = residual_words(output_text)
    source_words = residual_words(source_text)
    output_folded = [word.casefold() for word in output_words]
    source_folded = [word.casefold() for word in source_words]
    failures: list[str] = []
    for length in range(min(12, len(output_words), len(source_words)), 3, -1):
        source_runs = {
            tuple(source_folded[index:index + length])
            for index in range(len(source_words) - length + 1)
        }
        for index in range(len(output_words) - length + 1):
            run = tuple(output_folded[index:index + length])
            if run in source_runs and sum(word not in allowed for word in run) >= 4:
                failures.append(" ".join(output_words[index:index + length]))
                return failures
    return failures


def audit_residuals(
    work_dir: Path,
    output_pdf: Path,
    inventory: dict[str, Any],
    frames: dict[str, dict[str, Any]],
    ledger_rows: list[dict[str, Any]],
) -> tuple[bool, dict[str, Any]]:
    pdftoppm = _find_program("pdftoppm", [
        Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe"
    ])
    tesseract = _find_program("tesseract", [Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")])
    if not pdftoppm or not tesseract:
        raise ResidualAuditError("pdftoppm and Tesseract are required for independent visible-English audit")
    allowed = _allowed_words(ledger_rows)
    sources = {source["source_id"]: source for source in inventory["sources"]}
    frame_rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as temporary_name:
        temporary = Path(temporary_name)
        for page in inventory["pages"]:
            prefix = temporary / f"page-{page['output_page']:03d}"
            subprocess.run([
                str(pdftoppm), "-f", str(page["output_page"]), "-l", str(page["output_page"]),
                "-r", "200", "-png", "-singlefile", str(output_pdf), str(prefix)
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            image = Image.open(prefix.with_suffix(".png"))
            source_pdf = Path(str(sources[page["source_id"]]["pdf_path"]))
            if not source_pdf.is_absolute():
                source_pdf = work_dir / source_pdf
            source_prefix = temporary / f"source-{page['output_page']:03d}"
            subprocess.run([
                str(pdftoppm), "-f", str(page["source_page"]), "-l", str(page["source_page"]),
                "-r", "200", "-png", "-singlefile", str(source_pdf), str(source_prefix)
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            source_image = Image.open(source_prefix.with_suffix(".png"))
            media = [float(value) for value in page["media_box"]]
            sx = image.width / (media[2] - media[0])
            sy = image.height / (media[3] - media[1])
            for frame_id in page["frame_ids"]:
                frame = frames[frame_id]
                if frame["translation_action"] != "TRANSLATE":
                    continue
                x0, y0, x1, y1 = [float(value) for value in frame["bbox_pt"]]
                crop = image.crop((max(0, int(x0 * sx)), max(0, int(image.height - y1 * sy)),
                                   min(image.width, int(x1 * sx + 1)), min(image.height, int(image.height - y0 * sy + 1))))
                crop_path = temporary / f"{frame_id}.png"
                crop.save(crop_path)
                source_crop = source_image.crop((max(0, int(x0 * sx)), max(0, int(source_image.height - y1 * sy)),
                                                 min(source_image.width, int(x1 * sx + 1)),
                                                 min(source_image.height, int(source_image.height - y0 * sy + 1))))
                source_crop_path = temporary / f"{frame_id}-source.png"
                source_crop.save(source_crop_path)
                result = subprocess.run([
                    str(tesseract), str(crop_path), "stdout", "-l", "eng", "--psm", "6"
                ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
                source_result = subprocess.run([
                    str(tesseract), str(source_crop_path), "stdout", "-l", "eng", "--psm", "6"
                ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
                detected = result.stdout.strip()
                source_detected = source_result.stdout.strip()
                failures = _shared_source_runs(detected, source_detected, allowed)
                frame_rows.append({
                    "frame_id": frame_id,
                    "output_page": page["output_page"],
                    "ocr_text": detected,
                    "source_ocr_text": source_detected,
                    "unapproved_latin_runs": failures,
                    "passed": not failures,
                })
    failed = [row["frame_id"] for row in frame_rows if not row["passed"]]
    report = {
        "schema_version": 1,
        "auditor": "audit_untranslated_residuals.py",
        "method": "200-dpi frame-crop OCR with four-word Latin-run rejection",
        "passed": not failed,
        "failed_frame_ids": failed,
        "frames": frame_rows,
    }
    return not failed, report


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
