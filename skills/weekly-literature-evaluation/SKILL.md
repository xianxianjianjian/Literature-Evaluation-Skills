---
name: weekly-literature-evaluation
description: Coordinate the complete weekly literature-evaluation workflow across topic planning, search, translation, deep reading, A/B/C production, Zotero/Git handoff, resume and source updates without performing specialist academic work itself.
---

# Weekly Literature Evaluation

## Purpose

Act only as the V1 **Router + State Manager + Resume Coordinator** for:

- `literature-search`
- `paper-translation`
- `paper-deep-reading`

The router owns workflow continuity, not academic judgment.

It must not duplicate the specialist Skills' search, translation, or deep-reading rules. Before dispatching a stage, read that specialist's `SKILL.md` and the relevant references.

## Required contracts

Before changing weekly workflow state, read:

- [`../../shared/state-contract.md`](../../shared/state-contract.md)
- [`../../shared/source-identity-policy.md`](../../shared/source-identity-policy.md)
- [`../../shared/zotero-policy.md`](../../shared/zotero-policy.md)
- [`../../shared/identifier-policy.md`](../../shared/identifier-policy.md)
- [`references/workflow-routing.md`](references/workflow-routing.md)

Use `weekly_reviews/YYYY/YYYY-Wxx/workflow_manifest.yaml` as the single workflow source of truth.

## Intent classification

Route the current request into one of these modes:

- `FULL_WEEKLY`
- `SEARCH_ONLY`
- `TRANSLATION_ONLY`
- `DEEP_READING_ONLY`
- `RESUME`
- `UPDATE_EXISTING`

Do not force a full weekly workflow when the user directly invokes a specialist mode.

## Full weekly workflow

The normal V1 flow is:

```text
research context/history
→ topic candidates
→ Gate 1: user confirms topic
→ Journal Mapping + Search Strategy
→ Round 1 + Round 2 screening
→ Integrity Check + Primary/Alternatives
→ Gate 2: user confirms final paper
→ selected-paper/source/Zotero handoff
→ terminology + Canonical Abstract
→ Main/SI translation + A
→ Full Research Audit
→ Introduction/Methods/Results/Discussion reconstruction
→ B
→ C
→ knowledge/history/archive verification
```

The specialists own every academic decision inside those stages.

## Fixed human Gates

In the ordinary weekly flow there are exactly two fixed `WAITING_USER` Gates:

1. weekly topic confirmation;
2. final focal-paper confirmation.

Do not add routine confirmation prompts between Translation, Deep Reading, A, B, C, or ordinary Zotero handoff once the Paper Gate has been passed.

After the user says the equivalent of “就这篇”, ordinary legal source retrieval, source matching, translation, A/B/C generation, normal Zotero archive actions, and workflow/history updates are authorized unless a genuine exception arises.

## State management

Use only:

- `NOT_STARTED`
- `IN_PROGRESS`
- `WAITING_USER`
- `BLOCKED`
- `PROVISIONAL`
- `COMPLETE`

Never create `STALE`; use `needs_update: true/false` plus explicit `update_reason`.

The router must preserve the specialist meaning of each state and must not turn a named blocker into a generic failure message.

## Dependency-aware dispatch

Stages are ordered but not rigidly coupled.

### Search handoff

Search can hand off when the paper and source identity are sufficient for the downstream task even if Zotero remains temporarily unavailable. Keep the archive state `PROVISIONAL` when appropriate.

### Translation handoff

Deep Reading never depends on A as evidence. If Translation is blocked only by mirror-layout production but Main/SI are available, Deep Reading may proceed from source evidence.

### Deep Reading handoff

C must derive from Deep Reading/B in weekly context. Search notes alone are insufficient for the final evaluative comment.

Read the detailed dependency rules in `workflow-routing.md` rather than applying a blanket “previous stage must equal COMPLETE” rule.

## Resume behavior

When the user asks to continue or the session is resumed:

