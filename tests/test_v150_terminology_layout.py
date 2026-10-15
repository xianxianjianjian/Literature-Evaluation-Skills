from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import paragraph_styles
import render_exact_mirror
import terminology_registry as terms
import validate_paragraph_styles
import validate_terminology_consistency as consistency
from normalize_chinese_typography import normalize_chinese_text


class PsychologyTerminologyDatabaseTests(unittest.TestCase):
    def _registry(self, root: Path) -> Path:
        path = root / "terminology_registry.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerow(terms.FIELDS)
        return path

    def _add_args(self, registry: Path, term_id: str, domain: str, context: str, preferred: str) -> argparse.Namespace:
        return argparse.Namespace(
            registry=registry, term_id=term_id, english_term="temporal dynamics",
            preferred_chinese=preferred, alternative_chinese="时间动力学; 时间演变",
            abbreviation=None, domain=domain, subdomain="Memory", discipline=None,
            subfield=None, definition="Change over time", context=context,
            operational_use="Translate according to temporal scale and signal/process meaning",
            source_type="Chinese peer-reviewed literature", source_citation="示例专业文献",
            confidence="HIGH", evidence_id="TERMEV-0001", evidence_ids="TERMEV-0001",
            evidence_level="TE4", paper_id=None, first_seen="2026-09-16",
            last_used="2026-09-16", usage_count=0, status="CONTEXTUAL",
            verified_date="2026-09-16", notes=None,
        )

    def test_context_prevents_mechanical_dynamics_translation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = self._registry(Path(directory))
            terms.command_add(self._add_args(
                registry, "TERM-0001", "Cognitive Psychology",
                "behavioral process across sleep cycles", "时间动态",
            ))
            terms.command_add(self._add_args(
                registry, "TERM-0002", "Cognitive Neuroscience",
                "millisecond neural signal evolution", "时间动力学",
            ))
            rows = terms.read_registry(registry)
            resolved = terms.resolve_context_candidate(
                rows, english_term="temporal dynamics", domain="Cognitive Psychology",
                subdomain="Memory", context="behavioral process across sleep cycles",
            )
            self.assertEqual(resolved["auto_selected_term_id"], "TERM-0001")
            unresolved = terms.resolve_context_candidate(
                rows, english_term="temporal dynamics", domain="Sleep Psychology / Sleep Medicine",
                subdomain="Memory", context="overnight change",
            )
            self.assertEqual(unresolved["decision"], "EXTERNAL_VERIFICATION_REQUIRED")

    def test_usage_accumulates_once_per_paper(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = self._registry(Path(directory))
            terms.command_add(self._add_args(
                registry, "TERM-0001", "Cognitive Psychology",
                "behavioral process across sleep cycles", "时间动态",
            ))
            args = argparse.Namespace(
                registry=registry, term_ids="TERM-0001", paper_id="PAPER-A",
                used_date="2026-09-17",
            )
            terms.command_record_usage(args)
            terms.command_record_usage(args)
            row = terms.read_registry(registry)[0]
            self.assertEqual(row["Usage_Count"], "1")
            self.assertEqual(row["Last_Used"], "2026-09-17")
            self.assertEqual(row["Paper_ID"], "PAPER-A")

    def test_paper_sheet_accumulates_all_reviewed_terms(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = self._registry(root)
            terms.command_add(self._add_args(
                registry, "TERM-0001", "Cognitive Psychology",
                "behavioral process across sleep cycles", "时间动态",
            ))
            paper = root / "paper_terminology.csv"
            paper.write_text("Term_ID,English_Term\nTERM-0001,temporal dynamics\n", encoding="utf-8")
            terms.command_record_paper_usage(argparse.Namespace(
                registry=registry, paper_terminology=paper, paper_id="PAPER-C",
                used_date="2026-09-17",
            ))
            self.assertEqual(terms.read_registry(registry)[0]["Usage_Count"], "1")

    def test_legacy_registry_upgrades_on_next_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "terminology_registry.csv"
            row = {field: "" for field in terms.LEGACY_FIELDS}
            row.update({
                "Term_ID": "TERM-0001", "English_Term": "working memory",
                "Preferred_Chinese": "工作记忆", "Discipline": "Cognitive Psychology",
                "Subfield": "Memory", "Context": "capacity task", "Confidence": "HIGH",
                "Evidence_Level": "TE4", "Evidence_IDs": "TERMEV-0001",
                "Status": "ACTIVE", "First_Verified": "2026-09-01",
                "Last_Verified": "2026-09-01",
            })
            with registry.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=terms.LEGACY_FIELDS)
                writer.writeheader(); writer.writerow(row)
            self.assertEqual(terms.read_registry(registry)[0]["Domain"], "Cognitive Psychology")
            terms.command_record_usage(argparse.Namespace(
                registry=registry, term_ids="TERM-0001", paper_id="PAPER-B",
                used_date="2026-09-17",
            ))
            with registry.open("r", encoding="utf-8-sig", newline="") as handle:
                self.assertEqual(next(csv.reader(handle)), terms.FIELDS)

    def test_model_recommendation_is_not_accepted_as_source_citation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = self._registry(Path(directory))
            args = self._add_args(
                registry, "TERM-0001", "Cognitive Psychology",
                "behavioral process across sleep cycles", "时间动态",
            )
            args.source_citation = "ChatGPT recommended"
            with self.assertRaises(terms.TerminologyError):
                terms.command_add(args)

    def test_correction_preserves_previous_translation_and_event(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = self._registry(root)
            terms.command_add(self._add_args(
                registry, "TERM-0001", "Cognitive Psychology",
                "behavioral process across sleep cycles", "时间动态",
            ))
            terms.command_update(argparse.Namespace(
                registry=registry, term_id="TERM-0001", abbreviation=None,
                preferred_chinese="时间演变", alternative_chinese=None,
                domain=None, subdomain=None, discipline=None, subfield=None,
                definition=None, context=None, operational_use=None, source_type=None,
                source_citation="更高等级正式指南", confidence="HIGH",
                evidence_level="TE1", evidence_ids="TERMEV-0002", paper_id=None,
                verified_date="2026-09-18", note="正式指南采用时间演变",
                corrections=None,
            ))
            row = terms.read_registry(registry)[0]
            self.assertIn("时间动态", terms.split_alternatives(row["Alternative_Chinese"]))
            events = [json.loads(line) for line in (root / "terminology_corrections.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(events[0]["old_preferred_chinese"], "时间动态")
            self.assertEqual(events[0]["new_preferred_chinese"], "时间演变")

    def test_cross_document_gates_are_named_and_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = self._registry(root)
            terms.command_add(self._add_args(
                registry, "TERM-0001", "Cognitive Psychology",
                "behavioral process across sleep cycles", "时间动态",
            ))
            evidence = root / "evidence.jsonl"
            evidence.write_text(json.dumps({
                "schema_version": 2, "event_type": "ADD", "evidence_id": "TERMEV-0001",
                "roles": ["Translation Evidence"], "type": "TE4", "source": "示例专业文献",
                "supports": ["temporal dynamics"], "status": "ACTIVE",
            }, ensure_ascii=False) + "\n", encoding="utf-8")
            paper = root / "paper.csv"
            paper.write_text(
                "Term_ID,English_Term,Preferred_Chinese,Alternative_Chinese,Evidence_IDs,Domain,Subdomain,Context\n"
                "TERM-0001,temporal dynamics,时间动态,,TERMEV-0001,Cognitive Psychology,Memory,behavioral process across sleep cycles\n",
                encoding="utf-8",
            )
            artifacts = {}
            for name in "ABC":
                path = root / f"{name}.txt"
                path.write_text("研究关注时间动态。", encoding="utf-8")
                artifacts[name] = path
            result = consistency.validate_consistency(paper, registry, evidence, artifacts)
            self.assertTrue(result["passed"], result)
            self.assertTrue(all(item["passed"] for item in result["checks"]))


class ParagraphStyleEngineTests(unittest.TestCase):
    def test_role_mapping_distinguishes_body_heading_and_reference(self) -> None:
        body = paragraph_styles.paragraph_style("BODY", "zh-CN", 10)
        heading = paragraph_styles.paragraph_style("H1", "zh-CN", 14)
        reference = paragraph_styles.paragraph_style("REFERENCE", "en", 10)
        self.assertEqual((body["alignment"], body["first_line_indent_pt"]), ("justify", 20.0))
        self.assertEqual(heading["first_line_indent_pt"], 0.0)
        self.assertEqual((reference["alignment"], reference["hanging_indent_pt"]), ("left", 36.0))
        self.assertEqual(paragraph_styles.style_name_for_role("AFFILIATION", "zh-CN"), "CAPTION")
        self.assertEqual(paragraph_styles.style_name_for_role("OTHER", "zh-CN"), "CAPTION")
        abstract = paragraph_styles.exact_mirror_body_preference("ABSTRACT", "zh-CN", 10)
        self.assertEqual((abstract["alignment"], abstract["first_line_indent_pt"]), ("justify", 0.0))

    def test_paragraph_validator_accepts_chinese_body_and_apa_reference(self) -> None:
        records = [
            {"frame_id": "B1", "role": "BODY", "language": "zh-CN", "font_size_pt": 10,
             "style_name": "BODY_ZH", "alignment": "justify", "first_line_indent_pt": 20,
             "left_indent_pt": 0, "hanging_indent_pt": 0, "overflow": False, "clipping": False},
            {"frame_id": "H1", "role": "H1", "language": "zh-CN", "font_size_pt": 14,
             "style_name": "HEADING", "alignment": "left", "first_line_indent_pt": 0,
             "left_indent_pt": 0, "hanging_indent_pt": 0, "overflow": False, "clipping": False},
            {"frame_id": "R1", "role": "REFERENCE", "language": "en", "font_size_pt": 10,
             "style_name": "REFERENCE_APA", "alignment": "left", "first_line_indent_pt": -36,
             "left_indent_pt": 36, "hanging_indent_pt": 36, "overflow": False, "clipping": False},
        ]
        self.assertTrue(all(item.passed for item in validate_paragraph_styles.validate_records(records)))

    def test_bilingual_typography_preserves_statistics(self) -> None:
        text = normalize_chinese_text("结果显示，p = .032，r = .46，F(1, 38) = 5.21，95% CI [0.12, 0.45]。")
        check = validate_paragraph_styles.validate_bilingual_texts([
            {"frame_id": "T1", "language": "zh-CN", "text": text}
        ])
        self.assertTrue(check.passed)
        for token in ("p = .032", "r = .46", "F(1, 38) = 5.21", "95% CI [0.12, 0.45]"):
            self.assertIn(token, text)

    @unittest.skipUnless(Path(r"C:\Windows\Fonts\simsun.ttc").is_file(), "SimSun unavailable")
    def test_exact_mirror_applies_style_only_when_geometry_fits(self) -> None:
        try:
            pdfmetrics.getFont("SimSun")
        except KeyError:
            pdfmetrics.registerFont(TTFont("SimSun", r"C:\Windows\Fonts\simsun.ttc", subfontIndex=0))
        frame = {
            "frame_id": "F1", "role": "BODY", "kind": "body", "bbox_pt": [0, 0, 90, 10],
            "rotation": 0, "source_font_size_pt": 10.0, "source_leading_pt": 12.0,
            "alignment": "left", "first_line_indent_pt": 0.0, "style_runs": [],
            "render_font_name": "SimSun",
        }
        fitted = render_exact_mirror._layout("中文正文测试文本", "中文正文测试文本", frame)
        self.assertIsNotNone(fitted)
        _, _, _, typography = fitted
        self.assertEqual(typography["alignment"], "left")
        self.assertEqual(typography["layout_exception"]["code"], "LAYOUT_EXCEPTION")
        records = [{**typography, "frame_id": "F1", "font_size_pt": 10,
                    "exact_mirror": True, "left_indent_pt": 0, "hanging_indent_pt": 0}]
        self.assertTrue(all(item.passed for item in validate_paragraph_styles.validate_records(records)))


if __name__ == "__main__":
    unittest.main()
