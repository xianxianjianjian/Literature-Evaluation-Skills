# V1 Release Checklist

Use this checklist before moving the cumulative V1 development tree into `main`.

This checklist separates **structural/release-candidate verification**, **integration implementation**, and **real-paper/live production acceptance**. Synthetic/mock tests may verify state/routing/helper/protocol behavior, but they must never be presented as a substitute for source-based academic validation or a real Zotero Desktop write test.

## 1. Branch lineage

- [x] `phase-6-v1-hardening` is based on the cumulative Phase 1–5 line.
- [x] Phase 6 rule-layer RC is not behind its intended parent.
- [x] `main` remains at the initial stable line until explicit release approval.
- [x] Phase 7 extends Phase 6 with parent-create integration only.
- [x] Phase 8 extends Phase 7 with durable Zotero 10+ existing-parent attachment integration only.
- [x] Latest Phase 7→8 compare is one-way cumulative with no reverse divergence.

## 2. Repository hygiene

- [x] No paper Main/SI binaries, A/B deliverables, local Zotero files, secrets, tokens or credentials are committed.
- [x] `work/`, caches and temporary render artifacts remain ignored.
- [x] `.gitignore` guards PDF/DOCX research binaries, local environments, `.env` files and Zotero/local database artifacts from accidental future commits.
- [x] Local Zotero authorization keys are never printed or persisted by the Phase-8 helper.
- [x] No V2-only implementation has leaked into V1.

## 3. Rule-layer consistency

- [x] Four `SKILL.md` files use the shared evidence/state/source/Zotero contracts.
- [x] All 19 specialist reference files are present.
- [x] TE1–TE7 means evidence-source type, not confidence rank.
- [x] Two fixed `WAITING_USER` Gates only: topic and final paper.
- [x] `PROVISIONAL`, `BLOCKED`, `needs_update` and Source Gap semantics are aligned.
- [x] C comment threshold applies only to the review/comment body.
- [x] `reading_history.csv` is COMPLETE-only.
- [x] Public-Git source-text policy prevents web-visible text from being silently treated as freely republishable Original Abstract/source content.
- [x] Zotero policy now distinguishes Connector parent creation from Zotero 10+ Local API durable attachment.

## 4. Helper/script consistency

- [x] `workflow_state.py` can create/read/update/resume V1 manifest fields without academic judgment.
- [x] Downstream stages/outputs cannot start before `paper_id` is established.
- [x] `history_manager.py` uses week-scoped selection dedupe and global completed-reading dedupe, and verifies `Deep Reading = COMPLETE` before reading-history append.
- [x] `terminology_registry.py` implements the frozen lookup/add/update/context/status/export interfaces and preserves context/history.
- [x] `validate_deliverables.py` checks V1 structure without pretending to judge academic quality and provides `--require-workflow-complete`.
- [x] `mirror_pdf.py` keeps the frozen layout escalation and requires visual render QA.
- [x] `zotero_bridge.py` exposes parent create and durable attach as separate, truthful operations.
- [x] `zotero_local_write.py` implements Zotero 10+ Server-ID-bound authorization/item/full-upload primitives without persisting the Local API key.
- [x] `zotero_local_archive.py` implements idempotent/resumable attachment planning and conflict refusal.

## 5. Automated verification

The integration workflow runs:

```bash
python -m compileall scripts tests
python -m unittest discover -s tests -v
python scripts/validate_deliverables.py --repo-root .
```

- [x] Phase 6 exact-head smoke tests passed on Python 3.11 and 3.12.
- [x] Phase 7 parent-create exact-head smoke tests passed on Python 3.11 and 3.12.
- [x] Phase 8 durable-attachment exact-head smoke tests passed on Python 3.11 and 3.12 after the null-MD5 resume edge case was corrected.
- [x] Draft PR #1 provides the Phase-6 RC audit surface.
- [x] Draft PR #2 provides the Phase-7 parent-create audit surface.
- [x] Draft PR #3 provides the Phase-8 durable-attachment audit surface.
- [x] The committed Mullins 2025 blocked/provisional manifest remains protected by CI.

## 6. Copyright-free synthetic / mock acceptance matrix

These automated scenarios protect deterministic contracts only:

