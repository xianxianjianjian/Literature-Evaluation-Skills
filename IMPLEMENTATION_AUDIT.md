# Literature Evaluation P0 Implementation Audit

Audit date: 2026-09-06 (Asia/Shanghai)
Audited revision: `dd071166862f13df7df4d6ac936355bfb61a426e`
Branch: `main`
Remote `origin/main`: `dd071166862f13df7df4d6ac936355bfb61a426e`
Plugin version at audit start: `1.3.0`

## Runtime and archive context

- Plugin source root: `D:\codex\workplace\reference\Literature-Evaluation-Skills`
- Research data root: `D:\codex\workplace\reference\.literature-evaluation`
- Current research Git root: `D:\codex\workplace\reference\Literature-Evaluation-Skills` (weekly records are currently mixed into the plugin repository)
- Zotero collection policy: selected focal papers are archived to the user-selected collection; the active W36 target is `SLEEPY` (`CXGQF4XF`).
- Zotero focal parent at audit time: Yuksel 2025, parent `89TU6WAS`; verified Main attachment `BH9KQ377`. On 2026-09-06 the user deleted that item; the PDF-first re-import subsequently generated parent `BHX9LWRZ` with verified Main attachment `NQSZH9AA` (see the W36 archive record).
- Baseline test result: 152 run, 151 passed, 1 failed (`test_real_bbox_can_require_intermediate_97_percent_scale`).
- B-runtime gap: `python-docx` is not importable by the default Python and `soffice` is not on `PATH`; therefore an independent DOCX render cannot currently be certified by that runtime.

## ALREADY_IMPLEMENTED

- `FULL_MIRROR` defaults to `EXACT_TEXT_FRAME`; `STRUCTURAL_MIRROR` requires an explicit user selection in the weekly and translation skills.
- Schema-v2 exact source inventory, reviewed text-frame inventory, exact ledger, SimSun font map, page/box/rotation checks, frame fit, table-cell topology, embedded-font checks and outside-frame raster invariance are implemented.
- The exact renderer and independent translation validator are separate entry points.
- Translation and Deep Reading academic completion are separated from Zotero archive completion.
- Zotero parent matching, duplicate refusal, existing-parent attachment upload, post-write verification and pending-action recording exist.
- DOCX metadata sanitizer removes comments and generator metadata.
- History append is deduplicated and completed-reading append requires an academically complete manifest.
- Terminology records are context-aware, preserve earlier preferred translations, and have ACTIVE/CONTEXTUAL/DEPRECATED states.

## PARTIALLY_IMPLEMENTED

- Translation numeric checks mention common statistics in policy, but the validator does not independently compare a normalized, auditable Main/SI numeric-token inventory, scientific notation, signs, units, DOI and software versions.
- Figures and tables are inventoried, but embedded figure text has no independent `figure_text_inventory.jsonl` lifecycle (`reviewed/rendered/validated`).
- Terminology consistency is governed by `paper_terminology.csv`, but A/B/C are not independently cross-checked against that sheet and registry evidence.
- Main/SI conflicts are expected to become `AUD-xxx`, but no machine-enforced source-conflict ledger prevents silent normalization.
- B checks require broad section markers and metadata sanitation, but not the exact Chinese 0–10 heading schema, required Methods/Results/Discussion subsections, OOXML relationships, `python-docx` readability, independent office render, all-page PNG output or visual-QA findings.
- Zotero supports verified metadata parent creation and later attachment, while the normal selected-paper command path is not PDF-first recognition.
- Workspace initialization isolates user data from the install bundle, but `workspace.json` does not yet expose `plugin_root`, `data_root`, `research_git_root`, and `zotero_collection`.

## NOT_IMPLEMENTED

- `numeric_integrity.json` hard gate with explicit discrepancy whitelist and Main/SI source preservation.
- `figure_text_inventory.jsonl` schema and exact-A completion enforcement.
- `source_conflicts.jsonl` audit contract for Main/SI disagreements.
- An independent `validate_deep_reading_package.py` with required DOCX package/render/visual checks.
- `zotero_bridge.py ingest-pdf` as the default new-focal-paper workflow, with a reasoned metadata-only fallback that can never close the archive.
- `history_manager.py reconcile-selection` / `reconcile-reading` and append-only `history_corrections.jsonl`.
- Terminology evidence `add-evidence`, `unlink-evidence`, `deprecate-evidence`, and evidence-link validation.
- Dedicated schema validation for topic/search records and a managed journal registry command surface (P1).

## IMPLEMENTED_BUT_NOT_TEST_ENFORCED

- Clean JATS/HTML as language authority while keeping the Version-of-Record PDF as geometry authority.
- No automatic downgrade from exact to structural output across all public entry points.
- Exact-rendered figure labels and complete label coverage.
- Main/SI source conflicts remain separately represented.
- Cross-artifact A/B/C terminology consistency.
- B render failure forces `PROVISIONAL` / `needs_update` rather than `COMPLETE`.
- Archive completion requires parent, Main, required SI, A, B and an empty pending-action list.

## RULE/CODE_CONFLICT

- `skills/literature-search/references/zotero-ingest.md` documents `zotero_bridge.py create` as the current parent-create route, which conflicts with the newly required PDF-first default.
- `scripts/validate_deliverables.py` currently accepts B from ZIP validity plus broad heading text, which conflicts with the required independent render and visual-QA hard gate.
- Yuksel W36 contains a structural A and an earlier B marked complete; under the strengthened rules A must stay `PROVISIONAL`, and B cannot remain `COMPLETE` until the new validator passes.
- Yuksel `TERMEV-0005` currently attributes `cluster-based permutation test` to the focal paper even though the paper reports FDR-corrected time-frequency cluster identification; the link must be corrected without deleting history.

## Implementation decisions

1. Add independent, auditable validators and schemas instead of duplicating generator-side assertions.
2. Preserve structural mirror code only as an explicit preview/debug mode; it is never valid evidence for exact-A completion.
3. Make PDF-first ingest the preferred command and label metadata-only creation as a fallback that returns an archive-incomplete result.
4. Preserve historical rows through correction records; do not silently overwrite Search-time or completed-reading history.
5. Keep W36 in place for this repair. Record a non-destructive research-repository migration plan; do not move user research data during the plugin code change.

## Post-implementation disposition

- All P0 items listed as partial, missing, not test-enforced, or conflicting above are implemented and covered by the v1.4 validator/test surface.
- The original 152-test baseline failure was isolated to ReportLab's process-global test font registry; the regression fixture now assigns its synthetic font deterministically without weakening the production font gate.
- Yuksel W36 A has since been rebuilt and independently validated as `FULL_MIRROR / EXACT_TEXT_FRAME`; B remains `PROVISIONAL` until the v1.4 Chinese heading, renderer-provenance, all-page PNG and visual-QA gates pass.
- Zotero collection `CXGQF4XF`, parent `BHX9LWRZ` and Main child `NQSZH9AA` remain verified. After the desktop upgrade to Zotero 10.0.1 and explicit local-write authorization, A child `C3YDZ6JF` was attached and matched to the local artifact by SHA-256, MD5 and byte length; SI and B remain pending.
- The managed topic/search schema and journal registry remain P1. Research-record extraction into a dedicated private Git repository is also deferred under the non-destructive migration plan.
