#!/usr/bin/env python3
"""Metadata normalization, role attachment, archive verification, and PDF-first ingest helpers for Zotero bridge."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse
from urllib.request import url2pathname

import zotero_attachment_contract as attachment_contract
import zotero_local_write as local_write
from artifact_binding import fingerprint, resolve_path, same_content

SCHEMA_VERSION = 1
DEFAULT_LIBRARY_PREFIX = "users/0"


class ZoteroBridgeError(RuntimeError):
    """Raised when Zotero cannot satisfy a requested bridge operation."""


def emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def normalize_doi(value: str) -> str:
    normalized = value.strip().casefold()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if normalized.startswith(prefix):
            return normalized[len(prefix):].strip()
    return normalized


def item_data(item: dict[str, Any]) -> dict[str, Any]:
    data = item.get("data")
    return data if isinstance(data, dict) else {}


def is_parent_bibliographic_item(item: dict[str, Any]) -> bool:
    data = item_data(item)
    if data.get("parentItem"):
        return False
    return data.get("itemType") not in {"attachment", "note", "annotation"}


def _zb():
    import zotero_bridge
    return zotero_bridge


def load_metadata(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ZoteroBridgeError(f"Metadata file does not exist: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ZoteroBridgeError(f"Metadata file is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ZoteroBridgeError("Metadata root must be a JSON object.")
    return value


def normalized_creators(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize personal/institutional creators to Zotero translator-item fields."""
    creators = metadata.get("creators")
    if creators is None:
        creators = metadata.get("authors", [])
    if creators is None:
        return []
    if not isinstance(creators, list):
        raise ZoteroBridgeError("creators/authors must be a list of structured objects.")

    normalized: list[dict[str, Any]] = []
    for index, creator in enumerate(creators):
        if not isinstance(creator, dict):
            raise ZoteroBridgeError(
                "Author names are not parsed from free-text strings. "
                f"creators/authors[{index}] must be an object."
            )
        first = str(creator.get("firstName", "")).strip()
        last = str(creator.get("lastName", "")).strip()
        single_name = str(creator.get("name", "")).strip()
        creator_type = str(creator.get("creatorType", "author")).strip() or "author"

        if single_name and not (first or last):
            normalized.append(
                {
                    "lastName": single_name,
                    "fieldMode": 1,
                    "creatorType": creator_type,
                }
            )
            continue
        if not last:
            raise ZoteroBridgeError(
                f"creators/authors[{index}] requires lastName or a single-field name."
            )
        record: dict[str, Any] = {
            "firstName": first,
            "lastName": last,
            "creatorType": creator_type,
        }
        if creator.get("fieldMode") == 1:
            if first:
                raise ZoteroBridgeError(
                    f"creators/authors[{index}] fieldMode=1 cannot include firstName."
                )
            record.pop("firstName", None)
            record["fieldMode"] = 1
        normalized.append(record)
    return normalized


