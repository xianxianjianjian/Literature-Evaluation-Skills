#!/usr/bin/env python3
"""Validate v1.4.2 narrative, figure and source-mapping evidence for B."""

from __future__ import annotations

import csv
import json
import zipfile
import posixpath
import re
from xml.etree import ElementTree as ET
from pathlib import Path
from typing import Any

NARRATIVE_SECTIONS = {
    "INTRODUCTION", "METHODS", "RESULTS", "DISCUSSION", "INNOVATION",
    "LIMITATIONS", "REDESIGN", "TRANSFER",
}
CORE_CLAIM_CLASSES = {"CLM", "AN", "AUD", "HYPOTHESIS"}
FIGURE_CATEGORIES = {
    "DESIGN", "METHOD", "CORE_RESULT", "MECHANISM", "ROBUSTNESS", "NULL",
    "SUPPORTING", "NONESSENTIAL",
}
CORE_FIGURE_CATEGORIES = {
    "DESIGN", "METHOD", "CORE_RESULT", "MECHANISM", "ROBUSTNESS", "NULL",
}
MAPPING_FIELDS = {
    "source_id", "source_locator", "notebook_section", "claim_id", "coverage_type",
}


class DeepEvidenceError(ValueError):
    pass


def _substantive(value: Any, minimum: int = 80) -> bool:
    # A locator/title is not an explanation; no total-word-count score is used.
    return isinstance(value, str) and bool(re.search(r'[A-Za-z\u3400-\u9fff].+[。.!?！？]', value))


