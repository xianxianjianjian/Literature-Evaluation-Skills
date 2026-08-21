# V1 Hardening Audit

This document tracks the post-rule-layer audit after Phase 5. It distinguishes a structurally hardened release candidate from real-paper scientific acceptance. Passing this audit does not make an individual paper archive scientifically complete.

## Branch basis

`phase-6-v1-hardening` is based on the cumulative `phase-5-orchestration` line, which already contains Phases 1–5. Draft PR #1 (`phase-6-v1-hardening → main`) is an audit/CI container only and is not merge authorization.

## Audit dimensions

1. Skill rules ↔ shared contracts
2. Skill rules ↔ knowledge schemas
3. Skill rules ↔ workflow manifest behavior
4. Skill rules ↔ helper scripts
5. deterministic tests / regression protection
6. honest capability boundaries
7. release/copyright/branch hygiene

## Current findings

### workflow_state.py — HARDENED

Now provides V1 manifest normalization/validation, two-Gate `WAITING_USER` semantics, stable `paper_id`, A/B/C state, blockers, pending Zotero actions, source-check date, `needs_update`, resume summary, and backward-compatible additive normalization.

Additional Phase 6 invariant: Search cannot be `PROVISIONAL/COMPLETE` without a selected `paper_id`, and Translation/Deep Reading/A/B/C cannot start before Minimal Intake establishes `paper_id`.

### validate_deliverables.py — HARDENED

Now verifies the complete V1 rule/reference inventory, A PDF signature, B DOCX package/Base Schema markers, C required sections, comment-only Chinese-character threshold, optional Canonical Abstract equality, and core manifest relationships.

`--require-workflow-complete` adds an explicit release/final-archive gate requiring:

- all four stages `COMPLETE`;
- A/B/C `COMPLETE`;
- stable `paper_id`;
- verified A/B Zotero keys and C Git path;
- no unresolved `needs_update`;
- no blockers;
- no pending Zotero actions;
- a dated source-change check.

These are deterministic structural checks only. They do not judge translation accuracy, statistical interpretation, methodological critique or visual quality.

### terminology_registry.py — FROZEN V1 INTERFACES COMPLETE

Implemented interfaces now cover:

- `lookup`
- `add`
- `update`
- `context`
- `status` (`update-status` retained as alias)
- `export`
- `list-ambiguous`

Context identity remains `English_Term + Discipline + Subfield + Context`. The helper never auto-selects a preferred translation. Changing `Preferred_Chinese` requires an explicit note and preserves the prior preferred wording in alternatives/history; supplied alternatives are merged rather than allowed to erase the old preferred wording. TE1–TE7 remains separate from HIGH/MEDIUM/LOW confidence.

Dedicated CRUD for `terminology_evidence.jsonl` is still a possible later convenience, but the frozen V1 terminology-registry interface itself is now present.

### history_manager.py — HARDENED

Selection history remains week-scoped for duplicate prevention, while completed reading history remains globally deduplicated by stable identity.

`append-reading` now requires a workflow manifest and mechanically verifies:

- record week matches manifest week;
- record `Paper_ID` matches active `paper_id`;
- `deep_reading = COMPLETE`;
- no unresolved Deep Reading `needs_update` or blocker;
- B is `COMPLETE` with a verified Zotero attachment key.

Thus a `PROVISIONAL` archive cannot silently enter `reading_history.csv` as completed work.

### mirror_pdf.py — HARDENED WITH HONEST V1 SCOPE

The helper validates source PDF/page-map structure, freezes `Strict Mirror → Adaptive Mirror → Readable Extension`, preserves 1.05–1.15 initial Chinese font scale and 8.5 pt safety floor, records per-page overflow/extension/render-inspection state, and does not permit layout QC to pass before visual inspection is accounted for.

It remains a deterministic layout/QC helper, not a publisher-grade automatic relayout engine. Real A still requires `render → inspect → iterate → re-render`.

### zotero_bridge.py — TRUTHFUL PARTIAL INTEGRATION

Read-only Local API interfaces are implemented: `status / find / children / verify`. Connector readiness can be probed separately. `create / attach` remain declared workflow interfaces but return `WRITE_ROUTE_NOT_IMPLEMENTED_OR_VERIFIED` until a supported write adapter is actually implemented and tested. `pending` only prepares a manifest record and never pretends to write Zotero.

Remaining production integration gap: verified parent creation and local-file attachment through an appropriate Connector/plugin write adapter.

