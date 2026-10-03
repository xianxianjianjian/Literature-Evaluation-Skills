# Terminology Policy

Professional terminology must be controlled by evidence and context. Ordinary language does not require source-by-source verification, but important terms in psychology, neuroscience, sleep medicine, statistics, experimental paradigms, instruments and core constructs do.

## Context-aware identity

Match or create terminology records using the combination of:

- `English_Term`;
- `Domain`;
- `Subdomain`;
- conceptual meaning/definition;
- current paper context.

The same English term may legitimately have multiple `TERM-xxxx` records when discipline, subfield or conceptual context differs. Do not force one global Chinese equivalent.

Supported starting domains include General, Cognitive, Social, Developmental, Clinical and Health Psychology; Neuropsychology; Cognitive Neuroscience; Sleep Psychology / Sleep Medicine; Emotion; Memory; Learning; Attention; Perception; Psychometrics; Experimental Psychology; Statistics / Research Methods; Neuroimaging; and EEG / ERP / PSG. These values are extensible. They guide matching and do not form a closed enum.

The shared `terminology_registry.csv` is a cross-paper professional database. Its current schema records `Domain`, `Subdomain`, `Definition`, `Context`, `Operational_Use`, source type/citation, evidence IDs and level, paper IDs, first/last use, usage count, status and notes. Older Discipline/Subfield registries remain readable and are upgraded on the next explicit write.

## Decision order

Before writing A, B or C:

1. extract candidate professional terms;
2. query the shared registry;
3. compare Domain, Subdomain, definition and current context;
4. reuse one exact, high-confidence, evidence-linked match;
5. when multiple candidates remain, decide from Context rather than spelling;
6. when no reliable match remains, verify against an appropriate external terminology source;
7. record the paper-specific choice and update the shared registry after completion.

Never use a direct word-level replacement as the decision rule. In particular, `dynamics`, `recruitment`, `engagement`, `representation` and `processing` require construct and method context. For example, behavioral change over sleep cycles may use “时间动态/时间演变”, while millisecond neural-system evolution may justify “时间动力学”.

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

After one paper closes, run the registry usage update once per TERM ID and Paper ID. This increments `Usage_Count`, updates `Last_Used`, and preserves the accumulated Paper IDs. A later higher-level source may update evidence without replacing wording; a preferred-wording correction additionally appends a `TERM_CORRECTION` event to `terminology_corrections.jsonl`, retaining the old preferred wording as an alternative.

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

Choose terms by scientific meaning and natural Chinese usage as well as literal correspondence. For example, `temporal dynamics` may mean 时间动态、动态变化、时间演变 or 时间动力学 according to context; never apply a global `dynamics → 动力学` replacement. Record a paper-specific choice and context note when alternatives are plausible.

Translation priority is scientific meaning, professional terminology, causal strength, statistical direction, natural Chinese, then literal form. Preserve distinctions such as `associated with ≠ 导致`, `correlated with ≠ 影响`, `predict ≠ 因果预测`, `suggest ≠ 证明`, and `mediate ≠ 已证实机制`.
