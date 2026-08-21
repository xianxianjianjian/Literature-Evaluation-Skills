# V1 Scope Freeze

This document freezes the release scope for the first usable version of Literature Evaluation Skills.

## Release goal

V1 is considered **usable** when the academic workflow can run end to end without depending on a specific Zotero write transport:

```text
Topic planning
→ Search and paper selection
→ source/package audit
→ Translation + A
→ Deep Reading + B
→ weekly C
→ knowledge/history update
→ resumable workflow state
```

The core product is the research workflow and its evidence/QC contracts. Zotero remains the preferred long-term archive, but automatic Zotero writing is an integration layer rather than a prerequisite for academic completion.

## Frozen core capabilities

V1 includes:

- `literature-search` with topic planning, Journal Mapping, targeted search, two-round screening, Quality Gate, 7D ranking, integrity checks and final-paper Gate;
- `paper-translation` with contextual terminology, one Canonical Abstract, accountable Main/SI coverage, table/figure integrity, mirror-layout policy and A;
- `paper-deep-reading` with Full Research Audit, Introduction/Methods/Results/Discussion reconstruction, Dynamic Coverage, B and weekly C;
- `weekly-literature-evaluation` as a thin router/state/resume layer with exactly two fixed user Gates;
- stable evidence/source identifiers, source-gap vocabulary, author/evaluator separation and causal-strength protections;
- Git-persistent research profile, terminology/history/selection registries and weekly manifest;
- A/B/C structural validators, workflow state helpers, synthetic acceptance tests and CI;
- local handoff/pending-action fallback when Zotero cannot be written automatically.

## Two completion dimensions

V1 separates **academic completion** from **archive completion**.

### Academic completion

The academic workflow is complete when the applicable specialist stages and A/B/C QC gates pass, source identity/evidence gaps are resolved to the required scope, required history/weekly records are updated, and no consequential academic blocker or `needs_update` remains.

A Zotero outage or unavailable automatic write adapter does **not** by itself downgrade Search, Translation, Deep Reading, A or B from `COMPLETE`.

### Archive completion

Archive completion is a stricter optional closure check. It additionally requires the desired Zotero Main/SI/A/B records/attachments to be observable and verified and all `pending_zotero_actions` to be cleared.

Until then, report the archive as pending/provisional without mislabeling it as saved to Zotero.

## Zotero in V1

Preferred long-term archive remains:

```text
Zotero: Main / SI / A / B
Git:    Skills / policies / knowledge / Search records / C / workflow state
```

However, V1 must remain usable when automatic Zotero writing is unavailable:

1. keep academic work running when source evidence itself is available;
2. stage files under `work/<paper_id>/handoff/` when a local runtime exists;
3. record concrete `pending_zotero_actions`;
4. allow manual Zotero attachment/import as an acceptable operational fallback;
5. never claim a parent/attachment exists until it is actually verified.

The experimental Zotero 10+ Local API write/attachment helpers remain in the repository as an optional integration and future optimization. Their live local validation, group-library behavior and parent-create unification are not release blockers for V1.

## Deferred optimization backlog

The following are explicitly deferred and must not delay V1 release:

- unified Local API parent creation for user/group libraries;
- fully live-validated automatic Zotero Main/SI/A/B write flow on the user's desktop;
- group-library routing and collection targeting;
- publisher-grade fully automatic PDF relayout;
- systematic review/PRISMA, meta-analysis, citation graphs, bulk downloading, dashboards, multi-agent orchestration and raw-data reanalysis.

## Release rule

Do not create additional numbered Phase branches for ordinary V1 polishing. Work from `v1-release-candidate`, fix only release-blocking contradictions, keep CI green, run final repository audit, and then make an explicit decision about merging the cumulative RC into `main`.
