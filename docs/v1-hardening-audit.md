# V1 Hardening and Integration Audit

This document separates three meanings that must not be collapsed:

1. **rule-layer / structural hardening**;
2. **integration implementation + deterministic/mock verification**;
3. **real-paper / live production validation**.

Passing one level does not imply the next.

## Branch basis

- `phase-6-v1-hardening` is the sealed cumulative Phase 1–5 rule-layer RC.
- `phase-7-zotero-write-adapter` adds bibliographic-parent creation.
- `phase-8-zotero-local-attachments` adds durable Zotero 10+ existing-parent attachment.
- Draft PR #1, #2 and #3 are audit/CI containers only; none is merge authorization.

## Audit dimensions

1. Skill rules ↔ shared contracts
2. Skill rules ↔ knowledge schemas
3. Skill rules ↔ workflow manifest behavior
4. Skill rules ↔ helper scripts
5. deterministic tests / regression protection
6. truthful capability boundaries
7. release/copyright/branch hygiene
8. live external integration validation

## Phase-6 rule-layer findings

### workflow_state.py — HARDENED

Provides V1 manifest normalization/validation, two-Gate `WAITING_USER` semantics, stable `paper_id`, A/B/C state, blockers, pending Zotero actions, source-check date, `needs_update`, resume summary, and backward-compatible additive normalization.

Search cannot become `PROVISIONAL/COMPLETE` without a selected `paper_id`; Translation/Deep Reading/A/B/C cannot start before Minimal Intake establishes `paper_id`.

### validate_deliverables.py — HARDENED

Verifies the frozen Skill/reference inventory, A PDF signature, B DOCX package/Base Schema markers, C required sections, comment-only Chinese-character threshold, optional Canonical Abstract equality, manifest relationships, and `--require-workflow-complete` closure rules.

These are deterministic structural checks only; they do not judge translation accuracy, statistical interpretation, methodological critique or visual quality.

### terminology_registry.py — FROZEN V1 INTERFACES COMPLETE

Supports `lookup / add / update / context / status / export / list-ambiguous`. Context identity remains `English_Term + Discipline + Subfield + Context`; no automatic preferred-term decision is made. Prior preferred wording/history is preserved. TE1–TE7 remains separate from HIGH/MEDIUM/LOW confidence.

### history_manager.py — HARDENED

Selection history is week-scoped for duplicate prevention. Completed reading history is globally deduplicated by stable identity. `append-reading` requires manifest consistency, `Deep Reading = COMPLETE`, no unresolved update/blocker, and verified B attachment state.

### mirror_pdf.py — HARDENED WITH HONEST V1 SCOPE

Freezes `Strict Mirror → Adaptive Mirror → Readable Extension`, layout/QC metadata and mandatory visual inspection. It remains a deterministic helper rather than a publisher-grade fully automatic relayout engine.

### Search / Translation / Deep Reading rule audits — PASS

The frozen evidence model, topic/paper Gates, two-round Search, Quality Gate + fixed 7D scoring, integrity wording, Canonical Abstract, Translation Units, Main+SI handling, full research audit, sample/model-N discipline, non-significant-result retention, author/evaluator separation, Dynamic Coverage and COMPLETE-only reading history remain aligned.

### Public-source/data-format boundary — HARDENED

Web visibility is not treated as permission to republish exact source text in a public Git repository. Exact Original Abstract/source-text fields require an acceptable source basis or remain an explicit gap/PROVISIONAL.

## Phase-7 Zotero parent-create audit — PASS AT IMPLEMENTATION/MOCK LEVEL

Phase 7 established a truthful Connector parent-create path:

- `selected-target` via `/connector/getSelectedCollection`;
- structured personal/institutional creator normalization;
- duplicate check by normalized DOI/exact title;
- `--yes` mechanical write boundary;
- `/connector/saveItems` requires HTTP 201;
- post-write Local API identity lookup is mandatory;
- only one DOI/title match yields `CREATED_AND_VERIFIED`;
- ambiguous/unverified writes are explicitly non-complete.

Connector `/saveAttachment` was deliberately rejected as the generic archive solution because it depends on a short-lived Connector save session and Connector-side parent id. That design decision remains valid.

Live parent-create validation against the user's Zotero Desktop remains OPEN.

## Phase-8 Zotero durable attachment audit — PASS AT IMPLEMENTATION/MOCK LEVEL

