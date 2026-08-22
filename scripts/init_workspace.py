#!/usr/bin/env python3
"""Initialize or safely migrate a writable Literature Evaluation workspace."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from runtime_paths import plugin_root, resolve_data_root

MIGRATION_DIRECTORIES = ("knowledge", "weekly_reviews", "work")


class WorkspaceInitError(ValueError):
    """Raised when initialization would overwrite or ambiguously merge data."""


def collect_files(root: Path) -> dict[Path, Path]:
    """Return relative-to-source file mappings for an existing tree."""
    if not root.is_dir():
        raise WorkspaceInitError(f"Source directory does not exist: {root}")
    return {
        path.relative_to(root): path
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def desired_files(
    template_root: Path, migrate_from: Path | None
) -> dict[Path, tuple[Path, bool]]:
    """Build the desired tree, allowing legacy data to replace clean seed files."""
    desired = {
        relative: (source, False)
        for relative, source in collect_files(template_root).items()
    }
    if migrate_from is None:
        return desired

    if not migrate_from.is_dir():
        raise WorkspaceInitError(f"Legacy root does not exist: {migrate_from}")
    for directory in MIGRATION_DIRECTORIES:
        source = migrate_from / directory
        if not source.exists():
            continue
        if not source.is_dir():
            raise WorkspaceInitError(f"Legacy path is not a directory: {source}")
        for relative, path in collect_files(source).items():
            desired[Path(directory) / relative] = (path, True)
    return desired


def initialize_workspace(
    data_root: Path,
    *,
    template_root: Path,
    migrate_from: Path | None = None,
    dry_run: bool = False,
) -> tuple[int, int, int]:
    """Create missing files after a complete conflict preflight."""
    data_root = data_root.resolve()
    template_root = template_root.resolve()
    if migrate_from is not None:
        migrate_from = migrate_from.resolve()
        if migrate_from == data_root:
            raise WorkspaceInitError("Legacy root and destination data root must differ.")

    desired = desired_files(template_root, migrate_from)
    conflicts: list[Path] = []
    identical = 0
    preserved = 0
    pending: list[tuple[Path, Path]] = []
    for relative, (source, from_migration) in desired.items():
        destination = data_root / relative
        if destination.exists():
            if not destination.is_file():
                conflicts.append(destination)
            elif destination.read_bytes() == source.read_bytes():
                identical += 1
            elif from_migration:
                conflicts.append(destination)
            else:
                preserved += 1
        else:
            pending.append((source, destination))

    if conflicts:
        rendered = "\n".join(f"- {path}" for path in conflicts)
        raise WorkspaceInitError(
            "Refusing to overwrite files with different content:\n" + rendered
        )

    if not dry_run:
        data_root.mkdir(parents=True, exist_ok=True)
        (data_root / "work").mkdir(parents=True, exist_ok=True)
        for source, destination in pending:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    return len(pending), identical, preserved


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace-root",
        type=Path,
        help="Writable data root. Defaults to env override or .literature-evaluation/.",
    )
    parser.add_argument(
        "--migrate-from",
        type=Path,
        help="Legacy root containing knowledge/, weekly_reviews/, and optional work/.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    data_root = resolve_data_root(args.workspace_root)
    template_root = plugin_root() / "assets" / "workspace-template"
    try:
        created, identical, preserved = initialize_workspace(
            data_root,
            template_root=template_root,
            migrate_from=args.migrate_from,
            dry_run=args.dry_run,
        )
    except (WorkspaceInitError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    mode = "Dry run" if args.dry_run else "Initialized"
    print(f"{mode}: {data_root}")
    print(
        f"New files: {created}; existing identical files: {identical}; "
        f"existing user files preserved: {preserved}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
