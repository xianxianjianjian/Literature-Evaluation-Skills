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
- backward-compatible additive normalization for earlier manifests.

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

These are deterministic structural checks only. Visual PDF/DOCX QA and academic-quality judgments remain specialist responsibilities.

### terminology_registry.py — PASS WITH LATER ENHANCEMENT POSSIBLE

Current behavior correctly allows one English term to have different records by `English_Term + Discipline + Subfield + Context`, while rejecting the same contextual identity. TE1–TE7 is kept separate from HIGH/MEDIUM/LOW confidence in the shared policy.

Possible later enhancement: dedicated terminology-evidence JSONL management/export commands. This is not currently treated as a release-blocking contradiction in the frozen V1 rule layer because evidence IDs and context are already persistable in the registry, but it remains a useful implementation improvement.

### history_manager.py — PASS

Selection history deduplicates within a week but allows the same paper to re-enter in later weeks. Completed reading history remains globally deduplicated by stable paper identity.

### mirror_pdf.py — UPDATED WITH HONEST V1 SCOPE

Previous issue:

- still labeled itself as a Phase 1/future-engine placeholder;
- lacked explicit plan validation and render-QC state.

Hardening result:

- now identifies itself as a V1 deterministic layout/QC helper;
- validates source PDF signature and page-map structure;
- freezes `Strict Mirror → Adaptive Mirror → Readable Extension`;
- enforces 1.05–1.15 initial Chinese font scale and 8.5 pt safety floor;
- records per-page strategy, overflow, extension-page and render-inspection state;
- `LAYOUT_QC_PASSED` cannot be declared until all planned pages are marked inspected;
- explicitly requires the human/tool loop `render → inspect → iterate → re-render`.

It still does **not** pretend to be a publisher-grade fully automatic relayout engine and does not translate content.

### zotero_bridge.py — UPDATED, WRITE ADAPTER STILL AN EXPLICIT GAP

Previous issue:

- safe read interfaces existed but the script still described itself as Phase 1;
- `create` / `attach` returned old Phase 1 stub language;
- Connector-server readiness was not exposed.

Hardening result:

- Local API read interfaces remain `status / find / children / verify`;
- Local API is explicitly labeled read-only;
- `status` now distinguishes Local API availability from Connector-server availability;
- `connector-status` probes `/connector/ping`;
- `create` / `attach` remain declared but return `WRITE_ROUTE_NOT_IMPLEMENTED_OR_VERIFIED` rather than pretending success;
- `pending` can prepare a `pending_zotero_actions` record without modifying Zotero.

Remaining V1 integration gap: a verified Connector/plugin adapter for bibliographic-parent creation and local-file attachment. The Local API itself cannot satisfy this because it is read-only. This gap must remain explicit until a real write route is implemented and tested.

### Automated tests — ADDED, REMOTE RUN NOT YET VERIFIED

Added:

- `tests/test_core.py` with stdlib regression checks for workflow state, history dedupe, terminology context identity, C comment isolation, B DOCX Base Schema markers and mirror layout policy;
- `.github/workflows/v1-smoke.yml` for Python 3.11/3.12 compile + unittest + repository validation.

The current ChatGPT execution container cannot resolve `github.com`, so a direct `git clone` test run from that container is unavailable. The GitHub connector currently exposes no verified push-triggered workflow run for the latest branch commits. Therefore the repository must **not** yet claim that GitHub Actions passed. Confirm the actual Actions run before release/merge.

### Branch hygiene — PASS SO FAR

`phase-6-v1-hardening` is ahead of `phase-5-orchestration` with no divergence. Current Phase 6 changes are limited to hardening scripts, tests, CI, README and documentation; the specialist academic rule files and suspended Mullins manifest were not rewritten by Phase 6.

## Remaining release work

Before merging to `main`:

1. confirm smoke/unit tests actually run and pass in an environment with the full repository;
2. decide whether the Zotero write adapter is required for V1 release or remains a documented `PROVISIONAL` integration boundary;
3. optionally add terminology-evidence JSONL helper operations if they are judged necessary for V1 rather than a later enhancement;
4. execute final repository hygiene/diff review;
5. resume real T01–T04 / specialist-mode / resume / new-SI tests when suitable source packages are available;
6. keep the real Mullins acceptance manifest factual (`Translation/A = BLOCKED`) until its source-PDF blocker is actually resolved.

## Merge rule

Do not merge the development chain to `main` until:

- V1 rule ↔ script consistency audit is closed or each remaining gap is explicitly accepted/documented;
- automated smoke tests pass;
- no temporary/copyrighted paper binaries or secrets are committed;
- the suspended Mullins acceptance record remains factually unchanged;
- a final branch diff confirms that V2 features have not leaked into V1.
