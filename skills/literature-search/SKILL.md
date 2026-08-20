---
name: literature-search
description: Plan, search, screen, and record literature for a weekly evaluation, ending with a user-confirmed paper and safe Zotero handoff; Phase 1 provides the contract skeleton only.
---

# Literature Search

## Purpose

Own topic planning, journal and literature search, screening, final paper selection, and Zotero ingest preparation. This Phase 1 skill defines boundaries and outputs; database routing, scoring, and full screening procedures belong to Phase 2 references.

## Supported Entry Modes

Support full weekly context and Search-only use. Do not require Translation or Deep Reading to run.

## Required Inputs

Use the user request, confirmed research profile, relevant reading history, target week, and explicit constraints. Do not modify long-term research direction without user confirmation.

## Topic Planning Gate

Propose evidence-grounded topic candidates before formal searching when the topic is not yet fixed. Set `WAITING_USER` and continue only after the user confirms the topic.

## Search Workflow

Phase 2 will define query construction, database routing, journal mapping, source acquisition, saturation checks, and audit logging. Phase 1 must not pretend these searches have been implemented or run.

## Screening Workflow

Phase 2 will define overall and detailed screening, exclusion codes, integrity checks, and selection scoring. Preserve non-significant findings and Supplement evidence during later screening.

## Paper Selection Gate

Present candidates and reasons; the user selects the final paper. Do not auto-select and proceed as if confirmed.

## Zotero Ingest

Only the user-confirmed paper enters the formal Zotero archive. Follow [`../../shared/zotero-policy.md`](../../shared/zotero-policy.md); never report a write as successful without verification.

## Outputs

Produce or update these stable interfaces:

- `topic_selection.md`
- `search_record.md`
- `selected_paper.yaml`
- `source_manifest.json`

## Completion States

Use only the shared state enum. Search is `COMPLETE` only after the paper Gate, identity audit, required records, and verified or explicitly pending Zotero handoff. Use `PROVISIONAL` for explicit evidence or system gaps.

## Hard Rules

- Do not guess information absent from sources.
- Keep author explanation, direct content, evaluator analysis, and external evidence separate.
- Do not treat correlation, mediation, or connectivity as stronger causal evidence than reported.
- Search candidates must not all be ingested into Zotero.
- Do not implement Phase 2 search logic during Phase 1.
