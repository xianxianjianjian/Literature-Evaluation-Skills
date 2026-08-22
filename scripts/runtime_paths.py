#!/usr/bin/env python3
"""Resolve writable Literature Evaluation data roots without touching plugin files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

DATA_HOME_ENV = "LITERATURE_EVALUATION_HOME"
DEFAULT_DATA_DIRECTORY = ".literature-evaluation"


def resolve_data_root(
    explicit: Path | str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    cwd: Path | str | None = None,
) -> Path:
    """Resolve explicit path, environment override, then the workspace default."""
    if explicit is not None and str(explicit).strip():
        return Path(explicit).expanduser().resolve()

    values = os.environ if environ is None else environ
    configured = values.get(DATA_HOME_ENV, "").strip()
    if configured:
        return Path(configured).expanduser().resolve()

    base = Path.cwd() if cwd is None else Path(cwd)
    return (base / DEFAULT_DATA_DIRECTORY).resolve()


def plugin_root() -> Path:
    """Return the plugin root containing this helper's scripts directory."""
    return Path(__file__).resolve().parents[1]
