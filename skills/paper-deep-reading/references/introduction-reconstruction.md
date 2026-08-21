# Introduction Reconstruction

The Introduction module reconstructs the scientific argument. Do not produce a paragraph-by-paragraph summary unless the user explicitly asks for one.

## Core argument chain

Reconstruct the paper as:

`real/research problem → established findings → theory/mechanism → unresolved evidence problem → Research Gap → Research Question → Aim → Hypothesis/Prediction/Exploratory Question`

For each important step record:

- source anchor;
- what the authors claim;
- what evidence/citation they use;
- why that step is necessary for the present study;
- whether the present study actually tests it or only uses it as motivation.

## Background Claim Table

For important background claims, capture:

- `CLM-xxx`
- claim text in precise paraphrase;
- source anchor in the focal paper;
- cited source(s) used by the authors;
- role: background / theory / gap / method justification / hypothesis basis / novelty;
- whether independent external verification was performed;
- verification result or `not checked`.

Do not treat a source cited by the focal paper as independently verified external evidence unless that source was actually retrieved and checked.

## Theory and concept reconstruction

For each core theory, construct, or mechanism explain only what is needed for this paper:

1. definition;
2. boundary from adjacent concepts;
3. role in the paper's logic;
4. operationalization in the study;
5. what empirical result would support or weaken the paper's use of the theory;
6. whether the study genuinely tests the theory/mechanism or merely invokes it.

Avoid writing a generic textbook chapter detached from the focal study.

## Research Gap: four mandatory questions

A defensible Gap reconstruction must answer:

1. **What is already known?**
2. **What remains unknown or insufficient?**
3. **Why does that uncertainty matter scientifically or methodologically?**
4. **What exactly does this study add to close or narrow the gap?**

If the paper merely states that “few studies exist” without establishing a substantive gap, say so.

## Distinguish question types

Do not collapse the following:

- **Research Question (RQ):** what the study asks;
- **Aim/Objectives:** what the study intends to do;
- **Hypothesis:** testable expected relationship/difference;
- **Prediction:** directional or quantitative expected outcome;
- **Exploratory Question:** investigated without a prespecified prediction.

## Hypothesis status

Use only:

- `EXPLICIT`: stated as a hypothesis/prediction in the paper;
- `INFERRED_PREDICTION`: not labeled as a hypothesis but a reasonably specific expectation is directly inferable from the authors' wording;
- `EXPLORATORY`: no defensible prespecified prediction.

Never invent directionality. If the Introduction motivates an association but does not predict positive/negative direction, do not create a directional H1.

## Hypothesis Matrix

Create one row for every meaningful hypothesis/prediction/exploratory question. Suggested fields:

- Hypothesis/RQ ID (`H1`, `H2`, `RQ1`, ...);
- status (`EXPLICIT`, `INFERRED_PREDICTION`, `EXPLORATORY`);
- source anchor;
- predictor/condition;
- outcome;
- expected direction/contrast, if explicitly supported;
- theoretical/citation basis;
- planned analysis if identifiable;
- later Result Analysis IDs (`AN-xxx`);
- final support status.

The same IDs must be reused in Results rather than inventing a second hypothesis numbering system.

## External citation tracing

Use three levels:

### Level I — ordinary background

Examples: broad field facts that are not decisive to the paper's novelty or design. Retrieval is optional unless the user asks.

### Level II — gap/theory/critical method

Prefer to inspect the cited primary or authoritative source when feasible, especially if the current argument depends on it.

### Level III — core evidentiary basis

Strongly verify when accessible:

- direct basis for a main hypothesis;
- central method/measurement source;
- important numeric prevalence/effect claims;
- claims of priority, uniqueness, or lack of prior work;
- “first study”, “no previous research”, or equivalent novelty assertions.

Record verified outside material as `【外部依据 EXT-xxx】` rather than as focal-paper direct evidence.

## Novelty-claim rule

Do not repeat statements such as “this is the first study” as established fact merely because the authors wrote them. If the novelty claim matters to the paper's contribution, perform an external check or label it explicitly as an author claim whose completeness has not been verified.

## Introduction output

The Introduction section of B should normally contain:

- compact argument map / logic diagram;
- Background Claim Table;
- core theory/concept reconstruction;
- Research Gap analysis;
- RQ/Aim/Hypothesis distinctions;
- Hypothesis Matrix;
- important external verification notes;
- evaluator observations on logical gaps, clearly labeled as `【评译者分析】`.

Do not move Results or Discussion interpretation backward into the Introduction reconstruction.