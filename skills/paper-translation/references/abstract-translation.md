# Abstract Translation

The Abstract has the highest translation priority because it is reused verbatim in A/B/C.

## Three-pass workflow

1. **Pass 1 — semantic fidelity**: translate sentence by sentence while preserving the original logical structure, scope, qualifiers, direction and causal strength.
2. **Pass 2 — terminology and register**: apply the paper-specific terminology sheet and professional Chinese academic register without changing meaning.
3. **Pass 3 — alignment check**: align source and Chinese sentences/clauses and verify that nothing was omitted, added, strengthened or weakened.

Explicitly verify when present:

- background/problem;
- objective/research question;
- sample and N;
- measures/methods;
- analysis;
- result direction and significance;
- effect size / CI / p / ICC / agreement statistic;
- conclusion;
- uncertainty and causal language.

## Canonical Abstract

Write exactly one approved Chinese version to `<data-root>/work/<paper_id>/canonical_abstract.md`.

A, B and C must reuse this version exactly rather than independently retranslate or paraphrase it. Later changes require an explicit update to the canonical file and downstream `needs_update` routing.

## Scientific-strength preservation

Examples of strength that must not drift:

- `associated with` / `correlated with` must not become causal language;
- mediation does not automatically become a proven mechanism;
- `may`, `might`, `suggest`, `possible`, `cannot rule out` must retain uncertainty;
- non-significant findings must not disappear;
- author overclaiming, if present, is translated faithfully and critiqued later in Deep Reading rather than silently corrected here.
