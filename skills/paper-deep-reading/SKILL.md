---
name: paper-deep-reading
description: Audit and deeply read an academic paper with traceable evidence, reconstruct its theory, methods, statistics, results and discussion, and produce complete research notes plus a weekly evaluation when requested.
---

# Paper Deep Reading

## Purpose

Own the complete V1 Deep Reading stage:

```text
source/package intake
→ Full Research Audit
→ Paper Structure Inventory
→ Introduction reconstruction
→ Methods reconstruction
→ Results/statistical route reconstruction
→ Discussion + evaluator critique
→ Dynamic Coverage closure
→ B research archive
→ C weekly review when required
→ knowledge/history update
```

This Skill may run independently from Search and Translation. Translation output A can improve language consistency, but all academic judgments must return to the original source package or explicitly checked external evidence.

## Required shared contracts

Before substantive work, read:

- [`../../shared/evidence-policy.md`](../../shared/evidence-policy.md)
- [`../../shared/identifier-policy.md`](../../shared/identifier-policy.md)
- [`../../shared/source-identity-policy.md`](../../shared/source-identity-policy.md)
- [`../../shared/zotero-policy.md`](../../shared/zotero-policy.md)
- [`../../shared/state-contract.md`](../../shared/state-contract.md)
- [`../../shared/data-format-policy.md`](../../shared/data-format-policy.md)

When running in weekly context, use `weekly_reviews/YYYY/YYYY-Wxx/workflow_manifest.yaml` as the workflow source of truth.

## Reference routing

Read the reference that owns each decision:

- source identity, Main/SI package, three-level audit, consistency checks → [`references/source-audit.md`](references/source-audit.md)
- theory, gap, RQ/Aim/Hypothesis, citation tracing → [`references/introduction-reconstruction.md`](references/introduction-reconstruction.md)
- sample, measurement, participant/researcher flows, acquisition/preprocessing → [`references/methods-reconstruction.md`](references/methods-reconstruction.md)
- analysis tree, Result Matrix, statistics and hypothesis closure → [`references/results-analysis.md`](references/results-analysis.md)
- author interpretation, ED0–ED3, critique, innovation, limitations, redesign, transfer → [`references/discussion-and-critique.md`](references/discussion-and-critique.md)
- paper-specific sections and Source→Notebook closure → [`references/dynamic-coverage.md`](references/dynamic-coverage.md)
- B/C production, completion gate and final QC → [`references/deliverables-and-qc.md`](references/deliverables-and-qc.md)

## Supported entry modes

### Full weekly context

Use the focal paper already confirmed by Search when available. Preserve the existing Search record; later audit findings must not silently rewrite Search-time history.

### Deep-Reading-only

Accept a directly supplied PDF/source package, DOI, or Zotero item. Perform a Minimal Intake rather than running a hidden full Search.

### Resume

Read the workflow manifest and existing `source_manifest.json`, `audit_log.jsonl`, `claim_evidence_map.csv`, canonical Abstract, translation artifacts, and partial B. Resume from the first incomplete or update-required component.

### Update existing archive

When new SI, correction, source version, or missing evidence becomes available, mark affected sections `needs_update`, update only the necessary audit/notes, and preserve prior provenance.

## Minimal Intake

Before analysis:

1. establish `paper_id` and publication identity;
2. distinguish Version of Record / accepted manuscript / preprint;
3. identify Main, SI, corrections, protocol/preregistration, code and data when discoverable;
4. assign stable source IDs (`SRC-M1`, `SRC-S1`, ...);
5. determine readiness: `READY / READY_WITH_GAPS / BLOCKED`;
6. create a Paper Structure Inventory before applying the notebook schema.

Do not use A as a substitute for unavailable Main/SI evidence.

## Evidence contract

Every important claim must preserve both:

- evidence class: `【原文直接内容】 / 【作者解释】 / 【评译者分析】 / 【外部依据 EXT-xxx】`;
- source location: Section/Subsection/Page/Table/Figure/SI whenever possible.

Do not treat a citation merely mentioned by the focal paper as independently verified external evidence.

Use the shared source-gap vocabulary precisely. Never fill unreported methods, parameters, model N, hypotheses or results from common practice.

## Full Research Audit

Run the three-level audit contract and the full Deep Reading audit before relying on the paper's narrative coherence.

At minimum check:

- publication/version/source package;
- Abstract ↔ Results;
- Introduction ↔ hypotheses;
- Methods ↔ Results;
- Main ↔ SI;
- text ↔ table/figure;
- sample flow ↔ analysis-specific N;
- statistical test ↔ reported statistic;
- statistic/df ↔ p when calculable;
- effect ↔ CI;
- correction ↔ significance claim.

Visually inspect scientifically important tables and figures. Perform consistency recalculation whenever the reported information is sufficient, but never replace the author's original value; create `AUD-xxx` instead.

