# V1 Release Checklist

This checklist governs the usable V1 release from `v1-release-candidate` to `main`.

V1 release is no longer blocked by a particular Zotero write transport or by completing every possible real-paper acceptance scenario. Those remain post-release validation/optimization work. The release must nevertheless be truthful: no source gap, Zotero write or scientific check may be fabricated as complete.

## 1. Frozen scope

- [x] Four-Skill architecture is complete.
- [x] All 19 specialist reference files exist.
- [x] Exactly two fixed `WAITING_USER` Gates remain: weekly topic and final paper.
- [x] Search/Translation/Deep Reading support independent entry and Resume.
- [x] A/B/C contracts are defined.
- [x] Evidence classes, Source Anchors, stable IDs, Source Gap vocabulary and causal-strength rules are fixed.
- [x] `docs/v1-scope-freeze.md` defines the usable release boundary.
- [x] No additional numbered Phase is required for V1 release.

## 2. Academic completion semantics

- [x] Search completion depends on selection/source handoff, not Zotero transport.
- [x] Translation/A completion depends on translation/QC/artifact identity, not Zotero attachment key.
- [x] Deep Reading/B/C completion depends on evidence/audit/QC, not Zotero attachment key.
- [x] Completed Deep Reading may enter `reading_history.csv` while Zotero key fields remain empty.
- [x] Zotero-only pending work is recorded in `pending_zotero_actions` and does not force an academic stage to `PROVISIONAL`.
- [x] Real source/SI/version/evidence gaps still produce `PROVISIONAL` or `BLOCKED` as appropriate.
- [x] `validate_deliverables.py --require-academic-complete` exists.
- [x] Strict archive closure remains separately testable with `--require-archive-complete`.
- [x] Legacy `--require-workflow-complete` remains an archive-strict compatibility alias.

## 3. Core rule consistency

- [x] Four `SKILL.md` files read the shared state/source/evidence/Zotero policies.
- [x] TE1–TE7 is evidence-source type, separate from HIGH/MEDIUM/LOW confidence.
- [x] C comment minimum applies only to the comment/review body.
- [x] Canonical Abstract is single-source for A/B/C Chinese Abstract.
- [x] Main/SI are treated as one evidence package with explicit missing-source labels.
- [x] Overall N cannot replace unknown model N.
- [x] Important prespecified non-significant results remain represented.
- [x] Author interpretation and evaluator critique remain separate.
- [x] Statistical inconsistencies are audited, not silently replaced.
- [x] Public-Git source-text policy does not treat online visibility as republication permission.

## 4. Helper/script consistency

- [x] `workflow_state.py` manages one manifest, stable `paper_id`, two Gates, blockers, pending archive actions and `needs_update`.
- [x] `history_manager.py` uses week-scoped Selection dedupe and global completed-reading dedupe.
- [x] `history_manager.py` requires academic Deep Reading/B completion but not Zotero keys.
- [x] `terminology_registry.py` implements lookup/add/update/context/status/export without auto-selecting preferred translation.
- [x] `validate_deliverables.py` checks foundation, A/B/C structure, academic completion and strict archive completion separately.
- [x] `mirror_pdf.py` keeps `Strict Mirror → Adaptive Mirror → Readable Extension` and visual-QC requirements.
- [x] Zotero helpers remain truthful optional integrations and never fake successful writes.

## 5. Repository hygiene

- [x] `work/`, handoff files, caches and local environments are ignored.
- [x] Main/SI/A/B research binaries are not committed to the public repository.
- [x] No Zotero database, API/local authorization key, token or credential is committed.
- [x] No V2-only feature has become a hidden V1 responsibility.
- [x] Historical Phase branches are documented as cumulative development snapshots.

## 6. Automated acceptance required before merge

The exact `v1-release-candidate` HEAD must pass:

```bash
python -m compileall scripts tests
python -m unittest discover -s tests -v
python scripts/validate_deliverables.py --repo-root .
```

Required regression coverage includes:

- [x] two fixed Gate/state invariants;
- [x] paper identity before downstream stages;
- [x] terminology context/history behavior;
- [x] Selection and reading-history dedupe;
- [x] C comment-body counting;
- [x] B Base Schema markers;
- [x] mirror-layout strategy;
- [x] synthetic T01–T04/source-update scenarios;
- [x] Search-only / Translation-only / Deep-Reading-only / Resume;
- [x] Zotero pending without academic downgrade;
- [x] academic completion with missing Zotero keys;
- [x] strict archive completion requiring Zotero keys/no pending actions;
- [x] Mullins blocked trace remains un-fabricated.

Scope-freeze CI evidence observed before this checklist-only update:

- [x] Python 3.11 green after V1 scope-freeze changes.
- [x] Python 3.12 green after V1 scope-freeze changes.
- [x] foundation validator green after V1 scope-freeze changes.

The checklist commit itself must still receive one final exact-head CI pass before merge.

## 7. Real-paper validation backlog — not a V1 release blocker

These are important confidence-building tests, but they can continue after a usable V1 is published:

- [ ] real T01 ordinary empirical paper without SI.
- [ ] real T02 neuroscience paper with many figures/tables.
- [ ] real T03 Main + complex SI.
- [ ] real T04 missing SI → later upgrade.
- [ ] real A render → inspect → iterate → re-render.
- [ ] real B source-anchor closure.
- [ ] real weekly C production.
- [ ] resume Mullins 2025 when a usable Main PDF becomes available.

The existing Mullins run must remain factually blocked rather than being rewritten to satisfy the checklist.

## 8. Zotero optimization backlog — not a V1 release blocker

Current optional helpers may continue to be tested and improved, but V1 is usable without automatic Zotero writing.

Deferred items include:

- [ ] controlled live Zotero Desktop authorization/write validation;
- [ ] Local API parent-create unification;
- [ ] group-library/collection routing;
- [ ] automated reconciliation of pending Main/SI/A/B actions;
- [ ] broader live compatibility testing across Zotero versions.

Manual Zotero import/attachment followed by verification is an acceptable V1 operational fallback.

## 9. Final RC audit before merge

- [x] exact `v1-release-candidate` HEAD identified for the scope-freeze audit.
- [x] scope-freeze HEAD CI was green on Python 3.11 and 3.12.
- [x] `main...v1-release-candidate` is ahead-only with no accidental reverse divergence.
- [x] final changed-file list contains no research binaries/secrets/temp data.
- [x] active V1 rules no longer say “Zotero pending ⇒ academic stage PROVISIONAL”.
- [x] active V1 rules no longer require A/B Zotero attachment key for academic completion/history.
- [x] README describes the usable V1 rather than an unfinished Phase roadmap.
- [x] release meaning is explicitly approved: V1 is a complete usable academic Skill system; Zotero Local API refinements are deferred optimizations.
- [ ] final checklist-only HEAD CI green.

## 10. Release verdict model

After the last Section 9 item passes, the repository may be described as:

> **Literature Evaluation Skills V1 — usable academic workflow release**

This means the core Search → Translation → Deep Reading → A/B/C workflow, state/resume system and structural QA are complete and usable.

It does **not** mean every paper/source combination has been scientifically acceptance-tested, nor that optional Zotero automation has been live-validated on every desktop environment.

## 11. Main merge

Do not merge automatically merely because CI is green.

After the final audit, obtain explicit **merge approval**, then merge only:

```text
v1-release-candidate → main
```

Verify `main`, optionally tag `v1.0.0`, and only then consider cleaning historical branches.
