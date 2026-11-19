# Literature Evaluation Architecture

## Overview

Literature-Evaluation-Skills is a research-oriented workflow framework for evidence-traceable literature search, translation, and deep reading.

## Four Skill Architecture

```text
weekly-literature-evaluation
        |
        |-- literature-search
        |-- paper-translation
        `-- paper-deep-reading
```

- `weekly-literature-evaluation`: routing, gates, workflow state, recovery and handoff.
- `literature-search`: topic planning, journal mapping, retrieval and paper selection.
- `paper-translation`: source verification, full-text translation and A mirror PDF generation.
- `paper-deep-reading`: research audit, methods/results reconstruction and critical evaluation.

## Current Release

v1.6.0 is the current release contract (version single source of truth: `.codex-plugin/plugin.json`).

Major features:

- FULL_MIRROR translation validation.
- Main/SI source package management.
- A/B/C deliverable workflow.
- Shared psychology terminology memory and role-aware academic typography.
- CI validation across Python versions and Windows production environments.
