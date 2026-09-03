# Deliverables and QC

Deep Reading produces B as the full research archive and, in weekly context or on explicit request, C as the concise weekly evaluation submission. C is derived from B; it is not an independent second reading that may introduce unsupported claims.

## B — Complete Research Notes DOCX

### Base Schema

Use this minimum structure, adapting dynamically when the paper requires it:

0. Literature Positioning & Research Audit
1. Abstract
2. Introduction
3. Methods
4. Results
5. Discussion
6. Innovation
7. Limitations
8. Redesign
9. Transfer Value
10. Terminology & Evidence Index

For every consequential conclusion, parameter, sample fact, hypothesis/result judgment, author limitation, audit issue, or transfer recommendation, preserve a Source Anchor or linked evidence ID.

### Section expectations

#### 0. Literature Positioning & Research Audit

Include publication identity/version, literature role, source package, SI status, integrity/current-notice status, Paper Structure Inventory, important `AUD-xxx` items, and readiness/completeness state.

#### 1. Abstract

Reuse `canonical_abstract.md` exactly when it exists. Do not create a competing translation.

#### 2. Introduction

Include argument reconstruction, theory/concept analysis, Research Gap, RQ/Aim/Hypothesis distinctions, citation tracing where required, and the Hypothesis Matrix.

#### 3. Methods

Include Study Architecture, Sample Ledger, Measurement Chain, participant/researcher process views, acquisition vs preprocessing, analysis map, and Reproducibility Gap Table as applicable.

Include **研究设计与适用方法规范 / Research Design and Applicable Method Standards**: selected design modules, why they apply, consequential non-applicable modules, reporting-completeness findings and separate validity judgments. Do not compute a checklist-derived total score.

#### 4. Results

Include Analysis Question Tree, Result Matrix, planned-vs-actual comparison, non-significant findings, correction accounting, figure/table evidence, consistency checks, and Hypothesis–Result closure.

#### 5. Discussion

Separate author interpretation from evaluator critique; include ED0–ED3 where useful.

#### 6–9

Use Innovation Matrix, three-layer Limitations, Redesign Matrix, and Transfer Value Matrix.

#### 10. Terminology & Evidence Index

Include key terminology, TERM/TERMEV identifiers when available, external evidence (`EXT-xxx`), claim/evidence IDs, audit IDs, and source-location index sufficient for later tracing.

## C — Weekly Evaluation Submission

Generate C when:

- running in weekly context; or
- the user explicitly asks for it.

C must contain at least:

- journal;
- publication/online date;
- English title;
- Chinese title;
- authors;
- original article URL/address;
- original Abstract;
- exact canonical Chinese Abstract;
- review/comment body;
- reviewer name from `<data-root>/knowledge/submission_profile.yaml` when configured.

The configured minimum (default 500 Chinese characters) applies **only to the review/comment body**, not metadata, title, or Abstract sections.

## C as second-stage synthesis

C should answer compactly:

1. Why is this paper worth reading for the current research question?
2. What did it actually do?
3. What are the main results, including important null/mixed results?
4. What is the paper's most transferable contribution?
5. What requires caution?
6. What does it change or suggest for the user's next research decision?

C must not introduce a critique or factual claim that B cannot support. Internal working metadata may retain `CLM-xxx`, `AN-xxx`, `AUD-xxx`, or `EXT-xxx` links even if the clean submission text omits those IDs.

## Knowledge updates

Append a paper to `<data-root>/knowledge/reading_history.csv` **only after Deep Reading genuinely reaches academic `COMPLETE`**. A source/evidence-provisional Deep Reading must not be recorded as completed.

After academic Deep Reading is complete:

- append the completed paper to `<data-root>/knowledge/reading_history.csv`;
- record Zotero parent/A/B attachment keys when already verified, otherwise leave those optional archive fields empty;
- record C path;
- keep unresolved Zotero operations in `pending_zotero_actions`;
- propose, but do not automatically apply, changes to `<data-root>/knowledge/research_profile.md`.

A Zotero-only pending action does not prevent the reading from entering completed history. A single paper must never silently redefine the long-term research direction.

## B archive handoff

Preferred Zotero attachment label:

`[B] 文献研究笔记·完整精读版`

When Zotero is writable, verify the parent item and attachment after writing. If Zotero is unavailable, stage under `<data-root>/work/<paper_id>/handoff/` and record a pending action. This archive pending state must not downgrade a B that already passed its academic/QC gate.

## Deep Reading Academic Completion Gate

For `COMPLETE`, require all applicable items below:

- publication/source identity resolved;
- Full Research Audit performed;
- Paper Structure Inventory complete;
- Main/SI status explicit;
- source→notebook mapping closed for all core items;
- canonical Abstract reused or appropriate Abstract mini-translation completed;
- Hypothesis/RQ Matrix complete;
- Sample Ledger complete to the extent reported;
- participant and researcher Methods views complete where relevant;
- acquisition/preprocessing and reproducibility gaps accounted for;
- Analysis Question Tree and Result Matrix complete;
- all important prespecified non-significant results retained;
- mandatory consistency recalculations performed where possible;
- important figures/tables visually inspected;
- Hypothesis–Result closure complete;
- Author Discussion and Evaluator Critique separated;
- limitations provenance separated;
- Innovation / Redesign / Transfer Value completed where relevant;
- every A3 audit issue prominently treated;
- B generated and verified as the correct artifact for the active paper/source version;
- B DOCX metadata sanitized and `docProps/core.xml` verified; no generator identifier or non-requested author/comments/keywords remain;
- C generated when weekly context requires it;
- required knowledge/history update recorded.

A verified Zotero attachment is **not** part of this academic completion gate.

## Archive Completion Add-on

If the user/workflow specifically requires closed Zotero archival status, additionally verify the applicable Main/SI/A/B parent and attachment keys and clear their pending actions. Manual Zotero attachment followed by verification is acceptable; full automation is not required by V1.

## PROVISIONAL vs BLOCKED

Use `PROVISIONAL` when the academic archive is scientifically usable but a named source/SI/version/evidence/content gap prevents full academic completeness.

Use `BLOCKED` when missing Main/SI/source identity prevents defensible reconstruction of a core part of the paper.

Do not use `PROVISIONAL` merely because Zotero automatic writing is unavailable. Do not call a file `COMPLETE` merely because a DOCX exists; it still has to pass the academic gate above.

## Final QC checklist

### Evidence QC

- all major claims have the correct evidence class;
- Source Anchors are present for important claims;
- external evidence is clearly separate;
- no unavailable source content was invented.

### Methods QC

- total N has not been substituted for unknown analysis N;
- acquisition and preprocessing are separate;
- important parameters and missing parameters are explicit.

### Results QC

- primary and important secondary analyses are represented;
- non-significant prespecified results are retained;
- corrected/uncorrected results are distinguished;
- statistical consistency checks are recorded.

### Discussion QC

- author interpretations are not presented as direct findings;
- evaluator critique is labeled;
- causal strength is not inflated;
- limitations and redesigns are specific to the paper.

### Deliverable QC

- B opens correctly and contains the required/dynamic sections;
- C uses the canonical Abstract and meets the comment-body length rule;
- Zotero/Git paths or pending actions match the workflow manifest;
- final report distinguishes academic completion from archive completion;
- final state accurately reflects unresolved source/evidence gaps.
