# Terminology Policy

Professional terminology must be controlled by evidence and context. Ordinary language does not require source-by-source verification, but important terms in psychology, neuroscience, sleep medicine, statistics, experimental paradigms, instruments and core constructs do.

## Context-aware identity

Match or create terminology records using the combination of:

- `English_Term`;
- `Discipline`;
- `Subfield`;
- conceptual meaning/definition;
- current paper context.

The same English term may legitimately have multiple `TERM-xxxx` records when discipline, subfield or conceptual context differs. Do not force one global Chinese equivalent.

## Confidence and reuse

- `HIGH`: may be reused without a new search only when the current context matches the verified context.
- `MEDIUM`: perform a context check; reverify when ambiguity could affect meaning.
- `LOW`: reverify whenever encountered in substantive translation.

Confidence describes reuse confidence, not source type.

## TE1–TE7 evidence-source types

Use the frozen meanings from `shared/identifier-policy.md`:

- `TE1`: official standard, professional guideline, expert consensus or formal norm;
- `TE2`: validated/official Chinese scale, tool, test or localization literature;
- `TE3`: authoritative professional institution, society, hospital or research body;
- `TE4`: high-quality Chinese peer-reviewed/core-journal research;
- `TE5`: professional textbook, academic monograph or authoritative reference work;
- `TE6`: stable usage across multiple professional publications without a higher-level unified standard;
- `TE7`: no sufficiently unified Chinese translation identified; use conservative Chinese plus the English term and document uncertainty.

`TE` type and `Confidence` must be judged separately. A context-matched TE4 usage may still yield `HIGH` confidence.

## Evidence roles

Distinguish:

- **Translation Evidence**: supports how the English term should be rendered in Chinese;
- **Definition Evidence**: supports what the construct means;
- **Methodological Evidence**: supports how a measure, algorithm, statistic or procedure works.

One source may support more than one role, but the role must be explicit.

## Registry lifecycle

Allowed terminology statuses:

- `ACTIVE`;
- `CONTEXTUAL`;
- `DEPRECATED`.

Never silently overwrite an older preferred translation. Preserve alternatives, contexts, evidence IDs and verification history. Conflicting evidence should create a traceable update rather than erase the previous record.

## Paper-specific terminology sheet

Before full translation, create/update `paper_terminology.csv` for all terms that are important, ambiguous, newly verified or reused by context match. Record at least:

- English term;
- chosen Chinese term;
- TERM ID when available;
- context;
- confidence;
- evidence type/ID;
- whether the choice is inherited, newly verified or provisional.

The paper-specific sheet governs consistency within A/B/C for the focal paper.