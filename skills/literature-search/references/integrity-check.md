# Integrity Check

Integrity checking in Search is an intake and selection safeguard. It cannot prove that a study is true, authentic, or free of undiscovered problems.

## Layer 1 — Search Intake Audit

For records that survive broad screening, verify when discoverable:

- title, authors, journal, year, DOI;
- publication/version status;
- Version of Record versus accepted manuscript/preprint;
- Main Article availability;
- Supplement/SI existence and availability;
- correction/erratum notices;
- retraction or Expression of Concern notices.

Identity or version conflicts must be resolved before a record can be treated as a clean focal candidate.

## Layer 2 — Final-candidate integrity review

For Round 2 candidates, especially the Primary and Strong Alternatives, check when discoverable:

- retraction;
- Expression of Concern;
- correction/erratum;
- Version of Record and DOI identity;
- supplementary information and whether expected SI is missing;
- data availability;
- code availability;
- preregistration/registration when methodologically relevant;
- conflict-of-interest/funding reporting;
- obvious internal reporting gaps that materially affect screening-level interpretability.

A candidate need not have open data/code/preregistration to be valid; absence is recorded as a transparency/completeness fact, not automatically as misconduct.

## Quality Gate relationship

Integrity findings feed the Search Quality Gate:

- `GREEN`: current checks found no obvious major integrity/identity/completeness warning;
- `AMBER`: usable but meaningful caveats require disclosure;
- `RED`: normally unsuitable as a core focal paper, such as a retracted paper, unresolved identity/version conflict, or severe core-reporting problem.

A `RED` candidate cannot be rescued by its weighted score.

Do not confuse this Search Quality Gate with later Deep Reading audit severity (`A0`–`A3`). Search gate labels help selection; Deep Reading audit codes evaluate specific paper-level issues after full reading.

## Required wording discipline

Never write:

- “the data are proven authentic”;
- “the paper has no integrity problems”;
- “the study is verified true”.

Preferred wording is bounded, for example:

> Current checks found no obvious integrity concern in the sources reviewed.

If a database, publisher notice page, SI location, or other expected source could not be checked, state that limitation explicitly.

## Post-reading separation

Do not retroactively rewrite the original Search gate when Deep Reading later discovers a new issue. Preserve the Search-time decision record and add a separate `post_reading_assessment` or workflow `needs_update` reason so the chronology remains auditable.