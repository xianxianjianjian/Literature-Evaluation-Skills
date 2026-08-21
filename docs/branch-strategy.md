# Branch Strategy

## What `main` means

`main` is the repository's default stable branch. A development phase does **not** become part of the stable project merely because its branch exists. It becomes part of `main` only after an explicit merge/update of the `main` ref.

At the current V1 integration stage, `main` still represents the original repository baseline and intentionally does not yet contain the cumulative V1 implementation.

## Phase branches are cumulative snapshots

The phase branches were created sequentially, not as independent parallel implementations:

```text
main
  ↓
phase-1-foundation
  ↓
phase-2-search
  ↓
phase-3-translation
  ↓
phase-4-deep-reading
  ↓
phase-5-orchestration
  ↓
phase-6-v1-hardening
  ↓
phase-7-zotero-write-adapter
  ↓
phase-8-zotero-local-attachments
```

Meaning:

- `phase-1-foundation` = repository foundation, shared policies, knowledge schemas, helper skeletons.
- `phase-2-search` = Phase 1 + Literature Search rule layer + search acceptance records.
- `phase-3-translation` = Phase 2 + Translation rule layer.
- `phase-4-deep-reading` = Phase 3 + Deep Reading rule layer.
- `phase-5-orchestration` = Phase 4 + thin weekly orchestrator.
- `phase-6-v1-hardening` = Phase 5 + rule/script consistency hardening, validators, regression tests and release preparation. This is the sealed rule-layer RC.
- `phase-7-zotero-write-adapter` = Phase 6 + verified Connector bibliographic-parent creation and target/identity checks.
- `phase-8-zotero-local-attachments` = Phase 7 + Zotero 10+ durable existing-parent Main/SI/A/B attachment implementation, idempotent resume semantics and Local API full-upload tests.

These branches are **milestone snapshots of one evolving V1 tree**, not separate Skills systems.

## Merge implication

After acceptance it is normally sufficient to merge the **latest accepted cumulative branch** into `main`. It is not necessary to merge every earlier phase separately because the successor already contains their history.

However, later integration phases have a different acceptance meaning from the sealed Phase-6 rule layer:

- Phase 6 structural/rule-layer RC has already passed its own audit;
- Phase 7/8 add Zotero integration code and require their own live-production checks;
- a decision to release Phase 6 now is not automatically a decision to release unfinished/live-unvalidated Phase 8 integration;
- a decision to release Phase 8 later should use the Phase-8 cumulative diff, not replay Phase 1–7 merges individually.

Before any merge to `main`:

1. identify the exact cumulative branch intended for release;
2. confirm its acceptance meaning (rule-layer/integration/production);
3. pass automated smoke/regression tests on that exact HEAD;
4. confirm no copyrighted paper binaries, secrets, Local API keys, Zotero databases or temporary work are included;
5. verify the real Mullins acceptance manifest remains factual;
6. review the final `main...release-branch` diff;
7. obtain explicit release approval;
8. merge without rewriting away useful phase history.

## After release

After the accepted V1 line is safely on `main`, old phase branches may be retained as development history or represented by immutable Git tags/releases and later deleted to reduce clutter. Do not delete them before final merge/release history has been verified.
