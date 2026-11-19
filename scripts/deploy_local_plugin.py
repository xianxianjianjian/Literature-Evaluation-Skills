#!/usr/bin/env python3
"""Automate local plugin bundle build, validation, cache installation, and workspace.json sync."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import build_plugin_bundle as bundle
import init_workspace
import validate_deliverables
import validate_plugin_package


class DeploymentError(ValueError):
    """Raised when local plugin deployment or verification fails."""


def _git_info(plugin_root: Path) -> dict[str, object]:
    info: dict[str, object] = {
        "source_commit": None,
        "short_sha": "nogit",
        "source_branch": None,
        "dirty_working_tree": False,
    }
    try:
        sha = subprocess.run(
            ["git", "-C", str(plugin_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            check=True,
        ).stdout.strip()
        branch = subprocess.run(
            ["git", "-C", str(plugin_root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            check=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(plugin_root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            check=True,
        ).stdout.strip()
        info["source_commit"] = sha
        info["short_sha"] = sha[:7] if sha else "nogit"
        info["source_branch"] = branch
        info["dirty_working_tree"] = bool(status)
    except (OSError, subprocess.SubprocessError):
        pass
    return info


def read_manifest_version(plugin_root: Path) -> str:
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    if not manifest_path.is_file():
        raise DeploymentError(f"Missing plugin manifest: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = str(data.get("version") or "").strip()
    if not version:
        raise DeploymentError("Plugin manifest is missing a non-empty version.")
    return version


def update_workspace_plugin_root(workspace_root: Path, installed_plugin_root: Path) -> Path:
    marker = workspace_root.resolve() / "workspace.json"
    if not marker.is_file():
        raise DeploymentError(f"workspace.json not found in data root: {marker}")
    payload = json.loads(marker.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DeploymentError("workspace.json root must be a JSON object.")
    payload["plugin_root"] = str(installed_plugin_root.resolve())
    marker.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return marker


def deploy_plugin(
    plugin_root: Path,
    *,
    deployments_dir: Path | None = None,
    output_dir: Path | None = None,
    archive_path: Path | None = None,
    build_json_path: Path | None = None,
    install_cache_root: Path | None = None,
    workspace_root: Path | None = None,
    rollback_marketplace: Path | None = None,
    create_archive: bool = False,
) -> dict[str, object]:
    plugin_root = plugin_root.expanduser().resolve()
    version = read_manifest_version(plugin_root)
    git_meta = _git_info(plugin_root)
    short_sha = str(git_meta["short_sha"])

    if output_dir is None:
        if deployments_dir is None:
            raise DeploymentError("Either --output or --deployments-dir must be provided.")
        output_dir = deployments_dir.expanduser().resolve() / f"literature-evaluation-{version}-{short_sha}"
    else:
        output_dir = output_dir.expanduser().resolve()

    if archive_path is None and create_archive:
        archive_path = output_dir.parent / f"{output_dir.name}.zip"
    elif archive_path is not None:
        archive_path = archive_path.expanduser().resolve()

    if build_json_path is None:
        build_json_path = output_dir.parent / f"{output_dir.name}.build.json"
    else:
        build_json_path = build_json_path.expanduser().resolve()

    if archive_path is not None:
        if archive_path.exists():
            raise DeploymentError(f"Archive already exists; refusing to overwrite: {archive_path}")
        bundle.validate_archive_path(output_dir, archive_path)

    plugin_target = bundle.build_bundle(plugin_root, output_dir)
    if archive_path is not None:
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.make_archive(
            str(archive_path.with_suffix("")),
            "zip",
            root_dir=output_dir.parent,
            base_dir=output_dir.name,
        )

    pkg_errors = validate_plugin_package.validate_package(plugin_target)
    if pkg_errors:
        raise DeploymentError(
            "Built plugin failed package validation:\n" + "\n".join(pkg_errors)
        )

    with tempfile.TemporaryDirectory(prefix="le-deploy-validate-") as tmp:
        temp_data_root = Path(tmp) / "data"
        init_workspace.initialize_workspace(
            temp_data_root,
            template_root=plugin_target / "assets" / "workspace-template",
        )
        init_workspace.configure_workspace_marker(
            temp_data_root,
            plugin_path=plugin_target,
        )
        checks = validate_deliverables.check_foundation(
            plugin_target,
            temp_data_root,
            require_workspace_marker=True,
        )
        failed = [c for c in checks if not c.passed]
        if failed:
            details = "; ".join(f"{c.name}: {c.detail}" for c in failed)
            raise DeploymentError(f"Temporary workspace validation failed: {details}")
        passed_count = len(checks)

    installed_path: Path | None = None
    if install_cache_root is not None:
        cache_root = install_cache_root.expanduser().resolve()
        installed_path = cache_root / version
        if installed_path.exists():
            shutil.rmtree(installed_path)
        installed_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(plugin_target, installed_path)
        cache_errors = validate_plugin_package.validate_package(installed_path)
        if cache_errors:
            raise DeploymentError(
                "Installed cache copy failed package validation:\n" + "\n".join(cache_errors)
            )

    active_plugin_path = installed_path if installed_path is not None else plugin_target
    updated_marker: Path | None = None
    if workspace_root is not None:
        updated_marker = update_workspace_plugin_root(workspace_root, active_plugin_path)

    build_record: dict[str, object] = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "version": version,
        "source_commit": git_meta["source_commit"],
        "source_branch": git_meta["source_branch"],
        "dirty_working_tree": git_meta["dirty_working_tree"],
        "bundle_root": str(output_dir),
        "plugin_target": str(plugin_target),
        "archive_path": str(archive_path) if archive_path is not None else None,
        "plugin_validation": "PASS",
        "temporary_workspace_validation": {
            "passed": passed_count,
            "failed": 0,
        },
        "installed_path": str(installed_path) if installed_path is not None else None,
        "workspace_marker_updated": str(updated_marker) if updated_marker is not None else None,
        "rollback_marketplace": str(rollback_marketplace.resolve()) if rollback_marketplace is not None else None,
    }
    build_json_path.parent.mkdir(parents=True, exist_ok=True)
    build_json_path.write_text(
        json.dumps(build_record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    build_record["build_json_path"] = str(build_json_path)
    return build_record


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plugin-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--deployments-dir",
        type=Path,
        help="Parent directory for versioned deployment bundles (e.g. D:/Workplace/Skill/deployments).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Explicit bundle output directory. If omitted, derived from --deployments-dir, version, and git short SHA.",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        help="Optional explicit .zip archive path outside the bundle output tree.",
    )
    parser.add_argument(
        "--create-archive",
        action="store_true",
        help="Automatically create <output>.zip alongside the bundle directory.",
    )
    parser.add_argument(
        "--build-json",
        type=Path,
        help="Optional explicit path for the .build.json metadata file.",
    )
    parser.add_argument(
        "--install-cache-root",
        type=Path,
        help="Optional Codex plugin cache directory (installs into <cache-root>/<version>).",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        help="Optional data root whose workspace.json.plugin_root will be updated.",
    )
    parser.add_argument(
        "--rollback-marketplace",
        type=Path,
        help="Optional previous verified marketplace bundle path to record for rollback.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        record = deploy_plugin(
            args.plugin_root,
            deployments_dir=args.deployments_dir,
            output_dir=args.output,
            archive_path=args.archive,
            build_json_path=args.build_json,
            install_cache_root=args.install_cache_root,
            workspace_root=args.workspace_root,
            rollback_marketplace=args.rollback_marketplace,
            create_archive=args.create_archive,
        )
    except (DeploymentError, bundle.BundleError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
