---
name: paper-translation
description: Translate a user-supplied or selected academic paper into evidence-faithful Chinese outputs, including a canonical abstract and mirror-PDF handoff; Phase 1 provides the contract skeleton only.
---

# Paper Translation

## Purpose

Own terminology verification, Canonical Abstract translation, full-text/Supplement translation, Figure/Table handling, A production, Zotero attachment, and proposed terminology updates. Full translation procedures belong to Phase 3 references.

## Entry Modes and Scope

Support weekly context and Translation-only requests. Search completion is not a prerequisite when the user supplies a paper or Zotero item.

## Minimal Intake

When Search artifacts are absent, establish paper identity, source manifest, source version, and minimum file-integrity information. Do not run a hidden full Search.

## Terminology Preflight

Read the terminology registry and evidence records, then identify terms that need verification. The script may manage records but must not decide the best Chinese translation automatically.

## Canonical Abstract

Create one source-grounded canonical Chinese abstract for reuse by downstream deliverables. Preserve uncertainty, direction, numbers, and causal strength.

## Full-text Translation

Cover all material that should be translated, including relevant Supporting Information. References normally remain in English. Missing or unreadable content must be marked, never reconstructed.

## Mirror PDF Production

A is the Chinese full-text mirror PDF. Phase 3 will implement layout behavior using Strict Mirror → Adaptive Mirror → Readable Extension while preserving source data and readable typography.

## Zotero Attachment

Attach verified A as `[A] 中文全文翻译镜像版` when supported. If unavailable, stage and record the pending action under the shared Zotero contract.

## Terminology Update

Propose evidence-backed registry updates with stable TERM/TERMEV identifiers. Do not silently change a preferred translation or long-term terminology record.

## Completion States

`COMPLETE` requires source coverage, terminology issue accounting, canonical abstract, A verification, and verified or pending attachment state. Use `PROVISIONAL` when the source package is incomplete.

## Hard Translation Rules

- Do not change causal strength.
- Do not change numbers, directions, statistical results, or significance markers.
- Do not add information absent from the source.
- If authors themselves overstate causality, translate faithfully and separate any evaluator warning.
- References remain in English by default.
- Figure data, axes, points, lines, error bars, scales, and markers must not change.
- Original errors must not be silently corrected.
