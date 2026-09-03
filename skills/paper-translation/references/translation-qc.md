# Translation QC

A may be described as academically `COMPLETE` only after four QC passes. Translation QC checks fidelity of the translation artifact; it does not replace the later research audit or the optional archive-completion check.

Read [`translation-evidence-contract.md`](translation-evidence-contract.md). For every manifest scope, the final inventory/ledger result must be recomputed by `validate_translation_package.py`; `FULL_MIRROR` also activates its layout checks. Do not accept a hand-authored QC manifest or a PDF-signature-only check as completion evidence.

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

- exact page count, page boxes, rotation and one-to-one Main/SI mapping;
- reviewed source/output text-frame containment;
- embedded SimSun for every CJK glyph with no fallback;
- 95%-100% font sizing with unchanged leading/frame geometry;
- exact table cells and figure-label replacement;
- no extension page, adaptive layout or page-wide reflow panel;
- zero same-renderer pixel changes outside reviewed replacement frames.

Layout QC requires actual render/visual inspection. A valid layout plan alone is not proof that the rendered PDF is visually correct.

## Academic Completion Gate

For any manifest scope, Translation/A can be `COMPLETE` when:

- Canonical Abstract exists and passes alignment;
- terminology issues are resolved or explicitly accounted for;
- Main coverage is complete;
- SI status is explicitly accounted for;
- no critical unlogged source gap remains;
- all four QC passes succeed;
- the independent translation-package validator passes and generates `translation_validation.json`;
- A has been generated and verified against the active paper/source version.

For `FULL_MIRROR/EXACT_TEXT_FRAME`, schema-v2 inventory/plan, `text_frame_inventory.jsonl`, `font_map.json` and validator-generated `layout_diff.json` must pass. A boolean render flag or notes cannot satisfy this gate. These exact checks are not imposed on `MAIN_ONLY` or `ABSTRACT_ONLY`; user-requested `STRUCTURAL_MIRROR` is reported separately and cannot be labeled exact.

A Zotero attachment key is **not** part of this academic Translation gate. If Zotero archive work is still pending, keep Translation/A `COMPLETE`, record the pending action, and report archive closure separately.

## Archive Completion Add-on

When the user/workflow specifically requires a fully closed Zotero archive, additionally verify:

- A exists as the intended Zotero child attachment;
- parent identity matches the active paper;
- attachment key is observable and stored;
- no conflicting/duplicate A attachment remains unresolved;
- the corresponding pending Zotero action is cleared.

Failure of this add-on means **archive pending**, not Translation failure.

Consequential missing SI/source coverage still keeps the academic stage `PROVISIONAL` or `BLOCKED` according to whether defensible work can continue.

`TRI-xxx` is reserved for translation/production issues. Do not use `TRI` for methodological or statistical research-audit findings.
