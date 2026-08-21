---
name: literature-search
description: Plan, search, screen, rank, integrity-check, and archive literature for a weekly evaluation, ending with a user-confirmed focal paper and verified or explicitly provisional Zotero handoff.
---

# Literature Search

## Purpose

Own the complete V1 weekly Search stage:

```text
research context
→ topic candidates
→ user topic Gate
→ Journal Mapping
→ Search Question Profile
→ database/source routing
→ Round 1 screening
→ Round 2 Quality Gate + ranking
→ integrity checks
→ Primary + Strong Alternatives
→ user paper Gate
→ selected-paper identity/source package
→ Zotero ingest or explicit provisional handoff
```

This Skill may run independently from Translation and Deep Reading.

## Required shared contracts

Before substantive work, read:

- [`../../shared/evidence-policy.md`](../../shared/evidence-policy.md)
- [`../../shared/identifier-policy.md`](../../shared/identifier-policy.md)
- [`../../shared/source-identity-policy.md`](../../shared/source-identity-policy.md)
- [`../../shared/zotero-policy.md`](../../shared/zotero-policy.md)
- [`../../shared/state-contract.md`](../../shared/state-contract.md)
- [`../../shared/data-format-policy.md`](../../shared/data-format-policy.md)

Use `weekly_reviews/YYYY/YYYY-Wxx/workflow_manifest.yaml` as the workflow source of truth when running in weekly context.

## Reference routing

Read the reference that owns each decision instead of duplicating its rules here:

- Topic generation and first user Gate → [`references/topic-planning.md`](references/topic-planning.md)
- Journal source map → [`references/journal-mapping.md`](references/journal-mapping.md)
- Search Question Profile, query blocks, database routing, recency, saturation → [`references/search-strategy.md`](references/search-strategy.md)
- Round 1/2 screening, EX codes, Quality Gate, seven-dimensional score, method transfer → [`references/screening-and-ranking.md`](references/screening-and-ranking.md)
- Retraction/correction/version/SI/data/code/prereg/conflict checks → [`references/integrity-check.md`](references/integrity-check.md)
- Final-paper Zotero/source-package handoff → [`references/zotero-ingest.md`](references/zotero-ingest.md)

## Supported entry modes

### Full weekly context

Start from topic planning unless the manifest already contains a user-confirmed topic. Preserve both fixed user Gates.

### Search only

If the user supplies a confirmed topic, skip the topic-choice Gate and begin the search design. Still create enough structured records to make the Search auditable.

### Resume

Read the manifest and existing `topic_selection.md`, `search_record.md`, `selected_paper.yaml`, and `source_manifest.json`. Resume from the first incomplete or update-required step; do not repeat a user Gate that has already been explicitly satisfied.

## Required inputs

Use:

- current user request and constraints;
- confirmed `knowledge/research_profile.md` when relevant;
- recent `knowledge/reading_history.csv` and `selection_log.csv`;
- target week in weekly mode;
- already supplied paper/topic identity when using a direct entry mode.

Never auto-change the long-term research direction from one weekly search.

## Topic Planning Gate

When no topic has been confirmed:

1. generate normally 3–5 distinct candidates using the topic-planning policy;
2. write/update `topic_selection.md`;
3. set topic stage to `WAITING_USER`;
4. stop formal search until the user chooses.

After confirmation, record the choice and continue without asking for the same decision again.

## Search execution

After topic confirmation:

1. set Search to `IN_PROGRESS`;
2. build a topic-specific Journal Mapping when useful;
3. build and record the Search Question Profile and concept blocks;
4. route across field-specific and broad/index/citation sources when available;
5. record unavailable sources honestly;
6. strongly prefer recent high-fit work while preserving foundational roles;
7. continue until the documented saturation/stop condition is met.

This is a targeted weekly search, not a systematic review or PRISMA workflow.

## Screening and recommendation

Perform Round 1 before detailed evaluation. Use only the frozen `EX-01`–`EX-13` exclusion codes.

For Round 2:

1. run Search Intake/Integrity checks;
2. assign `GREEN / AMBER / RED` Quality Gate **before** using the weighted score;
3. a `RED` candidate cannot become Primary because of score;
4. calculate and explain the frozen 7D score: relevance 25, evidence quality 20, journal/source 15, method transfer 15, current-research transfer 10, novelty 10, fulltext/SI 5;
5. keep method-transfer reasoning explicit rather than hiding it inside the total.

Present one Primary and normally about two Strong Alternatives when the literature supports that distinction. Explain specifically why #1 outranks #2.

## Paper Selection Gate

The user makes the final focal-paper decision. Before explicit confirmation, do not ingest a candidate as the selected focal archive and do not start Translation automatically.

After confirmation, ordinary identity matching, legal-access Main/SI retrieval, normal Zotero parent/attachment actions, and selected-paper record creation are authorized. Stop only for duplicate ambiguity, DOI/title conflict, unresolved version conflict, or a true blocker.

## Zotero and source package

Only the final selected paper is formally ingested by default. Do not bulk-import the candidate pool.

Use the Zotero ingest policy and current bridge capabilities. A successful request is not enough: verify parent/attachment identity. If write capability is unavailable, stage under `work/<paper_id>/handoff/`, record `pending_zotero_actions`, and mark the archive state `PROVISIONAL` rather than claiming success.

## Outputs

Weekly decision records:

- `weekly_reviews/YYYY/YYYY-Wxx/topic_selection.md`
- `weekly_reviews/YYYY/YYYY-Wxx/search_record.md`

Selected-paper working records:

- `work/<paper_id>/selected_paper.yaml`
- `work/<paper_id>/source_manifest.json`

Long-term decision history:

- append the selected paper to `knowledge/selection_log.csv`;
- do **not** write `knowledge/reading_history.csv` until Deep Reading is actually complete.

## Completion states

Use only the shared state enum.

Search may be `COMPLETE` only when:

- topic confirmation is recorded or the topic was supplied directly;
- search routes and screening decisions are auditable;
- Primary/alternatives and their reasoning are recorded;
- final paper confirmation is recorded;
- selected paper identity/version has been checked;
- `selected_paper.yaml` and `source_manifest.json` exist when a final paper is selected;
- Zotero/source handoff is verified.

Use `PROVISIONAL` when the academic selection is usable but a named source/SI/Zotero system gap remains. Use `BLOCKED` only when the missing dependency prevents defensible continuation.

## Hard rules

- Do not guess information absent from sources.
- Do not claim that integrity checking proves authenticity or truth.
- Do not let journal prestige or impact factor replace paper-level evaluation.
- Do not let weighted score override a `RED` Quality Gate.
- Do not silently treat a preprint as the Version of Record.
- Do not bypass paywalls or authentication restrictions.
- Do not bulk-download or bulk-ingest all candidates.
- Keep external evidence distinct from the focal paper's own claims.
- Preserve the chronology of Search-time decisions; later Deep Reading findings belong in a separate post-reading assessment or `needs_update` record.