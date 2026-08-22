#!/usr/bin/env python3
"""Resolve writable Literature Evaluation data roots without touching plugin files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

DATA_HOME_ENV = "LITERATURE_EVALUATION_HOME"
DEFAULT_DATA_DIRECTORY = ".literature-evaluation"
WORKSPACE_MARKER = "workspace.json"


def _ancestors(start: Path) -> tuple[Path, ...]:
    start = start.resolve()
    return (start, *start.parents)


def find_existing_data_root(start: Path | str) -> Path | None:
    """Find an initialized data root from the current directory upward."""
    base = Path(start).expanduser().resolve()
    if (base / WORKSPACE_MARKER).is_file() and base.name == DEFAULT_DATA_DIRECTORY:
        return base
    for ancestor in _ancestors(base):
        candidate = ancestor / DEFAULT_DATA_DIRECTORY
        if (candidate / WORKSPACE_MARKER).is_file():
            return candidate.resolve()
    return None


def find_project_root(start: Path | str) -> Path | None:
    """Find a containing Git/workspace root without invoking Git itself."""
    base = Path(start).expanduser().resolve()
    for ancestor in _ancestors(base):
        marker = ancestor / ".git"
        if marker.exists():
            return ancestor
    return None


def resolve_data_root(
    explicit: Path | str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    cwd: Path | str | None = None,
) -> Path:
    """Resolve explicit, env, existing workspace, project root, then cwd default.

    Precedence is intentionally stable:
    1. explicit ``--workspace-root`` style value;
    2. ``LITERATURE_EVALUATION_HOME``;
    3. an already initialized ``.literature-evaluation/workspace.json`` found
       from the current directory upward;
    4. ``.literature-evaluation`` below the containing Git project root;
    5. ``.literature-evaluation`` below the current directory.
    """
    if explicit is not None and str(explicit).strip():
        return Path(explicit).expanduser().resolve()

    values = os.environ if environ is None else environ
    configured = values.get(DATA_HOME_ENV, "").strip()
    if configured:
        return Path(configured).expanduser().resolve()

    base = (Path.cwd() if cwd is None else Path(cwd)).expanduser().resolve()
    existing = find_existing_data_root(base)
    if existing is not None:
        return existing

    project_root = find_project_root(base)
    if project_root is not None:
        return (project_root / DEFAULT_DATA_DIRECTORY).resolve()

    return (base / DEFAULT_DATA_DIRECTORY).resolve()


def plugin_root() -> Path:
    """Return the plugin root containing this helper's scripts directory."""
    return Path(__file__).resolve().parents[1]
