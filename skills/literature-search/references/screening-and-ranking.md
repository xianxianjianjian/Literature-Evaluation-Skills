# Screening and Ranking

Screening proceeds in two rounds. Weighted scoring supports judgment but never overrides a failed quality or integrity gate.

## Round 1 — broad screening

After obvious deduplication, a flexible weekly target is roughly 15–30 records, narrowed to about 6–10 for detailed screening. These are targets, not quotas.

Use title, abstract, journal, year, study type, population/context, focal construct, method/measurement, outcome/relation, and likely source completeness.

Allowed decisions:

- `INCLUDE`;
- `MAYBE`;
- `EXCLUDE`.

Use standardized exclusion codes:

- `EX-01` Topic mismatch
- `EX-02` Wrong population/context
- `EX-03` Wrong method/paradigm/measurement
- `EX-04` Wrong outcome/relation
- `EX-05` Wrong study type
- `EX-06` Review only when a focal empirical study is required
- `EX-07` Conference/abstract-only record
- `EX-08` Insufficient information for meaningful screening
- `EX-09` Duplicate
- `EX-10` Superseded/non-preferred version
- `EX-11` Integrity concern
- `EX-12` Full text unavailable for the intended focal use
- `EX-13` Other — must include a free-text reason

Do not manufacture exclusion codes beyond this set without changing the shared identifier policy.

## Round 2 — detailed screening

Round 2 candidates should receive source/identity checks, integrity checks, design and reporting review, method-transfer review, and weighted evaluation.

### Quality Gate comes first

Assign one gate before calculating or using the weighted score:

- `GREEN`: no obvious major relevance, identity, integrity, design, or source-completeness problem found in current checks;
- `AMBER`: potentially useful, but one or more meaningful caveats must be disclosed and may limit focal use;
- `RED`: normally unsuitable as the Primary focal paper because of major identity/integrity failure, severe relevance mismatch, or a core reporting/design problem that prevents defensible interpretation.

A `RED` paper **cannot win through a high weighted score**. If retained at all, its role must be explicitly limited, for example as a cautionary, historical, or integrity-related example.

### Seven-dimension weighted score

Use the following fixed V1 weights:

| Dimension | Weight |
| --- | ---: |
| Direct topical relevance | 25 |
| Research/design/evidence quality | 20 |
| Journal/source reliability | 15 |
| Method transfer value | 15 |
| Transfer value to current research | 10 |
| Novelty/current contribution | 10 |
| Full text/SI completeness | 5 |

A convenient implementation is to rate each dimension 0–5 and normalize to 100, but the raw component ratings and rationale must remain inspectable. Do not hide an academic judgment inside a single total score.

### Method Transfer Checklist

When method transfer matters, explicitly inspect:

- sample/recruitment design;
- study architecture and timing;
- task/paradigm structure;
- measurement/tool choice;
- acquisition settings;
- preprocessing and QC;
- indicators/features/outcomes;
- statistical model and correction strategy;
- visualization/reporting practices;
- reproducibility details and availability of SI/code/data.

Classify useful method elements as:

- `DIRECTLY_REUSABLE`;
- `REUSABLE_WITH_MODIFICATION`;
- `NOT_RECOMMENDED`;
- `CANNOT_DETERMINE`.

At Search stage this is a screening-level judgment, not a substitute for the later Deep Reading methods audit.

## Final recommendation set

Present:

- one `Primary` recommendation;
- normally about two `Strong Alternatives` when available;
- useful `FOUNDATIONAL` / `BACKGROUND_REVIEW` sources separately.

For every final candidate report:

- literature role;
- Quality Gate;
- seven-dimension component scores and total;
- main strength;
- main caveat;
- source/SI availability;
- method-transfer value;
- current-research transfer value;
- integrity-check summary.

The final explanation must answer both:

1. why the Primary is worth reading;
2. **why the Primary is ranked above the strongest alternative**, rather than merely describing each paper independently.

The user makes the final paper decision. Do not auto-advance from ranking to focal-paper confirmation.