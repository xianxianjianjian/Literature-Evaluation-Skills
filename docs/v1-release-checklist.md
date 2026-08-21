# V1 Release Checklist

Use this checklist before moving the cumulative V1 development tree into `main`.

This checklist separates **structural/release-candidate verification** from **real-paper scientific acceptance**. Synthetic tests may verify state/routing/helper behavior, but they must never be presented as a substitute for source-based academic validation.

## 1. Branch lineage

- [x] `phase-6-v1-hardening` is based on the latest accepted cumulative phase branch (`phase-5-orchestration`).
- [x] Release branch is not behind its intended parent.
- [x] `main...phase-6-v1-hardening` PR file audit contains only intended V1/review-history files.

## 2. Repository hygiene

- [x] No paper Main/SI binaries, A/B deliverables, local Zotero files, secrets, tokens or credentials are committed.
- [x] `work/`, caches and temporary render artifacts remain ignored.
- [x] No V2-only implementation has leaked into V1; V2 topics appear only as explicit exclusions/boundaries.

## 3. Rule-layer consistency

- [x] Four `SKILL.md` files use the shared evidence/state/source/Zotero contracts.
- [x] All 19 specialist reference files are present.
- [x] TE1–TE7 means evidence-source type, not confidence rank.
- [x] Two fixed `WAITING_USER` Gates only: topic and final paper.
- [x] `PROVISIONAL`, `BLOCKED`, `needs_update` and Source Gap semantics are aligned.
- [x] C comment threshold applies only to the review/comment body.
- [x] `reading_history.csv` is COMPLETE-only; PROVISIONAL Deep Reading is not recorded as completed history.

## 4. Helper/script consistency

- [x] `workflow_state.py` can create/read/update/resume V1 manifest fields without academic judgment.
- [x] `history_manager.py` uses week-scoped selection dedupe and global completed-reading dedupe, and verifies `Deep Reading = COMPLETE` before reading-history append.
- [x] `terminology_registry.py` permits context-specific translations and preserves lifecycle history.
- [x] `validate_deliverables.py` checks V1 structure without pretending to judge academic quality.
- [x] `mirror_pdf.py` keeps the frozen layout escalation and requires visual render QA.
- [x] `zotero_bridge.py` accurately reports Local API/Connector capability and never fakes a Zotero write.

## 5. Automated verification

The release-candidate workflow runs:

```bash
python -m compileall scripts tests
python -m unittest discover -s tests -v
python scripts/validate_deliverables.py --repo-root .
```

- [x] Commands exit 0 in GitHub Actions.
- [x] `V1 Smoke Tests` pass on Python 3.11.
- [x] `V1 Smoke Tests` pass on Python 3.12.
- [x] Draft PR #1 provides an auditable CI/review surface without authorizing merge.

## 6. Copyright-free synthetic acceptance matrix

These automated scenarios protect state/routing/helper contracts only:

- [x] synthetic T01 ordinary empirical / no-SI completion state.
- [x] synthetic T02 many-figure/table mirror-plan preservation.
- [x] synthetic T03 Main + complex-SI single-workflow state model.
- [x] synthetic T04 SI unavailable → `PROVISIONAL` → `needs_update` → upgrade.
- [x] Search-only.
- [x] Translation-only.
- [x] Deep-Reading-only without A prerequisite.
- [x] Resume from an explicit blocker.
- [x] Zotero unavailable/downgrade with `pending_zotero_actions`.
- [x] New SI triggers targeted Translation/Deep Reading `needs_update`.

## 7. Real-paper scientific acceptance — still required before production claim

These tests require real source packages and human/visual academic QA. They remain intentionally open while the Mullins source-PDF blocker is unresolved:

- [ ] real T01 ordinary empirical paper without SI.
- [ ] real T02 neuroscience paper with many figures/tables.
- [ ] real T03 Main + complex SI.
- [ ] real T04 expected SI unavailable → PROVISIONAL → later upgrade.
- [ ] real Translation A render → inspect → iterate → re-render acceptance.
- [ ] real Deep Reading B evidence/source-anchor closure acceptance.
- [ ] real weekly C canonical-Abstract/comment/reviewer acceptance.
- [ ] real Zotero parent/Main/SI/A/B write + verification using a supported write adapter.

The suspended Mullins 2025 run remains a valid blocked/provisional acceptance trace. Do not fabricate completion merely to tick these boxes.

## 8. Current capability boundaries

The following are explicit V1 integration boundaries, not silent failures:

- Zotero Desktop Local API is read-only. The repository helper can probe the Connector server and generate pending actions, but `create/attach` must not report success until a supported write adapter is implemented and verified in the target runtime.
- `mirror_pdf.py` is a deterministic layout/QC helper, not a publisher-grade automatic relayout engine. Visual inspection remains mandatory.
- Structural validators cannot judge whether translation, methodological critique or statistical interpretation is academically correct; those require the specialist Skill plus source evidence.

## 9. Main merge decision

Do **not** merge the draft release PR merely because CI is green.

Before release to `main`:

1. review the latest PR diff after hardening stabilizes;
2. confirm automated checks are still green;
3. decide whether the open real-paper/Zotero integration gates are acceptable for a `V1 rule-layer release` or must be completed for a `V1 production release`;
4. obtain explicit release approval;
5. merge without rewriting away useful phase history;
6. verify `main` contains the expected V1 tree;
7. optionally create a `v1.0.0` tag/release;
8. only then consider deleting old phase branches.

`main` is the stable published line, not the active construction workspace.
