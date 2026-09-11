from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import audit_untranslated_residuals as residuals
import normalize_chinese_typography as typography


class ChineseTypographyTests(unittest.TestCase):
    def test_citation_semicolon_is_normalized_and_tokenized(self) -> None:
        tokens = typography.semantic_tokens("记忆获益[2; 3]。以及证据[12;15-18]")
        citations = [token.text for token in tokens if token.kind == "CITATION"]
        self.assertEqual(citations, ["2,3", "12,15–18"])

    def test_cjk_spacing_and_parentheses_are_normalized(self) -> None:
        value = typography.normalize_chinese_text("快速眼动睡眠 （ REM ） ， 支持 情绪 记忆 。")
        self.assertEqual(value, "快速眼动睡眠（REM），支持情绪记忆。")

    def test_cjk_latin_boundary_has_no_mechanical_spaces(self) -> None:
        value = typography.normalize_chinese_text("在 REM 中用 Bonferroni 校正，SWS 与 REM 相关。")
        self.assertEqual(value, "在REM中用Bonferroni校正，SWS与REM相关。")

    def test_units_percent_and_semantic_groups_remain_atomic(self) -> None:
        value = typography.normalize_chinese_text("记录 45min、400  Hz、63.9 % 和 SWS x REM")
        self.assertEqual(value, "记录 45 min、400 Hz、63.9% 和SWS×REM")
        groups = [(token.kind, token.text) for token in typography.semantic_tokens(value)]
        self.assertIn(("UNIT", "45 min"), groups)
        self.assertIn(("UNIT", "400 Hz"), groups)
        self.assertIn(("PROTECTED", "SWS×REM"), groups)

    def test_minus_and_scientific_exponent_are_preserved(self) -> None:
        value = typography.normalize_chinese_text("r = -0.15；p = 4 x 10^-4")
        self.assertIn("−0.15", value)
        self.assertIn("4 × 10−4", value)
        scientific = [token.text for token in typography.semantic_tokens(value) if token.kind in {"SCIENTIFIC", "STAT"} and "× 10" in token.text]
        self.assertEqual(scientific, ["p = 4 × 10−4"])

    def test_statistics_are_atomic_semantic_groups(self) -> None:
        tokens = typography.semantic_tokens("结果为β [ SE ] = −0.11 [0.05]，p = 4 × 10−4。")
        stats = [token.text for token in tokens if token.kind == "STAT"]
        self.assertIn("β[SE] = −0.11", stats)
        self.assertIn("p = 4 × 10−4", stats)

    def test_leading_decimal_p_value_is_atomic(self) -> None:
        tokens = typography.semantic_tokens("分别p = .36、p = .09。")
        stats = [token.text for token in tokens if token.kind == "STAT"]
        self.assertEqual(stats, ["p = .36", "p = .09"])

    def test_heading_break_is_a_hard_semantic_boundary(self) -> None:
        tokens = typography.semantic_tokens("结果\n\n在这里，我们展示结果。")
        self.assertEqual(sum(token.kind == "BREAK" for token in tokens), 2)

    def test_unicode_superscript_citation_becomes_semantic_citation(self) -> None:
        tokens = typography.semantic_tokens("记忆获益³³˒³⁴。")
        citations = [token.text for token in tokens if token.kind == "CITATION"]
        self.assertEqual(citations, ["33,34"])

    def test_plain_chinese_inline_citation_uses_source_group(self) -> None:
        value = typography.normalize_inline_citations(
            "参与者出现记忆受损46。声音持续1秒。",
            "participants showed memory impairment46. The sound lasted 1-s.",
        )
        self.assertEqual(value, "参与者出现记忆受损[46]。声音持续1秒。")

    def test_table_number_is_not_a_citation(self) -> None:
        self.assertEqual(typography.normalize_chinese_text("见补充表 [1]。"), "见补充表1。")


class ResidualAuditTests(unittest.TestCase):
    def test_four_unapproved_english_words_fail(self) -> None:
        failures = residuals._latin_failures(
            "Emotional charge of memories allows better remembering", {"rem", "nrem"}
        )
        self.assertEqual(len(failures), 1)

    def test_whitelisted_acronyms_do_not_fail(self) -> None:
        failures = residuals._latin_failures("REM NREM SWS TMR", {"rem", "nrem", "sws", "tmr"})
        self.assertEqual(failures, [])

    def test_source_matched_four_word_run_fails(self) -> None:
        failures = residuals._shared_source_runs(
            "Emotional charge of memories allows better remembering",
            "Emotional charge of memories allows better remembering including context",
            set(),
        )
        self.assertTrue(failures)

    def test_chinese_ocr_gibberish_not_in_source_does_not_fail(self) -> None:
        failures = residuals._shared_source_runs(
            "HEARS Re ER oR BB TB IZ", "Both slow wave and rapid eye movement sleep", set()
        )
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
