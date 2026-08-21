# CI Verification

This file records how V1 automated checks are verified before release.

## Purpose

`phase-6-v1-hardening` carries the release-candidate implementation. A draft pull request to `main` is used as an auditable CI surface; opening the draft PR does not authorize merge.

## Required automated checks

The workflow `.github/workflows/v1-smoke.yml` must run on Python 3.11 and 3.12 and execute:

1. `python -m compileall scripts tests`
2. `python -m unittest discover -s tests -v`
3. `python scripts/validate_deliverables.py --repo-root .`

A green workflow verifies structural/helper behavior only. It does not replace scientific acceptance tests, PDF visual inspection, Zotero write integration, or T01–T04 end-to-end validation.

## Merge meaning

Do not merge the draft PR solely because CI is green. Merge requires the release checklist, branch diff audit, capability-boundary audit, and explicit release decision.
