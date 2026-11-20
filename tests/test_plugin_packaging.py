from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_plugin_bundle as bundle
import deploy_local_plugin as deployer
import init_workspace as workspace
import runtime_paths
import validate_deliverables as validator
import validate_plugin_package as plugin_validator


class RuntimePathTests(unittest.TestCase):
    def test_resolution_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            explicit = root / "explicit"
            environment = root / "environment"
            default = root / "project"
            self.assertEqual(
                runtime_paths.resolve_data_root(
                    explicit,
                    environ={runtime_paths.DATA_HOME_ENV: str(environment)},
                    cwd=default,
                ),
                explicit.resolve(),
            )
            self.assertEqual(
                runtime_paths.resolve_data_root(
                    environ={runtime_paths.DATA_HOME_ENV: str(environment)},
                    cwd=default,
                ),
                environment.resolve(),
            )
            self.assertEqual(
                runtime_paths.resolve_data_root(environ={}, cwd=default),
                (default / ".literature-evaluation").resolve(),
            )

    def test_existing_workspace_is_discovered_from_nested_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            data = project / ".literature-evaluation"
            nested = project / "analysis" / "scripts"
            nested.mkdir(parents=True)
            data.mkdir(parents=True)
            (data / "workspace.json").write_text("{}\n", encoding="utf-8")
            self.assertEqual(
                runtime_paths.resolve_data_root(environ={}, cwd=nested),
                data.resolve(),
            )

    def test_git_project_root_is_used_before_nested_cwd_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            nested = project / "analysis" / "scripts"
            nested.mkdir(parents=True)
            (project / ".git").mkdir()
            self.assertEqual(
                runtime_paths.resolve_data_root(environ={}, cwd=nested),
                (project / ".literature-evaluation").resolve(),
            )


class WorkspaceInitializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.template = ROOT / "assets" / "workspace-template"

    def test_empty_workspace_and_repeat_preserve_user_updates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            created, identical, preserved = workspace.initialize_workspace(
                data_root, template_root=self.template
            )
            self.assertGreater(created, 0)
            self.assertEqual(identical, 0)
            self.assertEqual(preserved, 0)
            self.assertTrue((data_root / "workspace.json").is_file())
            self.assertTrue((data_root / "work").is_dir())
            selection_log = data_root / "knowledge" / "selection_log.csv"
            self.assertEqual(len(selection_log.read_text(encoding="utf-8").splitlines()), 1)
            self.assertFalse((data_root / "weekly_reviews" / "2026").exists())

            selection_log.write_text(
                selection_log.read_text(encoding="utf-8") + "user,data\n",
                encoding="utf-8",
            )
            before = selection_log.read_bytes()
            created, identical, preserved = workspace.initialize_workspace(
                data_root, template_root=self.template
            )
            self.assertEqual(created, 0)
            self.assertGreater(identical, 0)
            self.assertGreaterEqual(preserved, 1)
            self.assertEqual(selection_log.read_bytes(), before)

    def test_migration_copies_legacy_data_and_refuses_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "legacy"
            legacy_selection = legacy / "knowledge" / "selection_log.csv"
            legacy_selection.parent.mkdir(parents=True)
            legacy_selection.write_text("legacy-selection\n", encoding="utf-8")
            legacy_week = legacy / "weekly_reviews" / "2026" / "record.md"
            legacy_week.parent.mkdir(parents=True)
            legacy_week.write_text("legacy-week\n", encoding="utf-8")

            migrated = root / "migrated"
            workspace.initialize_workspace(
                migrated,
                template_root=self.template,
                migrate_from=legacy,
            )
            self.assertEqual(
                (migrated / "knowledge" / "selection_log.csv").read_text(encoding="utf-8"),
                "legacy-selection\n",
            )
            self.assertEqual(
                (migrated / "weekly_reviews" / "2026" / "record.md").read_text(encoding="utf-8"),
                "legacy-week\n",
            )

            conflicting = root / "conflicting"
            workspace.initialize_workspace(conflicting, template_root=self.template)
            with self.assertRaises(workspace.WorkspaceInitError):
                workspace.initialize_workspace(
                    conflicting,
                    template_root=self.template,
                    migrate_from=legacy,
                )

    def test_migration_rejects_overlapping_source_and_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "legacy"
            (legacy / "knowledge").mkdir(parents=True)
            with self.assertRaises(workspace.WorkspaceInitError):
                workspace.initialize_workspace(
                    legacy / ".literature-evaluation",
                    template_root=self.template,
                    migrate_from=legacy,
                )

    def test_dry_run_makes_no_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            created, _, _ = workspace.initialize_workspace(
                data_root,
                template_root=self.template,
                dry_run=True,
            )
            self.assertGreater(created, 0)
            self.assertFalse(data_root.exists())