Use A0–A3 severity. `A3` means the issue may affect a core conclusion and must be prominent in B/C.

## Deep-reading Base Schema

Use this as minimum required coverage:

```text
0 Literature Positioning & Research Audit
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

The Base Schema is not closed. Follow Dynamic Coverage for scientifically important paper-specific material.

## Introduction reconstruction

Reconstruct:

`problem → prior evidence → theory/mechanism → evidence limitation → Research Gap → RQ → Aim → Hypothesis/Prediction/Exploration`

Research Gap must answer: known / unknown / why it matters / what this study adds.

Distinguish `EXPLICIT`, `INFERRED_PREDICTION`, and `EXPLORATORY`. Never invent a directional hypothesis. Build one Hypothesis/RQ Matrix and reuse its IDs in Results.

Trace Level III external sources where feasible for core hypothesis basis, critical method sources, important numeric/priority claims, and “first/no previous study” novelty claims.

## Methods reconstruction

Restore the study to the maximum reproducible detail supported by Main + SI.

Mandatory where relevant:

- Study Architecture;
- Sample Ledger: Assessed → Eligible → Enrolled → Completed → Excluded → Final → Model-specific N;
- Measurement Chain;
- participant chronological view;
- researcher/replication pipeline;
- trial/task timeline and condition matrix;
- acquisition separated from preprocessing;
- statistical-analysis map;
- Reproducibility Gap Table.

Never substitute total N for an unreported model-specific N.

## Results analysis

Build a Data Analysis Question Tree from hypotheses, the Methods plan, and actual Results.

Use `AN-xxx` and a Result Matrix with RQ/H/IV/DV/indicator/method/model-N/estimate/CI/statistic/df/p/effect/correction/direction/source.

Explain important findings in four layers:

1. data;
2. statistical result;
3. research-question answer;
4. hypothesis consequence.

Retain prespecified non-significant findings. Separate primary/secondary/exploratory/post-hoc and corrected/uncorrected results.

Close hypotheses only as:

- `Fully Supported`
- `Partially Supported`
- `Not Supported`
- `Unplanned Finding`
- `Cannot Determine`

## Discussion and critique

For author interpretation reconstruct:

`Finding → Interpretation → Previous Evidence → Mechanism → Implication`

Use ED0–ED3 to mark inferential distance when consequential.

Keep evaluator analysis separate and apply only relevant validity dimensions: internal, measurement, statistical, causal, external, reproducibility/transparency.

Hard causal warnings include:

- cross-sectional ≠ temporal causality;
- correlation ≠ cause;
- cross-sectional mediation ≠ proven temporal mechanism;
- functional connectivity ≠ anatomical/directional control.

Complete Innovation, three-provenance Limitations, Redesign, and Transfer Value matrices where relevant.

## Dynamic Coverage

Start with the Paper Structure Inventory and end with Source→Notebook Mapping.

Every core source item—important section, analysis, table, figure, SI item, study/cohort, robustness analysis or open-science element—must map to B. Add a dynamic section when forcing the item into the Base Schema would erase its independent scientific meaning.

Do not create headings for trivial details simply to make B longer.

## Deliverables

### B

Create `[B] 文献研究笔记·完整精读版` as a DOCX research archive when the environment supports document generation. Important conclusions must be traceable to source anchors/evidence IDs.

### C

Generate C in weekly context or on explicit request. It must include the required bibliographic fields, original Abstract, exact canonical Chinese Abstract, reviewer field, and review body meeting the configured minimum Chinese-character requirement. The character threshold applies only to the review/comment body.

C is a second-stage synthesis of B and must not introduce unsupported critique or facts.

## Knowledge updates

Only after a paper has genuinely completed Deep Reading or has been explicitly accepted as a usable provisional archive:

- append appropriate completion information to `knowledge/reading_history.csv`;
- record verified Zotero A/B attachment keys;
- record C Git path;
- propose updates to `knowledge/research_profile.md` but never apply a research-direction change without explicit user approval.

## Completion states

`COMPLETE` requires the applicable Deep Reading completion gate in `deliverables-and-qc.md`, including audit, dynamic coverage closure, B/C requirements, evidence anchoring, statistical checks, and verified archive handoff.

Use `PROVISIONAL` when the archive is scientifically usable but a named SI/source/Zotero/attachment gap remains.

Use `BLOCKED` when missing source evidence prevents defensible reconstruction of a core part of the study.

## Hard prohibitions

- Do not invent missing hypotheses, methods, parameters, analyses, results, citations, model N, or SI content.
- Do not present author interpretation as direct data.
- Do not present evaluator analysis as the authors' claim.
- Do not present external literature as focal-paper evidence.
- Do not upgrade association to causation.
- Do not omit important prespecified non-significant results.
- Do not silently repair inconsistent statistics or source errors.
- Do not let a polished narrative override conflicting tables/figures/SI.
- Do not describe an `A0` audit as proof that the data or paper are true.
