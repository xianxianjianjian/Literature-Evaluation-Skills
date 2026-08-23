---
name: paper-translation
description: Professionally translate an academic paper into Chinese with terminology verification, a canonical abstract, full-text/SI coverage, figure/table integrity, and a page-structure-aware Chinese mirror PDF. Can run independently or from the weekly workflow.
---

# Paper Translation

## Purpose

Produce a faithful, terminology-controlled Chinese translation and deliverable A without changing scientific meaning, causal strength, numbers, statistics, source data or source-version identity.

The Translation Skill owns translation and production quality. It does **not** perform the later independent methodological/statistical critique that belongs to Deep Reading.

## Required shared contracts

Before substantive work, read:

- [`../../shared/evidence-policy.md`](../../shared/evidence-policy.md)
- [`../../shared/identifier-policy.md`](../../shared/identifier-policy.md)
- [`../../shared/source-identity-policy.md`](../../shared/source-identity-policy.md)
- [`../../shared/zotero-policy.md`](../../shared/zotero-policy.md)
- [`../../shared/state-contract.md`](../../shared/state-contract.md)
- [`../../shared/data-format-policy.md`](../../shared/data-format-policy.md)
- [`../../shared/workspace-contract.md`](../../shared/workspace-contract.md)

Resolve and initialize `<data-root>` through the workspace contract before any write. When running in weekly context, use `<data-root>/weekly_reviews/YYYY/YYYY-Wxx/workflow_manifest.yaml` as the workflow source of truth.

## Reference routing

Read the reference that owns each translation decision:

- terminology verification and registry use → [`references/terminology-policy.md`](references/terminology-policy.md)
- canonical Abstract → [`references/abstract-translation.md`](references/abstract-translation.md)
- Translation Units and full scientific coverage → [`references/fulltext-translation.md`](references/fulltext-translation.md)
- figures, tables and SI → [`references/figures-tables-supplement.md`](references/figures-tables-supplement.md)
- mirror layout → [`references/mirror-layout.md`](references/mirror-layout.md)
- source inventory, ledger, object/page mapping and independent validation → [`references/translation-evidence-contract.md`](references/translation-evidence-contract.md)
- completion QC → [`references/translation-qc.md`](references/translation-qc.md)

## Entry modes and scopes

Accept handoff from Search, a Zotero item, or a directly supplied source package. Supported scopes:

- `ABSTRACT_ONLY`
- `MAIN_ONLY`
- `SECTION_ONLY`
- `SUPPLEMENT_ONLY`
- `FULL_MIRROR`
- `UPDATE_EXISTING`

If the user simply asks to translate a paper without narrowing scope, default to `FULL_MIRROR`.

Search completion is not a prerequisite when the user directly supplies a paper, but a Minimal Intake is still mandatory.

## Minimal Intake

Before translation:

1. establish focal-paper identity and `paper_id`;
2. distinguish Version of Record, accepted manuscript, preprint and supplementary files;
3. assign stable source IDs (`SRC-M1`, `SRC-S1`, ...);
4. check source readability and expected page/figure/table/SI coverage;
5. record missing or ambiguous sources explicitly.

Prefer Version of Record for identity and page mapping. A legal author manuscript or other official version may be used as a working text source when necessary, but version differences must be recorded and never silently merged.

## Translation workflow

For `FULL_MIRROR`:

1. Minimal Intake and source identity check.
2. Fix-render paginated sources as needed, then build `source_inventory.json` before translation. Inventory PDF pages visually and inspect DOCX drawings/relationships; paragraph-only extraction is insufficient.
3. Run terminology preflight and create/update `paper_terminology.csv`.
4. Translate the Abstract through two translation passes plus an alignment pass and write `canonical_abstract.md`.
5. Translate Main Article by stable Translation Units and record `translation_ledger.jsonl`.
6. Translate/verify tables, figures, captions, notes and Supporting Information.
7. Record translation-specific issues in `translation_issues.jsonl` using `TRI-xxx`.
8. Create and use `mirror_layout_plan.json`; do not bypass the mirror helper with an unrelated reflow builder.
9. Render A, visually compare every planned source/output page, and record object/table placement and render notes.
10. Run Coverage, Semantic and Numeric QC, then run `validate_translation_package.py` to generate `translation_validation.json`.
11. Only after the independent validator passes, verify A as `[A] 中文全文翻译镜像版` and set Translation/A `COMPLETE`.
12. Archive A to Zotero when available; otherwise stage a handoff/pending action without changing the academic completion state.
13. Propose evidence-backed terminology-registry updates where warranted.