class PluginMetadataTests(unittest.TestCase):
    def test_repository_plugin_metadata_is_valid(self) -> None:
        self.assertEqual(plugin_validator.validate_package(ROOT), [])
        manifest = json.loads(
            (ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["interface"]["category"], "Education & Research")
        self.assertLessEqual(len(manifest["interface"]["shortDescription"]), 30)

    def test_version_mismatch_in_readme_or_architecture_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin = bundle.build_bundle(ROOT, Path(tmp) / "bundle")
            self.assertEqual(plugin_validator.validate_package(plugin), [])
            version = json.loads(
                (plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
            )["version"]

            readme = plugin / "README.md"
            original_readme = readme.read_text(encoding="utf-8")
            readme.write_text(
                original_readme.replace(f"**v{version}**", "**v0.0.1**", 1),
                encoding="utf-8",
            )
            errors = plugin_validator.validate_package(plugin)
            self.assertTrue(any("README.md" in err for err in errors), errors)
            readme.write_text(original_readme, encoding="utf-8")

            arch = plugin / "docs" / "architecture.md"
            original_arch = arch.read_text(encoding="utf-8")
            arch.write_text(
                original_arch.replace(f"v{version} is", "v0.0.1 is", 1),
                encoding="utf-8",
            )
            errors = plugin_validator.validate_package(plugin)
            self.assertTrue(any("docs/architecture.md" in err for err in errors), errors)


class PluginBundleTests(unittest.TestCase):
    def test_bundle_contains_four_skills_and_resolvable_shared_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "bundle"
            plugin = bundle.build_bundle(ROOT, output)
            marketplace = json.loads(
                (output / ".agents" / "plugins" / "marketplace.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(marketplace["name"], bundle.MARKETPLACE_NAME)
            self.assertEqual(
                marketplace["plugins"][0]["source"]["path"],
                "./plugins/literature-evaluation",
            )
            self.assertEqual(
                marketplace["plugins"][0]["category"],
                "Education & Research",
            )

            expected = {
                "weekly-literature-evaluation",
                "literature-search",
                "paper-translation",
                "paper-deep-reading",
            }
            actual = {
                path.parent.name
                for path in (plugin / "skills").glob("*/SKILL.md")
            }
            self.assertEqual(actual, expected)
            for skill in expected:
                skill_root = plugin / "skills" / skill
                self.assertTrue((skill_root / "agents" / "openai.yaml").is_file())
                text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("../../shared/workspace-contract.md", text)
                shared_links = re.findall(r"\]\((\.\./\.\./shared/[^)]+)\)", text)
                self.assertGreater(len(shared_links), 0)
                for relative in shared_links:
                    self.assertTrue((skill_root / relative).resolve().is_file(), relative)

            self.assertEqual(plugin_validator.validate_package(plugin), [])
            data_root = root / "data"
            workspace.initialize_workspace(
                data_root,
                template_root=plugin / "assets" / "workspace-template",
            )
            failures = [
                check.detail
                for check in validator.check_foundation(
                    plugin,
                    data_root,
                    require_workspace_marker=True,
                )
                if not check.passed
            ]
            self.assertEqual(failures, [])

    def test_bundle_refuses_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "bundle"
            output.mkdir()
            with self.assertRaises(bundle.BundleError):
                bundle.build_bundle(ROOT, output)

    def test_bundle_refuses_output_inside_source_tree(self) -> None:
        with self.assertRaises(bundle.BundleError):
            bundle.build_bundle(ROOT, ROOT / "dist-test-inside-source")

    def test_archive_must_be_outside_bundle_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "bundle"
            with self.assertRaises(bundle.BundleError):
                bundle.validate_archive_path(output, output / "bundle.zip")

    def test_legacy_repo_root_validator_interface_remains_supported(self) -> None:
        with redirect_stdout(StringIO()):
            result = validator.main(["--repo-root", str(ROOT)])
        self.assertEqual(result, 0)

        with redirect_stdout(StringIO()):
            conflict = validator.main(
                [
                    "--repo-root",
                    str(ROOT),
                    "--plugin-root",
                    str(ROOT),
                ]
            )
        self.assertEqual(conflict, 1)

    def test_deploy_local_plugin_builds_validates_installs_and_updates_workspace_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            deployments = root / "deployments"
            cache_root = root / "cache"
            data_root = root / "data"
            previous = cache_root / deployer.read_manifest_version(ROOT)
            previous.mkdir(parents=True)
            (previous / "old-build.txt").write_text("previous install", encoding="utf-8")
            workspace.initialize_workspace(
                data_root,
                template_root=ROOT / "assets" / "workspace-template",
            )
            record = deployer.deploy_plugin(
                ROOT,
                deployments_dir=deployments,
                create_archive=True,
                install_cache_root=cache_root,
                workspace_root=data_root,
            )
            self.assertEqual(record["plugin_validation"], "PASS")
            self.assertEqual(record["temporary_workspace_validation"]["failed"], 0)
            self.assertTrue(Path(str(record["bundle_root"])).is_dir())
            self.assertTrue(Path(str(record["archive_path"])).is_file())
            self.assertTrue(Path(str(record["build_json_path"])).is_file())
            installed_path = Path(str(record["installed_path"]))
            self.assertTrue(installed_path.is_dir())
            self.assertEqual(installed_path, previous.resolve())
            self.assertFalse((installed_path / "old-build.txt").exists())
            self.assertEqual(list(cache_root.iterdir()), [previous])
            marker = json.loads((data_root / "workspace.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(marker["plugin_root"]), installed_path.resolve())

    def test_deploy_rejects_invalid_workspace_before_writing_and_can_retry(self) -> None:
        with tempfile.TemporaryDirectory(prefix="le-test-codex-") as tmp:
            root = Path(tmp)
            output = root / "bundle"
            cache_root = root / "cache"
            data_root = root / "data"
            data_root.mkdir()
            marker = data_root / "workspace.json"
            args = [
                "--plugin-root", str(ROOT),
                "--output", str(output),
                "--create-archive",
                "--install-cache-root", str(cache_root),
                "--workspace-root", str(data_root),
            ]
            for contents, expected in (
                (None, "workspace.json not found"),
                ("{", "Invalid workspace.json"),
                ("[]", "root must be a JSON object"),
            ):
                with self.subTest(contents=contents):
                    if contents is not None:
                        marker.write_text(contents, encoding="utf-8")
                    with redirect_stderr(StringIO()) as errors:
                        self.assertEqual(deployer.main(args), 2)
                    self.assertIn(expected, errors.getvalue())
                    self.assertFalse(output.exists())
                    self.assertFalse(output.with_suffix(".zip").exists())
                    self.assertFalse(output.with_suffix(".build.json").exists())
                    self.assertFalse(cache_root.exists())

            marker.write_text('{"user_setting": "preserve"}', encoding="utf-8")
            with redirect_stdout(StringIO()) as result:
                self.assertEqual(deployer.main(args), 0)
            installed = Path(json.loads(result.getvalue())["installed_path"])
            self.assertTrue(installed.is_dir())
            self.assertEqual(json.loads(marker.read_text(encoding="utf-8")), {
                "user_setting": "preserve",
                "plugin_root": str(installed),
            })

    def test_failed_cache_copy_preserves_previous_install(self) -> None:
        with tempfile.TemporaryDirectory(prefix="le-test-codex-") as tmp:
            root = Path(tmp)
            source = root / "built-plugin"
            source.mkdir()
            installed = root / "cache" / "1.6.0"
            installed.mkdir(parents=True)
            previous_file = installed / "existing.txt"
            previous_file.write_text("previous install", encoding="utf-8")

            def fail_after_partial_copy(_source: Path, destination: Path) -> None:
                destination.mkdir()
                (destination / "partial.txt").write_text("partial copy", encoding="utf-8")
                raise OSError("cache copy interrupted")

            with patch.object(deployer.shutil, "copytree", side_effect=fail_after_partial_copy):
                with self.assertRaisesRegex(OSError, "cache copy interrupted"):
                    deployer.install_validated_plugin(source, installed)

            self.assertEqual(previous_file.read_text(encoding="utf-8"), "previous install")
            self.assertEqual(list(installed.parent.iterdir()), [installed])


if __name__ == "__main__":
    unittest.main()
