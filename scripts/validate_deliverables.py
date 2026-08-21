#!/usr/bin/env python3
"""Validate V1 repository structure, workflow state, and A/B/C deliverable contracts.

This helper performs deterministic structural checks only. It does not replace
visual PDF/DOCX QA or academic-quality judgment required by the specialist
Skills.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from workflow_state import WorkflowStateError, load_manifest

REQUIRED_DIRECTORIES = [
    "skills/weekly-literature-evaluation/references",
    "skills/literature-search/references",
    "skills/paper-translation/references",
    "skills/paper-deep-reading/references",
    "shared",
    "knowledge",
    "scripts",
    "weekly_reviews",
]
REQUIRED_FILES = [
    "README.md", ".gitignore",
    "skills/weekly-literature-evaluation/SKILL.md",
    "skills/weekly-literature-evaluation/references/workflow-routing.md",
    "skills/literature-search/SKILL.md",
    "skills/literature-search/references/topic-planning.md",
    "skills/literature-search/references/journal-mapping.md",
    "skills/literature-search/references/search-strategy.md",
    "skills/literature-search/references/screening-and-ranking.md",
    "skills/literature-search/references/integrity-check.md",
    "skills/literature-search/references/zotero-ingest.md",
    "skills/paper-translation/SKILL.md",
    "skills/paper-translation/references/terminology-policy.md",
    "skills/paper-translation/references/abstract-translation.md",
    "skills/paper-translation/references/fulltext-translation.md",
    "skills/paper-translation/references/figures-tables-supplement.md",
    "skills/paper-translation/references/mirror-layout.md",
    "skills/paper-translation/references/translation-qc.md",
    "skills/paper-deep-reading/SKILL.md",
    "skills/paper-deep-reading/references/source-audit.md",
    "skills/paper-deep-reading/references/introduction-reconstruction.md",
    "skills/paper-deep-reading/references/methods-reconstruction.md",
    "skills/paper-deep-reading/references/results-analysis.md",
    "skills/paper-deep-reading/references/discussion-and-critique.md",
    "skills/paper-deep-reading/references/dynamic-coverage.md",
    "skills/paper-deep-reading/references/deliverables-and-qc.md",
    "shared/evidence-policy.md", "shared/identifier-policy.md",
    "shared/source-identity-policy.md", "shared/zotero-policy.md",
    "shared/state-contract.md", "shared/data-format-policy.md",
    "knowledge/research_profile.md", "knowledge/submission_profile.yaml",
    "knowledge/journal_registry.csv", "knowledge/terminology_registry.csv",
    "knowledge/terminology_evidence.jsonl", "knowledge/reading_history.csv",
    "knowledge/selection_log.csv", "scripts/zotero_bridge.py",
    "scripts/terminology_registry.py", "scripts/history_manager.py",
    "scripts/workflow_state.py", "scripts/validate_deliverables.py",
    "scripts/mirror_pdf.py",
]
CSV_HEADERS = {
    "journal_registry.csv": "Journal,Field,Scope,Publisher,Peer_Reviewed,Priority,Strength,Caution,Status,Verified_Date".split(","),
    "terminology_registry.csv": "Term_ID,English_Term,Abbreviation,Preferred_Chinese,Alternative_Chinese,Discipline,Subfield,Definition,Context,Confidence,Evidence_Level,Evidence_IDs,Status,First_Verified,Last_Verified,Notes".split(","),
    "reading_history.csv": "Week,Topic,Paper_ID,Title,DOI,Journal,Year,Study_Type,Core_Finding,Method_Value,Transfer_Value,Major_Limitation,Open_Questions,Next_Reading_Direction,Zotero_Item_Key,A_Attachment_Key,B_Attachment_Key,Git_Review_Path,Completed_Date".split(","),
    "selection_log.csv": "Week,Topic,Paper_ID,Title,DOI,Journal,Year,Role,Quality_Gate,Weighted_Score,Selection_Decision,Selection_Reason,Zotero_Item_Key,Logged_Date".split(","),
}
COMMENT_HEADING_PATTERN = re.compile(r"^##\s+(?:评论|评译评论|Comment|Review)\s*$", re.IGNORECASE)
SECTION_HEADING_PATTERN = re.compile(r"^##\s+(.+?)\s*$")
SECTION_END_PATTERN = re.compile(r"^#{1,2}\s+")
C_FIELD_ALIASES = {
    "journal": ("期刊", "journal"),
    "publication_date": ("发表日期", "出版日期", "上线日期", "publication date", "online date"),
    "english_title": ("英文题目", "英文标题", "english title"),
    "chinese_title": ("中文题目", "中文标题", "chinese title"),
    "authors": ("作者", "authors"),
    "url": ("原文链接", "原文地址", "url", "article url"),
    "original_abstract": ("原文摘要", "original abstract"),
    "translated_abstract": ("中文摘要", "摘要译文", "canonical chinese abstract", "translated abstract"),
    "comment": ("评论", "评译评论", "comment", "review"),
    "reviewer": ("评阅人", "评译人", "reviewer"),
}
B_SECTION_ALIASES = [
    ("文献定位", "research audit", "literature positioning"),
    ("摘要", "abstract"),
    ("引言", "introduction"),
    ("方法", "methods"),
    ("结果", "results"),
    ("讨论", "discussion"),
    ("创新", "innovation"),
    ("局限", "limitations"),
    ("改进", "redesign"),
    ("迁移", "transfer value"),
    ("术语", "terminology", "evidence index"),
]


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


def load_profile(root: Path) -> dict:
    return json.loads(
        (root / "knowledge" / "submission_profile.yaml").read_text(encoding="utf-8")
    )


def check_foundation(root: Path) -> list[Check]:
    checks: list[Check] = []
    for relative in REQUIRED_DIRECTORIES:
        exists = (root / relative).is_dir()
        checks.append(Check(f"directory:{relative}", exists, "present" if exists else "missing"))
    for relative in REQUIRED_FILES:
        exists = (root / relative).is_file()
        checks.append(Check(f"file:{relative}", exists, "present" if exists else "missing"))
    try:
        profile = load_profile(root)
        weekly = profile.get("weekly_review", {})
        valid = (
            profile.get("schema_version") == 1
            and isinstance(weekly, dict)
            and isinstance(weekly.get("minimum_comment_chars"), int)
            and weekly.get("minimum_comment_chars", 0) > 0
            and isinstance(weekly.get("original_abstract_required"), bool)
            and isinstance(weekly.get("translated_abstract_required"), bool)
        )
        checks.append(
            Check("submission_profile", valid, "schema valid" if valid else "invalid schema")
        )
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        checks.append(Check("submission_profile", False, str(exc)))
    for name, expected in CSV_HEADERS.items():
        path = root / "knowledge" / name
        if not path.is_file():
            continue
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                actual = next(csv.reader(handle), None)
            checks.append(
                Check(
                    f"schema:{name}",
                    actual == expected,
                    "header valid" if actual == expected else "header mismatch",
                )
            )
        except (OSError, csv.Error) as exc:
            checks.append(Check(f"schema:{name}", False, str(exc)))
    return checks


def check_manifest(path: Path, *, require_workflow_complete: bool = False) -> list[Check]:
    try:
        data = load_manifest(path)
    except (WorkflowStateError, OSError) as exc:
        return [Check("manifest", False, str(exc))]

    checks = [Check("manifest", True, f"valid: {path}")]
    stages, outputs = data["stages"], data["outputs"]

    if stages["translation"]["status"] == "COMPLETE":
        passed = outputs["A"]["status"] == "COMPLETE"
        checks.append(
            Check(
                "manifest:translation-output",
                passed,
                "A COMPLETE" if passed else "Translation COMPLETE requires A COMPLETE",
            )
        )
    if outputs["A"]["status"] == "COMPLETE":
        passed = stages["translation"]["status"] == "COMPLETE"
        checks.append(
            Check(
                "manifest:A-translation",
                passed,
                "Translation COMPLETE" if passed else "A COMPLETE requires Translation COMPLETE",
            )
        )

    if stages["deep_reading"]["status"] == "COMPLETE":
        passed = outputs["B"]["status"] == "COMPLETE"
        checks.append(
            Check(
                "manifest:deep-reading-B",
                passed,
                "B COMPLETE" if passed else "Deep Reading COMPLETE requires B COMPLETE",
            )
        )
    if outputs["B"]["status"] == "COMPLETE":
        passed = stages["deep_reading"]["status"] == "COMPLETE"
        checks.append(
            Check(
                "manifest:B-deep-reading",
                passed,
                "Deep Reading COMPLETE" if passed else "B COMPLETE requires Deep Reading COMPLETE",
            )
        )

    if outputs["A"]["status"] == "COMPLETE":
        passed = bool(outputs["A"].get("zotero_attachment_key"))
        checks.append(
            Check(
                "manifest:A-zotero-key",
                passed,
                "attachment key present" if passed else "A COMPLETE requires verified Zotero attachment key",
            )
        )
    if outputs["B"]["status"] == "COMPLETE":
        passed = bool(outputs["B"].get("zotero_attachment_key"))
        checks.append(
            Check(
                "manifest:B-zotero-key",
                passed,
                "attachment key present" if passed else "B COMPLETE requires verified Zotero attachment key",
            )
        )
    if outputs["C"]["status"] == "COMPLETE":
        passed = bool(outputs["C"].get("git_path"))
        checks.append(
            Check(
                "manifest:C-git-path",
                passed,
                "git path present" if passed else "C COMPLETE requires git_path",
            )
        )
    if any(stage["status"] == "BLOCKED" for stage in stages.values()):
        passed = bool(data.get("blocking_issues"))
        checks.append(
            Check(
                "manifest:blocker-record",
                passed,
                "blocking issue recorded" if passed else "BLOCKED stage requires blocking_issues entry",
            )
        )

    if require_workflow_complete:
        all_stages = all(stage["status"] == "COMPLETE" for stage in stages.values())
        checks.append(
            Check(
                "workflow:stages-complete",
                all_stages,
                "all four stages COMPLETE" if all_stages else "full workflow requires all four stages COMPLETE",
            )
        )
        all_outputs = all(output["status"] == "COMPLETE" for output in outputs.values())
        checks.append(
            Check(
                "workflow:outputs-complete",
                all_outputs,
                "A/B/C COMPLETE" if all_outputs else "full workflow requires A/B/C COMPLETE",
            )
        )
        paper_ok = bool(data.get("paper_id"))
        checks.append(
            Check(
                "workflow:paper-id",
                paper_ok,
                "paper_id present" if paper_ok else "full workflow requires paper_id",
            )
        )
        no_updates = not any(stage["needs_update"] for stage in stages.values())
        checks.append(
            Check(
                "workflow:no-needs-update",
                no_updates,
                "no unresolved needs_update" if no_updates else "full workflow has unresolved needs_update",
            )
        )
        no_blockers = not data.get("blocking_issues")
        checks.append(
            Check(
                "workflow:no-blockers",
                no_blockers,
                "no blockers" if no_blockers else "full workflow has unresolved blocking_issues",
            )
        )
        no_pending = not data.get("pending_zotero_actions")
        checks.append(
            Check(
                "workflow:no-pending-zotero",
                no_pending,
                "no pending Zotero actions" if no_pending else "full workflow has pending_zotero_actions",
            )
        )
        source_checked = bool(data.get("source_change", {}).get("last_checked"))
        checks.append(
            Check(
                "workflow:source-check",
                source_checked,
                "source-change check dated" if source_checked else "full workflow requires source_change.last_checked",
            )
        )
    return checks


def check_pdf(path: Path | None, required: bool) -> Check:
    if path is None:
        return Check("artifact:A", not required, "not requested" if not required else "path required")
    if not path.is_file() or path.stat().st_size == 0:
        return Check("artifact:A", False, f"missing or empty: {path}")
    if path.suffix.lower() != ".pdf":
        return Check("artifact:A", False, "A must be a .pdf file")
    try:
        header = path.read_bytes()[:5]
    except OSError as exc:
        return Check("artifact:A", False, str(exc))
    return Check(
        "artifact:A",
        header == b"%PDF-",
        "PDF signature valid" if header == b"%PDF-" else "invalid PDF signature",
    )


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    return "\n".join(text for text in root.itertext() if text and text.strip())


def check_docx_b(path: Path | None, required: bool) -> Check:
    if path is None:
        return Check("artifact:B", not required, "not requested" if not required else "path required")
    if not path.is_file() or path.stat().st_size == 0:
        return Check("artifact:B", False, f"missing or empty: {path}")
    if path.suffix.lower() != ".docx":
        return Check("artifact:B", False, "B must be a .docx file")
    try:
        text = docx_text(path).casefold()
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        return Check("artifact:B", False, f"invalid DOCX package: {exc}")
    missing = [
        aliases[0]
        for aliases in B_SECTION_ALIASES
        if not any(alias.casefold() in text for alias in aliases)
    ]
    return Check(
        "artifact:B",
        not missing,
        "base schema markers found" if not missing else f"missing base-schema markers: {', '.join(missing)}",
    )


def parse_markdown_sections(markdown: str) -> dict[str, str]:
    lines = markdown.splitlines()
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        match = SECTION_HEADING_PATTERN.fullmatch(line.strip())
        if match:
            current = match.group(1).strip()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
    return {name: "\n".join(body).strip() for name, body in sections.items()}


def find_section(sections: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    for name, body in sections.items():
        folded = name.casefold()
        if any(alias.casefold() in folded for alias in aliases):
            return body
    return None


def extract_comment_section(markdown: str) -> str:
    lines = markdown.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if COMMENT_HEADING_PATTERN.fullmatch(line.strip()):
            start = index + 1
            break
    if start is None:
        raise ValueError(
            "Comment section not found. Use a level-2 heading such as '## 评论'."
        )
    end = len(lines)
    for index in range(start, len(lines)):
        if SECTION_END_PATTERN.match(lines[index].strip()):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def effective_chinese_characters(text: str) -> int:
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", text))


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text).strip()


def check_c(
    root: Path,
    path: Path | None,
    required: bool,
    canonical_abstract: Path | None,
) -> list[Check]:
    if path is None:
        return [Check("artifact:C", not required, "not requested" if not required else "path required")]
    if not path.is_file() or path.stat().st_size == 0:
        return [Check("artifact:C", False, f"missing or empty: {path}")]
    if path.suffix.lower() not in {".md", ".markdown"}:
        return [Check("artifact:C", False, "C must be Markdown in weekly_reviews/")]
    try:
        markdown = path.read_text(encoding="utf-8")
        profile = load_profile(root)["weekly_review"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        return [Check("artifact:C", False, str(exc))]
    sections = parse_markdown_sections(markdown)
    missing_fields = [
        field
        for field, aliases in C_FIELD_ALIASES.items()
        if find_section(sections, aliases) is None
    ]
    checks = [
        Check(
            "artifact:C",
            not missing_fields,
            "required sections found" if not missing_fields else f"missing C sections: {', '.join(missing_fields)}",
        )
    ]
    try:
        comment = extract_comment_section(markdown)
        count = effective_chinese_characters(comment)
        minimum = profile["minimum_comment_chars"]
        checks.append(
            Check(
                "comment_chars",
                count >= minimum,
                f"{count}/{minimum} Chinese characters in comment body",
            )
        )
    except (ValueError, KeyError, TypeError) as exc:
        checks.append(Check("comment_chars", False, str(exc)))
    reviewer_required = profile.get("reviewer_name") is not None
    reviewer = find_section(sections, C_FIELD_ALIASES["reviewer"])
    if reviewer_required:
        passed = normalize_text(reviewer or "") == normalize_text(str(profile["reviewer_name"]))
        checks.append(
            Check(
                "C:reviewer",
                passed,
                "reviewer matches profile" if passed else "reviewer does not match submission_profile",
            )
        )
    if canonical_abstract is not None:
        try:
            canonical = canonical_abstract.read_text(encoding="utf-8")
            translated = find_section(sections, C_FIELD_ALIASES["translated_abstract"])
            passed = translated is not None and normalize_text(translated) == normalize_text(canonical)
            checks.append(
                Check(
                    "C:canonical-abstract",
                    passed,
                    "canonical Abstract reused exactly (ignoring whitespace)"
                    if passed
                    else "C translated Abstract differs from canonical_abstract.md",
                )
            )
        except OSError as exc:
            checks.append(Check("C:canonical-abstract", False, str(exc)))
    return checks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--a-path", type=Path)
    parser.add_argument("--b-path", type=Path)
    parser.add_argument("--c-path", type=Path)
    parser.add_argument("--canonical-abstract", type=Path)
    parser.add_argument("--require-a", action="store_true")
    parser.add_argument("--require-b", action="store_true")
    parser.add_argument("--require-c", action="store_true")
    parser.add_argument(
        "--require-workflow-complete",
        action="store_true",
        help="Require full weekly workflow closure; also requires --manifest.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.repo_root.resolve()
    if args.require_workflow_complete and args.manifest is None:
        print("[FAIL] workflow: --require-workflow-complete requires --manifest")
        return 1
    checks = check_foundation(root)
    if args.manifest:
        checks.extend(
            check_manifest(
                args.manifest,
                require_workflow_complete=args.require_workflow_complete,
            )
        )
    checks.append(check_pdf(args.a_path, args.require_a))
    checks.append(check_docx_b(args.b_path, args.require_b))
    checks.extend(
        check_c(root, args.c_path, args.require_c, args.canonical_abstract)
    )
    for check in checks:
        print(f"[{'PASS' if check.passed else 'FAIL'}] {check.name}: {check.detail}")
    failures = sum(not check.passed for check in checks)
    print(f"Summary: {len(checks) - failures} passed, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
