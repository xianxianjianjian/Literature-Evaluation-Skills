# CI Verification

This file records how changes to the stable plugin line are automatically checked before merge to `main`.

## Release branch

The stable release line is:

```text
main
```

Historical Phase branches remain development snapshots only. New work uses topic branches and normal pull requests targeting `main`; a green PR does not authorize merge.

## Required automated checks

The workflow `.github/workflows/v1-smoke.yml` must run on Python 3.11 and 3.12 and execute:

1. `python -m compileall scripts tests`
2. `python -m unittest discover -s tests -v`
3. `python scripts/validate_deliverables.py --repo-root .`
4. `python scripts/validate_plugin_package.py --plugin-root .`

The test suite must protect both completion dimensions:

- **academic completion** can pass with `pending_zotero_actions` and empty Zotero key fields when Search/Translation/Deep Reading/A/B/C themselves are complete;
- **archive completion** remains stricter and requires the applicable verified Zotero keys plus no unresolved pending Zotero actions.

It must also preserve real source blockers such as the Mullins Main-PDF trace rather than rewriting them to completion.

## What green CI means

Green CI verifies deterministic repository contracts: syntax, state invariants, history/terminology logic, translation inventory/ledger/layout coverage, table topology, DOCX metadata, psychology-method routing, structural A/B/C checks, synthetic acceptance scenarios and archive-integration helper behavior.

It does **not** prove:

- that every future paper has been scientifically evaluated correctly;
- that a rendered A PDF is visually acceptable without inspection;
- that every Zotero desktop/version/group-library combination has been live-tested;
- that unavailable source material may be treated as present.

Those boundaries are intentional and do not make the core V1 unusable.

## Release check

Before merge:

1. confirm the exact topic-branch HEAD passed Python 3.11 and 3.12;
2. review the final `main...<topic-branch>` diff;
3. ensure no stale rule makes Zotero transport a prerequisite for academic completion;
4. ensure strict archive checks still reject unverified Zotero claims;
5. obtain explicit approval before merge or release tagging;
6. merge only the reviewed topic branch into `main`.
