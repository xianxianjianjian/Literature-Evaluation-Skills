# Literature Evaluation v1.4.2 Implementation Audit

Audit date: 2026-09-07  
Baseline commit: `63c80804fd18cdf8d181e40ce1cf140116abd2fa` (`main`, equal to `origin/main`)  
Source and installed baseline: `1.4.1`  
Baseline tests: 187/187 passed

This audit compares the v1.4.1 repository and the live W36 Yuksel package with the v1.4.2 execution requirements. Yuksel is treated only as a real-paper regression case; no paper-specific TMR/SWS/REM/Figure logic belongs in production code.

## ALREADY_IMPLEMENTED

- Exact-mirror geometry already preserves source page count, PDF boxes, rotation, one-to-one page mapping, text-frame bounding boxes, object placement, table-cell topology and pixels outside reviewed replacement regions.
- The renderer already embeds SimSun, prohibits fallback, supports synthetic bold/italic intent, preserves source text color and alignment, renders raised citation/scientific-exponent tokens, and searches role-like frame kinds across the 0.95–1.10 scale and 1.15–1.45 leading ranges.
- Numeric integrity already extracts signed values, statistics, scientific notation, units, DOI, version and time-point tokens and compares source/translation multisets with reviewed whitelisting.
- Main/SI have separate source identities and language/geometry authorities; source conflicts, figure labels, terminology evidence and translation issues already have independent artifacts.
- Deep Reading already has the 0–10 Base Schema, Main/SI audit, evidence classes, source anchors, hypothesis/result identifiers, sample/method/result reconstruction, dynamic coverage guidance, DOCX metadata sanitation, OOXML checks, office rendering and all-page visual-QA checks.
- Zotero already supports PDF-first parent creation, durable local attachment upload, parent/title/file identity verification, idempotency/conflict refusal, explicit pending actions, and separate academic/archive completion semantics.
- Workflow and history helpers already parse structured files and write them atomically; history corrections preserve old/new values.

## PARTIALLY_IMPLEMENTED

- Residual-English auditing is frame-cropped and source-aware, but it rejects only shared runs of four or more substantive English words and does not use a formal region-role policy.
- Frame records already contain `kind`, source font, size, leading, weight, alignment and RGB fields, but there is no normalized H1/H2/H3 role vocabulary, `style_map.json`, or independent `style_fidelity.json` gate.
- Figure-label translation has a closed lifecycle, but figure-internal labels are currently treated as translatable labels rather than a separately allowed `FIGURE_INTERNAL` role.
- Source intake inventories Main/SI/corrections/data/code, but there is no `source_cross_reference.json` validator or explicit Source Package/Source Archive stage object in the workflow manifest.
- The psychology method router covers quantitative/qualitative/mixed, intervention, observational, MRI/fMRI and mediation/SEM, but not EEG/PSG, MEG, graph/network, machine learning, animal/database, repeated-measures or the required design-specific prompt details.
- B requires important figures to be inspected and mapped, but the validator checks only headings/markers/evidence files and technical rendering; it does not prove prose coverage or embedded core-figure interpretation.
- Source→Notebook closure is described, but the validator only checks that evidence files exist and does not validate `source_to_notebook_mapping.csv` semantics.

## RULE/CODE_CONFLICT

- The current residual gate and documentation allow an unapproved source-English run shorter than four words; v1.4.2 requires any matched residual in translatable prose roles to fail.
- Current figure rules expect embedded figure labels to be translated in exact A; v1.4.2 freezes original scientific figure internals while requiring translated captions and unchanged figure data pixels.
- Current workflow order treats Zotero closure mainly as an optional end-stage cleanup. v1.4.2 requires Source Archive before Translation when available, while preserving an explicit `PENDING` route when Zotero is unavailable.
- W36 currently records A/B v1.4.1 as `COMPLETE`, but the new acceptance criteria require a traceable correction to `PROVISIONAL` before rebuilding.

## NOT_IMPLEMENTED

- Formal region roles with `translatable` and `preserve_english` semantics.
- Style fingerprint normalization, reusable CJK style mapping and independent style-fidelity report.
- Explicit source-package cross-reference closure and separate source/output archive stage records.
- B narrative-coverage artifact and key-claim prose-closure validation.
- B figure inventory with core/non-core classification, embed/caption/interpretation/source-anchor gates.
- Validated design profile and broad method router for EEG/PSG, MEG, network, machine-learning, repeated-measures, longitudinal, animal and database designs.
- v1.4.2 release/implementation notes and the requested targeted tests.
- Yuksel v1.4.2 A/B regression artifacts, archive replacement, C review and knowledge reconciliation.

## IMPLEMENTED_BUT_NOT_TEST_ENFORCED

- Existing rendering retains color/alignment and synthetic weight/italic intent, but tests do not yet enforce H1/H2/H3 hierarchy, source color, italic support, superscript or distinct body/heading mappings as a coherent style contract.
- Source manifests can record SI keys and the current W36 archive is live-verified, but workflow validation does not yet enforce Source Archive and Output Archive as separate completion dimensions.
- Dynamic Coverage guidance asks for important source-item mapping and prose explanation, but current completion code does not validate either requirement.
- Zotero 10.0.1 attachment upload has now been exercised successfully on the real W36 paper, while the shared documentation still describes desktop live validation as deferred.

## Implementation direction

The smallest coherent change is to extend existing evidence contracts and validators rather than create a parallel workflow: add role/style fields to exact-mirror frames, add source-package and B evidence validators, expand the current method router, extend the manifest additively, and preserve backward-readable v1.4.1 records while requiring the v1.4.2 artifacts for new completion claims.
