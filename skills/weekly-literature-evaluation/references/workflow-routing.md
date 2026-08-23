# Workflow Routing

The weekly orchestrator is a thin coordination layer. It never replaces the specialist Skills' academic judgment. Its job is to determine **what should run next**, preserve state/provenance, and prevent duplicated or contradictory work.

## Single source of truth

In weekly context, always read:

`<data-root>/weekly_reviews/YYYY/YYYY-Wxx/workflow_manifest.yaml`

before routing.

When Translation is requested, preserve `stages.translation.scope` in the manifest. Default an unqualified paper-translation request to `FULL_MIRROR`; do not infer a narrower scope merely because source extraction or layout is difficult.

The manifest owns workflow status. Other files contain evidence or stage-specific records but must not maintain a competing global status.

## Supported request modes

| Request mode | Route |
| --- | --- |
| Full weekly workflow | Topic planning → Topic Gate → Search → Paper Gate → source handoff → Translation → Deep Reading → A/B/C + knowledge verification → optional archive closure |
| Topic/Search only | `literature-search` and stop at the user's requested boundary |
| Translation only | establish Minimal Intake if Search artifacts are absent → `paper-translation` |
| Deep Reading only | establish Minimal Intake if needed → `paper-deep-reading`; A is optional, never evidentiary prerequisite |
| Resume | inspect manifest/artifacts → continue from first unresolved academic dependency or update-required stage |
| Update existing paper | inspect `needs_update` + source change → rerun only affected stage(s) and downstream consumers |
| New SI/correction/version | source identity audit → mark affected stages `needs_update` → update Translation/Deep Reading as required |
| Archive cleanup | inspect `pending_zotero_actions` → perform automatic/manual Zotero reconciliation without rerunning completed academic work |

## Full weekly route

```text
NOT_STARTED
  ↓
literature-search: topic planning
  ↓
WAITING_USER — Gate 1: topic confirmation
  ↓
literature-search: Journal Mapping → search → screening → integrity → ranking
  ↓
WAITING_USER — Gate 2: final paper confirmation
  ↓
literature-search: selected-paper/source package handoff
  ↓
paper-translation: terminology → canonical Abstract → Main/SI → A
  ↓
paper-deep-reading: audit → Intro/Methods/Results/Discussion → B → C
  ↓
academic validation + Git/knowledge closure
  ↓
optional Zotero archive reconciliation
```

The specialists may return `PROVISIONAL` or `BLOCKED`; the router must preserve those states instead of forcing forward progress. A Zotero-only pending action does not itself make an academic stage provisional.

## Two fixed user Gates

In the ordinary weekly workflow the only fixed `WAITING_USER` Gates are:

1. **Topic Gate** — user confirms the weekly topic.
2. **Paper Gate** — user confirms the final focal paper.

Once a Gate is explicitly satisfied, never ask for the same decision again merely because another stage starts.

### Post-Paper-Gate authorization

After the user confirms the focal paper, ordinary execution is authorized for:

- identity/version matching;
- legal-access Main/SI retrieval;
- normal Zotero parent/attachment actions where a safe route exists;
- Main/SI handoff;
- Translation and A production;
- Deep Reading and B production;
- weekly C generation;
- normal history/manifest updates.

Stop for user input only when there is a genuine exception such as:

- duplicate bibliographic parents that cannot be safely resolved;
- DOI/title/version conflict;
- materially different source versions;
- a risky/destructive write not already covered by the workflow;
- a true scientific/technical blocker requiring user material or decision.

Zotero automatic writing being unavailable is normally a recoverable archive condition, not a new user Gate.

## Manifest stage semantics

Allowed states are defined only in `shared/state-contract.md`:

- `NOT_STARTED`
- `IN_PROGRESS`
- `WAITING_USER`
- `BLOCKED`
- `PROVISIONAL`
- `COMPLETE`

Do not create `STALE` or local synonyms.

### `NOT_STARTED`

The stage has not begun and no usable partial output should be inferred.

### `IN_PROGRESS`

Work is actively underway or partial working artifacts exist.

### `WAITING_USER`

Use only for a real decision Gate in the ordinary weekly workflow. Do not use it as a generic error state.

### `BLOCKED`

An academic/source dependency prevents defensible continuation. Record the blocker precisely, including stage, source/system, and what would resolve it.

### `PROVISIONAL`

The work is scientifically usable at the stated scope, but a named source/evidence/version/content gap prevents academic completion. A Zotero-only archive gap belongs in `pending_zotero_actions`, not in the academic stage state.

### `COMPLETE`

The specialist's own academic/artifact completion gate has passed. Archive closure is evaluated separately.

## Dependency-aware routing

Do not treat stages as a simplistic linear pipeline when dependencies differ.

### Search → Translation

Translation needs an identified source package, not a Zotero parent.

If Search is complete academically while Zotero is pending, Translation proceeds normally.

If Search is `BLOCKED` because the focal paper/version itself is unresolved, Translation must not proceed.

### Translation → Deep Reading

