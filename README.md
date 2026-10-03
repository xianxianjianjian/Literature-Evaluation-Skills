# Literature Evaluation Plugin

A research-oriented workflow framework for **literature search → full-text translation → systematic deep reading → weekly evaluation submission**.

> Current development version: **v1.5.0**
>
> Validated with:
> - Python 3.11 CI
> - Python 3.12 CI
> - Windows SimSun production gate
> - Full workflow regression tests

## Overview

Literature-Evaluation-Skills focuses on reproducible and evidence-traceable literature workflows rather than simple summaries.

Core principles:

- Conclusions remain traceable to original sources.
- Author interpretation and evaluator analysis are separated.
- Main article and Supporting Information are handled together.
- Translation, methods, results and discussion each have explicit quality rules.

## Four Skill Architecture

```text
weekly-literature-evaluation
        |
        |-- literature-search
        |-- paper-translation
        `-- paper-deep-reading
```

- `weekly-literature-evaluation`: workflow routing, gates, state and recovery.
- `literature-search`: topic planning, retrieval, screening and source handoff.
- `paper-translation`: source verification, full translation and A mirror PDF.
- `paper-deep-reading`: research audit, methods/results reconstruction and critical evaluation.

## Quick Start

Install the plugin bundle and run the required Skill entry point.

Available entries:

- `literature-evaluation:weekly-literature-evaluation`
- `literature-evaluation:literature-search`
- `literature-evaluation:paper-translation`
- `literature-evaluation:paper-deep-reading`

For detailed installation and update workflow, see:

- [`docs/local-plugin-updates.md`](docs/local-plugin-updates.md)
- [`docs/architecture.md`](docs/architecture.md)
- [`docs/workflow-spec.md`](docs/workflow-spec.md)

## Deliverables

The workflow produces:

- **A**: Chinese full-text mirror PDF with a real selectable, copyable and searchable Chinese text layer.
- **B**: Complete DOCX research notes plus a validated PDF reading copy.
- **C**: 800–1000-character Chinese submission review, with a private Main-source map.

## Validation

v1.5.0 adds:

- FULL_MIRROR validation.
- Main/SI source package management.
- A/B/C archive workflow.
- Automated structural and regression validation.
- Zotero role titles `pdf / SI / A翻译 / B精读` and separate academic/archive gates.
- A cross-paper, evidence-linked psychology terminology database with Domain/Subdomain/Context matching, usage accumulation and correction history.
- Shared paragraph roles for Chinese body formatting, APA-oriented English/reference formatting, bilingual typography and Exact-Mirror layout exceptions.

## Release History

### v1.5.0 (development)

- Replace translated English text objects with selectable/searchable Chinese PDF text and reject stale English layers.
- Promote validated B DOCX renders to PDF for Zotero archive.
- Use an 800–1000-character C submission contract with Main-visible evidence and author-acknowledged limitations.
- Normalize Zotero attachment display titles while preserving original filenames and data SI.
- Reuse verified psychology terminology by context across papers and keep usage/correction history.
- Apply project Chinese body styling separately from APA-oriented English and reference formatting without weakening Exact Mirror geometry.

### v1.4.2

- Hardened translation mirror validation.
- Improved CI and Windows font testing.
- Added workflow documentation and archive rules.

### v1.3.0

- Introduced evidence-hardened exact mirror workflow.

### v1.1.0

- Introduced plugin packaging architecture.

## Documentation

Detailed specifications remain available under [`docs/`](docs/).
