# Deliverables and QC

For new v1.5.0 B, use `validate_deep_reading_package.py --contract-version 1.5.0`. It preserves narrative, design, figure, source mapping, metadata, OOXML, independent render and all-page visual gates.

Deep Reading produces B as the full research archive and, in weekly context or on explicit request, C as the concise weekly evaluation submission. C is derived from B; it is not an independent second reading that may introduce unsupported claims.

## B — Complete Research Notes DOCX

Apply the shared paragraph roles from the Translation typography contract: generated Chinese body paragraphs are justified with a 2em first-line indent; English body paragraphs are left aligned with a 0.5-inch first-line indent when reformatting is intended; headings, captions, tables and footnotes do not inherit body indentation. Skill-generated references use a 0.5-inch hanging indent. These Chinese rules are project rules, while the English/reference choices are APA-oriented.

### Base Schema

Use this minimum structure, adapting dynamically when the paper requires it:

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

For every consequential conclusion, parameter, sample fact, hypothesis/result judgment, author limitation, audit issue, or transfer recommendation, preserve a Source Anchor or linked evidence ID.

### Section expectations

#### 0. Literature Positioning & Research Audit

Include publication identity/version, literature role, source package, SI status, integrity/current-notice status, Paper Structure Inventory, important `AUD-xxx` items, and readiness/completeness state.

#### 1. Abstract

Reuse `canonical_abstract.md` exactly when it exists. Do not create a competing translation.

#### 2. Introduction

Include argument reconstruction, theory/concept analysis, Research Gap, RQ/Aim/Hypothesis distinctions, citation tracing where required, and the Hypothesis Matrix.

#### 3. Methods

Include Study Architecture, Sample Ledger, Measurement Chain, participant/researcher process views, acquisition vs preprocessing, analysis map, and Reproducibility Gap Table as applicable.

Include **研究设计与适用方法规范 / Research Design and Applicable Method Standards**: selected design modules, why they apply, consequential non-applicable modules, reporting-completeness findings and separate validity judgments. Do not compute a checklist-derived total score.

#### 4. Results

Include Analysis Question Tree, Result Matrix, planned-vs-actual comparison, non-significant findings, correction accounting, figure/table evidence, consistency checks, and Hypothesis–Result closure.

#### 5. Discussion

Separate author interpretation from evaluator critique; include ED0–ED3 where useful.

#### 6–9

Use Innovation Matrix, three-layer Limitations, Redesign Matrix, and Transfer Value Matrix.

#### 10. Terminology & Evidence Index

Include key terminology, TERM/TERMEV identifiers when available, external evidence (`EXT-xxx`), claim/evidence IDs, audit IDs, and source-location index sufficient for later tracing.

## C — Weekly Evaluation Submission

Generate C when:

- running in weekly context; or
- the user explicitly asks for it.

C must contain at least:

- journal;
- publication/online date;
- English title;
- Chinese title;
- authors;
- original article URL/address;
- original Abstract;
- exact canonical Chinese Abstract;
- review/comment body;
- reviewer name from `<data-root>/knowledge/submission_profile.yaml` when configured.

For new v1.5.0 C, the `## 评论` body must contain 800–1000 effective visible characters, targeting 850–950. The count excludes metadata and both Abstracts. Legacy pre-1.5.0 C keeps its original contract and is not rewritten or retroactively failed.

When C is exported to DOCX/PDF rather than retained as Markdown, apply the same role engine: Chinese comment body uses the project body style, metadata headings remain unindented, and references, if explicitly requested, use the reference style rather than the body style.

## C as second-stage synthesis

C is a natural 3–5 paragraph submission review: background and gap; study design and 2–4 core results; innovation with author-acknowledged uncertainty; conclusion and field connection. Read [`c-submission.md`](c-submission.md) before writing or validating C. B informs selection and ordering, while each visible paper fact in default C must be supported by Main. SI-only results and independent evaluator criticism remain in B unless the user explicitly requests a different commentary mode. Internal working metadata retains source IDs and audit links; public C shows none.

## Knowledge updates

Append a paper to `<data-root>/knowledge/reading_history.csv` **only after Deep Reading genuinely reaches academic `COMPLETE`**. A source/evidence-provisional Deep Reading must not be recorded as completed.

After academic Deep Reading is complete:

- append the completed paper to `<data-root>/knowledge/reading_history.csv`;
- record Zotero parent/A/B attachment keys when already verified, otherwise leave those optional archive fields empty;
- record C path;
- keep unresolved Zotero operations in `pending_zotero_actions`;
- propose, but do not automatically apply, changes to `<data-root>/knowledge/research_profile.md`.

A Zotero-only pending action does not prevent the reading from entering completed history. A single paper must never silently redefine the long-term research direction.

## B archive handoff

Promote the independently rendered B PDF with `scripts/export_b_pdf.py` only after the DOCX academic report and visual QA pass. Keep the DOCX as editable source; Zotero receives the PDF with display title `B精读`. If PDF export fails, B academic status stays intact and Archive remains pending.

When Zotero is writable, verify the parent item and attachment after writing. If Zotero is unavailable, stage under `<data-root>/work/<paper_id>/handoff/` and record a pending action. This archive pending state must not downgrade a B that already passed its academic/QC gate.

