#!/usr/bin/env python3
"""Validate the v1.5 public C submission and its private Main-source map."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import hashlib
from datetime import datetime
from dataclasses import asdict, dataclass
from pathlib import Path

from main_source_index import build_index, locate
from artifact_binding import fingerprint


REQUIRED_HEADINGS = (
    "期刊", "发表日期", "英文题目", "中文题目", "作者", "原文地址",
    "评阅人", "Original Abstract", "中文摘要", "评论",
)
SEMANTIC_GATES = (
    "BACKGROUND_GAP_PASS", "CORE_RESULT_CHAIN_PASS", "MAIN_SOURCE_SCOPE_PASS",
    "AUTHOR_LIMITATION_POLICY_PASS", "NO_SI_ONLY_CLAIMS_PASS", "FIELD_IMPLICATION_PASS",
    "CLAIM_STRENGTH_PASS", "STYLE_NATURALNESS_PASS",
)
INTERNAL_PATTERN = re.compile(r"\b(?:AUD|AN|CLM)-\d+\b|\bZotero\s*key\b|B\s*§\s*\d|\bSI\s*(?:Table|Figure)\s*S?\d+", re.I)


@dataclass(frozen=True)
class CCheck:
    code: str
    passed: bool
    detail: str


def extract_comment(markdown: str) -> str:
    match = re.search(r"(?m)^##\s+评论\s*$", markdown)
    if not match:
        raise ValueError("C requires a level-2 评论 heading")
    tail = markdown[match.end():]
    return re.split(r"(?m)^#{1,2}\s+", tail, maxsplit=1)[0].strip()


def visible_text(markdown: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", markdown)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"(?m)^\s*(?:#{1,6}\s+|>\s*|[-*+]\s+|\d+\.\s+)", "", text)
    text = re.sub(r"(?<!\w)[*_~`]+|[*_~`]+(?!\w)", "", text)
    return text


def effective_visible_char_count(markdown: str) -> int:
    return sum(
        1 for char in visible_text(markdown)
        if not unicodedata.category(char).startswith(("Z", "C")) and not char.isspace()
    )


def validate(markdown: str, source_map: dict | None, *, min_chars: int = 800, max_chars: int = 1000,
             source_index: dict | None = None, expected_identity: dict | None = None) -> list[CCheck]:
    headings = re.findall(r"(?m)^##\s+(.+?)\s*$", markdown)
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in headings]
    checks = [CCheck("C_SUBMISSION_PROFILE_PASS", headings == list(REQUIRED_HEADINGS),
                     "public headings match submission profile" if headings == list(REQUIRED_HEADINGS)
                     else f"missing or extra headings: missing={missing}, observed={headings}")]
    try:
        comment = extract_comment(markdown)
    except ValueError as exc:
        return checks + [CCheck("COMMENT_LENGTH_PASS", False, str(exc))]
    # Callers may tighten the submission window, never relax the v1.5 contract.
    min_chars, max_chars = max(800, min_chars), min(1000, max_chars)
    count = effective_visible_char_count(comment)
    checks.append(CCheck("COMMENT_LENGTH_PASS", min_chars <= count <= max_chars, f"{count} visible characters; required {min_chars}-{max_chars}"))
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", comment) if part.strip()]
    checks.append(CCheck("C_PARAGRAPH_SHAPE_PASS", 3 <= len(paragraphs) <= 5, f"{len(paragraphs)} paragraphs; expected 3-5"))
    matches = INTERNAL_PATTERN.findall(markdown)
    checks.append(CCheck("NO_INTERNAL_AUDIT_METADATA_PASS", not matches, f"internal markers: {matches}" if matches else "no internal markers in public C"))
    if not isinstance(source_map, dict):
        checks.append(CCheck("C_SOURCE_MAP_PASS", False, "private source map required for v1.5 C"))
        return checks
    mapped = source_map.get("paragraphs")
    valid_map = isinstance(mapped, list) and len(mapped) == len(paragraphs)
    violations: list[str] = []
    identity_ok = bool(source_index) and all(source_map.get(key) == source_index.get(key) and source_index.get(key)
                                            for key in ("paper_id", "doi", "source_id", "sha256", "version"))
    if expected_identity:
        identity_ok = identity_ok and all(source_map.get(k) == v and v for k, v in expected_identity.items())
    if not identity_ok:
        violations.append("REVIEW_REQUIRED: verified Main index/identity/version missing or mismatched")
    claim_records = {}
    critique = source_map.get("critique_approval", {})
    critique_ok = source_map.get("critique_mode") == "author_plus_major" and isinstance(critique, dict) and all(
        str(critique.get(k) or "").strip() for k in ("reviewer", "reviewed_at", "reason"))
    if source_map.get("source_scope") != "MAIN_VISIBLE_ONLY":
        violations.append("C requires MAIN_VISIBLE_ONLY source scope")
    if valid_map:
        for index, entry in enumerate(mapped):
            claims = entry.get("claims") if isinstance(entry, dict) else None
            if not isinstance(entry, dict) or entry.get("paragraph_index") != index + 1 or not isinstance(claims, list) or not claims:
                violations.append(f"paragraph {index + 1}: missing claim mapping")
                continue
            for claim in claims:
                if not isinstance(claim, dict):
                    violations.append(f"paragraph {index + 1}: invalid claim")
                    continue
                snippet = str(claim.get("text") or "").strip()
                claim_id = str(claim.get("claim_id") or "").strip()
                if not claim_id or claim_id in claim_records:
                    violations.append(f"paragraph {index + 1}: missing/duplicate claim ID")
                else:
                    claim_records[claim_id] = claim
                if not snippet or snippet not in paragraphs[index]:
                    violations.append(f"paragraph {index + 1}: claim text absent")
                if claim.get("source_class") != "MAIN" or not identity_ok or not locate(claim.get("source_anchor"), source_index):
                    violations.append(f"{claim_id or index + 1}: Main page/block/quote/source cannot be located")
                if claim.get("kind") == "limitation" and (
                    claim.get("author_acknowledged") is not True
                    or not isinstance(claim.get("source_anchor"), dict)
                    or str(claim["source_anchor"].get("section") or "").casefold() not in {"discussion", "limitations"}
                ):
                    violations.append(f"paragraph {index + 1}: limitation lacks author Discussion anchor")
                if claim.get("kind") == "evaluator_critique" and not (critique_ok and claim.get("attribution") == "reviewer"):
                    violations.append(f"{claim_id}: evaluator critique requires reviewed explicit configuration and attribution")
    checks.append(CCheck("C_SOURCE_MAP_PASS", bool(valid_map) and not violations,
                         "; ".join(violations) if violations else "each paragraph has Main-anchored claims"))
    reviews = source_map.get("semantic_review", {})
    signoff = source_map.get("signoff", {})
    if not isinstance(signoff, dict):
        signoff = {}
    signoff_ok = isinstance(signoff, dict) and all(str(signoff.get(k) or "").strip() for k in ("reviewer", "reviewed_at"))
    try:
        signed_at = datetime.fromisoformat(str(signoff.get("reviewed_at") or "").replace("Z", "+00:00"))
        signoff_ok = signoff_ok and signed_at.tzinfo is not None
    except (ValueError, AttributeError):
        signoff_ok = False
    signoff_ok = signoff_ok and identity_ok and signoff.get("main_sha256") == source_map.get("sha256") and signoff.get("comment_sha256") == hashlib.sha256(comment.encode("utf-8")).hexdigest()
    judgments = signoff.get("claims", []) if isinstance(signoff, dict) else []
    judged = {}
    if isinstance(judgments, list):
        for judgment in judgments:
            if not isinstance(judgment, dict) or judgment.get("claim_id") in judged:
                signoff_ok = False
                continue
            judged[judgment.get("claim_id")] = judgment
    signoff_ok = signoff_ok and bool(claim_records) and set(judged) == set(claim_records)
    for cid, claim in claim_records.items():
        judgment = judged.get(cid, {})
        signoff_ok = signoff_ok and judgment.get("status") == "PASS" and bool(str(judgment.get("reason") or "").strip()) and judgment.get("claim_text_sha256") == hashlib.sha256(str(claim.get("text") or "").encode("utf-8")).hexdigest() and judgment.get("source_anchor") == claim.get("source_anchor")
    signoff_ok = signoff_ok and signoff.get("all_material_claims_reviewed") is True
    if critique_ok:
        signoff_ok = signoff_ok and signoff.get("critique_approval") == critique
    checks.append(CCheck("C_HUMAN_SIGNOFF_PASS", bool(signoff_ok) and bool(valid_map) and not violations,
                         "source-bound reviewer record present; semantic judgment is human responsibility" if signoff_ok and not violations else "REVIEW_REQUIRED: valid Main-bound human sign-off required; rejected claims must retain reasons"))
    for gate in SEMANTIC_GATES:
        entry = reviews.get(gate) if isinstance(reviews, dict) else None
        passed = bool(signoff_ok) and not violations and isinstance(entry, dict) and entry.get("status") == "PASS" and bool(str(entry.get("evidence") or "").strip()) and bool(entry.get("claim_ids")) and set(entry["claim_ids"]).issubset(claim_records) and signoff.get("semantic_review") == reviews
        checks.append(CCheck(gate, passed, "reviewed with recorded evidence" if passed else "requires source-grounded semantic review"))
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--c-path", type=Path, required=True)
    parser.add_argument("--source-map", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True, help="Verified Canonical Main source package; never trust an embedded map index")
    parser.add_argument("--manifest", type=Path, required=True, help="Workflow identity to bind to C")
    parser.add_argument("--index-report", type=Path, help="Private generated Main page/block index")
    parser.add_argument("--min-chars", type=int, default=800)
    parser.add_argument("--max-chars", type=int, default=1000)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    identity, source_index = {}, None
    try:
        markdown = args.c_path.read_text(encoding="utf-8-sig")
        source_map = json.loads(args.source_map.read_text(encoding="utf-8-sig"))
        source_index = build_index(args.source_manifest)
        workflow = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
        identity = {k: workflow.get(k) for k in ("paper_id", "workflow_id", "contract_version")}
        if args.index_report:
            args.index_report.write_text(json.dumps(source_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        checks = validate(markdown, source_map, min_chars=args.min_chars, max_chars=args.max_chars,
                          source_index=source_index, expected_identity=identity)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        checks = [CCheck("C_INPUT_PASS", False, str(exc))]
    payload = {"passed": all(check.passed for check in checks), "checks": [asdict(check) for check in checks]}
    payload.update({"schema_version": 1, **identity})
    if source_index:
        payload["main"] = {k: source_index[k] for k in ("source_id", "sha256", "size_bytes", "version", "doi")}
        payload["public_c"] = fingerprint(args.c_path)
        payload["private_source_map"] = fingerprint(args.source_map)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
