from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import audit_untranslated_residuals as residuals
import deep_reading_evidence as deep
import exact_mirror
import psychology_method_router as router
import source_package
import style_fidelity
import translation_integrity


def frame(role="BODY", **overrides):
    value = {
        "frame_id": "F1", "kind": "body", "role": role,
        "source_font": "Source", "source_font_size_pt": 10.0,
        "source_leading_pt": 12.0, "weight": "regular", "italic": False,
        "text_rgb": [0, 0, 0], "alignment": "left", "superscript": False,
        "first_line_indent_pt": 0.0, "paragraph_spacing_before_pt": 0.0,
        "paragraph_spacing_after_pt": 0.0, "baseline_offset_pt": 0.0,
        "translatable": role in exact_mirror.TRANSLATABLE_FRAME_ROLES,
        "preserve_english": role in exact_mirror.PRESERVE_ENGLISH_FRAME_ROLES,
    }
    value.update(overrides)
    return value


def rendered(value):
    value["rendered_style"] = {
        "font_family": "SimSun", "font_size_pt": 10.0, "leading_pt": 12.0,
        "weight": value["weight"], "italic": value["italic"],
        "color_rgb": value["text_rgb"], "alignment": value["alignment"],
        "superscript": value["superscript"],
        "first_line_indent_pt": value["first_line_indent_pt"],
        "paragraph_spacing_before_pt": value["paragraph_spacing_before_pt"],
        "paragraph_spacing_after_pt": value["paragraph_spacing_after_pt"],
        "baseline_offset_pt": value["baseline_offset_pt"],
        "style_runs": value.get("style_runs", []),
    }
    return value


class ResidualRoleContractTests(unittest.TestCase):
    def test_01_single_source_word_fails(self):
        self.assertTrue(residuals._shared_source_runs("memory", "emotional memory", set(), minimum_words=1))

    def test_02_two_source_words_fail(self):
        self.assertTrue(residuals._shared_source_runs("emotional memory", "emotional memory", set(), minimum_words=1))

    def test_03_non_source_gibberish_passes(self):
        self.assertFalse(residuals._shared_source_runs("xyzzy", "emotional memory", set(), minimum_words=1))

    def test_04_approved_term_passes(self):
        self.assertFalse(residuals._shared_source_runs("REM", "REM sleep", {"rem"}, minimum_words=1))

    def test_04b_approved_group_and_statistic_tokens_pass(self):
        self.assertFalse(residuals._shared_source_runs("E-Wake AError", "E-Wake %AError", {"e-wake", "aerror"}, minimum_words=1))

    def test_05_body_is_translatable(self):
        self.assertTrue(exact_mirror.role_is_translatable("BODY"))

    def test_06_caption_is_translatable(self):
        self.assertTrue(exact_mirror.role_is_translatable("CAPTION"))

    def test_07_figure_internal_preserves_english(self):
        self.assertIn("FIGURE_INTERNAL", exact_mirror.PRESERVE_ENGLISH_FRAME_ROLES)

    def test_08_reference_preserves_english(self):
        self.assertFalse(exact_mirror.role_is_translatable("REFERENCE"))