Deep Reading does not require A. It requires defensible Main/SI evidence.

If Translation is `BLOCKED` only because page-mirror PDF production cannot run but Main/SI text is available, Deep Reading may still run from the original sources.

If Translation is blocked because Main/SI source evidence itself is unavailable, Deep Reading must assess independently whether its Minimal Intake is `READY`, `READY_WITH_GAPS`, or `BLOCKED`.

### Deep Reading → C

In weekly context C is generated from B/Deep Reading evidence. Do not generate a polished C from Search notes alone when Deep Reading has not established the critique/evidence basis.

## Resume algorithm

When the user says “continue”, “resume”, or returns after an interruption:

1. read the manifest;
2. read `paper_id`, `pending_zotero_actions`, `blocking_issues`, `source_change`, and all `needs_update` flags;
3. verify referenced artifacts rather than trusting filenames alone;
4. determine whether an earlier source update invalidates downstream work;
5. route to the smallest set of steps needed to restore academic consistency;
6. preserve already verified work and stable IDs;
7. process archive-only pending actions separately, without reopening academic stages unless the archive check exposes a real source/version conflict.

Do not rerun expensive academic work solely because the session changed or Zotero is still pending.

## Existing artifact detection

Before creating an artifact, check whether it already exists and whether its identity matches the active `paper_id` and source version.

Examples:

- `canonical_abstract.md` must belong to the active source version;
- an existing A must be checked for source/page coverage before reuse;
- an existing B must be checked for source identity and `needs_update` state;
- C must use the current canonical Abstract and Deep Reading assessment.

Do not overwrite a different paper/version merely because the expected filename matches.

## Source changes and update propagation

When new SI, a correction, a replacement source version, or a material source discrepancy appears:

1. update source identity/manifest;
2. set `needs_update: true` on directly affected stage(s);
3. record `update_reason` with a concrete description;
4. identify downstream consumers;
5. update only affected content;
6. clear `needs_update` only after verification.

Examples:

```text
New SI contains additional Methods parameters
→ Translation: needs_update
→ Deep Reading: Methods/Reproducibility Gap sections need update
→ C only if the new evidence changes the weekly evaluation
```

```text
Correction changes one Results value
→ Translation: affected Translation Unit/A numeric check
→ Deep Reading: Result Matrix + audit + hypothesis closure
→ C if conclusion/critique changes
```

Never silently rewrite the historical Search score/ranking with post-reading knowledge. Use a post-reading assessment or update record.

## PROVISIONAL propagation

A downstream stage does not automatically become `PROVISIONAL` just because an upstream stage is provisional. Propagate only the actual unresolved academic dependency.

Examples:

- Zotero outage; Main/SI verified → Search/Translation/Deep Reading can still reach `COMPLETE`; archive remains pending.
- Translation provisional due to missing SI that is irrelevant to the focal analysis → Deep Reading may be complete if Full Research Audit independently establishes that the missing item is non-consequential.
- Missing SI contains required methods/results → Deep Reading remains provisional or blocked.

Always name the reason.

## Zotero outage / archive-pending route

If Zotero is unavailable or automatic writing is not suitable:

- continue all safe academic work;
- stage A/B or source files under `<data-root>/work/<paper_id>/handoff/` when a local runtime exists;
- append explicit `pending_zotero_actions` to the manifest;
- preserve expected attachment labels;
- permit manual Zotero import/attachment later;
- verify and clear each pending action when archive access returns.

Do not report “saved to Zotero” until the actual parent/attachment is verified.

## Academic workflow completion

The weekly **academic workflow** is complete when:

- topic Gate confirmed;
- focal-paper Gate confirmed;
- Search decision/audit records exist;
- selected paper/source identity is stable for the requested scope;
- canonical Abstract exists for full workflow;
- A exists and passes the independent translation-package validator when `stages.translation.scope` is `FULL_MIRROR`;
- B exists and passes Deep Reading completion/QC;
- C exists in weekly context and meets submission-profile requirements;
- required `selection_log.csv` / `reading_history.csv` records are correct;
- no unresolved academic/source `BLOCKED` stage;
- no unresolved consequential `needs_update`.

`pending_zotero_actions` are allowed at this level.

## Archive completion

A stricter archive-complete check additionally requires the intended Zotero Main/SI/A/B records/attachments to be verified and relevant pending actions cleared. This may be completed automatically or manually.

Report these dimensions separately:

```text
Academic workflow: COMPLETE
Zotero archive: PENDING | COMPLETE
```

Do not downgrade academic completion because the archive is pending, and do not claim archive completion merely because A/B/C exist.

## V1 stop boundary

The router must not expand the workflow into:

- systematic review / PRISMA;
- meta-analysis;
- bulk candidate downloading;
- autonomous multi-agent research;
- impact-factor database automation;
- dashboard construction;
- raw-data reanalysis or experiment-code reproduction.

Zotero Local API parent-create unification, group-library routing and fully live-validated automatic archive transport are deferred optimizations, not reasons to extend V1 construction.
