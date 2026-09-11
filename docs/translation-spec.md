# Translation Specification

## Purpose

This document defines the translation workflow requirements for Literature-Evaluation-Skills.

The goal is not ordinary machine translation, but a traceable academic translation package with source alignment, terminology control, and quality validation.

## FULL_MIRROR Workflow

The default translation mode is `FULL_MIRROR`.

Validation dimensions:

- Geometry fidelity: preserve text frame positions and page structure.
- Content fidelity: preserve meaning, numbers, tables, figures, and scientific labels.
- Style fidelity: preserve typography, emphasis, colors, superscripts, and alignment.

## Translation Rules

- Main text and Supporting Information are treated as separate source packages.
- Important terminology follows the terminology registry.
- Figure labels remain unchanged when they represent scientific notation.
- Figure captions are translated according to source meaning.
- Unsupported interpretation must not be inserted into translation output.

## Output

Translation output produces:

- A: Chinese full-text mirror PDF.
- Validation report.
- Source archive records.

A completed translation requires both content verification and rendering validation.
