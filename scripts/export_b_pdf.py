#!/usr/bin/env python3
"""Promote an independently rendered, academically validated B PDF for archive."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from pypdf import PdfReader

from validate_deep_reading_package import TOP_LEVEL_HEADINGS
from artifact_binding import fingerprint, matches_fingerprint, require_identity, resolve_path, same_content, source_bindings


def validate_bound_report(b_path: Path, academic_report: Path, report: dict, root: Path,
                          allowed_roots: tuple[Path, ...] = (), *, rendered_pdf: Path | None = None) -> Path:
    """Validate a signed content chain; an archive copy can replace cleaned render caches."""
    if report.get("passed") is not True or report.get("contract_version") != "1.5.0":
        raise ValueError("v1.5 export requires a passed new v1.5 academic report")
    resolve = lambda value, exists=True: resolve_path(value or "", root, allowed_roots=allowed_roots, must_exist=exists)
    if resolve(report.get("artifact")) != b_path or resolve(report.get("source_docx", {}).get("path")) != b_path:
        raise ValueError("B academic report belongs to another DOCX")
    required = {"B:independent-render", "B:rendered-pdf", "B:all-page-png", "B:visual-qa",
                "B:content-binding", "B:body-consistency", "B:metadata"}
    passed = {item.get("code") for item in report.get("checks", []) if item.get("passed") is True}
    if not required.issubset(passed):
        raise ValueError(f"v1.5 academic report lacks gates: {sorted(required - passed)}")
    source_paper, current_sources = source_bindings(resolve(report.get("source_manifest")))
    if source_paper != report.get("paper_id") or current_sources != report.get("source_fingerprints"):
        raise ValueError("academic report belongs to different Main/SI source versions")
    bound_pdf = resolve(report.get("rendered_pdf", {}).get("path"), exists=rendered_pdf is None)
    active_pdf = rendered_pdf or bound_pdf
    current_docx, current_pdf = fingerprint(b_path), fingerprint(active_pdf)
    if not same_content(current_docx, report.get("source_docx")) or not same_content(current_pdf, report.get("rendered_pdf")):
        raise ValueError("stale source_docx/rendered_pdf content binding; re-render and review")
    if len(PdfReader(str(active_pdf)).pages) != report["rendered_pdf"].get("pages"):
        raise ValueError("rendered PDF page count differs from validated report")
    qa = report.get("visual_qa", {})
    qa_path = resolve(qa.get("path"))
    if not matches_fingerprint(qa_path, qa):
        raise ValueError("visual sign-off differs from validated report")
    qa_data = json.loads(qa_path.read_text(encoding="utf-8-sig"))
    if not same_content(current_docx, qa_data.get("source_docx")) or not same_content(current_pdf, qa_data.get("rendered_pdf")):
        raise ValueError("visual sign-off is not bound to current DOCX/PDF")
    if not qa_data.get("reviewer") or not qa_data.get("reviewed_at"):
        raise ValueError("REVIEW_REQUIRED: missing attributable visual reviewer")
    return active_pdf


def export(b_path: Path, academic_report: Path, rendered_pdf: Path, output: Path, *,
           workspace_root: Path | None = None, identity: dict | None = None,
           contract_version: str = "1.5.0", allowed_roots: tuple[Path, ...] = ()) -> dict:
    root = workspace_root or academic_report.resolve().parent
    b_path = resolve_path(b_path, root, allowed_roots=allowed_roots)
    academic_report = resolve_path(academic_report, root, allowed_roots=allowed_roots)
    rendered_pdf = resolve_path(rendered_pdf, root, allowed_roots=allowed_roots)
    output = resolve_path(output, root, allowed_roots=allowed_roots, must_exist=False)
    report = json.loads(academic_report.read_text(encoding="utf-8-sig"))
    if report.get("passed") is not True or resolve_path(report.get("artifact", ""), root, allowed_roots=allowed_roots) != b_path:
        raise ValueError("B academic report has not passed for this DOCX")
    required = {"B:independent-render", "B:rendered-pdf", "B:all-page-png", "B:visual-qa"}
    passed = {item.get("code") for item in report.get("checks", []) if item.get("passed") is True}
    if not required.issubset(passed):
        raise ValueError(f"B academic report lacks rendered visual gates: {sorted(required - passed)}")
    if contract_version == "1.5.0":
        require_identity(report, identity or {k: report.get(k) for k in ("paper_id", "workflow_id", "contract_version")})
        if validate_bound_report(b_path, academic_report, report, root, allowed_roots) != rendered_pdf:
            raise ValueError("requested PDF path differs from signed independent render")
    else:
        render_evidence = next((str(item.get("detail") or "") for item in report.get("checks", []) if item.get("code") == "B:independent-render"), "")
        prefix = "rendered by independent office engine: "
        if not render_evidence.startswith(prefix) or resolve_path(render_evidence[len(prefix):], root, allowed_roots=allowed_roots) != rendered_pdf:
            raise ValueError("requested B PDF is not the academic report's independent render")
    if not rendered_pdf.is_file() or rendered_pdf.stat().st_size == 0:
        raise ValueError("independent B PDF is missing or empty")
    reader = PdfReader(str(rendered_pdf))
    if not reader.pages:
        raise ValueError("B PDF has no pages")
    if contract_version == "1.5.0" and report["rendered_pdf"].get("pages") != len(reader.pages):
        raise ValueError("rendered PDF page count differs from validated report")
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    missing = [heading for heading in TOP_LEVEL_HEADINGS if heading not in text]
    if missing:
        raise ValueError(f"B PDF headings not extractable: {missing}")
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(rendered_pdf, output)
    result = {
        "schema_version": 1,
        "B_PDF_EXPORT_PASS": True,
        "source_docx": str(b_path.resolve()),
        "pdf_path": str(output.resolve()),
        "pages": len(reader.pages),
        "academic_report": str(academic_report.resolve()),
    }
    if contract_version == "1.5.0":
        copied_binding = fingerprint(output)
        if not same_content(copied_binding, report["rendered_pdf"]):
            raise ValueError("archive PDF copy differs from signed render")
        result.update({k: report[k] for k in ("paper_id", "workflow_id", "contract_version")})
        result.update({"source_docx_binding": report["source_docx"], "rendered_pdf_binding": report["rendered_pdf"],
                       "pdf_binding": copied_binding, "academic_report_binding": fingerprint(academic_report),
                       "visual_qa": report["visual_qa"], "source_fingerprints": report["source_fingerprints"]})
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--b-path", type=Path, required=True)
    parser.add_argument("--academic-report", type=Path, required=True)
    parser.add_argument("--rendered-pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--allow-external-root", type=Path, action="append", default=[])
    args = parser.parse_args(argv)
    try:
        identity = json.loads(resolve_path(args.manifest, args.workspace_root, allowed_roots=tuple(args.allow_external_root)).read_text(encoding="utf-8-sig"))
        payload = export(args.b_path, args.academic_report, args.rendered_pdf, args.output,
                         workspace_root=args.workspace_root, identity=identity,
                         contract_version=identity.get("contract_version"), allowed_roots=tuple(args.allow_external_root))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    try:
        report_path = resolve_path(args.report, args.workspace_root, allowed_roots=tuple(args.allow_external_root), must_exist=False)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
