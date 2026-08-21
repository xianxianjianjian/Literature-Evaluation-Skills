# Workflow Routing

The weekly orchestrator is a thin coordination layer. It never replaces the specialist Skills' academic judgment. Its job is to determine **what should run next**, preserve state/provenance, and prevent duplicated or contradictory work.

## Single source of truth

In weekly context, always read:

`weekly_reviews/YYYY/YYYY-Wxx/workflow_manifest.yaml`

before routing.

The manifest owns workflow status. Other files contain evidence or stage-specific records but must not maintain a competing global status.

## Supported request modes

| Request mode | Route |
| --- | --- |
| Full weekly workflow | Topic planning → Topic Gate → Search → Paper Gate → Search handoff → Translation → Deep Reading → A/B/C + knowledge verification |
| Topic/Search only | `literature-search` and stop at the user's requested boundary |
| Translation only | establish Minimal Intake if Search artifacts are absent → `paper-translation` |
| Deep Reading only | establish Minimal Intake if needed → `paper-deep-reading`; A is optional, never evidentiary prerequisite |
| Resume | inspect manifest/artifacts → continue from first unresolved dependency or update-required stage |
| Update existing paper | inspect `needs_update` + source change → rerun only affected stage(s) and downstream consumers |
| New SI/correction/version | source identity audit → mark affected artifacts `needs_update` → update Translation/Deep Reading as required |

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
literature-search: selected-paper/source package/Zotero handoff
  ↓
paper-translation: terminology → canonical Abstract → Main/SI → A
  ↓
paper-deep-reading: audit → Intro/Methods/Results/Discussion → B → C
  ↓
validation + Zotero/Git/knowledge closure
```

The specialists may return `PROVISIONAL` or `BLOCKED`; the router must preserve those states instead of forcing forward progress.

## Two fixed user Gates

In the ordinary weekly workflow the only fixed `WAITING_USER` Gates are:

1. **Topic Gate** — user confirms the weekly topic.
2. **Paper Gate** — user confirms the final focal paper.

Once a Gate is explicitly satisfied, never ask for the same decision again merely because another stage starts.

### Post-Paper-Gate authorization

After the user confirms the focal paper, ordinary execution is authorized for:

- identity/version matching;
- legal-access Main/SI retrieval;
- normal Zotero parent matching/creation where a safe write route exists;
- Main/SI attachment;
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

A dependency prevents defensible continuation. Record the blocker precisely, including stage, source/system, and what would resolve it.

### `PROVISIONAL`

The work is scientifically usable at the stated scope, but a named source/system/archive gap prevents full completion. A provisional state is not equivalent to failure and must not be described as a complete research archive.

### `COMPLETE`

The specialist's own completion gate has passed and required handoff/verification is complete.

## Dependency-aware routing

Do not treat stages as a simplistic linear pipeline when dependencies differ.

### Search → Translation

Translation needs an identified source package, not necessarily `Search = COMPLETE`.

If Search is `PROVISIONAL` only because Zotero attachment is unavailable but paper identity/Main/SI are usable, Translation may continue.

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
4. determine whether an earlier stage's update invalidates downstream work;
5. route to the smallest set of steps needed to restore consistency;
6. preserve already verified work and stable IDs.

Do not rerun expensive academic work solely because the session changed.

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

A downstream stage does not automatically become `PROVISIONAL` just because an upstream stage is provisional. Propagate only the actual unresolved dependency.

Examples:

- Search provisional due to Zotero outage; Main/SI verified → Translation can still be complete at content level but archive attachment remains provisional.
- Translation provisional due to missing SI that is irrelevant to the focal analysis → Deep Reading may be complete if Full Research Audit independently establishes that the missing item is non-consequential.
- Missing SI contains required methods/results → Deep Reading remains provisional or blocked.

Always name the reason.

## Zotero outage route

If Zotero is unavailable:

- continue all safe work that does not require Zotero;
- stage A/B or source files under `work/<paper_id>/handoff/` when a local runtime exists;
- append explicit `pending_zotero_actions` to the manifest;
- preserve expected attachment labels;
- verify and clear each pending action when Zotero access returns.

Do not report “saved to Zotero” until the actual parent/attachment is verified.

## Full-workflow completion

The weekly workflow is `COMPLETE` only when all required specialist completion conditions and archive conditions pass.

At minimum:

- topic Gate confirmed;
- focal-paper Gate confirmed;
- Search decision/audit records exist;
- selected paper/source identity is stable;
- canonical Abstract exists for full workflow;
- A exists and is verified when FULL_MIRROR is required;
- B exists and passes Deep Reading completion/QC;
- C exists in weekly context and meets submission-profile requirements;
- required `selection_log.csv` / `reading_history.csv` records are correct;
- Zotero Main/SI/A/B attachment state is verified;
- no unresolved `BLOCKED` stage;
- no unresolved consequential `needs_update`;
- any accepted `PROVISIONAL` condition is explicitly reported rather than mislabeled `COMPLETE`.

If unresolved provisional gaps remain, the overall weekly archive must remain `PROVISIONAL` even if C can be submitted.

## V1 stop boundary

The router must not expand the workflow into:

- systematic review / PRISMA;
- meta-analysis;
- bulk candidate downloading;
- autonomous multi-agent research;
- impact-factor database automation;
- dashboard construction;
- raw-data reanalysis or experiment-code reproduction.

Those are separate future capabilities, not hidden responsibilities of the weekly router.