A later official-capability review established Zotero 10+ Local API write/full-upload support. Phase 8 uses that capability for durable existing-parent Main/SI/A/B attachment.

### Security / identity controls

- Requires discovery of `Zotero-Server-ID`.
- Requests write authorization through Zotero Desktop.
- Local API key stays in process memory only; never printed or persisted.
- Temporary/non-remembered authorization is discarded after successful write use.
- One 401 reauthorization attempt is supported.
- Server-ID mismatch/HTTP 412 stops the active archive operation.
- Local helper requests use a non-browser application User-Agent.

### File-upload controls

- Creates an imported-file child under a verified parent.
- Computes filename/filesize/mtime/MD5 locally.
- Uses the documented full-upload authorization → byte upload → upload-key registration flow.
- Performs read-after-write verification against the same Server-ID.
- Requires parent + filename + MD5 agreement before `ATTACHED_AND_VERIFIED`.
- Applies a project-side 256 MiB single-file safety limit.

### Resume / idempotency controls

- Exact same-title + filename + MD5 child → `ALREADY_ATTACHED_AND_VERIFIED`, no rewrite.
- Empty same-title child from an interrupted run → reuse and resume.
- Multiple same-title children or same-title different-file identity → `ATTACHMENT_CONFLICT`, no silent overwrite.
- Child-created/file-upload-incomplete → preserve attachment key in `ATTACHMENT_FILE_UPLOAD_INCOMPLETE` for recovery.
- Preview without `--yes` does not probe/authorize/write Zotero.

A real CI failure exposed a null-MD5 normalization edge case; the code was corrected so Zotero `md5: null` is treated as empty metadata for interrupted-child recovery. The corrected exact HEAD subsequently passed Python 3.11/3.12 smoke tests.

Live Phase-8 authorization/write validation against the user's Zotero Desktop remains OPEN.

## Automated verification — GREEN FOR CURRENT PHASE-8 CODE LINE

The workflow runs:

```bash
python -m compileall scripts tests
python -m unittest discover -s tests -v
python scripts/validate_deliverables.py --repo-root .
```

Regression coverage includes state/identity, terminology, history completion gating, A/B/C structure, mirror policy, synthetic T01–T04, specialist-only modes, Resume, Zotero downgrade/new-SI update, parent creation, Local API authorization, full file upload, Server-ID binding, attachment idempotency, conflict refusal and interrupted-run recovery.

Synthetic/mock tests protect deterministic contracts only; they do not replace real-paper scientific/visual acceptance or live Zotero Desktop testing.

## Branch and repository hygiene

The cumulative development line contains source code, Markdown/policies, CSV/JSONL/YAML state/schema files, tests/CI and the intentionally preserved weekly Search trace. No paper PDF/DOCX binaries, A/B files, Zotero databases, API keys, credentials or secrets are part of the repository changes. `work/` and research binaries remain ignored.

The real Mullins acceptance manifest remains factual: Search is provisional, Translation/A are blocked by unavailable Main PDF, and Deep Reading has not been falsely marked complete.

## Current acceptance verdict

- **Phase 6 rule-layer / structural RC: PASS.**
- **Phase 7 parent-create implementation/mock verification: PASS.**
- **Phase 8 durable attachment implementation/mock verification: PASS.**
- **Live Zotero production validation: OPEN.**
- **Real-paper A/B/C/T01–T04 scientific acceptance: OPEN.**

The remaining Zotero gap is now live-environment validation, not the absence of a durable existing-parent attachment implementation.

## Remaining production gates

Before describing the full system as production-validated, still require:

- controlled live Zotero 10+ Server-ID/authorization test;
- live synthetic parent create + verification;
- live synthetic existing-parent file attach + parent/filename/MD5 verification;
- idempotent rerun confirming no duplicate attachment;
- real Main/SI/A/B Zotero archive validation when actual source/output files are available;
- real T01–T04 scientific acceptance;
- real A render/visual iteration;
- real B evidence/source-anchor closure;
- real weekly C production from an acceptable exact Abstract source.

The Mullins Main PDF source blocker remains independent of Zotero capability.

## Merge rule

Do not merge to `main` merely because CI is green. Before any merge, identify the exact cumulative branch intended for release, re-check its HEAD/compare/CI, define whether the release claim is structural, integration, or production, and obtain explicit release approval.
