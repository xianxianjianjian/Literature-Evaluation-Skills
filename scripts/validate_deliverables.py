#!/usr/bin/env python3
"""Validate the Phase 1 repository foundation and basic A/B/C interfaces."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

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
    "README.md",
    ".gitignore",
    "skills/weekly-literature-evaluation/SKILL.md",
    "skills/weekly-literature-evaluation/references/workflow-routing.md",
    "skills/literature-search/SKILL.md",
    "skills/paper-translation/SKILL.md",
    "skills/paper-deep-reading/SKILL.md",
    "shared/evidence-policy.md",
    "shared/identifier-policy.md",
    "shared/source-identity-policy.md",
    "shared/zotero-policy.md",
    "shared/state-contract.md",
    "shared/data-format-policy.md",
    "knowledge/research_profile.md",
    "knowledge/submission_profile.yaml",
    "knowledge/journal_registry.csv",
    "knowledge/terminology_registry.csv",
    "knowledge/terminology_evidence.jsonl",
    "knowledge/reading_history.csv",
    "knowledge/selection_log.csv",
    "scripts/zotero_bridge.py",
    "scripts/terminology_registry.py",
    "scripts/history_manager.py",
    "scripts/workflow_state.py",
    "scripts/validate_deliverables.py",
    "scripts/mirror_pdf.py",
]
CSV_HEADERS = {
    "journal_registry.csv": "Journal,Field,Scope,Publisher,Peer_Reviewed,Priority,Strength,Caution,Status,Verified_Date".split(","),
    "terminology_registry.csv": "Term_ID,English_Term,Abbreviation,Preferred_Chinese,Alternative_Chinese,Discipline,Subfield,Definition,Context,Confidence,Evidence_Level,Evidence_IDs,Status,First_Verified,Last_Verified,Notes".split(","),
    "reading_history.csv": "Week,Topic,Paper_ID,Title,DOI,Journal,Year,Study_Type,Core_Finding,Method_Value,Transfer_Value,Major_Limitation,Open_Questions,Next_Reading_Direction,Zotero_Item_Key,A_Attachment_Key,B_Attachment_Key,Git_Review_Path,Completed_Date".split(","),
    "selection_log.csv": "Week,Topic,Paper_ID,Title,DOI,Journal,Year,Role,Quality_Gate,Weighted_Score,Selection_Decision,Selection_Reason,Zotero_Item_Key,Logged_Date".split(","),
}
COMMENT_HEADING_PATTERN = re.compile(r"^##\s+(?:评论|评译评论|Comment|Review)\s*$", re.IGNORECASE)
SECTION_END_PATTERN = re.compile(r"^#{1,2}\s+")


@dataclass
class Check:
    """One validation result."""

    name: str
    passed: bool
    detail: str


def check_foundation(root: Path) -> list[Check]:
    """Check required directories, files, and Knowledge schemas."""
    checks: list[Check] = []
    for relative in REQUIRED_DIRECTORIES:
        exists = (root / relative).is_dir()
        checks.append(Check(f"directory:{relative}", exists, "present" if exists else "missing"))
    for relative in REQUIRED_FILES:
        exists = (root / relative).is_file()
        checks.append(Check(f"file:{relative}", exists, "present" if exists else "missing"))

    profile_path = root / "knowledge" / "submission_profile.yaml"
    if profile_path.is_file():
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            valid = (
                profile.get("schema_version") == 1
                and isinstance(profile.get("weekly_review"), dict)
                and isinstance(profile["weekly_review"].get("minimum_comment_chars"), int)
                and isinstance(profile["weekly_review"].get("original_abstract_required"), bool)
                and isinstance(profile["weekly_review"].get("translated_abstract_required"), bool)
            )
            checks.append(Check("submission_profile", valid, "schema valid" if valid else "invalid schema"))
        except (json.JSONDecodeError, OSError) as exc:
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


def check_manifest(path: Path) -> Check:
    """Validate a workflow manifest and its allowed state enum."""
    try:
        load_manifest(path)
    except (WorkflowStateError, OSError) as exc:
        return Check("manifest", False, str(exc))
    return Check("manifest", True, f"valid: {path}")


def check_artifact(label: str, path: Path | None, required: bool) -> Check:
    """Check an A, B, or C path when supplied or required."""
    if path is None:
        return Check(f"artifact:{label}", not required, "not requested" if not required else "path required")
    exists = path.is_file() and path.stat().st_size > 0
    return Check(f"artifact:{label}", exists, str(path) if exists else f"missing or empty: {path}")


def effective_chinese_characters(text: str) -> int:
    """Count CJK unified ideographs as the Phase 1 C-comment baseline."""
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", text))


def extract_comment_section(markdown: str) -> str:
    """Extract only the dedicated comment/review section from a weekly review.

    The 500-character requirement applies to the evaluator's comment body, not
    metadata, original abstract, translated abstract, titles, or references.
    """
    lines = markdown.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if COMMENT_HEADING_PATTERN.fullmatch(line.strip()):
            start = index + 1
            break
    if start is None:
        raise ValueError(
            "Comment section not found. Use a level-2 heading such as '## 评论' "
            "or pass --comment-text with the comment body only."
        )
    end = len(lines)
    for index in range(start, len(lines)):
        if SECTION_END_PATTERN.match(lines[index].strip()):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def check_comment(root: Path, text: str | None, file: Path | None) -> Check:
    """Check only C's evaluator-comment body against the configured minimum."""
    try:
        profile = json.loads((root / "knowledge" / "submission_profile.yaml").read_text(encoding="utf-8"))
        minimum = profile["weekly_review"]["minimum_comment_chars"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        return Check("comment_chars", False, f"cannot load threshold: {exc}")
    if file is not None:
        try:
            markdown = file.read_text(encoding="utf-8")
            text = extract_comment_section(markdown)
        except (OSError, ValueError) as exc:
            return Check("comment_chars", False, str(exc))
    if text is None:
        return Check("comment_chars", True, f"interface ready; configured minimum={minimum}")
    count = effective_chinese_characters(text)
    return Check("comment_chars", count >= minimum, f"{count}/{minimum} Chinese characters in comment body")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--a-path", type=Path)
    parser.add_argument("--b-path", type=Path)
    parser.add_argument("--c-path", type=Path)
    parser.add_argument("--require-a", action="store_true")
    parser.add_argument("--require-b", action="store_true")
    parser.add_argument("--require-c", action="store_true")
    comment = parser.add_mutually_exclusive_group()
    comment.add_argument("--comment-text", help="Comment body only; do not include metadata/abstracts.")
    comment.add_argument(
        "--comment-file",
        type=Path,
        help="Weekly-review Markdown containing a dedicated '## 评论' (or equivalent) section.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run validation and return non-zero if any check fails."""
    args = build_parser().parse_args(argv)
    root = args.repo_root.resolve()
    checks = check_foundation(root)
    if args.manifest:
        checks.append(check_manifest(args.manifest))
    checks.extend(
        [
            check_artifact("A", args.a_path, args.require_a),
            check_artifact("B", args.b_path, args.require_b),
            check_artifact("C", args.c_path, args.require_c),
            check_comment(root, args.comment_text, args.comment_file),
        ]
    )
    for check in checks:
        label = "PASS" if check.passed else "FAIL"
        print(f"[{label}] {check.name}: {check.detail}")
    failures = sum(not check.passed for check in checks)
    print(f"Summary: {len(checks) - failures} passed, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
