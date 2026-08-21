# Journal Mapping

Journal Mapping is a topic-specific source-prioritization step. It helps Search decide where to look first, but it must never be treated as proof that an individual paper is valid.

## Build a topic-specific map

When useful, build a pool of roughly 5–10 journals and classify them as:

- **Core**: highly relevant to the confirmed topic and recognized within the field;
- **Recommended**: credible journals that regularly publish relevant work;
- **Supplementary**: adjacent, interdisciplinary, methods, or measurement journals that may contain important studies missed by the core set.

The map should be generated from the confirmed topic, not from a permanently fixed prestige list.

## Journal assessment dimensions

Consider, when discoverable:

- fit to the confirmed topic and subfield;
- peer-review status;
- field role and audience;
- publisher, society, or institutional reputation;
- indexing and discoverability;
- reporting and transparency norms;
- frequency of relevant empirical work;
- known integrity or editorial concerns;
- methodological or cross-disciplinary transfer value.

Impact factor or other citation metrics may be contextual information, but must not be used as a single proxy for research quality or paper validity. Do not permanently store rapidly changing impact-factor values in the registry unless the project later adds a separately maintained source for them.

## Registry

Stable observations may be recorded in `knowledge/journal_registry.csv` with status:

- `ACTIVE`;
- `CAUTION`;
- `DO_NOT_PRIORITIZE`.

Reverify old observations when they materially affect a current decision. Registry entries are aids to routing, not automatic inclusion/exclusion rules.

## Output in `search_record.md`

Record:

- journals considered;
- classification as Core / Recommended / Supplementary;
- why each journal is relevant;
- any caution;
- whether it was actually searched or only mapped;
- date of the check.

Journal Mapping should complement broad/index/citation database searching rather than replace it.