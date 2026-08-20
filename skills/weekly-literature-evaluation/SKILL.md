---
name: weekly-literature-evaluation
description: Route and resume the weekly literature evaluation workflow across search, translation, and deep reading without performing the academic analysis itself.
---

# Weekly Literature Evaluation

## Purpose and Scope

Act only as Router + State Manager + Resume Coordinator. Coordinate `literature-search`, `paper-translation`, and `paper-deep-reading`; keep the weekly manifest as the single source of truth.

Before changing workflow state, read:

- [`../../shared/state-contract.md`](../../shared/state-contract.md)
- [`references/workflow-routing.md`](references/workflow-routing.md)

Read the relevant specialist Skill before dispatching that stage.

## Intent Routing

Classify the request as full weekly workflow, Search only, Translation only, Deep Reading only, resume, or update. Do not require a full workflow when the user invokes a specialist entry mode directly.

## Full Weekly Workflow

Route in order: topic planning → Search → Translation → Deep Reading → A/B/C verification. Let each specialist own its academic decisions and outputs.

## User Decision Gates

The only fixed human Gates are:

1. the user confirms the topic;
2. the user confirms the final paper.

Mechanical steps should not repeatedly ask once the relevant Gate is passed, except when new authorization, material risk, or a genuine exception requires input.

## Workflow State and Resume

Use `weekly_reviews/YYYY/YYYY-Wxx/workflow_manifest.yaml` as the only workflow source of truth. Inspect it and existing artifacts, then resume from the first incomplete or update-required stage. Use only the states defined in the shared state contract.

## Existing Artifact Detection

Verify artifacts rather than inferring completion from filenames alone. Reuse verified artifacts and preserve their identifiers. Do not silently overwrite a different source version.

## Source Change and Update Routing

When source identity, Supplement, Correction, or status changes, set `needs_update: true`, record explicit reasons, and route only affected stages. Do not create a `STALE` state.

## Completion Rules

Full workflow completion requires verified specialist completion, required A/B/C state, resolved or explicitly provisional evidence gaps, and recorded pending Zotero actions. `PROVISIONAL` must never be described as a complete research archive.

## What This Skill Must Not Do

- Do not perform literature screening, translation, or deep academic analysis.
- Do not invent missing evidence or repair paper errors silently.
- Do not maintain a second global status file.
- Do not implement Phase 2–4 specialist logic in this router.
