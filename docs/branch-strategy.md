# Branch Strategy

## What `main` means

`main` is the stable published branch. Development branches do not become part of the usable project merely because they exist; they become stable only after an explicit release decision and merge.

At the current V1 release-candidate stage, `main` still represents the original repository baseline.

## Historical Phase branches

The numbered Phase branches were created sequentially as cumulative development snapshots:

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

They are not separate Skill systems. Each successor contains the earlier work.

The historical meaning is:

- Phase 1: repository foundation/shared/knowledge/helper base;
- Phase 2: Search rule layer;
- Phase 3: Translation rule layer;
- Phase 4: Deep Reading rule layer;
- Phase 5: thin weekly orchestrator;
- Phase 6: consistency hardening, validators, CI and synthetic acceptance;
- Phase 7: Zotero parent-create integration work;
- Phase 8: Zotero 10+ existing-parent local attachment integration work.

## Numbered Phase development is now frozen

V1 is no longer being developed by opening Phase 9, Phase 10, etc.

The Phase-9 experiment is deferred as a future optimization and is not part of the current release line. Parent-create Local API unification, group-library routing and further Zotero automation can be revisited after a usable V1 is published.

All remaining V1 release work happens on:

```text
v1-release-candidate
```

This branch starts from the accepted cumulative Phase-8 tree and changes only release-blocking contradictions, usability/completion semantics, documentation, tests and final hygiene.

## Release meaning

The V1 release target is a **complete usable academic Skill system**:

- Search → Translation → Deep Reading → A/B/C works without requiring a specific Zotero write transport;
- Zotero remains the preferred long-term archive;
- automatic/manual/deferred Zotero handling is an archive dimension, not a condition for academic stage completion;
- source/evidence gaps still correctly produce `PROVISIONAL`/`BLOCKED`;
- no Zotero operation may be falsely reported as successful.

See `docs/v1-scope-freeze.md`.

## Merge implication

Because the history is cumulative, do **not** merge Phase 1, then Phase 2, etc. separately.

After final RC acceptance, merge only:

```text
v1-release-candidate → main
```

Before that merge:

1. stop feature expansion;
2. pass compile/unit/foundation tests on the exact RC HEAD;
3. run academic-completion regression tests;
4. confirm archive-completion checks remain strict and truthful;
5. confirm no copyrighted Main/SI/A/B binaries, secrets, Local API keys, Zotero databases or temporary work are committed;
6. verify the Mullins blocked trace remains factual;
7. review the final `main...v1-release-candidate` diff;
8. obtain explicit release approval;
9. merge and verify `main` contains the expected V1 tree.

## After release

Old Phase branches may be retained as development history or eventually replaced by immutable tags/releases and deleted to reduce branch clutter. Do not delete them until the V1 merge and history have been verified.

Future improvements should normally use issue/topic branches named for the optimization (for example `zotero-local-parent-create`) rather than restarting the Phase numbering scheme.
