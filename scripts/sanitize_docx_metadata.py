#!/usr/bin/env python3
"""Remove generator-identifying metadata and comments from a DOCX package."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CORE_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
FORBIDDEN_PATTERNS = (
    re.compile(r"python-docx", re.IGNORECASE),
    re.compile(r"chatgpt", re.IGNORECASE),
    re.compile(r"openai", re.IGNORECASE),
    re.compile(r"codex", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z])AI(?![A-Za-z])", re.IGNORECASE),
)
COMMENT_PART_PREFIXES = (
    "word/comments",
    "word/people.xml",
)


class DocxMetadataError(ValueError):
    """Raised when a DOCX package cannot be safely sanitized or validated."""


def _contains_forbidden(text: str) -> bool:
    return any(pattern.search(text) for pattern in FORBIDDEN_PATTERNS)


def _remove_comment_markup(xml: bytes) -> bytes:
    root = ET.fromstring(xml)
    comment_tags = {
        f"{{{W_NS}}}commentRangeStart",
        f"{{{W_NS}}}commentRangeEnd",
        f"{{{W_NS}}}commentReference",
    }
    for parent in root.iter():
        for child in list(parent):
            if child.tag in comment_tags:
                parent.remove(child)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _sanitize_core(xml: bytes, author: str | None) -> bytes:
    root = ET.fromstring(xml)
    clear_names = {
        f"{{{CORE_NS}}}lastModifiedBy",
        f"{{{CORE_NS}}}keywords",
        f"{{{DC_NS}}}description",
        f"{{{DC_NS}}}subject",
    }
    creator = f"{{{DC_NS}}}creator"
    found_creator = False
    for element in root.iter():
        if element.tag == creator:
            element.text = author or ""
            found_creator = True
        elif element.tag in clear_names:
            element.text = ""
        elif element.text and _contains_forbidden(element.text):
            element.text = ""
    if not found_creator:
        ET.SubElement(root, creator).text = author or ""
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _sanitize_property_xml(xml: bytes) -> bytes:
    root = ET.fromstring(xml)
    for element in root.iter():
        if element.text and _contains_forbidden(element.text):
            element.text = ""
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _sanitize_relationships(xml: bytes) -> bytes:
    root = ET.fromstring(xml)
    for relationship in list(root):
        relation_type = str(relationship.attrib.get("Type", "")).casefold()
        target = str(relationship.attrib.get("Target", "")).casefold()
        if "comments" in relation_type or relation_type.endswith("/people") or target.startswith("comments") or target == "people.xml":
            root.remove(relationship)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _sanitize_content_types(xml: bytes) -> bytes:
    root = ET.fromstring(xml)
    for override in list(root):
        part_name = str(override.attrib.get("PartName", "")).lstrip("/").casefold()
        if part_name.startswith("word/comments") or part_name == "word/people.xml":
            root.remove(override)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def sanitize_docx(source: Path, output: Path | None = None, *, author: str | None = None) -> Path:
    source = source.resolve()
    output = (output or source).resolve()
    if source.suffix.casefold() != ".docx" or not source.is_file():
        raise DocxMetadataError(f"DOCX input missing or invalid: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx", dir=output.parent) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(source, "r") as incoming, zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED
        ) as outgoing:
            for info in incoming.infolist():
                name = info.filename
                folded = name.casefold()
                if any(folded.startswith(prefix) for prefix in COMMENT_PART_PREFIXES):
                    continue
                data = incoming.read(name)
                if name == "docProps/core.xml":
                    data = _sanitize_core(data, author)
                elif name in {"docProps/app.xml", "docProps/custom.xml"}:
                    data = _sanitize_property_xml(data)
                elif name == "word/_rels/document.xml.rels":
                    data = _sanitize_relationships(data)
                elif name == "[Content_Types].xml":
                    data = _sanitize_content_types(data)
                elif folded.startswith("word/") and folded.endswith(".xml"):
                    data = _remove_comment_markup(data)
                outgoing.writestr(info, data)
        temporary.replace(output)
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        temporary.unlink(missing_ok=True)
        raise DocxMetadataError(f"Cannot sanitize DOCX: {exc}") from exc
    return output


def validate_docx_metadata(path: Path, *, expected_author: str | None = None) -> list[str]:
    failures: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            comment_parts = [
                name for name in names if any(name.casefold().startswith(prefix) for prefix in COMMENT_PART_PREFIXES)
            ]
            if comment_parts:
                failures.append(f"comment parts remain: {', '.join(comment_parts)}")
            core_name = "docProps/core.xml"
            if core_name not in names:
                failures.append("docProps/core.xml missing")
            else:
                core = ET.fromstring(archive.read(core_name))
                values = {element.tag: (element.text or "").strip() for element in core.iter()}
                creator = values.get(f"{{{DC_NS}}}creator", "")
                if expected_author is None and creator:
                    failures.append("author is not empty")
                elif expected_author is not None and creator != expected_author:
                    failures.append(f"author {creator!r} does not match {expected_author!r}")
                for tag, label in (
                    (f"{{{CORE_NS}}}lastModifiedBy", "last_modified_by"),
                    (f"{{{CORE_NS}}}keywords", "keywords"),
                    (f"{{{DC_NS}}}description", "comments/description"),
                    (f"{{{DC_NS}}}subject", "subject"),
                ):
                    if values.get(tag, ""):
                        failures.append(f"{label} is not empty")
            for name in names:
                if not (name.startswith("docProps/") and name.endswith(".xml")):
                    continue
                text = archive.read(name).decode("utf-8", errors="ignore")
                if _contains_forbidden(text):
                    failures.append(f"forbidden generator identifier remains in {name}")
    except (OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        failures.append(f"invalid DOCX package: {exc}")
    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--author")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output = sanitize_docx(args.input, args.output, author=args.author)
        failures = validate_docx_metadata(output, expected_author=args.author)
    except DocxMetadataError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1
    print(f"Sanitized DOCX metadata: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
