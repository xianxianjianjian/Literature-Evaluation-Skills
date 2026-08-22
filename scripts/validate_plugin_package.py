#!/usr/bin/env python3
"""Validate plugin metadata and four-skill packaging contracts.

This is a repository-local structural validator. It complements, rather than
replaces, host-level OpenAI plugin validation and runtime discovery tests.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PLUGIN_NAME = "literature-evaluation"
PLUGIN_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
PLUGIN_CATEGORY = "Education & Research"
EXPECTED_CAPABILITIES = {"Interactive", "Read", "Write"}
MAX_NAMESPACED_SKILL_NAME = 64
EXPECTED_SKILLS = {
    "weekly-literature-evaluation",
    "literature-search",
    "paper-translation",
    "paper-deep-reading",
}
AGENT_REQUIRED_KEYS = (
    "display_name:",
    "short_description:",
    "default_prompt:",
    "allow_implicit_invocation:",
)


class PluginValidationError(ValueError):
    """Raised when plugin metadata is structurally invalid."""


def validate_manifest(plugin_root: Path) -> list[str]:
    errors: list[str] = []
    path = plugin_root / ".codex-plugin" / "plugin.json"
    if not path.is_file():
        return [f"missing manifest: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid plugin.json: {exc}"]

    if data.get("name") != PLUGIN_NAME:
        errors.append(f"plugin name must be {PLUGIN_NAME!r}")
    version = str(data.get("version") or "")
    if not PLUGIN_VERSION_PATTERN.fullmatch(version):
        errors.append("plugin version must be semver-like x.y.z")
    if data.get("skills") != "./skills/":
        errors.append("plugin skills entry must be './skills/'")

    interface = data.get("interface")
    if not isinstance(interface, dict):
        errors.append("plugin interface must be an object")
        return errors
    if interface.get("category") != PLUGIN_CATEGORY:
        errors.append(f"plugin category must be {PLUGIN_CATEGORY!r}")
    capabilities = interface.get("capabilities")
    if not isinstance(capabilities, list) or set(capabilities) != EXPECTED_CAPABILITIES:
        errors.append(
            "interface.capabilities must declare Interactive, Read, and Write"
        )
    short = interface.get("shortDescription")
    if not isinstance(short, str) or not short.strip():
        errors.append("interface.shortDescription must be a non-empty string")
    elif len(short.strip()) > 30:
        errors.append("project policy requires interface.shortDescription <= 30 characters")
    prompts = interface.get("defaultPrompt")
    if isinstance(prompts, str):
        prompts = [prompts]
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3:
        errors.append("interface.defaultPrompt must be a string or 1-3 strings")
    elif not all(isinstance(item, str) and item.strip() for item in prompts):
        errors.append("interface.defaultPrompt entries must be non-empty strings")
    elif any(len(item) > 128 for item in prompts):
        errors.append("interface.defaultPrompt entries must be <= 128 characters")
    return errors


def _frontmatter_skill_name(skill_file: Path) -> str | None:
    try:
        text = skill_file.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"(?m)^name:\s*([^\s]+)\s*$", text)
    return match.group(1).strip() if match else None


def validate_skills(plugin_root: Path) -> list[str]:
    errors: list[str] = []
    skills_root = plugin_root / "skills"
    if not skills_root.is_dir():
        return [f"missing skills directory: {skills_root}"]
    actual = {
        path.parent.name
        for path in skills_root.glob("*/SKILL.md")
        if path.is_file()
    }
    if actual != EXPECTED_SKILLS:
        errors.append(
            f"expected skills {sorted(EXPECTED_SKILLS)}, found {sorted(actual)}"
        )
    for skill in sorted(EXPECTED_SKILLS):
        namespaced = f"{PLUGIN_NAME}:{skill}"
        if len(namespaced) > MAX_NAMESPACED_SKILL_NAME:
            errors.append(
                f"namespaced skill name exceeds {MAX_NAMESPACED_SKILL_NAME} characters: {namespaced}"
            )
        skill_root = skills_root / skill
        skill_file = skill_root / "SKILL.md"
        agent_file = skill_root / "agents" / "openai.yaml"
        if not skill_file.is_file():
            errors.append(f"missing {skill_file}")
            continue
        frontmatter_name = _frontmatter_skill_name(skill_file)
        if frontmatter_name != skill:
            errors.append(
                f"{skill_file}: frontmatter name must be {skill!r}, found {frontmatter_name!r}"
            )
        if not agent_file.is_file():
            errors.append(f"missing {agent_file}")
            continue
        try:
            agent_text = agent_file.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"cannot read {agent_file}: {exc}")
            continue
        for key in AGENT_REQUIRED_KEYS:
            if key not in agent_text:
                errors.append(f"{agent_file}: missing {key.rstrip(':')}")
        if "allow_implicit_invocation: true" not in agent_text:
            errors.append(
                f"{agent_file}: allow_implicit_invocation must remain true"
            )
    return errors


def validate_package(plugin_root: Path) -> list[str]:
    plugin_root = plugin_root.expanduser().resolve()
    errors = validate_manifest(plugin_root)
    errors.extend(validate_skills(plugin_root))
    for relative in ("shared", "scripts", "assets/workspace-template"):
        path = plugin_root / relative
        if not path.exists():
            errors.append(f"missing packaged resource: {path}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plugin-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors = validate_package(args.plugin_root)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        print(f"Summary: {len(errors)} plugin validation error(s).")
        return 1
    print("[PASS] plugin manifest, skills, agents, and packaged resources")
    return 0


if __name__ == "__main__":
    sys.exit(main())
