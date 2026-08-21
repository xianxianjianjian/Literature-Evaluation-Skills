# Translation QC

A may be described as `COMPLETE` only after four QC passes. Translation QC checks fidelity of the translation artifact; it does not replace the later research audit.

## QC-1 Content Coverage

Confirm that all expected translation units are accounted for, including:

- title/abstract/keywords;
- every section and paragraph;
- captions and notes;
- tables;
- figures;
- acknowledgements/funding/COI/data statements;
- scientifically relevant Supporting Information.

Any missing or unreadable source unit must be explicitly logged rather than silently omitted.

## QC-2 Semantic Fidelity

Check:

- terminology consistency and context match;
- causal strength;
- negation;
- higher/lower and increase/decrease direction;
- uncertainty/modal language;
- sample identity and N;
- method parameters;
- corrected/uncorrected and significant/non-significant distinctions.

## QC-3 Numeric/Data Integrity

Compare source versus translation tokens such as:

- N / n;
- percentages;
- p values;
- F / t / χ² / z;
- β / r / ICC;
- OR / HR;
- CI;
- df;
- durations/times;
- frequencies/sampling rates;
- software versions;
- table cells and significance markers.

Do not replace author-reported values with recalculated values during Translation. If an apparent inconsistency is noticed, preserve the source and flag it for `AUD-xxx` review later.

## QC-4 Layout Integrity

Check:

- overflow/clipping;
- reading/column order;
- font readability;
- table legibility;
- figure/caption placement;
- continuation/extension pages;
- Main/SI boundaries;
- source-page reverse mapping.

Layout QC requires actual render/visual inspection. A valid layout plan alone is not proof that the rendered PDF is visually correct.

## Completion Gate

For `FULL_MIRROR`, Translation can be `COMPLETE` only when:

- Canonical Abstract exists and passes alignment;
- terminology issues are resolved or explicitly accounted for;
- Main coverage is complete;
- SI status is explicitly accounted for;
- no critical unlogged source gap remains;
- all four QC passes succeed;
- A has been generated and verified;
- A is verified as the correct Zotero child attachment of the selected paper.

If the translation/A is scientifically usable but Zotero attachment is still pending, keep Translation/A `PROVISIONAL` and record `pending_zotero_actions`; do **not** mark Translation `COMPLETE` merely because the file exists locally.

Likewise, consequential missing SI/source coverage keeps the stage `PROVISIONAL` or `BLOCKED` according to whether defensible work can continue.

`TRI-xxx` is reserved for translation/production issues. Do not use `TRI` for methodological or statistical research-audit findings.