def build_connector_item(metadata: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if metadata.get("attachments"):
        raise ZoteroBridgeError(
            "Parent create does not accept attachment payloads. Use attach/pending separately."
        )
    title = str(metadata.get("title", "")).strip()
    if not title:
        raise ZoteroBridgeError("Metadata requires a non-empty title.")

    item: dict[str, Any] = {
        "itemType": str(metadata.get("itemType", "journalArticle")).strip()
        or "journalArticle",
        "title": title,
        "creators": normalized_creators(metadata),
        "attachments": [],
    }
    mapping = {
        "publicationTitle": ("publicationTitle", "journal"),
        "date": ("date", "year"),
        "volume": ("volume",),
        "issue": ("issue",),
        "pages": ("pages",),
        "url": ("url",),
        "abstractNote": ("abstractNote", "abstract"),
        "language": ("language",),
    }
    for target, sources in mapping.items():
        for source in sources:
            value = metadata.get(source)
            if value is not None and str(value).strip():
                item[target] = str(value).strip()
                break

    doi_raw = str(metadata.get("DOI", metadata.get("doi", ""))).strip()
    doi = normalize_doi(doi_raw) if doi_raw else ""
    if doi:
        item["DOI"] = doi

    source_uri = str(metadata.get("source_uri", "")).strip()
    if not source_uri:
        source_uri = str(item.get("url", "")).strip()
    if not source_uri and doi:
        source_uri = f"https://doi.org/{doi}"
    if not source_uri:
        raise ZoteroBridgeError(
            "Metadata requires source_uri, url, or DOI so Connector save provenance is explicit."
        )
    return item, source_uri


def create_preview(metadata: dict[str, Any]) -> dict[str, Any]:
    item, source_uri = build_connector_item(metadata)
    return {"items": [item], "uri": source_uri}


def item_key(item: dict[str, Any]) -> str | None:
    key = item.get("key")
    if isinstance(key, str) and key.strip():
        return key.strip()
    data = item_data(item)
    key = data.get("key")
    return key.strip() if isinstance(key, str) and key.strip() else None



def command_attach_role(args: argparse.Namespace) -> int:
    try:
        args.name = attachment_contract.role_title(
            args.role, args.si_number, data_si=args.data_si
        )
    except ValueError as exc:
        raise ZoteroBridgeError(str(exc)) from exc
    if args.role not in {"VIDEO", "DATA"} and not args.data_si and args.file.suffix.casefold() != ".pdf":
        raise ZoteroBridgeError(f"{args.role} reading attachment must be a PDF")
    if args.data_si and args.role != "SI":
        raise ZoteroBridgeError("--data-si applies only to SI")
    if args.role in {"MAIN", "A", "B"} or (args.role == "SI" and not args.data_si):
        from pypdf import PdfReader
        try:
            with args.file.open("rb") as handle: signature = handle.read(5)
            if signature != b"%PDF-" or not PdfReader(args.file).pages:
                raise ValueError("invalid PDF")
        except Exception as exc:
            raise ZoteroBridgeError(f"Unreadable PDF: {exc}") from exc
    if args.role in {"A", "B"}:
        if not args.qc_report:
            raise ZoteroBridgeError("A/B attachment requires --qc-report bound to final PDF")
        from prepare_si_bundle import fingerprint
        qc = load_metadata(args.qc_report)
        binding = qc.get("pdf_binding") or qc.get("pdf") or {}
        valid = (qc.get("passed") is True or qc.get("B_PDF_EXPORT_PASS") is True)
        if not (valid and (qc.get("pdf_sha256") == fingerprint(args.file) or binding.get("sha256") == fingerprint(args.file))):
            raise ZoteroBridgeError("A/B PDF QC failed or does not bind this file")
    _, existing = _zb()._parent_children(args)
    legacy = {
        "MAIN": ("[ORIGINAL] Main Article", "pdf"),
        "A": ("[A]", "A翻译"),
        "B": ("[B]", "B精读"),
        "SI": ("[SUPPLEMENT]",), "VIDEO": (), "DATA": (),
    }[args.role]
    old = [item_key(child) for child in existing if any(
        str(item_data(child).get("title") or "").casefold().startswith(label.casefold()) for label in legacy
    )]
    if old:
        raise ZoteroBridgeError(f"Legacy {args.role} attachment exists; normalize/verify before attaching a duplicate: {old}")
    return _zb().command_attach(args)


def _parent_children(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    prefix = args.library_prefix.strip().strip("/")
    parent_key = quote(args.parent_key.strip(), safe="")
    parent = _zb().api_get(args.api_base_url, f"/{prefix}/items/{parent_key}", timeout=args.timeout)
    children = _zb().api_get(args.api_base_url, f"/{prefix}/items/{parent_key}/children", timeout=args.timeout)
    if not isinstance(parent, dict) or not isinstance(children, list):
        raise ZoteroBridgeError("Unexpected parent/children response")
    return parent, children


def command_verify_archive(args: argparse.Namespace) -> int:
    workspace_root = getattr(args, "workspace_root", None)
    allowed_roots = tuple(getattr(args, "allow_external_root", []))
    if workspace_root:
        args.spec = resolve_path(args.spec, workspace_root, allowed_roots=allowed_roots)
        if args.report:
            args.report = resolve_path(args.report, workspace_root, allowed_roots=allowed_roots, must_exist=False)
    spec = load_metadata(args.spec)
    if spec.get("parent_key") != args.parent_key:
        raise ZoteroBridgeError("Archive spec parent key differs from requested parent")
    parent, children = _zb()._parent_children(args)
    if spec.get("naming_version", 1) >= 2 and spec.get("library_prefix") != args.library_prefix:
        raise ZoteroBridgeError("Archive library mismatch")
    if (spec.get("contract_version") == "1.5.0" or spec.get("naming_version", 1) >= 2) and workspace_root is None:
        raise ZoteroBridgeError("v1.5 verification requires --workspace-root")
    result = attachment_contract.validate_archive(parent, children, spec, workspace_root=workspace_root,
                                                  allowed_roots=allowed_roots)
    readable_failures: list[str] = []
    if result["passed"]:
        for row in spec["attachments"]:
            attachment_key = str(row["key"])
            url = _zb().request_text(
                args.api_base_url.rstrip("/") + f"/{args.library_prefix.strip().strip('/')}/items/{quote(attachment_key, safe='')}/file/view/url",
                timeout=args.timeout,
            ).strip()
            parsed = urlparse(url)
            if parsed.scheme != "file":
                readable_failures.append(attachment_key)
                continue
            path = Path(url2pathname(parsed.path))
            if parsed.netloc:
                path = Path(f"//{parsed.netloc}{url2pathname(parsed.path)}")
            try:
                if not path.is_file() or path.stat().st_size == 0:
                    readable_failures.append(attachment_key)
                if row.get("mime", "application/pdf") == "application/pdf":
                    from pypdf import PdfReader
                    if not PdfReader(str(path)).pages:
                        readable_failures.append(attachment_key)
                if (spec.get("contract_version") == "1.5.0" or spec.get("naming_version", 1) >= 2) and path.is_file():
                    actual = fingerprint(path)
                    record = result["content_bindings"].get(attachment_key, {})
                    digest = hashlib.md5()
                    with path.open("rb") as handle:
                        for chunk in iter(lambda: handle.read(1024*1024), b""): digest.update(chunk)
                    md5 = digest.hexdigest()
                    record.update({"actual": actual, "actual_md5": md5})
                    if not same_content(actual, record.get("local", {})) or md5 != record.get("api_md5"):
                        readable_failures.append(attachment_key)
            except (OSError, ValueError):
                readable_failures.append(attachment_key)
    if readable_failures:
        result["passed"] = False
        result["failures"].append(f"unreadable or content-mismatched attachment files: {readable_failures}")
    result["files_readable"] = result["passed"] and not readable_failures
    result.update({"schema_version": 1, "command": "verify-archive", "library_prefix": args.library_prefix})
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    emit(result)
    return 0 if result["passed"] else 2


def command_normalize_titles(args: argparse.Namespace) -> int:
    spec = load_metadata(args.spec)
    if spec.get("parent_key") != args.parent_key:
        raise ZoteroBridgeError("Normalization spec parent key differs from requested parent")
    parent, children = _zb()._parent_children(args)
    if attachment_contract.key(parent) != args.parent_key:
        raise ZoteroBridgeError("Parent identity mismatch")
    actual = {attachment_contract.key(child): child for child in children}
    targets = [attachment_contract.role_title(row["role"], row.get("si_number"), data_si=row.get("data_si") is True) for row in spec.get("attachments", [])]
    if len(targets) != len(set(targets)):
        raise ZoteroBridgeError("Multiple old reading SI require a verified complete bundle; merge pending, retain old keys and annotations")
    from prepare_si_bundle import fingerprint
    for row in spec.get("attachments", []):
        item = actual.get(str(row.get("key") or ""), {})
        child = item_data(item)
        if child.get("parentItem") != args.parent_key:
            raise ZoteroBridgeError("Migration parent mismatch")
        path = row.get("local_path")
        if not path or not row.get("sha256") or fingerprint(Path(path)) != row["sha256"]:
            raise ZoteroBridgeError("Migration requires verified local_path/sha256")
        import hashlib
        digest = hashlib.md5()
        with Path(path).open("rb") as f:
            for chunk in iter(lambda: f.read(1024*1024), b""): digest.update(chunk)
        if digest.hexdigest() != child.get("md5"):
            raise ZoteroBridgeError("Migration attachment bytes differ from verified source")
        if row.get("role") in {"MAIN", "SI", "A", "B"} and child.get("contentType") != "application/pdf":
            raise ZoteroBridgeError("Legacy Word requires a verified replacement PDF; retain old attachment")
    changes: list[dict[str, Any]] = []
    for row in spec.get("attachments", []):
        try:
            title = attachment_contract.role_title(
                row["role"], row.get("si_number"), data_si=row.get("data_si") is True, naming_version=spec.get("naming_version", 2)
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise ZoteroBridgeError(f"Invalid normalization row: {exc}") from exc
        attachment_key = str(row.get("key") or "").strip()
        item = actual.get(attachment_key)
        if item is None:
            raise ZoteroBridgeError(f"Attachment not found under parent: {attachment_key}")
        old_title = str(item_data(item).get("title") or "")
        if old_title != title:
            conflicts = [child for child in children if item_data(child).get("title") == title]
            if conflicts:
                if len(conflicts) == 1 and item_data(conflicts[0]).get("md5") == item_data(item).get("md5"):
                    changes.append({"key": attachment_key, "old_title": old_title, "new_title": title,
                                    "reuse_key": item_key(conflicts[0]), "action": "REUSE_EXISTING_RETAIN_OLD"})
                    continue
                raise ZoteroBridgeError(f"Target title already belongs to another child: {title}")
            changes.append({"key": attachment_key, "old_title": old_title, "new_title": title,
                            "version": item.get("version") or item_data(item).get("version")})
    def migration_report(status):
        result = {"status": status, "changes": changes, "deleted": [], "parent_key": args.parent_key}
        if getattr(args, "report", None):
            from build_paper_status_overview import save
            save(args.report, result)
        return result
    if not args.yes:
        emit(migration_report("DRY_RUN"))
        return 0
    client = local_write.LocalWriteClient.connect(args.api_base_url, timeout=args.timeout)
    migration_report("PENDING")
    for change in changes:
        if change.get("reuse_key"): continue
        if not isinstance(change["version"], int):
            raise ZoteroBridgeError(f"Missing item version for {change['key']}")
        try:
            client.request(
                f"/{args.library_prefix.strip().strip('/')}/items/{quote(change['key'], safe='')}",
                method="PATCH", data=json.dumps({"title": change["new_title"]}, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Unmodified-Since-Version": str(change["version"])},
                expected_statuses={204},
            )
        except local_write.LocalAPIError as exc:
            raise ZoteroBridgeError(str(exc)) from exc
        change["applied"] = True
        migration_report("PARTIAL")
    _, updated = _zb()._parent_children(args)
    updated_by_key = {attachment_contract.key(child): child for child in updated}
    verified = all(
        item_data(updated_by_key.get(change.get("reuse_key") or change["key"], {})).get("title") == change["new_title"]
        for change in changes
    )
    for change in changes:
        item = updated_by_key.get(change["key"], {})
        change["new_version"] = item.get("version") or item_data(item).get("version")
    emit(migration_report("UPDATED_AND_VERIFIED" if verified else "UPDATE_NOT_VERIFIED"))
    return 0 if verified else 2


def pdf_ingest_preview(args: argparse.Namespace) -> dict[str, Any]:
    """Describe the PDF-first ingest without treating metadata creation as success."""
    pdf = args.pdf.resolve()
    metadata = load_metadata(args.metadata)
    _, normalized_doi = build_connector_item(metadata)
    if not pdf.is_file() or pdf.suffix.casefold() != ".pdf":
        raise ZoteroBridgeError(f"Main Article PDF does not exist or is not PDF: {pdf}")
    if not args.collection_key.strip():
        raise ZoteroBridgeError("PDF-first ingest requires --collection-key.")
    if args.fallback_metadata and not (args.fallback_reason or "").strip():
        raise ZoteroBridgeError("Metadata-only fallback requires --fallback-reason.")
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": "PDF_FIRST_INGEST",
        "pdf": str(pdf),
        "expected_identity": {
            "doi": normalized_doi or None,
            "title": str(metadata.get("title") or "").strip(),
            "year": str(metadata.get("year") or metadata.get("date") or "").strip() or None,
        },
        "target_collection_key": args.collection_key.strip(),
        "steps": [
            "import Main PDF into target collection",
            "allow Zotero automatic metadata recognition to create the parent",
            "verify DOI/title/year and target collection",
            "verify Main PDF is a child of that parent",
        ],
        "metadata_only_fallback_requested": bool(args.fallback_metadata),
        "fallback_reason": (args.fallback_reason or "").strip() or None,
        "archive_complete": False,
    }


def _parent_in_collection(item: dict[str, Any], collection_key: str) -> bool:
    data = item_data(item)
    collections = data.get("collections")
    return isinstance(collections, list) and collection_key in collections


def command_ingest_pdf(args: argparse.Namespace) -> int:
    """Gate a Zotero Desktop PDF-first recognition workflow.

    Zotero owns recognition of a newly imported PDF.  This command plans the
    operation and independently verifies the recognized parent/child result.  It
    never substitutes a metadata-only parent without an explicit recorded reason.
    """
    preview = pdf_ingest_preview(args)
    if not args.yes:
        preview["status"] = "PREVIEW"
        preview["next_action"] = (
            "Import the PDF into the selected Zotero collection with Zotero Desktop "
            "and rerun with --recognized-parent-key <key> --yes after recognition."
        )
        emit(preview)
        return 0

    metadata = load_metadata(args.metadata)
    title = str(metadata.get("title") or "").strip()
    doi = str(metadata.get("doi") or "").strip()
    matches = _zb().find_parent_matches(
        api_base_url=args.api_base_url,
        timeout=args.timeout,
        doi=doi or None,
        title=title or None,
        limit=25,
    )
    if len(matches) > 1:
        raise ZoteroBridgeError("PDF-first ingest stopped: multiple plausible parent items matched.")

    recognized_key = (args.recognized_parent_key or "").strip()
    if recognized_key:
        verified = _zb().api_get(
            args.api_base_url,
            f"/{DEFAULT_LIBRARY_PREFIX}/items/{quote(recognized_key, safe='')}",
            timeout=args.timeout,
        )
        if not isinstance(verified, dict) or not is_parent_bibliographic_item(verified):
            raise ZoteroBridgeError("Recognized parent key is not a bibliographic parent item.")
        if matches and item_key(matches[0]) != recognized_key:
            raise ZoteroBridgeError("Recognized parent conflicts with DOI/title duplicate precheck.")
        if not _parent_in_collection(verified, args.collection_key.strip()):
            raise ZoteroBridgeError("Recognized parent is not in the requested target collection.")
        children = _zb().api_get(
            args.api_base_url,
            f"/{DEFAULT_LIBRARY_PREFIX}/items/{quote(recognized_key, safe='')}/children",
            timeout=args.timeout,
        )
        pdf_children = [
            child
            for child in children
            if isinstance(child, dict)
            and item_data(child).get("itemType") == "attachment"
            and str(item_data(child).get("contentType") or "").casefold() == "application/pdf"
        ] if isinstance(children, list) else []
        confirmed_main = getattr(args, "main_attachment_key", None)
        if confirmed_main:
            pdf_children = [child for child in pdf_children if item_key(child) == confirmed_main]
        if not pdf_children:
            raise ZoteroBridgeError("Recognized parent has no PDF child; archive remains incomplete.")
        if len(pdf_children) != 1:
            raise ZoteroBridgeError("Recognized parent has multiple PDF children; identify Main before archive closure.")
        actual = item_data(verified)
        expected_doi = normalize_doi(doi)
        actual_doi = normalize_doi(str(actual.get("DOI") or actual.get("doi") or ""))
        if expected_doi and expected_doi != actual_doi:
            raise ZoteroBridgeError("Recognized DOI does not match expected DOI.")
        if title and str(actual.get("title") or "").strip().casefold() != title.casefold():
            raise ZoteroBridgeError("Recognized title does not match expected title.")
        main_title_pass = item_data(pdf_children[0]).get("title") == attachment_contract.role_title("MAIN")
        preview.update(
            {
                "status": "VERIFIED" if main_title_pass else "TITLE_NORMALIZATION_REQUIRED",
                "recognized_parent_key": recognized_key,
                "main_attachment_keys": [item_key(child) for child in pdf_children],
                "main_title_pass": main_title_pass,
                "source_archive_complete": main_title_pass,
                "archive_complete": False,
            }
        )
        emit(preview)
        return 0 if main_title_pass else 4

    if args.fallback_metadata:
        preview.update(
            {
                "status": "METADATA_FALLBACK_REQUIRED",
                "archive_complete": False,
                "pending_zotero_action": {
                    "action": "replace_metadata_fallback_with_pdf_first_parent",
                    "reason": args.fallback_reason.strip(),
                    "expected_attachment_name": attachment_contract.role_title("MAIN"),
                },
                "note": (
                    "Metadata-only fallback is explicitly recorded but is not archive completion. "
                    "Use the existing create/attach helpers only as a resumable fallback."
                ),
            }
        )
        emit(preview)
        return 4

    preview.update(
        {
            "status": "AWAITING_ZOTERO_AUTO_RECOGNITION",
            "archive_complete": False,
            "next_action": (
                "Import the Main PDF into the target collection in Zotero Desktop, wait for "
                "automatic recognition, then rerun with --recognized-parent-key and --yes."
            ),
        }
    )
    emit(preview)
    return 4

