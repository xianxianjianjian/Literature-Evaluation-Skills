#!/usr/bin/env python3
"""Build a local Codex marketplace bundle from the repository-root plugin."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

PLUGIN_NAME = "literature-evaluation"
MARKETPLACE_NAME = "literature-evaluation-local"
PACKAGE_ENTRIES = (
    ".codex-plugin",
    ".gitignore",
    "skills",
    "shared",
    "scripts",
    "assets",
    "docs",
    "README.md",
)


class BundleError(ValueError):
    """Raised when a safe, valid bundle cannot be produced."""


def ignore_runtime_files(_directory: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name == "__pycache__" or name.endswith((".pyc", ".pyo"))
    }


def build_bundle(plugin_root: Path, output: Path) -> Path:
    plugin_root = plugin_root.resolve()
    output = output.resolve()
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    if not manifest_path.is_file():
        raise BundleError(f"Missing plugin manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("name") != PLUGIN_NAME:
        raise BundleError(f"Manifest name must be {PLUGIN_NAME!r}.")
    if output.exists():
        raise BundleError(f"Output already exists; refusing to overwrite: {output}")
    try:
        output.relative_to(plugin_root)
    except ValueError:
        pass
    else:
        if output == plugin_root:
            raise BundleError("Bundle output cannot replace the plugin root.")

    plugin_target = output / "plugins" / PLUGIN_NAME
    marketplace_target = output / ".agents" / "plugins" / "marketplace.json"
    plugin_target.mkdir(parents=True)
    for entry in PACKAGE_ENTRIES:
        source = plugin_root / entry
        if not source.exists():
            raise BundleError(f"Required package entry is missing: {source}")
        destination = plugin_target / entry
        if source.is_dir():
            shutil.copytree(source, destination, ignore=ignore_runtime_files)
        else:
            shutil.copy2(source, destination)

    marketplace = {
        "name": MARKETPLACE_NAME,
        "interface": {"displayName": "Literature Evaluation Local"},
        "plugins": [
            {
                "name": PLUGIN_NAME,
                "source": {"source": "local", "path": f"./plugins/{PLUGIN_NAME}"},
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL",
                },
                "category": "Research",
            }
        ],
    }
    marketplace_target.parent.mkdir(parents=True)
    marketplace_target.write_text(
        json.dumps(marketplace, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return plugin_target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--plugin-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--archive",
        type=Path,
        help="Optional .zip path. It must not already exist.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        archive_path = None
        if args.archive:
            archive_path = args.archive.resolve()
            if archive_path.exists():
                raise BundleError(
                    f"Archive already exists; refusing to overwrite: {archive_path}"
                )
            if archive_path.suffix.lower() != ".zip":
                raise BundleError("--archive must end in .zip")
        plugin_target = build_bundle(args.plugin_root, args.output)
        if archive_path:
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.make_archive(
                str(archive_path.with_suffix("")),
                "zip",
                root_dir=args.output.resolve().parent,
                base_dir=args.output.resolve().name,
            )
    except (BundleError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Built plugin: {plugin_target}")
    if archive_path:
        print(f"Built archive: {archive_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
