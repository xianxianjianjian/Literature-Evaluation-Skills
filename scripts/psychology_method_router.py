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
    "qualitative",
    "mixed_methods",
}
KNOWN_MODALITIES = {"mri", "fmri"}
KNOWN_ANALYSES = {"mediation", "sem"}


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
    if designs & {"observational", "cross_sectional", "longitudinal"}:
        add("STROBE", "observational study reporting prompts")
    if modalities & {"mri", "fmri"}:
        add("COBIDAS-MRI", "MRI/fMRI acquisition, processing and modeling")
    if analyses & {"mediation", "sem"}:
        add("MEDIATION-SEM-TEMPORALITY", "mediation/SEM temporal and alternative-model audit")

    warnings: list[str] = []
    if "cross_sectional" in designs and analyses & {"mediation", "sem"}:
        warnings.append(
            "Cross-sectional mediation/SEM does not establish a longitudinal or causal mechanism."
        )
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

    return {
        "modules": modules,
        "warnings": warnings,
        "interpretation_requirements": interpretation_requirements,
        "scoring": "NONE",
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
