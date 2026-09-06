# v1.4.0 Implementation Notes

Implementation date: 2026-09-06

## Component map

- `translation_integrity.py` owns numeric-token comparison, the reviewed discrepancy whitelist, figure-text closure, Main/SI conflict preservation and paper-level terminology evidence checks. `validate_translation_package.py` invokes it as an independent exact-A gate.
- `validate_deep_reading_package.py` owns the exact Chinese 0–10 B schema, dynamic Methods/Results/Discussion coverage, OOXML and sanitized metadata checks, `python-docx` readability, independent office-render evidence, all-page PNG coverage and visual QA.
- `validate_terminology_consistency.py` compares the focal-paper terminology sheet and event-replayed evidence registry with A/B/C artifact text.
- `zotero_bridge.py ingest-pdf` expresses the normal PDF-first recognition and post-recognition verification path. Metadata-only creation requires a reason and always remains archive-incomplete.
- `history_manager.py` writes selection/reading corrections with old values, new values, reason and date to append-only `history_corrections.jsonl`.
- `terminology_registry.py` replays evidence lifecycle events and validates add, update, unlink and deprecate operations.
- `workflow_state.py` and `validate_deliverables.py` enforce explicit structural-layout selection and the strict parent/Main/SI/A/B/no-pending archive boundary.

## Compatibility and migration

Schema changes are additive. Older manifests gain missing archive fields during normalization, but earlier structural A or unvalidated B artifacts are not grandfathered into v1.4 completion. Research records remain in their existing locations; `docs/research-repository-migration-plan.md` describes a later, non-destructive split into a dedicated private repository.

## Yuksel W36 regression

- The previously verified SLEEPY collection (`CXGQF4XF`), parent (`89TU6WAS`) and Main PDF child (`BH9KQ377`) are retained.
- The focal-paper method term was corrected from the unsupported cluster-based permutation-test attribution to `FDR-corrected time-frequency cluster identification`; the earlier evidence state remains in the append-only event history.
- A and B are now `PROVISIONAL`. Required SI, exact-A regeneration, B schema/render/visual-QA evidence and Zotero A/B attachment are still pending.
- The existing B DOCX core metadata contains no generator identity and no comments part, but that hygiene check alone is insufficient for completion.

## Verification

- 172 unit and regression tests pass.
- 88 repository deliverable checks pass.
- All four skills and both the source and bundled plugin structures pass their official validators.
- The validated v1.4.0 local bundle was installed from `dist/literature-evaluation-v1.4.0-20260906`.