class StyleContractTests(unittest.TestCase):
    def test_01_default_map_covers_roles(self):
        mapping = style_fidelity.default_style_map([frame()])
        self.assertIn("BODY", mapping["roles"])

    def test_02_body_render_passes(self):
        rows = [rendered(frame())]
        self.assertTrue(style_fidelity.validate_rendered_styles(rows, style_fidelity.default_style_map(rows))["passed"])

    def test_03_heading_body_distinct_hierarchy(self):
        rows = [rendered(frame()), rendered(frame("H1", frame_id="F2", kind="heading", source_font_size_pt=15.0))]
        self.assertTrue(style_fidelity.validate_style_map(style_fidelity.default_style_map(rows), rows))

    def test_04_color_mismatch_fails(self):
        row = rendered(frame(text_rgb=[20, 30, 40]))
        row["rendered_style"]["color_rgb"] = [0, 0, 0]
        self.assertFalse(style_fidelity.validate_rendered_styles([row], style_fidelity.default_style_map([row]))["passed"])

    def test_05_italic_preserved(self):
        row = rendered(frame(italic=True))
        self.assertTrue(style_fidelity.validate_rendered_styles([row], style_fidelity.default_style_map([row]))["passed"])

    def test_06_superscript_mismatch_fails(self):
        row = rendered(frame(superscript=True))
        row["rendered_style"]["superscript"] = False
        self.assertFalse(style_fidelity.validate_rendered_styles([row], style_fidelity.default_style_map([row]))["passed"])

    def test_07_leading_outside_range_fails(self):
        row = rendered(frame())
        row["rendered_style"]["leading_pt"] = 20.0
        self.assertFalse(style_fidelity.validate_rendered_styles([row], style_fidelity.default_style_map([row]))["passed"])

    def test_08_missing_role_mapping_fails(self):
        with self.assertRaises(style_fidelity.StyleFidelityError):
            style_fidelity.validate_style_map({"schema_version": 1, "roles": {}}, [frame()])

    def test_09_spacing_fingerprint_mismatch_fails(self):
        row = rendered(frame(first_line_indent_pt=8.0))
        row["rendered_style"]["first_line_indent_pt"] = 0.0
        self.assertFalse(style_fidelity.validate_rendered_styles([row], style_fidelity.default_style_map([row]))["passed"])

    def test_10_run_level_style_is_bound_to_rendered_evidence(self):
        run = {"target_text": "结果", "font_family": "SimHei", "weight": "bold", "italic": False, "size_ratio": 1.0}
        row = rendered(frame(style_runs=[run]))
        row["rendered_style"]["style_runs"] = []
        report = style_fidelity.validate_rendered_styles([row], style_fidelity.default_style_map([row]))
        self.assertFalse(report["passed"])


class NumericHardGateTests(unittest.TestCase):
    def test_01_minus_is_preserved(self):
        self.assertEqual(translation_integrity.extract_numeric_tokens("r = −0.15"), translation_integrity.extract_numeric_tokens("r = -0.15"))

    def test_02_exponent_is_preserved(self):
        self.assertEqual(translation_integrity.extract_numeric_tokens("p = 4 × 10−4"), translation_integrity.extract_numeric_tokens("p=4 x 10^-4"))

    def test_03_changed_p_value_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = translation_integrity.validate_numeric_integrity(Path(tmp), {"U": {"source_text": "p=.04", "translated_text": "p=.40"}})
            self.assertFalse(result.passed)

    def test_04_units_and_statistics_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = translation_integrity.validate_numeric_integrity(Path(tmp), {"U": {"source_text": "t(20)=−2.1, 400 Hz", "translated_text": "t(20)=−2.1，400 Hz"}})
            self.assertTrue(result.passed)


class SourcePackageTests(unittest.TestCase):
    def package(self):
        return {"schema_version": 1, "missing_required_policy": "BLOCK", "sources": [
            {"source_id": "SRC-M1", "source_type": "MAIN", "required": True, "available": True, "local_path": "main.pdf"},
            {"source_id": "SRC-S1", "source_type": "SI", "required": True, "available": True, "local_path": "si.pdf", "relation_to_main": "supplements"},
        ], "source_archive": {"status": "VERIFIED", "archived_source_ids": ["SRC-M1", "SRC-S1"]}}

    def test_01_main_and_si_ready(self):
        self.assertEqual(source_package.validate_source_cross_reference(self.package())["status"], "READY")

    def test_02_missing_required_si_blocked(self):
        data = self.package(); data["sources"][1]["available"] = False; data["sources"][1]["local_path"] = ""
        self.assertEqual(source_package.validate_source_cross_reference(data)["status"], "BLOCKED")

    def test_03_exactly_one_main_required(self):
        data = self.package(); data["sources"].pop(0)
        with self.assertRaises(source_package.SourcePackageError): source_package.validate_source_cross_reference(data)

    def test_04_pending_archive_is_explicit(self):
        data = self.package(); data["source_archive"] = {"status": "PENDING"}
        self.assertEqual(source_package.validate_source_cross_reference(data)["source_archive_status"], "PENDING")

    def test_05_verified_archive_requires_all_required(self):
        data = self.package(); data["source_archive"]["archived_source_ids"] = ["SRC-M1"]
        with self.assertRaises(source_package.SourcePackageError): source_package.validate_source_cross_reference(data)


