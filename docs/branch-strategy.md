# Branch Strategy

## What `main` means

`main` is the repository's default stable branch. A development phase does **not** become part of the stable project merely because its branch exists. It becomes part of `main` only after an explicit merge/update of the `main` ref.

At the current V1 hardening stage, `main` still represents the original repository baseline and intentionally does not yet contain the cumulative V1 implementation.

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
```

Meaning:

- `phase-1-foundation` = repository foundation, shared policies, knowledge schemas, helper skeletons.
- `phase-2-search` = everything in Phase 1 + complete Literature Search rule layer + search acceptance records.
- `phase-3-translation` = everything in Phase 2 + complete Translation rule layer.
- `phase-4-deep-reading` = everything in Phase 3 + complete Deep Reading rule layer.
- `phase-5-orchestration` = everything in Phase 4 + complete thin weekly orchestrator.
- `phase-6-v1-hardening` = everything in Phase 5 + rule/script consistency hardening, validators, tests and release preparation.

Therefore these branches are best understood as **milestone snapshots of one evolving V1 tree**, not five separate Skills systems.

## Merge implication

Because the chain is cumulative, after final V1 acceptance it is normally sufficient to merge the **latest accepted cumulative branch** (`phase-6-v1-hardening`, or its final successor) into `main`.

It is not necessary to merge Phase 1, then Phase 2, then Phase 3, etc. separately: the latest branch already contains their commit history and files.

Before that merge:

1. complete V1 hardening/audit;
2. pass automated smoke/regression tests;
3. confirm no copyrighted paper binaries, secrets or temporary work are included;
4. verify the suspended real acceptance-test manifest remains factual;
5. review the final `main...release-branch` diff;
6. merge only after explicit acceptance.

## After release

After V1 is safely on `main`, old phase branches may either be retained as development history or replaced by immutable Git tags/releases and then deleted to reduce branch clutter. Do not delete them before the final merge/release history has been verified.