- [x] synthetic T01 ordinary empirical / no-SI completion state.
- [x] synthetic T02 many-figure/table mirror-plan preservation.
- [x] synthetic T03 Main + complex-SI single-workflow state model.
- [x] synthetic T04 SI unavailable → `PROVISIONAL` → `needs_update` → upgrade.
- [x] Search-only / Translation-only / Deep-Reading-only.
- [x] Resume from explicit blocker.
- [x] Zotero unavailable/downgrade with `pending_zotero_actions`.
- [x] New SI triggers targeted Translation/Deep Reading `needs_update`.
- [x] Full-workflow completion rejects pending Zotero, blockers and unresolved `needs_update`.
- [x] Zotero parent create preview / duplicate refusal / unique post-write verification.
- [x] Zotero Local API Server-ID discovery and authorization behavior.
- [x] Local full-upload authorization → byte upload → registration → verification.
- [x] Exact attachment rerun is idempotent.
- [x] Interrupted empty attachment child is reused rather than duplicated.
- [x] Same-title different-file/multiple-child cases stop as conflicts.
- [x] Incomplete upload preserves the attachment key for recovery.
- [x] Server-ID mismatch stops the archive operation.

## 7. Real-paper scientific acceptance — still required before production claim

- [ ] real T01 ordinary empirical paper without SI.
- [ ] real T02 neuroscience paper with many figures/tables.
- [ ] real T03 Main + complex SI.
- [ ] real T04 expected SI unavailable → PROVISIONAL → later upgrade.
- [ ] real Translation A render → inspect → iterate → re-render acceptance.
- [ ] real Deep Reading B evidence/source-anchor closure acceptance.
- [ ] real weekly C canonical-Abstract/comment/reviewer acceptance.

The suspended Mullins 2025 run remains a valid blocked/provisional acceptance trace. Do not fabricate completion merely to tick these boxes.

## 8. Zotero live integration acceptance

Implementation/mock status is separate from live production status.

- [x] Phase-7 bibliographic parent-create adapter implemented.
- [x] Phase-8 durable existing-parent local-file attachment adapter implemented.
- [x] Phase-8 adapter performs same-server parent/filename/MD5 verification before success.
- [ ] live Zotero Desktop test: discover Zotero 10+ `Zotero-Server-ID`.
- [ ] live Zotero Desktop test: user grants Local API write authorization.
- [ ] live Zotero Desktop test: safe synthetic parent create + verification.
- [ ] live Zotero Desktop test: safe synthetic file attach + attachment-key/MD5 verification.
- [ ] live Zotero Desktop test: rerun same attachment and confirm no duplicate is created.
- [ ] live Zotero Desktop test: Main/SI/A/B workflow against a real selected-paper archive when source files are available.

Until these live checks pass, describe the adapters as **implemented and mock/CI-verified**, not production-validated.

## 9. Current capability boundaries

- Zotero 10+ Local API durable attachment code exists, but GitHub Actions cannot exercise the user's Desktop authorization dialog/library. Live validation remains open.
- Phase-7 parent creation still uses Connector `/saveItems`; it may later be migrated to Local API writes, but migration is not required to validate Phase 8 attachments.
- `mirror_pdf.py` is a deterministic layout/QC helper, not a publisher-grade automatic relayout engine. Visual inspection remains mandatory.
- Structural validators cannot judge translation, methodological critique or statistical interpretation quality.
- The Mullins Main PDF source blocker remains independent of Zotero capability.

## 10. Release verdict

**Phase 6 rule-layer / structural Release Candidate: PASS.**

**Phase 7 parent-create implementation/mock verification: PASS.**

**Phase 8 durable attachment implementation/mock verification: PASS.**

**Production validation: OPEN.**

The remaining blockers are live Zotero validation plus real source-based A/B/C/T01–T04 acceptance, not the absence of a durable existing-parent attachment implementation.

## 11. Main merge decision

Do **not** merge any draft PR merely because CI is green.

Before release to `main`:

1. choose which cumulative integration line is intended for release;
2. re-check that exact HEAD and its final compare;
3. confirm all automated checks are green;
4. decide whether `main` is being published as a rule-layer/integration release or only after production live/scientific gates close;
5. obtain explicit release approval;
6. merge without rewriting away useful phase history;
7. verify `main` contains the expected tree;
8. optionally tag the chosen release meaning;
9. only then consider deleting old phase branches.

`main` is the stable published line, not the active construction workspace.