1. load the manifest;
2. inspect `paper_id`, stage/output status, `needs_update`, `update_reason`, `blocking_issues`, `pending_zotero_actions`, and `source_change`;
3. inspect existing artifacts referenced by the workflow;
4. verify identity/version before reusing them;
5. resume at the smallest unresolved dependency;
6. do not repeat already satisfied user Gates;
7. preserve stable identifiers and prior audit history.

Never redo a complete translation or deep reading merely because a new chat/session started.

## Existing artifact handling

Verify rather than infer:

- source identity/version;
- canonical Abstract ownership;
- A source/page coverage;
- B source/audit state;
- C use of the current canonical Abstract and B evidence;
- Zotero parent/attachment keys.

Do not overwrite an artifact that belongs to another version or paper.

## Update routing

When a correction, new SI, new Version of Record, replacement attachment, or material source discrepancy appears:

- update source identity records;
- set affected stages `needs_update: true`;
- record a concrete reason;
- identify downstream consumers;
- update only affected material;
- preserve historical Search decisions;
- clear the flag only after verification.

Do not silently rewrite a previously recorded Search score because Deep Reading later discovers a caveat.

## PROVISIONAL and BLOCKED

`PROVISIONAL` means usable work with a named incompleteness. `BLOCKED` means defensible continuation is impossible without resolving the dependency.

Do not mechanically propagate an upstream state downstream. Propagate the actual unresolved dependency.

Examples:

- Zotero unavailable but Main/SI verified → academic work may continue; archive remains provisional.
- A mirror PDF blocked but source PDF/text available → Deep Reading may continue.
- consequential SI unavailable → Deep Reading may be provisional or blocked depending on whether the core evidence can be reconstructed.

## Zotero and Git boundary

Long-term intended archive:

```text
Zotero: Main / SI / A / B
Git:    Skills / shared policies / knowledge registries / weekly Search decisions / C / workflow manifest
```

Preferred Zotero child labels:

- `[ORIGINAL] Main Article`
- `[SUPPLEMENT] ...`
- `[A] 中文全文翻译镜像版`
- `[B] 文献研究笔记·完整精读版`

If Zotero is unavailable, preserve `pending_zotero_actions` and use `work/<paper_id>/handoff/` when a local runtime exists. Never claim an attachment was created until verified.

## A/B/C contract

- **A**: Chinese full-text mirror PDF, owned by Translation.
- **B**: complete research-note DOCX, owned by Deep Reading.
- **C**: weekly evaluation submission, derived from B in weekly context.

The router verifies required state/paths/attachments but does not create academic content itself.

## Knowledge management

The router may coordinate updates to:

- `knowledge/selection_log.csv`
- `knowledge/reading_history.csv`
- terminology registries through the Translation workflow
- weekly manifest and C path

`knowledge/research_profile.md` may only change after explicit user approval. Specialist Skills may propose an update, but the router must not silently accept it.

## Full workflow completion

The weekly archive may be declared `COMPLETE` only when the applicable specialist gates and archive checks pass, including:

- both user Gates resolved;
- Search decision records complete;
- focal source identity stable;
- Translation content/QC and required A complete;
- Deep Reading audit/B complete;
- C complete in weekly context;
- required knowledge records updated;
- required Zotero Main/SI/A/B attachments verified;
- no unresolved consequential `needs_update`;
- no unresolved `BLOCKED` stage.

If a named archive/source gap remains, retain `PROVISIONAL`; do not describe the research archive as complete merely because C is ready to submit.

## V1 boundaries

Do not expand this router into:

- a systematic-review/PRISMA engine;
- meta-analysis;
- bulk literature downloading;
- citation-network research;
- multi-agent orchestration;
- impact-factor database automation;
- web dashboard;
- automatic raw-data reanalysis or experiment-code reproduction.

## Hard prohibitions

- Do not perform specialist literature screening, translation, statistical interpretation, or critique in the router.
- Do not invent missing source content.
- Do not silently repair source errors.
- Do not maintain a second global status file.
- Do not repeat a user Gate already satisfied.
- Do not label a `PROVISIONAL` workflow as a complete archive.
- Do not let Zotero/network limitations erase safe academic work that can continue independently.