## Deep Reading Academic Completion Gate

For `COMPLETE`, require all applicable items below:

- publication/source identity resolved;
- Full Research Audit performed;
- Paper Structure Inventory complete;
- Main/SI status explicit;
- source→notebook mapping closed for all core items;
- canonical Abstract reused or appropriate Abstract mini-translation completed;
- Hypothesis/RQ Matrix complete;
- Sample Ledger complete to the extent reported;
- participant and researcher Methods views complete where relevant;
- acquisition/preprocessing and reproducibility gaps accounted for;
- Analysis Question Tree and Result Matrix complete;
- all important prespecified non-significant results retained;
- mandatory consistency recalculations performed where possible;
- important figures/tables visually inspected;
- Hypothesis–Result closure complete;
- Author Discussion and Evaluator Critique separated;
- limitations provenance separated;
- Innovation / Redesign / Transfer Value completed where relevant;
- every A3 audit issue prominently treated;
- B generated and verified as the correct artifact for the active paper/source version;
- B DOCX metadata sanitized and `docProps/core.xml` verified; no generator identifier or non-requested author/comments/keywords remain;
- B DOCX remains the editable source; its independently rendered PDF is checked and promoted for Zotero archive after B academic validation;
- C generated when weekly context requires it;
- required knowledge/history update recorded.

A verified Zotero attachment is **not** part of this academic completion gate.

## Archive Completion Add-on

If the user/workflow requires closed Zotero archival status, additionally require `B_PDF_EXPORT_PASS`, the role/title/MIME verification report for Main/SI/A/B, and `pending_zotero_actions = []`. Manual Zotero attachment followed by verification is acceptable.

## PROVISIONAL vs BLOCKED

Use `PROVISIONAL` when the academic archive is scientifically usable but a named source/SI/version/evidence/content gap prevents full academic completeness.

Use `BLOCKED` when missing Main/SI/source identity prevents defensible reconstruction of a core part of the paper.

Do not use `PROVISIONAL` merely because Zotero automatic writing is unavailable. Do not call a file `COMPLETE` merely because a DOCX exists; it must pass `validate_deep_reading_package.py`, including independent office rendering and all-page visual QA. Render failure is a B production gap and therefore keeps B/Deep Reading `PROVISIONAL` with `needs_update`.

## Final QC checklist

### Evidence QC

- all major claims have the correct evidence class;
- Source Anchors are present for important claims;
- external evidence is clearly separate;
- no unavailable source content was invented.

### Methods QC

- total N has not been substituted for unknown analysis N;
- acquisition and preprocessing are separate;
- important parameters and missing parameters are explicit.

### Results QC

- primary and important secondary analyses are represented;
- non-significant prespecified results are retained;
- corrected/uncorrected results are distinguished;
- statistical consistency checks are recorded.

### Discussion QC

- author interpretations are not presented as direct findings;
- evaluator critique is labeled;
- causal strength is not inflated;
- limitations and redesigns are specific to the paper.

### Deliverable QC

- B opens correctly and contains the required/dynamic sections;
- C uses the canonical Abstract and meets the comment-body length rule;
- Zotero/Git paths or pending actions match the workflow manifest;
- final report distinguishes academic completion from archive completion;
- final state accurately reflects unresolved source/evidence gaps.

### v1.5 B content binding

The academic report binds the current DOCX SHA-256/size, independently rendered PDF SHA-256/size/page count, visual QA file, paper/workflow/contract identity, and verified Main/SI fingerprints from the existing source manifest. All nonempty DOCX paragraphs and table cells must appear in PDF extraction in order with repetition preserved. This content check supplements Office provenance and all-page visual review; it does not certify page geometry.

`b_visual_qa.json` includes `source_docx` and `rendered_pdf` SHA-256/size records, `reviewer`, ISO `reviewed_at`, renderer, existing all-page defect flags, and each page's reviewed PNG `image` SHA-256/size. These hashes invalidate visual signatures when their source or reviewed image changes. Keep the signed minimal QA JSON; render PDFs, PNGs and duplicate DOCX copies can be cleaned after promotion.

Generate the academic report with `validate_deep_reading_package.py --contract-version 1.5.0 --manifest <workflow_manifest> ...`. Promote with `export_b_pdf.py --workspace-root <data-root> --manifest <workflow_manifest> --b-path <B.docx> --academic-report <report.json> --rendered-pdf <Office.pdf> --output <handoff/B.pdf> --report <export.json>`. Export refuses stale bytes or another same-named file; the copied PDF must match the reviewed render. Export does not write Zotero.

Archive validation binds manifest B DOCX/PDF/report, current source versions and the Zotero B attachment's local/actual file fingerprints. The archived PDF can satisfy the signed render content after rendering caches are cleaned. Paths relative to `work/...` resolve from an explicit data root; the source manifest's source paths resolve from its own directory. Outside absolute artifacts require `--allow-external-root`; traversal, missing files and symlink escapes fail clearly. v1.4.x reports keep their old rules. Deliberately upgrading old B requires a new render/review/report and preserved historical records.
