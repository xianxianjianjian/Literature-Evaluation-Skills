# Psychology Methods Routing

Use this reference when the focal paper is in psychology, behavioral science, cognitive neuroscience or an adjacent field. Select only modules that match the actual design, measures and claims. Record the selection and its reason in B under **Research Design and Applicable Method Standards / 研究设计与适用方法规范**.

When the design profile is clear, `scripts/psychology_method_router.py --profile <profile.json>` can produce a reproducible module list. Treat it as routing assistance only: it does not score the paper or replace academic judgment.

Reporting standards help locate information needed to evaluate a study. They are not study-quality scores. In particular, STROBE explicitly says its checklist is not a quality-assessment instrument. Keep reporting completeness, risk of bias, statistical validity and substantive importance as separate judgments.

## Reading sequence

Adapt Keshav's three-pass method to empirical psychology:

1. **Position** — identify paper type, question, constructs, design, claimed contribution and source package. Decide which method modules apply.
2. **Reconstruct** — read Methods/Results closely; inspect figures, tables and SI; rebuild sample, measurement, preprocessing and analysis chains.
3. **Audit** — virtually reproduce the logic from design to inference, challenge assumptions, compare planned/reported analyses, identify alternative explanations and specify a concrete redesign.

Do not stop after the first pass for a requested deep reading.

## Universal psychology reporting prompts

Use APA Journal Article Reporting Standards (JARS) as reporting-completeness prompts:

- distinguish primary, secondary, exploratory and post-hoc aims/analyses;
- identify sampling, participant characteristics, measures and psychometric evidence;
- record exclusions, missingness, transformations, diagnostics and analytic decisions;
- check protocol/preregistration, data, code and material availability when relevant.

Use JARS-Qual for qualitative studies and MMARS for mixed-methods studies. Do not force qualitative evidence into a quantitative bias checklist.

## Design modules

### Experimental and randomized intervention

For randomized social/psychological interventions, use JARS plus CONSORT-SPI reporting prompts. Examine:

- sequence generation, allocation concealment and who could be blinded;
- intervention content, delivery, provider and fidelity;
- participant flow, attrition, exclusions and analysis population;
- outcome timing, selective reporting, contamination and treatment contrast.

Use result-specific risk-of-bias signaling questions when an intervention-effect conclusion warrants them. Do not run a full Cochrane scoring workflow for every paper.

### Observational, cross-sectional and longitudinal

Use JARS plus STROBE reporting prompts. Examine:

- sampling frame, selection and representativeness;
- exposure/outcome measurement and shared-method bias;
- prespecified confounders, residual/unmeasured confounding and model specification;
- missing data, exclusions and analysis-specific N;
- temporal alignment of measures and whether the design supports the claimed direction.

Reporting omissions and validity threats must be reported separately.

### Qualitative

Use JARS-Qual. Examine:

- research paradigm and researcher positioning/reflexivity;
- sampling logic and context;
- data-generation procedure and researcher-participant relationship;
- analytic process, integrity/credibility practices and evidence for interpretations;
- limits on transferability.

### Mixed methods

Use MMARS plus the applicable quantitative and qualitative modules. Identify:

- why mixing was needed;
- timing and priority of components;
- where data or inferences were integrated;
- contradictions between components and how they were handled;
- whether the integrated conclusion exceeds either evidence stream.

### MRI/fMRI

Use COBIDAS MRI prompts in addition to the design module. Reconstruct:

- design and behavioral timing;
- acquisition hardware/sequences and exclusions;
- preprocessing order, parameters and QC;
- first- and higher-level models, covariates and contrasts;
- search space, multiplicity correction, ROI independence and circularity risks;
- effect/uncertainty reporting, data/code availability and reproducibility gaps.

Functional connectivity supports statistical association between signals; it does not by itself establish anatomical connectivity, causal direction or control.

### Mediation and SEM

Record temporal ordering, model identification, measurement assumptions, covariates, indirect-effect uncertainty, alternative models and sensitivity. A cross-sectional mediation path does not demonstrate a longitudinal mechanism; explicitly downgrade temporal/causal claims and cite this as evaluator analysis.

## Statistical interpretation

For every consequential result, seek:

- analysis-specific N;
- estimate/direction and unit;
- confidence/credible interval or another uncertainty measure;
- effect size and practical/scientific meaning;
- exact p value when reported;
- multiplicity correction and role of the analysis.

Do not infer that a hypothesis is true/false or an effect is important from a thresholded p value. Distinguish a near-zero estimate from a wide interval and missing information. Review the paper's sample-size justification in terms of its stated goal—power, precision, smallest effect of interest, feasibility or another defensible rationale—rather than demanding one universal calculation.

## Open-science and claim verification

Check whether empirical claims are verifiable from available data, code, materials, protocol/preregistration and complete reporting. Absence of an open artifact is not automatically misconduct or proof of invalidity; describe what verification or reproduction it prevents.

## Maintained sources

- Keshav, *How to Read a Paper*: https://cs.uwaterloo.ca/~brecht/courses/856/readings/how-to-read/keshav-paper-reading.pdf
- APA JARS: https://www.apa.org/pubs/journals/resources/apa-style-jars
- JARS-Qual/MMARS: https://www.equator-network.org/reporting-guidelines/journal-article-reporting-standards-for-qualitative-primary-qualitative-meta-analytic-and-mixed-methods-research-in-psychology-the-apa-publications-and-communications-board-task-force-report/
- STROBE: https://www.equator-network.org/reporting-guidelines/strobe/
- CONSORT-SPI: https://www.equator-network.org/reporting-guidelines/consort-spi/
- COBIDAS MRI: https://www.humanbrainmapping.org/files/2016/COBIDASreport.pdf
- ASA p-value statement: https://www.amstat.org/asa/files/pdfs/p-valuestatement.pdf
- Cochrane result interpretation: https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-15
- Lakens, *Sample Size Justification*: https://online.ucpress.edu/collabra/article/8/1/33267/120491/Sample-Size-Justification
- Maxwell & Cole, cross-sectional mediation bias: https://pubmed.ncbi.nlm.nih.gov/17402810/
- TOP Guidelines: https://www.cos.io/initiatives/top-guidelines
