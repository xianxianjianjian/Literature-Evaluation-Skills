# V1 Hardening Audit

This document tracks the post-Skill-rule audit performed after Phase 5. It distinguishes completed rule-layer work from executable helper coverage and must not be used to mark a scientific workflow complete.

## Branch basis

`phase-6-v1-hardening` is based on `phase-5-orchestration`, which already cumulatively contains Phases 1–5.

## Audit dimensions

1. Skill rules ↔ shared contracts
2. Skill rules ↔ knowledge schemas
3. Skill rules ↔ workflow manifest behavior
4. Skill rules ↔ helper scripts
5. deterministic tests / regression protection
6. honest capability boundaries

## Current findings

### workflow_state.py — UPDATED

Previous issue:

- still described itself as Phase 1;
- did not create/validate `blocking_issues` although the V1 router depends on it;
- `needs_update` was not normalized across all stages;
- no CLI support for paper identity, output state, blockers, pending Zotero actions, or source-change dates;
- mechanically allowed `WAITING_USER` in non-Gate stages.

Hardening result:

- V1 manifest normalization and validation;
- two-Gate `WAITING_USER` semantics;
- `set-paper`, `set-output`, blocker, pending-Zotero and source-check commands;
- resume-oriented `summary` command;
- backward-compatible normalization for earlier manifests.

### validate_deliverables.py — UPDATED

Previous issue:

- still validated only the Phase 1 foundation and basic file existence;
- did not require the 19 specialist reference files;
- did not structurally validate B or the required C fields;
- did not compare C with `canonical_abstract.md`;
- did not check key manifest completion relationships.

Hardening result:

- full V1 repository/reference inventory checks;
- A PDF signature check;
- B DOCX package + Base Schema marker check;
- C required-section and comment-body validation;
- optional Canonical Abstract equality check;
- basic manifest completion consistency checks.

These are structural checks only. Visual PDF/DOCX QA and academic-quality judgments remain specialist responsibilities.

### terminology_registry.py — PASS WITH LATER ENHANCEMENT POSSIBLE

Current behavior correctly allows one English term to have different records by `English_Term + Discipline + Subfield + Context`, while rejecting the same contextual identity. TE1–TE7 is kept separate from HIGH/MEDIUM/LOW confidence in the shared policy.

Possible later enhancement: dedicated terminology-evidence JSONL management. Not a blocker for the frozen V1 registry contract.

### history_manager.py — PASS

Selection history deduplicates within a week but allows the same paper to re-enter in later weeks. Completed reading history remains globally deduplicated by stable paper identity.

### mirror_pdf.py — NEEDS V1 LABEL/QA HARDENING

The frozen V1 scope treats this as a deterministic layout helper, not a publisher-grade automatic relayout engine. The current script still labels itself `PHASE_1_LAYOUT_PLAN_ONLY` and lacks explicit plan-validation/render-QC interfaces. It should be upgraded without pretending it can replace the required render → inspect → iterate workflow.

### zotero_bridge.py — PARTIAL BY DESIGN, WRITE ROUTE UNRESOLVED

Read-only Local API operations are implemented and correct. Zotero Desktop Local API itself is read-only. Safe writes require the Connector server/plugin route or another explicitly supported write adapter. The helper must not claim `create` / `attach` success until such a route is implemented and verified.

This is an explicit integration gap, not permission to fake writes.

### Automated tests — IN PROGRESS

Add stdlib-only regression tests for state, history, terminology, validator and layout helpers, plus a GitHub Actions smoke workflow. Zotero read behavior can be tested with a local mock HTTP server; real library writes remain an integration test.

## Merge rule

Do not merge the development chain to `main` until:

- V1 rule ↔ script consistency audit is closed or each remaining gap is explicitly documented;
- automated smoke tests pass;
- no temporary/copyrighted paper binaries are committed;
- the suspended Mullins acceptance record remains factually unchanged;
- a final branch diff confirms that V2 features have not leaked into V1.
