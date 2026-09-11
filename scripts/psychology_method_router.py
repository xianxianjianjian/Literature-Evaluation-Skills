#!/usr/bin/env python3
"""Select applicable psychology-method reading modules without scoring a paper."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

KNOWN_DESIGNS = {
    "experimental",
    "randomized_intervention",
    "observational",
    "cross_sectional",
    "longitudinal",
    "repeated_measures",
    "intervention",
    "animal",
    "database",
    "qualitative",
    "mixed_methods",
}
KNOWN_MODALITIES = {"eeg", "psg", "meg", "mri", "fmri", "behavioral"}
KNOWN_ANALYSES = {"mediation", "sem", "graph_network", "machine_learning"}


class MethodRoutingError(ValueError):
    """Raised when a study profile is invalid."""


def _tokens(profile: dict[str, Any], field: str) -> set[str]:
    values = profile.get(field, [])
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise MethodRoutingError(f"{field} must be a list of strings")
    return {value.strip().casefold() for value in values if value.strip()}


def select_modules(profile: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(profile, dict):
        raise MethodRoutingError("study profile must be an object")
    designs = _tokens(profile, "designs")
    modalities = _tokens(profile, "modalities")
    analyses = _tokens(profile, "analyses")
    unknown = (designs - KNOWN_DESIGNS) | (modalities - KNOWN_MODALITIES) | (analyses - KNOWN_ANALYSES)
    if unknown:
        raise MethodRoutingError(f"unknown profile values: {', '.join(sorted(unknown))}")
    if not designs:
        raise MethodRoutingError("at least one design is required")

    modules: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(module_id: str, reason: str) -> None:
        if module_id not in seen:
            modules.append({"module_id": module_id, "reason": reason})
            seen.add(module_id)

    quantitative = bool(
        designs
        & {
            "experimental",
            "randomized_intervention",
            "observational",
            "cross_sectional",
            "longitudinal",
            "repeated_measures",
            "intervention",
            "animal",
            "database",
        }
    )
    if quantitative:
        add("APA-JARS-QUANT", "quantitative psychology reporting prompts")
    if "qualitative" in designs:
        add("APA-JARS-QUAL", "qualitative psychology design")
    if "mixed_methods" in designs:
        add("APA-MMARS", "mixed-methods integration")
        add("APA-JARS-QUAL", "mixed-methods qualitative component")
        add("APA-JARS-QUANT", "mixed-methods quantitative component")
    if "randomized_intervention" in designs:
        add("CONSORT-SPI", "randomized social or psychological intervention")
    if "intervention" in designs:
        add("INTERVENTION-FIDELITY", "non-randomized intervention, adherence and contamination")
    if designs & {"observational", "cross_sectional", "longitudinal"}:
        add("STROBE", "observational study reporting prompts")
    if modalities & {"mri", "fmri"}:
        add("COBIDAS-MRI", "MRI/fMRI acquisition, processing and modeling")
    if modalities & {"eeg", "psg"}:
        add("EEG-PSG", "electrode montage, referencing, sleep staging, artifact handling and event physiology")
    if "meg" in modalities:
        add("MEG", "sensor/head-position handling, source model and leakage control")
    if analyses & {"mediation", "sem"}:
        add("MEDIATION-SEM-TEMPORALITY", "mediation/SEM temporal and alternative-model audit")
    if "graph_network" in analyses:
        add("GRAPH-NETWORK", "node/edge definition, thresholding, null model and multiplicity")
    if "machine_learning" in analyses:
        add("MACHINE-LEARNING", "leakage-safe splits, nested validation, calibration and external generalization")
    if "repeated_measures" in designs:
        add("REPEATED-MEASURES", "within-person dependency, order, carryover and missing visits")
    if "longitudinal" in designs:
        add("LONGITUDINAL", "time metric, attrition, within/between-person effects and temporal ordering")
    if "animal" in designs:
        add("ARRIVE", "animal model, randomization/blinding, exclusions and translational boundary")
    if "database" in designs:
        add("DATABASE-PROVENANCE", "cohort construction, coding provenance, missingness and dataset shift")

    warnings: list[str] = []
    if "cross_sectional" in designs and analyses & {"mediation", "sem"}:
        warnings.append(
            "Cross-sectional mediation/SEM does not establish a longitudinal or causal mechanism."
        )
    if modalities & {"eeg", "psg"} and not profile.get("event_definitions"):
        warnings.append("EEG/PSG profile should state scoring and event-definition authorities.")
    if "machine_learning" in analyses and not profile.get("validation_strategy"):
        warnings.append("Machine-learning profile should state validation and test-set separation.")
    interpretation_requirements: list[str] = []
    if quantitative or "mixed_methods" in designs:
        interpretation_requirements.extend(
            [
                "analysis-specific N",
                "estimate and direction",
                "uncertainty interval",
                "effect size and scientific meaning",
                "exact p value when reported",
                "multiplicity status",
                "sample-size justification",
            ]
        )
    if designs & {"qualitative", "mixed_methods"}:
        interpretation_requirements.extend(
            [
                "claim-to-excerpt or observation traceability",
                "evidence adequacy and negative cases",
                "researcher-position and analytic-process context",
            ]
        )
    if "mixed_methods" in designs:
        interpretation_requirements.append("integration-point and joint-inference consistency")
    if modalities & {"eeg", "psg", "meg"}:
        interpretation_requirements.extend(
            ["channel/sensor and reference definition", "artifact/exclusion denominator", "time-frequency or event window"]
        )
    if modalities & {"mri", "fmri"}:
        interpretation_requirements.extend(
            ["contrast and analysis-specific N", "space/smoothing/threshold", "ROI or whole-brain multiplicity"]
        )
    if analyses & {"mediation", "sem"}:
        interpretation_requirements.extend(
            ["temporal order", "direct/indirect/total effects", "alternative-model sensitivity"]
        )
    if "machine_learning" in analyses:
        interpretation_requirements.extend(
            ["train/validation/test separation", "performance uncertainty", "calibration and external validity"]
        )

    return {
        "modules": modules,
        "warnings": warnings,
        "interpretation_requirements": interpretation_requirements,
        "scoring": "NONE",
        "profile": {
            "designs": sorted(designs),
            "modalities": sorted(modalities),
            "analyses": sorted(analyses),
        },
        "note": "Reporting completeness and validity judgments must remain separate.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        profile = json.loads(args.profile.read_text(encoding="utf-8-sig"))
        result = select_modules(profile)
    except (OSError, json.JSONDecodeError, MethodRoutingError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
