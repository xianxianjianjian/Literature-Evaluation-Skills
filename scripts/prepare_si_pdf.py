#!/usr/bin/env python3
"""Prepare a PDF reading copy of documentary SI while preserving source files."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

from validate_deep_reading_package import _find_soffice


READING = {".pdf", ".doc", ".docx", ".html", ".htm", ".txt", ".rtf"}


def prepare(source: Path, output: Path, soffice: Path | None = None) -> dict:
    if not source.is_file():
        raise ValueError(f"SI source missing: {source}")
    suffix = source.suffix.casefold()
    if suffix not in READING:
        return {"status": "DATA_SI_ORIGINAL_RETAINED", "source": str(source.resolve()),
                "pdf_path": None, "original_retained": True}
    output.parent.mkdir(parents=True, exist_ok=True)
    if suffix == ".pdf":
        if source.resolve() != output.resolve():
            shutil.copyfile(source, output)
    else:
        executable = _find_soffice(soffice)
        if executable is None:
            raise ValueError("LibreOffice/compatible PDF converter unavailable")
        process = subprocess.run(
            [str(executable), "--headless", "--convert-to", "pdf", "--outdir", str(output.parent), str(source)],
            capture_output=True, text=True, timeout=180, check=False,
        )
        produced = output.parent / f"{source.stem}.pdf"
        if process.returncode or not produced.is_file():
            raise ValueError(f"SI PDF conversion failed: {(process.stderr or process.stdout).strip()}")
        if produced.resolve() != output.resolve():
            produced.replace(output)
    reader = PdfReader(str(output))
    if not reader.pages:
        raise ValueError("SI reading PDF has no pages")
    return {"status": "SI_PDF_READY", "source": str(source.resolve()),
            "pdf_path": str(output.resolve()), "pages": len(reader.pages), "original_retained": source.is_file()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--soffice", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = prepare(args.source, args.output, args.soffice)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