def validate_narrative_coverage(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise DeepEvidenceError("b_narrative_coverage.json schema_version must be 1.")
    sections = data.get("sections")
    if not isinstance(sections, dict):
        raise DeepEvidenceError("Narrative coverage requires sections.")
    failures: list[str] = []
    for name in sorted(NARRATIVE_SECTIONS):
        entry = sections.get(name)
        if not isinstance(entry, dict) or not _substantive(entry.get("prose")):
            failures.append(f"{name}: substantive prose is missing")
        elif not entry.get("source_anchors"):
            failures.append(f"{name}: source anchors are missing")
    claims = data.get("claim_closure")
    if not isinstance(claims, list) or not claims:
        failures.append("claim_closure is missing")
    else:
        seen_classes = set()
        for claim in claims:
            claim_id = str(claim.get("claim_id") or "")
            claim_class = str(claim.get("claim_class") or "").upper()
            seen_classes.add(claim_class)
            if not claim_id or not _substantive(claim.get("prose"), 40) or not claim.get("source_anchor"):
                failures.append(f"{claim_id or '<unknown>'}: prose closure/source anchor missing")
        absent = CORE_CLAIM_CLASSES - seen_classes
        if absent:
            failures.append(f"core claim classes missing: {sorted(absent)}")
    return {"schema_version": 1, "passed": not failures, "failures": failures}


def validate_figure_inventory(data: dict[str, Any], *, base_dir: Path | None = None) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise DeepEvidenceError("b_figure_inventory.json schema_version must be 1.")
    figures = data.get("figures")
    if not isinstance(figures, list):
        raise DeepEvidenceError("Figure inventory requires figures.")
    failures: list[str] = []
    for figure in figures:
        figure_id = str(figure.get("figure_id") or "<unknown>")
        category = str(figure.get("category") or "")
        if category not in FIGURE_CATEGORIES:
            failures.append(f"{figure_id}: invalid category")
            continue
        if not figure.get("source_anchor"):
            failures.append(f"{figure_id}: source anchor missing")
        if category in CORE_FIGURE_CATEGORIES:
            if figure.get("embedded") is not True:
                failures.append(f"{figure_id}: core figure is not embedded")
            image_path = str(figure.get("image_path") or "")
            if not image_path:
                failures.append(f"{figure_id}: image_path missing")
            elif base_dir is not None:
                path = Path(image_path)
                if not path.is_absolute():
                    path = base_dir / path
                if not path.is_file():
                    failures.append(f"{figure_id}: image file missing")
            if not str(figure.get("translated_caption") or "").strip():
                failures.append(f"{figure_id}: translated caption missing")
            if not _substantive(figure.get("interpretation"), 60):
                failures.append(f"{figure_id}: substantive interpretation missing")
    return {"schema_version": 1, "passed": not failures, "failures": failures}


def validate_docx_evidence(path: Path, narrative: dict[str, Any], figures: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    """Check the artifact, not merely the generator's coverage assertions.

    Narrative must occur in ordinary paragraphs outside tables. Core images
    must be referenced by a drawing in document.xml, not just stored in ZIP.
    Compare bytes directly: no extra integrity fingerprint is necessary.
    """
    normalize = lambda value: "".join(str(value).split())
    failures = []
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
          "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
        prose = "".join(normalize("".join(p.itertext())) for p in root.findall("w:body/w:p", ns))
        for name, row in narrative.get("sections", {}).items():
            if normalize(row.get("prose", "")) not in prose:
                failures.append(f"{name}: narrative absent from DOCX prose")
        for row in narrative.get("claim_closure", []):
            if normalize(row.get("prose", "")) not in prose:
                failures.append(f"{row.get('claim_id')}: claim closure absent from DOCX prose")
        used = {node.get(f"{{{ns['r']}}}embed") for node in root.findall('.//a:blip', ns)}
        rels = ET.fromstring(archive.read('word/_rels/document.xml.rels'))
        embedded = [archive.read(posixpath.normpath('word/' + row.get('Target')))
                    for row in rels if row.get('Id') in used and row.get('TargetMode') != 'External']
        for row in figures.get('figures', []):
            if row.get('category') not in CORE_FIGURE_CATEGORIES:
                continue
            figure_id = row.get('figure_id')
            img = base_dir / str(row.get('image_path') or '')
            if not img.is_file() or img.read_bytes() not in embedded:
                failures.append(f'{figure_id}: image not embedded in DOCX drawing')
            for field in ('translated_caption', 'interpretation', 'source_anchor'):
                if not row.get(field) or normalize(row[field]) not in prose:
                    failures.append(f'{figure_id}: {field} absent from DOCX prose')
    source_path = base_dir / 'source_figure_inventory.jsonl'
    if not source_path.is_file():
        failures.append('source figure inventory missing; cannot determine omitted evidence')
    else:
        source_rows = [json.loads(line) for line in source_path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
        indexed = {row.get('figure_id'): row for row in figures.get('figures', [])}
        for row in source_rows:
            item = indexed.get(row.get('figure_id'))
            if item is None:
                failures.append(f"{row.get('figure_id')}: source figure not classified")
            elif item.get('category') in CORE_FIGURE_CATEGORIES and row.get('translated_text') and normalize(item.get('translated_caption')) != normalize(row['translated_text']):
                failures.append(f"{row.get('figure_id')}: caption differs from full source-caption translation")
    return {'passed': not failures, 'failures': failures}


def validate_source_mapping(path: Path, *, required_claim_ids: set[str] | None = None) -> dict[str, Any]:
    if not path.is_file():
        raise DeepEvidenceError(f"Source mapping is missing: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        if not MAPPING_FIELDS.issubset(fields):
            raise DeepEvidenceError(f"Source mapping fields missing: {sorted(MAPPING_FIELDS-fields)}")
        rows = list(reader)
    failures: list[str] = []
    if not rows:
        failures.append("source mapping has no rows")
    mapped_claims: set[str] = set()
    for index, row in enumerate(rows, 2):
        if any(not str(row.get(field) or "").strip() for field in MAPPING_FIELDS):
            failures.append(f"row {index}: required semantic field is blank")
        source_id = str(row.get("source_id") or "")
        locator = str(row.get("source_locator") or "")
        if not source_id.startswith("SRC-") or not any(token in locator.lower() for token in ("p.", "page", "fig", "table", "section", "supp")):
            failures.append(f"row {index}: source identity/locator is not auditable")
        mapped_claims.add(str(row.get("claim_id") or ""))
    missing = (required_claim_ids or set()) - mapped_claims
    if missing:
        failures.append(f"required claims are unmapped: {sorted(missing)}")
    return {"schema_version": 1, "passed": not failures, "failures": failures, "row_count": len(rows)}


def validate_deep_evidence(
    narrative: dict[str, Any], figures: dict[str, Any], mapping_path: Path, *, base_dir: Path | None = None,
    docx_path: Path | None = None
) -> dict[str, Any]:
    narrative_report = validate_narrative_coverage(narrative)
    figure_report = validate_figure_inventory(figures, base_dir=base_dir)
    required_claims = {
        str(item.get("claim_id")) for item in narrative.get("claim_closure", []) if item.get("claim_id")
    }
    if base_dir is not None:
        evidence_path = base_dir / 'claim_evidence_map.csv'
        if evidence_path.is_file():
            with evidence_path.open(encoding='utf-8-sig', newline='') as handle:
                for row in csv.DictReader(handle):
                    required_claims.add(str(row.get('Claim_ID') or row.get('claim_id') or ''))
                    required_claims.update(re.findall(r'(?:AN|AUD)-\d+', str(row.get('Related_ID',''))))
        required_claims.discard('')
        closed = {str(row.get('claim_id')) for row in narrative.get('claim_closure', [])}
        absent = required_claims - closed
        if absent:
            narrative_report['failures'].append(f'core evidence-map claims lack prose closure: {sorted(absent)}')
            narrative_report['passed'] = False
    mapping_report = validate_source_mapping(mapping_path, required_claim_ids=required_claims)
    artifact_report = validate_docx_evidence(docx_path, narrative, figures, base_dir) if docx_path is not None and base_dir is not None else {'passed': False, 'failures': ['DOCX artifact required for completion']}
    return {
        "schema_version": 1,
        "contract_version": "1.4.2",
        "passed": all(report["passed"] for report in (narrative_report, figure_report, mapping_report, artifact_report)),
        "narrative": narrative_report,
        "figures": figure_report,
        "source_mapping": mapping_report,
        "artifact": artifact_report,
    }
