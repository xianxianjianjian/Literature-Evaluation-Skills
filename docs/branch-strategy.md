# Branch Strategy

## Stable line

`main` is now the stable published V1 line.

V1 was released by merging `v1-release-candidate` into `main` on 2026-08-21. The merge commit is:

```text
9a2f6e4c148f82853101d706751123afd91d3f20
```

The numbered Phase branches were cumulative development snapshots, not independent Skill systems.

## Historical Phase lineage

```text
main baseline
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
  ↓
v1-release-candidate
  ↓
main (V1 release)
```

Phase 9 was a paused post-V1 Zotero-parent-create experiment and was not part of the V1 release requirement.

Because the V1 release commit contains the cumulative history, deleting the old branch refs after a real `v1.0.0` tag is verified does not remove the commits from repository history.

## Retention decision

### Keep permanently

```text
main
```

`main` is the only permanent working/stable branch required for V1.

### Keep temporarily until the release tag is verified

```text
v1-release-candidate
```

This remains a convenient audit anchor for the exact pre-merge release candidate. Once a real Git tag `v1.0.0` points to the V1 release, this branch can also be deleted.

### Approved for deletion after tag verification

```text
phase-1-foundation
phase-2-search
phase-3-translation
phase-4-deep-reading
phase-5-orchestration
phase-6-v1-hardening
phase-7-zotero-write-adapter
phase-8-zotero-local-attachments
phase-9-zotero-local-parent-create
post-v1-release-housekeeping
v1-release-candidate
```

The old Phase branches no longer carry unique release value:

- Phase 1–8 are ancestors of the released cumulative tree.
- Phase 9 was intentionally deferred and does not contain required V1 functionality.
- `v1-release-candidate` is superseded by the immutable release tag once that tag exists.
- `post-v1-release-housekeeping` is only a temporary documentation-cleanup branch.

## Pull-request cleanup

The final release PR (#4) is merged.

The old Phase 7 and Phase 8 draft integration PRs are closed because their relevant code is already present in the released `main` history. Earlier Phase review history remains available through GitHub PR/commit history even after branch deletion.

## Release tags

For stable releases, prefer immutable Git tags rather than keeping milestone branches indefinitely.

V1 target:

```text
v1.0.0 → 9a2f6e4c148f82853101d706751123afd91d3f20
```

See `docs/releases/v1.0.0.md`.

## Future development

Do not restart the numbered Phase sequence.

Future work should use issue/topic branches such as:

```text
zotero-local-parent-create
zotero-group-routing
real-paper-t03-validation
mirror-layout-improvements
```

Merge reviewed improvements back into `main` using normal PRs and create new semantic-version tags for releases.