## Canonical Abstract

Create exactly one canonical Chinese Abstract. Preserve sample, methods, all reported directions/statistics, uncertainty and causal strength. A/B/C must reuse this version exactly rather than independently retranslate it.

## Full-text and SI coverage

Translate all scientifically relevant content required by the selected scope. For `FULL_MIRROR`, this includes Main and available scientific SI by default.

References normally remain in their original language. Missing/unreadable source content must be labeled using the shared source-gap vocabulary, never reconstructed from common practice or model knowledge.

## Figure and table integrity

Numerical table cells and figure data are locked to the source. Do not alter plotted points, axes, scales, error bars, significance markers or values.

Original conceptual figures may be localized only without changing structure and with clear identification. Explanatory redraws made later for Deep Reading must say `【根据原文重建，并非作者原图】`.

## Mirror PDF production

A follows the escalation:

`Strict Mirror → Adaptive Mirror → Readable Extension`

Prioritize page correspondence, then structure, nearby figure/table placement, paragraph correspondence and finally line correspondence. Protect readability. Chinese body text may often begin around 105%–115% of the source visual size when space allows; approximately 8.5 pt is an extreme safety floor rather than a target.

## Zotero archive handoff

Zotero remains the preferred long-term location for A. When a write-capable route is available, attach A as `[A] 中文全文翻译镜像版` and verify the returned parent/attachment identity.

If Zotero is unavailable, automation is not live-validated, or the user chooses manual archive handling:

- keep the verified A file;
- stage under `<data-root>/work/<paper_id>/handoff/` when a local runtime exists;
- record `pending_zotero_actions`;
- allow Translation/A to remain `COMPLETE` once their own translation/QC gate passes;
- report archive closure separately.

Never claim that A is in Zotero until the attachment is actually observed and verified.

## Terminology update

The registry is context-sensitive. Reuse a term only when the English term, discipline/subfield, conceptual meaning and paper context match. `HIGH / MEDIUM / LOW` confidence is distinct from TE1–TE7 evidence-source type.

Never silently overwrite an existing preferred translation; preserve evidence history and alternatives.

## Completion states

For any manifest scope, Translation `COMPLETE` requires:

- source identity/package accounted for;
- canonical Abstract complete;
- terminology issues resolved or explicitly accounted for;
- 100% expected translatable coverage accounted for;
- Main and SI status explicit;
- `source_inventory.json`, `translation_ledger.jsonl`, and `translation_issues.jsonl` cross-validate for the requested scope;
- no critical unlogged source gaps;
- Coverage/Semantic/Numeric/Layout QC complete;
- `translation_validation.json` was generated by the validator and passed for the active A;
- A generated and verified as the correct artifact for the active `paper_id`/source version.

`FULL_MIRROR` additionally requires `mirror_layout_plan.json` to cross-validate with no missing source page, translation unit, scientific figure or table, with table topology and rendered-page checks passing. Do not apply the mirror-layout requirements to `MAIN_ONLY` or `ABSTRACT_ONLY`.

**A verified Zotero attachment key is not required for Translation academic completion.** Pending Zotero work belongs to the archive layer.

Use `PROVISIONAL` when a named source/SI/content/layout gap affects the requested translation scope but the available translation remains usable. Use `BLOCKED` when missing source evidence prevents defensible translation. Do not use `PROVISIONAL` solely because Zotero automatic writing is unavailable.

## Hard translation rules

- Accuracy > professionalism > fidelity > fluency.
- Do not intensify or weaken causal language beyond the source.
- If authors themselves overstate causality, translate faithfully; criticism belongs to Deep Reading.
- Preserve all numbers, statistics, equations, parameters, software names and data.
- Do not add unreported experimental steps or parameter values.
- Preserve non-significant findings and uncertainty language.
- Do not silently correct source errors or inconsistencies.
- Do not independently translate author names.
- References normally remain in the original language.
- Do not change figure/table data.
- OCR is a last resort; unreliable source text must be marked rather than guessed.
