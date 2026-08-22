# Full Research Audit

Deep Reading begins with a source audit before interpretation. The audit is not a generic paper-quality score; it is a traceable check of identity, source completeness, internal consistency, and the evidence package required to support later claims.

## Three audit levels

### 1. Search Intake Audit

Usually inherited from Search when available. Confirm:

- title, authors, journal, DOI, publication year and online date;
- Version of Record / accepted manuscript / preprint identity;
- correction, erratum, retraction, or Expression of Concern status;
- whether Main Article, SI, data, code, protocol, or preregistration are known to exist.

Do not rewrite historical Search decisions after Deep Reading. If later evidence changes the assessment, record a post-reading assessment or `needs_update` reason.

### 2. Translation Intake Audit

When Translation artifacts exist, verify source coverage relevant to reading:

- page and section inventory;
- tables and figures;
- supplementary files;
- unreadable or missing source regions;
- known Translation Issues (`TRI-xxx`).

A is useful for language consistency, but it is not the evidentiary authority for Deep Reading. Academic claims must return to Main/SI or checked external evidence.

### 3. Deep Reading Full Research Audit

This is mandatory for B. Build a `Source Package Manifest` containing all discoverable scientific sources:

- `SRC-M1` Main Article;
- `SRC-S1...` Supporting Information;
- supplementary methods/results/tables/figures;
- correction/erratum notices;
- protocol / preregistration;
- code / analysis repository;
- data availability statement and accessible dataset metadata;
- related official appendix or repository material when directly part of the study package.

Record SI status as:

- `COMPLETE`
- `PARTIAL`
- `MISSING`
- `N/A`

## Publication identity

Never silently mix versions. Prefer the Version of Record for citation and page/figure identity. If content is inspected from another official version, record the exact version and material differences that may affect interpretation.

If title, DOI, author list, year, tables, figures, or reported results conflict across versions, create an `AUD-xxx` entry and mark downstream artifacts `needs_update` when necessary.

## Paper Structure Inventory

Before applying the notebook schema, inventory the paper as it actually exists:

- Abstract and highlights/key points;
- Introduction/theory sections;
- Methods subsections;
- Results subsections;
- Discussion/conclusion;
- every table and figure;
- every SI item;
- preregistration/open-science material;
- unusual sections such as validation studies, sensitivity analyses, robustness checks, secondary datasets, pilot studies, or multi-study appendices.

This inventory drives Dynamic Coverage. Do not force important scientific content into an unrelated template heading simply because the Base Schema lacks a dedicated section.

## Evidence and source anchors

For every important notebook claim, preserve two independent attributes:

1. evidence class from `shared/evidence-policy.md`;
2. source anchor.

Examples:

- `【原文直接内容｜Methods 2.4, p.5；Table 2】`
- `【作者解释｜Discussion 4.1, p.10】`
- `【评译者分析｜AUD-003】`
- `【外部依据 EXT-012】`

Useful anchors include Section/Subsection/Page/Table/Figure/Supplementary Table/Supplementary Figure/Appendix.

## Source-gap vocabulary

Use only distinctions that match the evidence state:

- `【原文未报告】`: Main + available SI were checked and the information is absent.
- `【补充材料待核验】`: the paper points to SI, but that SI is currently unavailable.
- `【当前资料未找到】`: not found in the current package, but absence has not been established.
- `【报告不明确】`: information exists but is not sufficiently clear or reproducible.
- `【原文内部不一致】`: two source locations conflict.
- `【无法判断】`: current evidence cannot support a defensible judgment.

Never replace any of these with a plausible value from common practice.

## Internal consistency matrix

At minimum check:

- Abstract ↔ Results;
- Introduction claims/hypotheses ↔ stated study aims;
- Methods analysis plan ↔ Results analyses;
- Main ↔ SI;
- text ↔ tables;
- text ↔ figures;
- participant flow ↔ final/model-specific N;
- reported statistical method ↔ statistic notation;
- statistic/df ↔ p where enough information is available;
- effect estimate ↔ confidence interval;
- correction method ↔ significance claim;
- table/figure labels ↔ narrative direction.

### Mandatory statistical consistency recalculation

When enough source information is reported to reproduce a consistency check, perform it. Examples include simple p/statistic/df consistency, CI/estimate relationships, percentages from counts, or sample-flow arithmetic.

Rules:

- preserve the author's original reported value;
- record the verification result separately;
- never silently replace the paper's number with a recalculated number;
- link discrepancies to `AUD-xxx`.

## Figure/table visual inspection

Do not audit tables/figures from captions alone. Visually inspect each scientifically important table and figure when available, including SI figures/tables. Check labels, units, group/sample identifiers, direction, correction annotations, and whether the narrative accurately describes the displayed result.

## Audit severity

Use:

- `A0`: no obvious issue found in the checked material;
- `A1`: minor reporting/clarity issue unlikely to change interpretation;
- `A2`: issue may materially affect interpretation, reproducibility, or transfer;
- `A3`: issue may affect a core conclusion or the defensibility of the study's main inference.

Severity is evidence-specific. Do not describe `A0` as proof that the study or data are true.

Every `A3` must appear prominently in B and in C when it affects the weekly evaluation.

## Readiness and completeness

Use two separate concepts:

### Readiness for Deep Reading

- `READY`
- `READY_WITH_GAPS`
- `BLOCKED`

### Final archive completeness

- `COMPLETE`
- `PROVISIONAL`

A paper may be readable with gaps but still remain `PROVISIONAL` because consequential SI, source identity, or attachment verification is missing.

## Audit artifacts

Maintain when the working environment supports them:

- `<data-root>/work/<paper_id>/audit_log.jsonl`
- `<data-root>/work/<paper_id>/claim_evidence_map.csv`

Suggested audit log fields:

- `audit_id`
- `severity`
- `category`
- `source_anchor`
- `reported_value_or_claim`
- `verification`
- `impact`
- `status`

Do not use the audit log to store unsupported criticism. Every issue must point to inspectable source evidence or an explicitly labeled external check.
