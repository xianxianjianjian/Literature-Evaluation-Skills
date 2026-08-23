# Full-text Translation

Translate the focal source package with stable, auditable Translation Units. The objective is 100% accountable scientific-content coverage, not free-form rewriting.

## Translation Units

Define units by:

`Source ID + Page + Section/Subsection + Paragraph order`

Example:

`SRC-M1 | p.4 | Methods 2.2 | P03`

Track them in `<data-root>/work/<paper_id>/translation_ledger.jsonl` so coverage can be checked and missing units cannot disappear silently.

Each ledger record must include:

- `unit_id`, source ID and fixed-render source page;
- section/subsection, scientific-content kind and positive unit index;
- source status and translation status (`TRANSLATED` or `SOURCE_GAP`);
- one or more output pages for translated units;
- issue IDs when present.

Build `source_inventory.json` first and require the ledger to cover exactly its translation units. See [`translation-evidence-contract.md`](translation-evidence-contract.md). A ledger produced from `doc.paragraphs` alone is invalid when the source also contains drawings, tables or floating objects.

## Coverage

Translate all scientifically relevant content, including when present:

- title;
- abstract and keywords;
- headings;
- body text;
- equations/explanatory text;
- table/figure captions and notes;
- acknowledgements;
- funding;
- conflicts of interest;
- data/code availability;
- author contributions;
- Supporting Information scientific text.

References normally remain in the original language. Author names, journal names, DOI, formulas, code/variable identifiers and standard software names are preserved unless an established Chinese presentation is genuinely useful and does not create ambiguity.

## Section-specific rules

### Methods

Translate only operations, parameters and decisions actually reported. Do not fill missing software versions, thresholds, preprocessing steps or analysis defaults from common practice.

### Results

Preserve:

- positive / negative;
- higher / lower;
- increase / decrease;
- significant / non-significant;
- corrected / uncorrected;
- confirmatory / exploratory / post hoc distinctions;
- every numerical value and statistical token.

### Discussion

Preserve modal distance and uncertainty, including language such as `may`, `might`, `suggest`, `speculate`, `possible`, `cannot rule out`, and explicit limitations.

## Source extraction fallback

Use the most reliable source available, in this order:

1. native PDF text layer / publisher full text;
2. direct visual inspection of the source page;
3. another authoritative official version when version differences are recorded;
4. OCR only as a last resort.

If a passage remains unreliable, do not guess. Use an explicit source-gap label such as:

- `【原文未报告】`;
- `【补充材料待核验】`;
- `【当前资料未找到】`;
- `【报告不明确】`;
- `【原文内部不一致】`;
- `【无法判断】`.

## Translation issues

Translation-specific issues use `TRI-xxx` and belong in `<data-root>/work/<paper_id>/translation_issues.jsonl`. They are distinct from research-audit issues `AUD-xxx`.

Examples include unreadable source text, uncertain table alignment, ambiguous abbreviation expansion, version wording differences, or a layout-induced continuation decision.
