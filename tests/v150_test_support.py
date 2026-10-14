"""Synthetic evidence only. Signers here are TEST attestations, not real reviews."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pymupdf
from artifact_binding import fingerprint
from main_source_index import build_index


def bind_c_map(root: Path, markdown: str, mapping: dict) -> tuple[dict, dict]:
    from validate_c_review import extract_comment
    pdf = root / "Main.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((40, 40), "10.1234/synthetic")
        page.insert_text((40, 80), "Discussion")
        page.insert_text((40, 120), "Memory improved after sleep; measurement limitations; p = .032.")
        doc.save(pdf)
    source = {"paper_id": "synthetic-paper", "doi": "10.1234/synthetic", "package_status": "READY",
              "sources": [{"source_type": "MAIN", "source_id": "SRC-M1", "availability": "AVAILABLE",
                           "version": "TEST-v1", "local_path": "Main.pdf", "sha256": fingerprint(pdf)["sha256"], "bytes": pdf.stat().st_size}]}
    manifest = root / "source_manifest.json"
    manifest.write_text(json.dumps(source), encoding="utf-8")
    index = build_index(manifest)
    result = copy.deepcopy(mapping)
    result.update({k: index[k] for k in ("paper_id", "doi", "source_id", "sha256", "version")})
    result.update({"workflow_id": "synthetic-workflow", "contract_version": "1.5.0", "source_scope": "MAIN_VISIBLE_ONLY"})
    judgments = []
    ids = []
    for number, paragraph in enumerate(result["paragraphs"], 1):
        for position, claim in enumerate(paragraph["claims"], 1):
            cid = f"TEST-{number}-{position}"
            ids.append(cid)
            claim["claim_id"] = cid
            claim["source_anchor"] = {"source_id": index["source_id"], "sha256": index["sha256"],
                                      "page": 1, "block": 3, "section": "discussion",
                                      "quote": "Memory improved after sleep"}
            judgments.append({"claim_id": cid, "status": "PASS", "reason": "TEST synthetic reviewer checks direction and scope against quoted block",
                              "claim_text_sha256": hashlib.sha256(claim["text"].encode()).hexdigest(),
                              "source_anchor": copy.deepcopy(claim["source_anchor"])})
    for entry in result["semantic_review"].values():
        entry["claim_ids"] = ids
    result["signoff"] = {"reviewer": "TEST synthetic human attestation", "reviewed_at": "2026-10-14T12:00:00+08:00",
                         "all_material_claims_reviewed": True,
                         "main_sha256": index["sha256"], "comment_sha256": hashlib.sha256(extract_comment(markdown).encode()).hexdigest(),
                         "claims": judgments, "semantic_review": copy.deepcopy(result["semantic_review"])}
    return result, index


def b_report(root: Path, b_path: Path, rendered: Path) -> dict:
    """Build an honest synthetic byte-binding fixture, not an Office attestation."""
    from pypdf import PdfReader
    from validate_deep_reading_package import body_consistency, VISUAL_FLAGS
    from sanitize_docx_metadata import sanitize_docx, validate_docx_metadata
    from artifact_binding import source_bindings
    sanitize_docx(b_path)
    assert not validate_docx_metadata(b_path)
    assert not body_consistency(b_path, rendered)
    bind_c_map(root, "## 评论\n测试", {"paragraphs": [], "semantic_review": {}})
    source_paper, sources = source_bindings(root / "source_manifest.json")
    pages = len(PdfReader(str(rendered)).pages)
    qa = {"renderer": "Microsoft Word TEST provenance fixture", "reviewer": "TEST synthetic reviewer",
          "reviewed_at": "2026-10-14T12:00:00+08:00", "wrong_page_count": False,
          "source_docx": fingerprint(b_path), "rendered_pdf": fingerprint(rendered),
          "pages": [{"page": i, "reviewed": True, **{flag: False for flag in VISUAL_FLAGS}} for i in range(1, pages + 1)]}
    qa_path = root / "visual_qa.json"
    qa_path.write_text(json.dumps(qa), encoding="utf-8")
    return {"passed": True, "artifact": str(b_path.resolve()), "paper_id": source_paper,
            "workflow_id": "synthetic-workflow", "contract_version": "1.5.0",
            "source_manifest": str((root / "source_manifest.json").resolve()), "source_fingerprints": sources,
            "source_docx": {"path": str(b_path.resolve()), **fingerprint(b_path)},
            "rendered_pdf": {"path": str(rendered.resolve()), **fingerprint(rendered), "pages": pages},
            "visual_qa": {"path": str(qa_path.resolve()), **fingerprint(qa_path)},
            "checks": [{"code": code, "passed": True, "detail": "TEST synthetic binding fixture"}
                       for code in ("B:independent-render", "B:rendered-pdf", "B:all-page-png", "B:visual-qa",
                                    "B:metadata", "B:body-consistency", "B:content-binding")]}
