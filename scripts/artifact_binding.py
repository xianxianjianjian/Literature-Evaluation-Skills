"""Content and path facts shared by v1.5 validators (no academic judgments)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def fingerprint(path: Path) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"sha256": digest.hexdigest(), "size_bytes": path.stat().st_size}


def matches_fingerprint(path: Path, record: dict) -> bool:
    return same_content(fingerprint(path), record)


def same_content(actual: dict, expected: dict) -> bool:
    return isinstance(expected, dict) and all(actual.get(k) == expected.get(k) and actual.get(k) is not None
                                              for k in ("sha256", "size_bytes"))


def resolve_path(value: str | Path, root: Path, *, allowed_roots: tuple[Path, ...] = (), must_exist: bool = True) -> Path:
    """Relative paths belong to the explicit workspace, never the process cwd.

    External absolute files require an explicitly authorized root. Resolving
    symlinks before containment prevents an in-workspace link escaping scope.
    """
    if not str(value).strip():
        raise ValueError("file path is missing")
    path = Path(value)
    if ".." in path.parts:
        raise ValueError(f"parent traversal is not allowed: {value}")
    path = (path if path.is_absolute() else root / path).resolve()
    roots = (root.resolve(), *(item.resolve() for item in allowed_roots))
    if not any(path.is_relative_to(item) for item in roots):
        raise ValueError(f"path outside authorized workspace roots: {value}")
    if must_exist and not path.is_file():
        raise ValueError(f"file missing: {value}")
    return path


def workflow_identity(manifest: dict) -> dict:
    return {k: manifest.get(k) for k in ("paper_id", "workflow_id", "contract_version")}


def require_identity(actual: dict, expected: dict) -> None:
    if any(not expected.get(k) or actual.get(k) != expected[k] for k in ("paper_id", "workflow_id", "contract_version")):
        raise ValueError("paper_id/workflow_id/contract_version mismatch or missing")


def source_bindings(manifest_path: Path) -> tuple[str, dict]:
    source = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if source.get("package_status") != "READY":
        raise ValueError("verified READY source package required")
    records = {}
    for row in source.get("sources", []):
        if row.get("source_type") not in {"MAIN", "SI"} or row.get("availability") != "AVAILABLE":
            continue
        path = resolve_path(row.get("local_path", ""), manifest_path.parent)
        actual = fingerprint(path)
        if actual["sha256"] != row.get("sha256") or actual["size_bytes"] != row.get("bytes"):
            raise ValueError(f"source version changed: {row.get('source_id')}")
        records[row["source_id"]] = {**actual, "source_class": row["source_type"], "version": row.get("version")}
    if sum(r["source_class"] == "MAIN" for r in records.values()) != 1:
        raise ValueError("exactly one verified Main required")
    return source.get("paper_id"), records
