# v1.4.2 Implementation Notes

v1.4.2 extends the existing pipeline rather than creating a parallel workflow.

- Exact A now has formal region roles and separate translatable/preserve-English semantics.
- Residual-English validation rejects any unapproved source-matched English token in translatable roles; figure internals, references, DOI/URL and formulas follow preserve roles.
- `style_map.json` and validator-owned `style_fidelity.json` cover hierarchy, size, leading, weight, italic, color, alignment and superscript intent.
- Numeric canonicalization treats Unicode/caret exponent spellings as the same value while preserving changed signs or exponent values as failures.
- `source_cross_reference.json` closes Main/SI/source-archive coverage.
- B uses `study_design_profile.json`, `b_narrative_coverage.json`, `b_figure_inventory.json` and semantic `source_to_notebook_mapping.csv` gates.
- Workflow state separates Source Package, Source Archive and Output Archive and supports an immutable correction chain for upgraded acceptance criteria.

The v1.4.1 contracts remain readable. New v1.4.2 completion claims must opt into the v1.4.2 validators and evidence files.
