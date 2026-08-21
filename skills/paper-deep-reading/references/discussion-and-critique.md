# Discussion and Critique

Discussion analysis must separate what the authors say from the evaluator's independent judgment. Do not blend author interpretation, external literature, and evaluator critique into one voice.

## Author Discussion Chain

For each major finding reconstruct:

`Finding → Author Interpretation → Previous Evidence → Proposed Mechanism → Implication`

Keep source anchors for each step. If the authors skip a step, do not fill it silently.

## Evidence Distance ED0–ED3

Assign an interpretation-distance label when useful:

- `ED0 Direct`: interpretation is almost identical to the measured result or prespecified operational meaning.
- `ED1 Near inference`: one limited inferential step beyond the result.
- `ED2 Mechanistic speculation`: invokes a process/mechanism not directly measured.
- `ED3 Broad extrapolation`: extends substantially to causal, clinical, societal, translational, or cross-level meaning.

ED level describes inferential distance, not automatic correctness or incorrectness.

## Evaluator critique

Label independent judgments as `【评译者分析】`. Apply only dimensions relevant to the paper:

### Internal validity

Consider design, confounding, selection, attrition, order effects, expectancy, contamination, temporal ambiguity, and alternative explanations.

### Measurement validity

Consider construct coverage, operationalization, instrument validity, reliability, ceiling/floor effects, detector/algorithm dependence, channel/site dependence, derived-variable validity, and whether the measure really captures the claimed construct.

### Statistical validity

Consider power/precision, model specification, assumptions, multiplicity, selective emphasis, overfitting, missing data, model-specific N, effect magnitude, CI, robustness, and analysis transparency.

### Causal validity

Ask whether the design actually supports causal or temporal language. Apply the hard warnings:

- cross-sectional association ≠ temporal causality;
- correlation ≠ cause;
- cross-sectional mediation ≠ demonstrated temporal mechanism;
- functional connectivity ≠ anatomical connection or directional control;
- group difference ≠ mechanism.

### External validity

Consider population, setting, equipment, task, age/clinical range, culture, sampling frame, and whether the authors generalize beyond them.

### Reproducibility/transparency

Consider SI completeness, preprocessing details, software/version reporting, preregistration, code/data availability, exclusion transparency, and whether another team could reconstruct the pipeline.

Do not generate a criticism merely because a generic checklist contains the category. Each critique must matter to the actual paper.

## Innovation Matrix

For each claimed or evaluator-identified contribution record:

- innovation dimension;
- previous state;
- what this study adds;
- evidence/source anchor;
- innovation level;
- caveat.

Useful dimensions include:

- substantive/theoretical;
- methodological;
- measurement/indicator;
- analytic/statistical;
- combinational/integrative;
- application/translational;
- reporting/open-science.

Distinguish:

- demonstrated contribution;
- incremental contribution;
- author-claimed novelty not independently verified.

If novelty depends on “first/no prior study,” use the Introduction external-verification rule.

## Limitations: three provenance layers

Keep limitation origin explicit:

### 1. Author-acknowledged

Limitations explicitly stated by the authors.

### 2. Audit-derived

Problems discovered through source/internal consistency audit (`AUD-xxx`).

### 3. Evaluator-inferred

Methodological/theoretical limitations inferred independently from the design and evidence.

Do not attribute evaluator-inferred limitations to the authors.

## Redesign Matrix

A useful redesign must solve a specific problem rather than vaguely saying “increase sample size” or “use better methods.”

Map:

`Limitation/Problem → Proposed Modification → Why Better → What It Tests/Fixes → Cost/Trade-off`

Examples of trade-offs include cost, burden, ecological validity, sample feasibility, recording duration, data complexity, statistical power, interpretability, or comparability with prior work.

When recommending additional measures/analyses, explain how they address the identified limitation.

## Transfer Value Matrix

Evaluate concrete transfer to the user's research across:

- theory/framework;
- hypotheses;
- sampling/recruitment;
- study architecture;
- task/paradigm;
- measurement/tool;
- acquisition;
- preprocessing/QC;
- indicator/feature;
- statistical model/correction;
- visualization;
- reporting/scientific writing.

Classify each item as:

- `DIRECTLY_REUSABLE`
- `REUSABLE_WITH_MODIFICATION`
- `NOT_RECOMMENDED`
- `CANNOT_DETERMINE`

For reusable items record:

- exact element;
- source anchor;
- why it transfers;
- what must change for the current project;
- risk/caveat.

## Discussion output

The Discussion/critique part of B should normally contain:

- finding-by-finding Author Discussion Chain;
- ED0–ED3 mapping for consequential interpretations;
- evaluator critique by relevant validity dimensions;
- Innovation Matrix;
- three-layer Limitations section;
- Redesign Matrix;
- Transfer Value Matrix.

The final evaluation should show where the paper is strong and useful as clearly as where it is limited. Critical reading is not synonymous with fault-finding.