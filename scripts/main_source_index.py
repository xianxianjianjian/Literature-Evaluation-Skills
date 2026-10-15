"""Extract a reproducible Main index from the verified source manifest."""
from __future__ import annotations

import json
import re
from pathlib import Path

try:
    import pymupdf
except ImportError:  # legacy/foundation checks must remain usable without it
    pymupdf = None

from artifact_binding import fingerprint, resolve_path
from validate_a_text_layer import normalize_text


def build_index(source_manifest_path: Path) -> dict:
    if pymupdf is None:
        raise ValueError("REVIEW_REQUIRED: PyMuPDF required to locate Canonical Main")
    manifest = json.loads(source_manifest_path.read_text(encoding="utf-8-sig"))
    mains = [s for s in manifest.get("sources", []) if s.get("source_type") == "MAIN" and s.get("availability") == "AVAILABLE"]
    if len(mains) != 1 or manifest.get("package_status") != "READY":
        raise ValueError("REVIEW_REQUIRED: one verified Canonical Main in a READY source package required")
    main = mains[0]
    path = resolve_path(main["local_path"], source_manifest_path.parent)
    actual = fingerprint(path)
    if actual["sha256"] != main.get("sha256") or actual["size_bytes"] != main.get("bytes"):
        raise ValueError("Canonical Main bytes differ from verified source manifest")
    pages = []
    section = ""
    with pymupdf.open(path) as document:
        for number, page in enumerate(document, 1):
            blocks = []
            for block in page.get_text("blocks", sort=True):
                if block[6] != 0:
                    continue
                text = block[4].strip()
                for line in text.splitlines():
                    heading = re.sub(r"^\s*\d+(?:\.\d+)*[. ]*", "", line.strip()).casefold()
                    if heading in {"introduction", "methods", "materials and methods", "results", "discussion", "limitations", "references"}:
                        section = heading
                blocks.append({"block": len(blocks) + 1, "bbox": list(block[:4]), "section": section, "text": text})
            pages.append({"page": number, "blocks": blocks})
        metadata = document.metadata or {}
    if not pages or not any(normalize_text("".join(b["text"] for b in p["blocks"])) for p in pages):
        raise ValueError("REVIEW_REQUIRED: Main has no reliable text; provide reviewed OCR with source binding")
    doi = str(manifest.get("doi") or "").casefold().removeprefix("https://doi.org/")
    identity_text = " ".join(b["text"] for b in pages[0]["blocks"]) + " ".join(str(v) for v in metadata.values())
    text = normalize_text(identity_text).casefold()
    title = str(manifest.get("publication_identity", {}).get("title") or "")
    has_doi = bool(re.search(r"10\.\d{4,9}/", identity_text))
    if not doi or (doi not in text and (has_doi or not title or normalize_text(title).casefold() not in text)):
        raise ValueError("REVIEW_REQUIRED: Main DOI/title cannot be matched to verified source identity")
    return {"schema_version": 1, "paper_id": manifest["paper_id"], "doi": doi, "source_id": main["source_id"],
            "source_class": "MAIN", "version": main.get("version"), **actual, "pages": pages}


def locate(anchor: dict, index: dict) -> bool:
    if not isinstance(anchor, dict):
        return False
    if anchor.get("source_id") != index.get("source_id") or anchor.get("sha256") != index.get("sha256"):
        return False
    number, block = anchor.get("page"), anchor.get("block")
    if not isinstance(number, int) or not isinstance(block, int) or number < 1 or block < 1:
        return False
    pages = index["pages"]
    if number > len(pages) or block > len(pages[number - 1]["blocks"]):
        return False
    actual = pages[number - 1]["blocks"][block - 1]
    quote = normalize_text(re.sub(r"(?<=[A-Za-z])-\s*\n\s*(?=[A-Za-z])", "", str(anchor.get("quote") or "")))
    section = str(anchor.get("section") or "").casefold()
    # An excerpt ending in .03 must not be accepted as the .032 statistic;
    # similarly, English word prefixes are not complete source words.
    def protected_tokens(value):
        value = re.sub(r"(?<=[A-Za-z])-\s*\n\s*(?=[A-Za-z])", "", value)
        spaced = " ".join(normalize_text(part) for part in value.split())
        return re.findall(r"[A-Za-z]+|\d+(?:\.\d+)*|\.\d+", spaced)
    wanted, observed = protected_tokens(str(anchor.get("quote") or "")), protected_tokens(actual["text"])
    tokens_match = not wanted or any(observed[start:start + len(wanted)] == wanted for start in range(len(observed) - len(wanted) + 1))
    source_text = re.sub(r"(?<=[A-Za-z])-\s*\n\s*(?=[A-Za-z])", "", actual["text"])
    return bool(quote and quote in normalize_text(source_text) and tokens_match and (not section or section == actual["section"]))
