# Dynamic Coverage

The Deep Reading Base Schema defines **minimum required coverage**, not a closed template. The notebook must follow the scientific content of the paper when important material falls outside the expected Introduction/Methods/Results/Discussion structure.

## Start with Paper Structure Inventory

Before writing B, inventory all meaningful source content from Main + SI:

- sections/subsections;
- tables/figures;
- supplementary tables/figures;
- multiple studies/cohorts/experiments;
- validation or calibration modules;
- sensitivity/robustness analyses;
- preregistration/protocol/open-science material;
- special methodological appendices;
- additional datasets;
- unusual statistical or theoretical sections.

The inventory is the source-side checklist for later closure.

## Base Schema

The default B schema is:

0. Literature Positioning & Research Audit
1. Abstract
2. Introduction
3. Methods
4. Results
5. Discussion
6. Innovation
7. Limitations
8. Redesign
9. Transfer Value
10. Terminology & Evidence Index

This is a minimum coverage contract. It does not mean every paper must be forced into exactly eleven flat sections.

## When to add dynamic sections

Add a paper-specific section when an item is scientifically important and forcing it into the Base Schema would erase its independent role or make evidence tracing unclear.

Typical examples:

- Study 1 / Study 2 / replication cohort;
- validation dataset;
- simulation;
- algorithm benchmarking;
- sensitivity/robustness analyses;
- qualitative component;
- preregistration deviations;
- data/code/open-science audit;
- special neuroimaging/EEG pipeline;
- mediation/network/model-comparison module;
- supplementary experiment with independent conclusions.

## When not to add a section

Do not create headings merely because:

- a paragraph contains a minor detail;
- a table can be explained within an existing Results subsection;
- a methodological parameter belongs naturally in the preprocessing pipeline;
- the purpose is to make B look more elaborate.

Dynamic coverage should increase scientific fidelity, not fragmentation.

## Source → Notebook Mapping

At the end of Deep Reading, map every important source item to its notebook location.

Suggested fields:

- source item ID/location;
- type: section/table/figure/SI/analysis/open-science;
- importance: core / supporting / minor;
- B section;
- related `CLM-xxx`, `AN-xxx`, `AUD-xxx`, or hypothesis ID;
- coverage status;
- note.

Every **core** item must be mapped. Supporting items may be summarized/grouped when doing so does not remove important distinctions.

## Closure rule

Before B is complete, ask:

1. Is every central theory/gap/hypothesis represented?
2. Is every consequential sample/method/parameter represented?
3. Is every planned and important unplanned result represented, including non-significant results?
4. Are every core table/figure and relevant SI item represented?
5. Are author limitations and major evaluator/audit concerns represented?
6. Is important open-science or version information represented?

If an important source item is unmapped, either map it to the correct existing section or create a justified dynamic section.

## Missing source items

Dynamic Coverage does not authorize reconstruction of unavailable SI. If an important item is referenced but unavailable, map the gap itself using the appropriate source-gap label and set `PROVISIONAL` when the gap prevents a complete archive.

## Multi-study papers

For multi-study papers, preserve both levels:

- cross-paper synthesis of shared theory/question;
- study-specific sample/method/result chains.

Do not blend study-specific N, methods, or results into one composite description unless the authors explicitly pooled them.

## Relationship to templates

Templates should make recurring work more reliable, but the evidence package is authoritative. When template and paper structure conflict, preserve all required Base Schema coverage **and** adapt the structure to the paper.