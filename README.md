# Literature Evaluation Plugin

A research-oriented workflow framework for **literature search → full-text translation → systematic deep reading → weekly evaluation submission**.

> Current stable release: **v1.4.2**
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

- **A**: Chinese full-text mirror PDF.
- **B**: Complete research reading document.
- **C**: Weekly literature evaluation submission draft.

## Validation

v1.4.2 includes:

- FULL_MIRROR validation.
- Main/SI source package management.
- A/B/C archive workflow.
- Automated structural and regression validation.

## Release History

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
