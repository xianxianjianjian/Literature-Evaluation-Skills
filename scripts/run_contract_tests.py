"""Run an explicit unittest suite and fail mandatory CI tests on any skip."""
from __future__ import annotations

import argparse
import json
import sys
import unittest
from pathlib import Path

MANDATORY_SIMSUN = (
    "tests.test_v150_contracts.ATextLayerTests.test_two_column_source_english_is_removed_before_chinese_overlay",
    "tests.test_v150_contracts.ArchiveTests.test_b_pdf_promotes_only_validated_independent_render",
    "tests.test_v150_terminology_layout.ParagraphStyleEngineTests.test_exact_mirror_applies_style_only_when_geometry_fits",
)


def run_suite(suite: unittest.TestSuite, *, allow_skips: bool = False) -> tuple[bool, dict]:
    expected = suite.countTestCases()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {"expected": expected, "run": result.testsRun,
               "passed": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
               "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped)}
    print(json.dumps(summary, sort_keys=True))
    return (expected > 0 and result.testsRun == expected and result.wasSuccessful() and (allow_skips or not result.skipped)), summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="*")
    parser.add_argument("--mandatory-simsun", action="store_true")
    parser.add_argument("--discover", action="store_true")
    parser.add_argument("--allow-skips", action="store_true")
    args = parser.parse_args(argv)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    if args.mandatory_simsun:
        if not Path(r"C:\Windows\Fonts\simsun.ttc").is_file():
            parser.error("mandatory real Windows SimSun font missing")
        import pymupdf, pypdf, reportlab, docx  # noqa: F401 - required runtime preflight
        if args.allow_skips:
            parser.error("mandatory SimSun suite must have skipped=0")
    names = [*(MANDATORY_SIMSUN if args.mandatory_simsun else ()), *args.names]
    suite = unittest.defaultTestLoader.discover("tests") if args.discover else unittest.defaultTestLoader.loadTestsFromNames(names)
    passed, _ = run_suite(suite, allow_skips=args.allow_skips)
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
