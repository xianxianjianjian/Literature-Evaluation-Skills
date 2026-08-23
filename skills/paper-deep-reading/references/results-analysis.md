# Results Analysis

Results analysis reconstructs the paper's inferential path from data to statistical result to research question to hypothesis. Do not reduce Results to a list of significant p-values.

## Data Analysis Question Tree

Before summarizing results, build the analysis tree from three sources:

1. Introduction Hypothesis/RQ Matrix;
2. Methods Statistical Analysis Map;
3. analyses actually reported in Results and SI.

For each branch identify:

- `AN-xxx`;
- RQ/Hypothesis ID;
- predictor/condition/contrast;
- outcome/indicator;
- analysis method;
- intended role: primary / secondary / exploratory / post-hoc;
- source anchor.

## Planned vs actual analyses

Compare Methods with Results explicitly.

Flag when:

- a planned analysis is omitted;
- a Results analysis has no clear Methods description;
- covariates/model specification changed without explanation;
- subgroup/sensitivity/post-hoc analyses appear later;
- correction strategy differs between plan and reporting.

Do not automatically call a mismatch misconduct. Record the discrepancy and its interpretive consequence.

## Result Matrix

Use at least these fields:

- `Analysis_ID`
- `RQ_ID`
- `Hypothesis_ID`
- `Role`
- `IV/Predictor/Condition`
- `DV/Outcome`
- `Indicator`
- `Method/Model`
- `Model-specific N`
- `Estimate`
- `SE/SD` when relevant
- `CI`
- `Statistic`
- `df`
- `p`
- `Effect size`
- `Correction`
- `Direction`
- `Result status`
- `Source anchor`
- `AUD_ID` if applicable

Use `【原文未报告】` rather than inserting overall N or a guessed effect size.

## Four-layer explanation

Explain each important result in four layers:

### 1. Data layer

What differed, changed, covaried, predicted, or remained similar? State the direction and unit/scale where supported.

### 2. Statistical layer

What model/test was used and what was reported? Include estimate/statistic, CI, p, effect size, correction, and analysis-specific N when available.

### 3. Research-question layer

What RQ does the result address? Avoid theoretical interpretation beyond what the statistical result supports.

### 4. Hypothesis layer

How does the result affect the corresponding hypothesis/prediction?

Keep mechanisms and broad meaning primarily in Discussion.

## Preserve non-significant results

All prespecified or scientifically important non-significant results must remain visible. Do not silently drop them to make the paper's story cleaner.

Distinguish:

- statistically non-significant but directionally consistent;
- null/near-zero estimate;
- wide CI / low precision;
- analysis with insufficient information;
- corrected non-significance after an uncorrected finding.

## Multiple comparisons

Record separately:

- correction family/method;
- corrected threshold or adjusted p when reported;
- which findings survive correction;
- uncorrected exploratory findings.

Never describe an uncorrected result as robust simply because p < .05.

## Effect and precision first

Where the study reports them, prioritize:

1. direction;
2. magnitude/effect estimate;
3. precision/CI;
4. practical/scientific meaning;
5. p-value/significance.

Do not infer practical importance from statistical significance alone.

Do not classify a finding only as “significant/non-significant.” Report the exact p value when available alongside estimate, interval, effect size, model-specific N, multiplicity status and scientific meaning. A p value is not the probability that the hypothesis is true and does not measure effect magnitude. Distinguish a near-zero estimate from an imprecise estimate with a wide interval.

When sample size is consequential, record the authors' justification and its target: power, precision, smallest effect of interest, feasibility, resource constraint or another stated rationale. Evaluate whether that rationale supports the analysis rather than imposing one universal power rule.

## Mandatory consistency checks

When enough information is available, recalculate consistency checks such as:

- p from reported statistic/df;
- CI compatibility with estimate/SE;
- percentages from counts;
- sample totals/subgroups;
- effect-size relationships;
- corrected significance thresholds.

Preserve the author's original value and add a verification note. Any material mismatch becomes `AUD-xxx`.

## Tables and figures

For each central table/figure:

- inspect visually;
- identify what analysis/claim it supports;
- confirm labels/units/groups;
- compare displayed direction with narrative text;
- capture important information available only in the figure/table;
- inspect SI versions when the main text delegates evidence there.

Do not infer exact numeric values from a plot unless the source explicitly provides them or the task requires a clearly labeled approximate extraction.

## Hypothesis–Result closure

At the end, update the Hypothesis Matrix using only:

- `Fully Supported`
- `Partially Supported`
- `Not Supported`
- `Unplanned Finding`
- `Cannot Determine`

A mixed set of outcomes should normally be `Partially Supported`, not forced into binary success/failure.

For exploratory questions, use `Unplanned Finding` or a descriptive RQ outcome rather than pretending an a priori hypothesis existed.

## Results output

The Results section of B should normally contain:

- Data Analysis Question Tree;
- planned-vs-actual analysis comparison;
- Result Matrix;
- structured explanation of all primary and important secondary/exploratory results;
- non-significant result coverage;
- multiple-comparison accounting;
- figure/table evidence integration;
- consistency-check findings;
- final Hypothesis–Result Matrix.

The objective is a complete statistical route, not a narrative optimized to match the authors' preferred story.
