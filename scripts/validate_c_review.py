#!/usr/bin/env python3
"""Validate the v1.5 public C submission and its private Main-source map."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path


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


def validate(markdown: str, source_map: dict | None, *, min_chars: int = 800, max_chars: int = 1000) -> list[CCheck]:
    headings = re.findall(r"(?m)^##\s+(.+?)\s*$", markdown)
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in headings]
    checks = [CCheck("C_SUBMISSION_PROFILE_PASS", not missing and len(headings) == len(REQUIRED_HEADINGS),
                     "public headings match submission profile" if not missing and len(headings) == len(REQUIRED_HEADINGS)
                     else f"missing or extra headings: missing={missing}, observed={headings}")]
    try:
        comment = extract_comment(markdown)
    except ValueError as exc:
        return checks + [CCheck("COMMENT_LENGTH_PASS", False, str(exc))]
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
                if not snippet or snippet not in paragraphs[index]:
                    violations.append(f"paragraph {index + 1}: claim text absent")
                if claim.get("source_class") != "MAIN" or not str(claim.get("source_anchor") or "").strip():
                    violations.append(f"paragraph {index + 1}: non-Main or unanchored claim")
                if claim.get("kind") == "limitation" and (
                    claim.get("author_acknowledged") is not True
                    or "Discussion" not in str(claim.get("source_anchor"))
                ):
                    violations.append(f"paragraph {index + 1}: limitation lacks author Discussion anchor")
    checks.append(CCheck("C_SOURCE_MAP_PASS", bool(valid_map) and not violations,
                         "; ".join(violations) if violations else "each paragraph has Main-anchored claims"))
    reviews = source_map.get("semantic_review", {})
    for gate in SEMANTIC_GATES:
        entry = reviews.get(gate) if isinstance(reviews, dict) else None
        passed = isinstance(entry, dict) and entry.get("status") == "PASS" and bool(str(entry.get("evidence") or "").strip())
        checks.append(CCheck(gate, passed, "reviewed with recorded evidence" if passed else "requires source-grounded semantic review"))
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--c-path", type=Path, required=True)
    parser.add_argument("--source-map", type=Path, required=True)
    parser.add_argument("--min-chars", type=int, default=800)
    parser.add_argument("--max-chars", type=int, default=1000)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        markdown = args.c_path.read_text(encoding="utf-8-sig")
        source_map = json.loads(args.source_map.read_text(encoding="utf-8-sig"))
        checks = validate(markdown, source_map, min_chars=args.min_chars, max_chars=args.max_chars)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        checks = [CCheck("C_INPUT_PASS", False, str(exc))]
    payload = {"passed": all(check.passed for check in checks), "checks": [asdict(check) for check in checks]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