def good_narrative():
    prose = "这是一段有来源锚点并完成因果边界说明的实质性中文分析。" * 5
    return {"schema_version": 1, "sections": {name: {"prose": prose, "source_anchors": ["SRC-M1 p.1"]} for name in deep.NARRATIVE_SECTIONS}, "claim_closure": [
        {"claim_id": f"{kind}-001", "claim_class": kind, "prose": prose, "source_anchor": "SRC-M1 p.1"} for kind in deep.CORE_CLAIM_CLASSES
    ]}


class BNarrativeTests(unittest.TestCase):
    def test_01_complete_narrative_passes(self): self.assertTrue(deep.validate_narrative_coverage(good_narrative())["passed"])
    def test_02_missing_methods_fails(self):
        data = good_narrative(); del data["sections"]["METHODS"]
        self.assertFalse(deep.validate_narrative_coverage(data)["passed"])
    def test_03_short_prose_fails(self):
        data = good_narrative(); data["sections"]["RESULTS"]["prose"] = "太短"
        self.assertFalse(deep.validate_narrative_coverage(data)["passed"])
    def test_04_missing_anchor_fails(self):
        data = good_narrative(); data["sections"]["DISCUSSION"]["source_anchors"] = []
        self.assertFalse(deep.validate_narrative_coverage(data)["passed"])
    def test_05_missing_audit_claim_fails(self):
        data = good_narrative(); data["claim_closure"] = [x for x in data["claim_closure"] if x["claim_class"] != "AUD"]
        self.assertFalse(deep.validate_narrative_coverage(data)["passed"])


class BFigureTests(unittest.TestCase):
    def inventory(self, image="fig.png"):
        prose = "该图显示核心方向、估计量与不确定性，并说明零结果和设计限制。" * 4
        return {"schema_version": 1, "figures": [{"figure_id": "F1", "category": "CORE_RESULT", "embedded": True, "image_path": image, "translated_caption": prose, "interpretation": prose, "source_anchor": "SRC-M1 Fig. 1"}]}
    def test_01_core_figure_passes(self): self.assertTrue(deep.validate_figure_inventory(self.inventory())["passed"])
    def test_02_core_must_embed(self):
        data=self.inventory(); data["figures"][0]["embedded"]=False
        self.assertFalse(deep.validate_figure_inventory(data)["passed"])
    def test_03_core_needs_caption(self):
        data=self.inventory(); data["figures"][0]["translated_caption"]=""
        self.assertFalse(deep.validate_figure_inventory(data)["passed"])
    def test_04_core_needs_interpretation(self):
        data=self.inventory(); data["figures"][0]["interpretation"]=""
        self.assertFalse(deep.validate_figure_inventory(data)["passed"])
    def test_05_invalid_category_fails(self):
        data=self.inventory(); data["figures"][0]["category"]="DECORATIVE"
        self.assertFalse(deep.validate_figure_inventory(data)["passed"])


class DesignRouterTests(unittest.TestCase):
    def ids(self, profile): return {row["module_id"] for row in router.select_modules(profile)["modules"]}
    def test_01_eeg_psg(self): self.assertIn("EEG-PSG", self.ids({"designs":["experimental"],"modalities":["eeg","psg"],"analyses":[]}))
    def test_02_fmri(self): self.assertIn("COBIDAS-MRI", self.ids({"designs":["experimental"],"modalities":["fmri"],"analyses":[]}))
    def test_03_observational(self): self.assertIn("STROBE", self.ids({"designs":["observational"],"modalities":[],"analyses":[]}))
    def test_04_longitudinal(self): self.assertIn("LONGITUDINAL", self.ids({"designs":["longitudinal"],"modalities":[],"analyses":[]}))
    def test_05_mediation(self): self.assertIn("MEDIATION-SEM-TEMPORALITY", self.ids({"designs":["cross_sectional"],"modalities":[],"analyses":["mediation"]}))
    def test_06_machine_learning(self): self.assertIn("MACHINE-LEARNING", self.ids({"designs":["database"],"modalities":[],"analyses":["machine_learning"]}))


if __name__ == "__main__":
    unittest.main()
