---
name: paper-deep-reading
description: Audit and deeply read an academic paper with traceable evidence, producing complete research notes and a weekly review when requested; Phase 1 provides the contract skeleton only.
---

# Paper Deep Reading

## Purpose

Own source audit, Introduction/Methods/Results/Discussion analysis, critical evaluation, B production, and C production in weekly context. Full academic procedures belong to Phase 4 references.

## Entry Modes

Support weekly context and Deep-Reading-only requests. Translation output A may improve consistency but is never required; academic judgments must return to the original paper.

## Evidence Rules

Read [`../../shared/evidence-policy.md`](../../shared/evidence-policy.md), identifier policy, and source identity policy. Bind important claims to Source Anchors and keep direct content, author interpretation, evaluator analysis, and external evidence distinct.

## Full Research Audit

Audit identity, version, Main Article, Supporting Information, corrections, integrity notices, hypotheses, samples, methods, analyses, results, interpretation, data/code availability, and material gaps. Do not replace unknown model N with total N.

## Deep-reading Workflow

Use this minimum Base Schema:

```text
0 文献定位与审计
1 Abstract
2 Introduction
3 Methods
4 Results
5 Discussion
6 Innovation
7 Limitations
8 Redesign
9 Transfer Value
10 Terminology & Evidence Index
```

## Dynamic Coverage

The Base Schema is Minimum Required Coverage, not a closed template. Add important paper-specific sections, analyses, appendices, figures, tables, or Supplement content even when the template did not anticipate them. Do not create unsupported content merely to fill a heading.

## Deliverables

- B: complete research-note DOCX.
- C: weekly evaluation submission when invoked in weekly context.

C reuses the Canonical Abstract when available and follows the configured minimum comment character requirement.

## Knowledge Updates

Only papers that truly complete Deep Reading may be appended to `reading_history.csv`. Suggest research-profile updates, but do not change long-term research direction without explicit user confirmation.

## Completion States

Use the shared enum. `COMPLETE` requires audit coverage, evidence anchors, dynamic content coverage, deliverable verification, and knowledge update. Missing cited Supplement or unresolved source identity normally requires `PROVISIONAL` or `BLOCKED`, with an explicit reason.

## Hard Prohibitions

- Do not invent missing source content, hypotheses, methods, results, or citations.
- Do not present author interpretation or external evidence as direct focal-paper evidence.
- Do not upgrade association to causation, mediation to proven mechanism, or functional connectivity to directional connection.
- Do not omit non-significant prespecified results.
- Do not silently repair inconsistencies or errors in the paper.
- Do not implement Phase 4 deep-reading logic during Phase 1.
