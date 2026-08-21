# Methods Reconstruction

The Methods module reconstructs what was actually done to the maximum reproducible detail supported by Main + SI. It must remain source-grounded: missing details are gaps, not invitations to fill in standard practice.

## Study Architecture

Identify and diagram the study architecture before listing procedural details. Record as applicable:

- observational / experimental;
- cross-sectional / longitudinal / repeated-measures;
- prospective / retrospective;
- within-subject / between-subject / mixed;
- single-study / multi-study / multi-cohort;
- laboratory / field / home / online setting;
- number and timing of sessions, visits, nights, waves, blocks, or tasks;
- primary vs secondary analyses;
- preregistered vs exploratory analyses when the paper reports this distinction.

Map the variables actually used:

- manipulated IV/condition;
- predictor/exposure;
- outcome/DV;
- mediator;
- moderator;
- covariates/confounders;
- grouping variables;
- repeated factor/time;
- subjective vs objective measures.

Do not assign variable roles that are not supported by the authors' design or analysis.

## Sample Ledger

Track participant/sample flow as a ledger:

`Assessed → Eligible → Enrolled/Included → Completed/Recorded → Excluded → Final Analytic Sample → Model-specific N`

For every transition record:

- N;
- reason;
- source anchor;
- whether exclusion was planned/criteria-based or post hoc;
- whether different analyses use different N.

### Model-specific N rule

Never substitute the overall sample N for an unreported model/analysis-specific N. Use `【原文未报告】` or another appropriate source-gap label.

Cross-check sample counts against tables, figures, subgroup totals, degrees of freedom, and SI. Arithmetic inconsistencies become `AUD-xxx` issues.

## Recruitment and eligibility

Capture when reported:

- recruitment source;
- inclusion/exclusion criteria;
- screening tools;
- diagnostic procedures;
- age/sex/gender and relevant demographics;
- clinical/cognitive/medication criteria;
- compensation;
- ethics approval and consent;
- power/sample-size calculation.

If representativeness or selection bias is relevant, evaluate it later as `【评译者分析】`; first preserve the authors' actual recruitment procedure.

## Measurement Chain

For every central construct or outcome, reconstruct:

`Construct → Instrument/Sensor/Task → Administration/Acquisition → Raw Response/Data → Scoring/Preprocessing → Derived Indicator → Model Use`

Include only what is reported and relevant:

- instrument/model/manufacturer;
- validated language/version;
- item count;
- response scale/range;
- recall period;
- scoring formula;
- reverse scoring;
- higher-score meaning;
- units;
- reliability/validity cited by the paper;
- derived variables/cutoffs.

For physiological/EEG/PSG measures, distinguish raw signal, scored events/stages, spectral/event features, and final statistical variables.

## Two mandatory process views

### Participant/Subject View

Reconstruct the chronological experience of a participant:

`recruitment → screening → consent → preparation → visit/session/night sequence → instructions → task/recording → breaks/interventions → questionnaires/ratings → completion/follow-up`

This should answer: **what did the participant actually experience, and in what order?**

Do not invent timing between steps when the paper does not report it.

### Researcher/Replication View

Reconstruct the operational pipeline:

`protocol setup → recruitment/screening → equipment/task setup → acquisition → raw data storage → QC → exclusion → preprocessing → feature/score extraction → merge/covariates → statistical dataset → analysis`

This should answer: **what would another research team need to reproduce the study?**

## Trial-level task reconstruction

For experimental or repeated-trial paradigms, reconstruct when applicable:

- stimulus/material source;
- conditions;
- cues/fixations;
- onset/duration;
- response window;
- rating/response mapping;
- ITI/ISI;
- trial and block counts;
- practice;
- randomization;
- counterbalancing;
- adaptive rules;
- control/sham conditions;
- feedback;
- condition contrasts.

Create a single-trial timeline and condition matrix when they materially improve reproducibility.

## Acquisition vs preprocessing

Keep these separate.

### Acquisition

Examples:

- hardware/device;
- sensor/electrode montage;
- reference/ground;
- sampling rate;
- filter settings applied during acquisition;
- impedance criteria;
- environment;
- recording timing/duration;
- behavioral event logging.

### Preprocessing / derivation

Examples:

- resampling;
- rereferencing;
- offline filtering;
- artifact rejection/correction;
- stage/event scoring;
- segmentation/epoching;
- baseline correction;
- feature extraction;
- spectral/event detector settings;
- averaging/normalization;
- thresholding;
- missing-data handling.

Do not move an unreported common preprocessing step into the pipeline.

## Software and parameter rule

Record software, package, algorithm, model, version, threshold, frequency band, window, overlap, detector definition, or correction parameter only when the source supports it. Missing reproducibility-critical parameters must be listed as gaps.

## Statistical Analysis Map

Before Results, reconstruct the Methods-side analysis plan:

- research question/hypothesis;
- outcome/predictor/condition;
- statistical model/test;
- random/fixed effects if applicable;
- covariates;
- repeated structure;
- assumption checks;
- transformations;
- multiple-comparison correction;
- effect size;
- CI;
- missing-data strategy;
- sensitivity/secondary/exploratory analyses.

Assign intended `AN-xxx` IDs where useful so Results can compare planned vs actual analyses.

## Reproducibility Gap Table

For every important missing detail, record:

- required information;
- source location checked;
- reported? (`YES / PARTIAL / NO / UNCLEAR`);
- sufficient to reproduce?;
- gap;
- likely impact;
- related `AUD-xxx`, if any.

Examples include missing software version, detector threshold, exact exclusion timing, model-specific N, correction family, or scoring rule.

## Methods output

The Methods section of B should normally include:

- Study Architecture diagram/table;
- Sample Ledger;
- recruitment/eligibility summary;
- Measurement Chain(s);
- Participant View flow;
- Researcher/Replication View flow;
- task/trial reconstruction where relevant;
- Acquisition pipeline;
- Preprocessing/feature pipeline;
- Statistical Analysis Map;
- Reproducibility Gap Table.

The goal is not maximal verbosity. The goal is to make every consequential design, sample, measurement, preprocessing, and analysis choice traceable and reproducible to the extent the paper permits.