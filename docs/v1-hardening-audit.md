# V1 Hardening Audit

This document records the final release-candidate audit after the numbered Phase development was frozen.

## Release basis

The usable release line is now:

```text
v1-release-candidate
```

It is based on the cumulative Phase-8 tree. Phase 1–8 remain development history; no Phase 9+ work is required for V1 release.

The release claim is deliberately narrower and more useful than “everything has been production-tested everywhere”:

> V1 is a complete usable academic literature-evaluation workflow with truthful optional archive integrations.

## Core architecture — PASS

The repository contains four Skills:

- thin weekly router/state/resume coordinator;
- Literature Search;
- Paper Translation;
- Paper Deep Reading.

The three specialist Skills remain independently usable.

All 19 specialist reference files are present and the shared contracts cover evidence, identifiers, source identity, state, data format and Zotero archive policy.

## Evidence/research rules — PASS

The final V1 preserves:

- four evidence classes with separate Source Anchors;
- stable `EXT / EX / AUD / CLM / TRI / TERM / TERMEV / AN / SRC / H` namespaces;
- Main + SI audit;
- no invention of unreported methods/parameters/results/model N;
- non-significant prespecified findings;
- corrected vs uncorrected distinctions;
- mandatory consistency checks when information permits;
- author interpretation separated from evaluator critique;
- ED0–ED3 interpretation distance;
- A0–A3 audit severity;
- causal-strength warnings;
- Dynamic Coverage rather than a closed notebook template.

## Search — PASS

Search includes topic planning, Journal Mapping, Search Question Profile, database/source routing, recency roles, Round 1/2 screening, EX codes, Quality Gate before 7D scoring, RED cannot win by score, Method Transfer Checklist, integrity checks, saturation/stop rule, Primary + Alternatives and two fixed user Gates.

Search academic completion now depends on an auditable selection and usable source/package handoff—not on Zotero transport.

## Translation — PASS

Translation includes context-sensitive terminology, TE1–TE7/source-type separation from confidence, one Canonical Abstract reused by A/B/C, Translation Units, Main/SI coverage, numeric/table/figure locks, source-gap handling, `Strict Mirror → Adaptive Mirror → Readable Extension`, and Coverage/Semantic/Numeric/Layout QC.

Translation/A academic completion requires the artifact and its QC, but not a Zotero attachment key. Archive pending is tracked separately.

## Deep Reading — PASS

Deep Reading includes Full Research Audit, Paper Structure Inventory, Introduction argument/gap/hypothesis reconstruction, Sample Ledger, Measurement Chain, participant/researcher methods views, acquisition/preprocessing separation, Analysis Question Tree, Result Matrix, hypothesis closure, Discussion/critique separation, Innovation/Limitation/Redesign/Transfer matrices and Source→Notebook closure.

Deep Reading/B/C academic completion no longer depends on Zotero attachment keys. A completed reading may enter `reading_history.csv` while archive fields remain empty; real source/evidence provisional work still cannot.

## Completion model — HARDENED

V1 now distinguishes two deterministic levels:

### Academic completion

Requires applicable stages and A/B/C to be complete, stable paper identity, no consequential `needs_update`, no academic blocker, and a dated source-change check. `pending_zotero_actions` are allowed.

Validator:

```bash
python scripts/validate_deliverables.py \
  --manifest <workflow_manifest.yaml> \
  --require-academic-complete
```

### Archive completion

Adds verified A/B Zotero keys and no pending Zotero actions. The older `--require-workflow-complete` remains a compatibility alias for this stricter level.

Validator:

```bash
python scripts/validate_deliverables.py \
  --manifest <workflow_manifest.yaml> \
  --require-archive-complete
```

This prevents both failure modes: Zotero cannot erase completed academic work, and completed academic work cannot be misreported as completed Zotero archival work.

## State/resume — PASS

`workflow_state.py` provides one manifest, stable `paper_id`, two-Gate `WAITING_USER`, A/B/C states, blockers, pending archive actions, source-change date and `needs_update`.

The router resumes the smallest unresolved academic dependency and does not repeat satisfied Gates or redo complete Translation/Deep Reading because an archive task remains pending.

## Knowledge/history — PASS

- Selection duplicate prevention is week-scoped.
- Completed reading dedupe is global by stable identity.
- `reading_history.csv` requires Deep Reading/B academic COMPLETE and no Deep Reading blocker/update.
- Zotero key columns are optional archive metadata and can be reconciled later.
- `research_profile.md` cannot be silently changed from one paper.

## A/B/C structural validation — PASS

`validate_deliverables.py` verifies:

- required repository/Skill/reference inventory;
- A PDF signature;
- B DOCX package and Base Schema markers;
- C required sections;
- comment-body-only Chinese-character minimum;
- reviewer profile when configured;
- Canonical Abstract equality when supplied;
- academic and archive completion as separate levels.

It does not pretend to judge scientific quality or visual layout quality.

## Zotero integration — OPTIONAL / TRUTHFUL

Zotero remains the preferred archive for Main/SI/A/B.

The repository contains:

- Connector parent-create integration;
- Zotero 10+ Local API existing-parent attachment implementation;
- Server-ID/authorization/full-upload/idempotency/conflict/recovery tests.

These helpers are retained as optional enhancements. Real desktop live validation, Local API parent-create unification, group-library routing and collection targeting are post-V1 optimizations.

When unavailable, V1 uses handoff files + `pending_zotero_actions` or manual Zotero handling. No unverified write may be reported as successful.

## Mirror PDF scope — HONEST

`mirror_pdf.py` is a deterministic layout/QC helper, not a publisher-grade automatic typesetting engine. The Translation Skill still requires render → inspect → iterate → re-render and can use the available document/PDF generation environment to produce A.

## Repository/copyright hygiene — PASS

The repository is intended to contain source code, rules, schemas, tests, C/weekly state and decision history—not copyrighted research binaries. Main/SI/A/B, local Zotero databases, secrets and temporary files remain excluded.

Public web visibility is not treated as permission to republish exact source text.

## Real Mullins trace — FACTUAL

The Mullins 2025 run remains an intentionally incomplete real acceptance trace because the Main PDF was unavailable. It must not be rewritten to `COMPLETE` simply to make a release checklist green.

That trace is now a Resume/blocker example rather than a V1 release blocker.

## Remaining validation backlog — NON-BLOCKING FOR V1 RELEASE

- additional real T01–T04 scientific acceptance;
- real A visual iteration;
- real B source-anchor closure;
- real weekly C production on a suitable source package;
- live Zotero Desktop write testing;
- group-library/archive-routing optimization.

These increase confidence and coverage but do not represent missing core Skill rules.

## Final release blockers

Before merging `v1-release-candidate` to `main`, only the following remain release-blocking:

1. exact-head Python 3.11/3.12 CI green;
2. foundation validator green;
3. final stale-rule scan finds no Zotero-only academic downgrade/key requirement;
4. final `main...v1-release-candidate` diff is clean and ahead-only;
5. no research binaries/secrets/temp files in the release diff;
6. explicit user approval to publish the usable V1.