### Search rule audit — PASS AFTER CAPABILITY SYNC

Search retains:

- 3–5 topic candidates and Topic Gate;
- Journal Mapping;
- Search Question Profile / concept blocks / unavailable-source logging;
- role-based recency;
- Round 1 targets and EX-01–EX-13;
- Quality Gate before the fixed 7D score;
- RED cannot win by score;
- Method Transfer Checklist;
- integrity wording that never claims truth/authenticity is proven;
- saturation/stop rule;
- Primary + Strong Alternatives and explicit #1-over-#2 rationale;
- immutable Search-time history with later findings separated.

`zotero-ingest.md` was updated from stale Phase-2 wording to the current V1 Local-API/Connector capability boundary and public-source reuse policy.

### Translation rule audit — PASS AFTER STATE FIXES

Canonical Abstract, Translation Units, 100% accountable coverage, source-gap vocabulary, numeric/data lock, Main+SI handling, mirror layout and four-layer QC remain aligned.

Two state inconsistencies were corrected:

- pending Zotero attachment cannot coexist with Translation `COMPLETE`; usable-but-unattached A remains `PROVISIONAL`;
- later-arriving SI sets stage-level Translation/Deep Reading `needs_update` and triggers affected A/B/C regeneration/reverification rather than inventing output-level `needs_update` fields.

### Deep Reading rule audit — PASS AFTER HISTORY FIX

Introduction, Methods, Results, Discussion, Dynamic Coverage and Full Research Audit remain aligned with the frozen evidence model. In particular:

- no overall-N substitution for unknown model N;
- important prespecified non-significant findings remain visible;
- mandatory consistency checks are performed when information permits;
- core figures/tables are visually inspected;
- author interpretation and evaluator critique remain separated;
- Dynamic Coverage cannot invent unavailable SI;
- `reading_history.csv` is COMPLETE-only.

### Public-source/data-format boundary — HARDENED

`shared/data-format-policy.md` now makes explicit that “online readable” does not automatically mean “safe to republish in a public Git repository.” Exact Original Abstract/source-text fields must come from a source with an acceptable reuse basis (for example user-supplied/owned material or an appropriately reusable source); otherwise the exact field remains a named gap/PROVISIONAL rather than being filled with copied or model-rewritten text presented as original.

## Automated verification — VERIFIED GREEN

Draft PR #1 provides the auditable CI surface. `V1 Smoke Tests` have been observed passing on Python 3.11 and Python 3.12 after the Phase 6 state/validator hardening.

The workflow runs:

```bash
python -m compileall scripts tests
python -m unittest discover -s tests -v
python scripts/validate_deliverables.py --repo-root .
```

Regression coverage now includes core state/identity, terminology history/context/export, history completion gating, C comment isolation, B structure, mirror-layout policy, truthful Zotero capability, synthetic T01–T04, specialist-only modes, Resume, Zotero downgrade, new-SI update, and full-workflow completion semantics.

Synthetic tests protect deterministic contracts only; they do not replace real-paper scientific/visual acceptance.

## Branch and repository hygiene — PASS FOR CURRENT RELEASE CANDIDATE

PR-level filename review contains only source code, Markdown/policies, CSV/JSONL/YAML state/schema files, tests/CI, and the intentionally preserved weekly Search test record. No paper PDF/DOCX binaries, A/B files, Zotero databases, credentials or secrets are part of the release candidate. `work/` and caches remain ignored.

The real Mullins acceptance manifest remains factual: Search is provisional, Translation/A are blocked by unavailable Main PDF, and Deep Reading has not been falsely marked complete.

## Remaining real-production gates

Before describing the system as fully production-validated, still require real source packages for:

- real T01–T04 scientific acceptance;
- real A render/visual iteration;
- real B evidence/source-anchor closure;
- real weekly C production from an acceptable exact Abstract source;
- real Zotero parent/Main/SI/A/B write + post-write verification through a supported adapter.

These remaining gates are documented capability/acceptance gaps, not permission to fabricate success.

## Merge rule

Do not merge to `main` merely because CI is green. Before any merge:

- re-check the latest PR HEAD CI;
- perform the final `main...phase-6-v1-hardening` diff/hygiene scan;
- confirm no consequential rule↔script contradiction remains;
- decide explicitly whether `main` is being published as a **V1 rule-layer/release-candidate implementation** or only after the remaining real-production gates are closed;
- obtain explicit release approval.
