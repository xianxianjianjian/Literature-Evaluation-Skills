# V1 Release Checklist

Use this checklist before moving the cumulative V1 development tree into `main`.

## 1. Branch lineage

- [ ] `phase-6-v1-hardening` (or its accepted successor) is based on the latest accepted cumulative phase branch.
- [ ] Release branch is not behind its intended parent.
- [ ] Final `main...release-branch` diff contains only intended V1 files/history.

## 2. Repository hygiene

- [ ] No paper Main/SI binaries, A/B deliverables, local Zotero files, secrets, tokens or credentials are committed.
- [ ] `work/`, handoff files, caches and temporary render artifacts remain ignored.
- [ ] No V2-only feature has leaked into V1.

## 3. Rule-layer consistency

- [ ] Four `SKILL.md` files match shared evidence/state/source/Zotero contracts.
- [ ] All 19 specialist reference files are present.
- [ ] TE1–TE7 means evidence-source type, not confidence rank.
- [ ] Two fixed `WAITING_USER` Gates only: topic and final paper.
- [ ] `PROVISIONAL`, `BLOCKED`, `needs_update` and Source Gap semantics are consistent.
- [ ] C comment threshold applies only to comment body.

## 4. Helper/script consistency

- [ ] `workflow_state.py` can create/read/update/resume all V1 manifest fields without academic judgment.
- [ ] `history_manager.py` uses week-scoped selection dedupe and global completed-reading dedupe.
- [ ] `terminology_registry.py` permits context-specific translations and preserves history.
- [ ] `validate_deliverables.py` checks V1 structure without pretending to judge academic quality.
- [ ] `mirror_pdf.py` keeps the frozen layout escalation and requires visual render QA.
- [ ] `zotero_bridge.py` accurately reports real read/write capability and never fakes a Zotero write.

## 5. Automated verification

Run in a clean checkout:

```bash
python -m compileall scripts tests
python -m unittest discover -s tests -v
python scripts/validate_deliverables.py --repo-root .
```

- [ ] All commands exit 0.
- [ ] GitHub Actions V1 Smoke Tests pass on supported Python versions.

## 6. Acceptance scenarios

Before calling the archive production-ready, execute/record as source packages permit:

- [ ] T01 ordinary empirical paper without SI.
- [ ] T02 neuroscience paper with many figures/tables.
- [ ] T03 Main + complex SI.
- [ ] T04 expected SI unavailable → PROVISIONAL → later upgrade.
- [ ] Search-only.
- [ ] Translation-only.
- [ ] Deep-Reading-only.
- [ ] Resume from interruption.
- [ ] Zotero unavailable/downgrade.
- [ ] New SI/correction triggers `needs_update` and targeted downstream refresh.

The suspended Mullins 2025 run may remain a documented blocked/provisional acceptance trace until its source-PDF blocker is resolved; do not fabricate completion merely to tick a box.

## 7. Main merge decision

Only after the release candidate is accepted:

1. create/review a final PR or equivalent diff from the latest cumulative branch into `main`;
2. confirm automated checks;
3. merge without rewriting away useful phase history;
4. verify `main` contains the expected V1 tree;
5. optionally create a `v1.0.0` tag/release;
6. only then consider deleting old phase branches to reduce clutter.

`main` is the stable published line, not the active construction workspace.
