from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_plugin_bundle as bundle
import init_workspace as workspace
import runtime_paths
import validate_deliverables as validator


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


if __name__ == "__main__":
    unittest.main()
