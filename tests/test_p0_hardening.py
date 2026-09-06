from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import history_manager
import exact_mirror
import terminology_registry
import translation_integrity
import validate_deep_reading_package as deep_validator
import validate_deliverables
import validate_terminology_consistency as term_consistency
import workflow_state
import zotero_bridge

try:
    from reportlab.pdfgen import canvas
except ImportError:
    canvas = None


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


class NumericIntegrityTests(unittest.TestCase):
    def test_scientific_notation_sign_statistics_units_and_doi_are_preserved(self) -> None:
        text = "β = −0.42, p < 4 × 10^-4, 95%, 12.5 Hz, R²=.31; 10.1000/test.v2"
        tokens = translation_integrity.extract_numeric_tokens(text)
        self.assertIn("p<4x10^-4", tokens)
        self.assertIn("beta=-0.42", tokens)
        self.assertIn("12.5hz", tokens)
        self.assertIn("10.1000/test.v2", tokens)

    def test_unapproved_sign_change_blocks_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            ledger = {"TU-1": {"source_text": "β = −0.42", "translated_text": "β = 0.42"}}
            result, report = translation_integrity.validate_numeric_integrity(work, ledger)
            self.assertFalse(result.passed)
            self.assertTrue(report["discrepancies"])

    def test_reviewed_whitelist_can_account_for_one_intentional_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            write_jsonl(
                work / "numeric_integrity_whitelist.jsonl",
                [{
                    "unit_id": "TU-1", "source_token": "−0.42", "translated_token": "0.42",
                    "reason": "quoted correction", "reviewer": "reviewer", "reviewed_date": "2026-09-06",
                }],
            )
            ledger = {"TU-1": {"source_text": "−0.42", "translated_text": "0.42"}}
            result, _ = translation_integrity.validate_numeric_integrity(work, ledger)
            self.assertTrue(result.passed)


class FigureAndConflictTests(unittest.TestCase):
    def test_missing_figure_label_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "figure_text_inventory.jsonl").write_text("", encoding="utf-8")
            inventory = {"objects": [{"object_id": "FIG-1", "kind": "figure", "label_frame_ids": ["TF-1"]}]}
            result = translation_integrity.validate_figure_text_inventory(
                work,
                inventory,
                {"TF-1": {"kind": "figure_label", "unit_id": "TU-1", "bbox_pt": [0, 0, 1, 1]}},
                {"TU-1": {"translated_text": "速度"}},
            )
            self.assertFalse(result.passed)


class SourceAuthorityTests(unittest.TestCase):
    def _inventory(self) -> dict:
        box = [0, 0, 612, 792]
        return {
            "schema_version": 2,
            "scope": "FULL_MIRROR",
            "layout_fidelity": "EXACT_TEXT_FRAME",
            "sources": [{
                "source_id": "SRC-MAIN", "role": "MAIN", "page_count": 1,
                "pdf_path": "main.pdf", "language_authority": "PUBLISHER_XML_JATS_HTML",
                "geometry_authority": "VERSION_OF_RECORD_PDF",
            }],
            "pages": [{
                "source_id": "SRC-MAIN", "source_page": 1, "output_page": 1,
                "media_box": box, "crop_box": box, "trim_box": box,
                "bleed_box": box, "art_box": box, "rotation": 0,
                "unit_ids": [], "object_ids": [], "frame_ids": [],
            }],
            "objects": [],
        }

    def test_clean_jats_language_with_vor_geometry_passes(self) -> None:
        result = exact_mirror.validate_exact_inventory(self._inventory())
        self.assertEqual(result["sources"][0]["language_authority"], "PUBLISHER_XML_JATS_HTML")

    def test_main_geometry_cannot_use_supplement_pdf(self) -> None:
        inventory = self._inventory()
        inventory["sources"][0]["geometry_authority"] = "PUBLISHER_SUPPLEMENT_PDF"
        with self.assertRaises(exact_mirror.ExactMirrorError):
            exact_mirror.validate_exact_inventory(inventory)

    def test_main_si_conflict_cannot_be_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            write_jsonl(
                work / "source_conflicts.jsonl",
                [{
                    "conflict_id": "CONFLICT-001", "source_values": ["12 Hz", "13 Hz"],
                    "unit_ids": ["TU-M", "TU-S"], "audit_ids": ["AUD-001"],
                    "preserved_separately": True,
                }],
            )
            result = translation_integrity.validate_source_conflicts(
                work,
                {"TU-M": {"translated_text": "12 Hz"}, "TU-S": {"translated_text": "12 Hz"}},
            )
            self.assertFalse(result.passed)


class ZoteroPdfFirstTests(unittest.TestCase):
    def _args(self, root: Path, **updates) -> argparse.Namespace:
        pdf = root / "main.pdf"
        pdf.write_bytes(b"%PDF-1.4\n")
        metadata = root / "metadata.json"
        metadata.write_text(json.dumps({"title": "Paper", "doi": "10.1000/test", "year": 2025}), encoding="utf-8")
        values = dict(
            pdf=pdf, metadata=metadata, collection_key="COLL", fallback_metadata=False,
            fallback_reason=None, recognized_parent_key=None, yes=False,
            api_base_url="http://127.0.0.1:23119/api", timeout=1.0,
        )
        values.update(updates)
        return argparse.Namespace(**values)

    def test_pdf_first_preview_never_claims_archive_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            preview = zotero_bridge.pdf_ingest_preview(self._args(Path(tmp)))
            self.assertEqual(preview["operation"], "PDF_FIRST_INGEST")
            self.assertFalse(preview["archive_complete"])

    def test_metadata_fallback_requires_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(zotero_bridge.ZoteroBridgeError):
                zotero_bridge.pdf_ingest_preview(self._args(Path(tmp), fallback_metadata=True))

    def test_metadata_fallback_blocks_archive_completion(self) -> None:
        data = workflow_state.initial_manifest("2026-W36")
        data["paper_id"] = "10.1000/test"
        for stage in workflow_state.STAGE_NAMES:
            data["stages"][stage]["status"] = "COMPLETE"
        for output in ("A", "B", "C"):
            data["outputs"][output]["status"] = "COMPLETE"
        data["outputs"]["A"]["zotero_attachment_key"] = "A"
        data["outputs"]["B"]["zotero_attachment_key"] = "B"
        data["outputs"]["C"]["git_path"] = "C.md"
        data["source_change"]["last_checked"] = "2026-09-06"
        data["archive"].update({
            "zotero_parent_key": "P", "zotero_collection_key": "C",
            "zotero_main_attachment_key": "M", "metadata_only_fallback": True,
        })
        check = next(item for item in validate_deliverables._archive_completion_checks(data) if item.name == "archive:no-metadata-fallback")
        self.assertFalse(check.passed)

    def test_missing_required_si_attachment_blocks_archive_completion(self) -> None:
        data = workflow_state.initial_manifest("2026-W36")
        data["archive"].update({
            "required_si_source_ids": ["SRC-S1"],
            "zotero_si_attachment_keys": {},
        })
        check = next(item for item in validate_deliverables._archive_completion_checks(data) if item.name == "archive:required-si")
        self.assertFalse(check.passed)


class LayoutChoiceTests(unittest.TestCase):
    def test_structural_layout_requires_explicit_user_choice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "workflow.json"
            workflow_state.write_manifest(manifest, workflow_state.initial_manifest("2026-W36"))
            args = argparse.Namespace(
                manifest=manifest,
                scope="FULL_MIRROR",
                layout_fidelity="STRUCTURAL_MIRROR",
                explicit_user_choice=False,
            )
            with self.assertRaises(workflow_state.WorkflowStateError):
                workflow_state.command_set_translation_profile(args)


class HistoryReconciliationTests(unittest.TestCase):
    def test_reconcile_records_old_and_new_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            history_path = root / "selection.csv"
            with history_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=history_manager.SELECTION_FIELDS)
                writer.writeheader()
                row = {field: "" for field in history_manager.SELECTION_FIELDS}
                row.update({"Week": "2026-W36", "Paper_ID": "P1", "Title": "Old", "Role": "Primary"})
                writer.writerow(row)
            corrections = root / "history_corrections.jsonl"
            event = history_manager.reconcile_record(
                history_path, history_manager.SELECTION_FIELDS, record_type="selection",
                paper_id="P1", doi=None, week="2026-W36", updates={"Title": "Corrected"},
                corrections_path=corrections, correction_id="HISTCOR-0001",
                reason="metadata correction", corrected_date="2026-09-06",
            )
            self.assertEqual(event["old_values"]["Title"], "Old")
            self.assertEqual(event["new_values"]["Title"], "Corrected")
            self.assertIn("HISTCOR-0001", corrections.read_text(encoding="utf-8"))

    def test_reconcile_reading_preserves_old_and_new_evaluation_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            history_path = root / "reading.csv"
            with history_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=history_manager.READING_FIELDS)
                writer.writeheader()
                row = {field: "" for field in history_manager.READING_FIELDS}
                row.update({"Week": "2026-W36", "Paper_ID": "P1", "Git_Review_Path": "old.md"})
                writer.writerow(row)
            event = history_manager.reconcile_record(
                history_path, history_manager.READING_FIELDS, record_type="reading",
                paper_id="P1", doi=None, week="2026-W36", updates={"Git_Review_Path": "new.md"},
                corrections_path=root / "history_corrections.jsonl", correction_id="HISTCOR-0001",
                reason="B package revalidated", corrected_date="2026-09-06",
            )
            self.assertEqual(event["old_values"]["Git_Review_Path"], "old.md")
            self.assertEqual(event["new_values"]["Git_Review_Path"], "new.md")


class TerminologyEvidenceTests(unittest.TestCase):
    def test_focal_te7_cannot_support_unreported_method(self) -> None:
        rows = [{
            field: "" for field in terminology_registry.FIELDS
        }]
        rows[0].update({
            "Term_ID": "TERM-0001", "English_Term": "cluster-based permutation test",
            "Confidence": "HIGH", "Status": "CONTEXTUAL", "Evidence_IDs": "TERMEV-0001",
        })
        events = [{
            "evidence_id": "TERMEV-0001", "roles": ["Methodological Evidence"],
            "type": "TE7", "source": "Focal paper operational definitions", "paper_id": "P1",
            "supports": ["cluster-based permutation test"], "reported_terms": ["FDR-corrected time-frequency cluster identification"],
        }]
        failures = terminology_registry.validate_evidence_links(rows, events)
        self.assertTrue(any("reported_terms" in failure for failure in failures))


class TerminologyConsistencyTests(unittest.TestCase):
    def _package(self, root: Path, b_text: str) -> tuple[Path, Path, Path, dict[str, Path]]:
        registry = root / "registry.csv"
        row = {field: "" for field in terminology_registry.FIELDS}
        row.update({
            "Term_ID": "TERM-0001", "English_Term": "sleep spindle",
            "Preferred_Chinese": "睡眠纺锤波", "Alternative_Chinese": "睡眠主轴",
            "Confidence": "HIGH", "Evidence_Level": "TE6", "Evidence_IDs": "TERMEV-0001",
            "Status": "ACTIVE", "First_Verified": "2026-09-06", "Last_Verified": "2026-09-06",
        })
        with registry.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=terminology_registry.FIELDS)
            writer.writeheader(); writer.writerow(row)
        evidence = root / "evidence.jsonl"
        write_jsonl(evidence, [{
            "evidence_id": "TERMEV-0001", "role": "Translation Evidence", "type": "TE6",
            "source": "stable use", "supports": ["sleep spindle"], "verified_date": "2026-09-06",
        }])
        paper_terms = root / "paper_terms.csv"
        paper_terms.write_text(
            "Term_ID,English_Term,Preferred_Chinese,Alternative_Chinese,Evidence_IDs\n"
            "TERM-0001,sleep spindle,睡眠纺锤波,睡眠主轴,TERMEV-0001\n",
            encoding="utf-8",
        )
        artifacts = {}
        for name, text in {"A": "睡眠纺锤波", "B": b_text, "C": "睡眠纺锤波"}.items():
            path = root / f"{name}.txt"; path.write_text(text, encoding="utf-8"); artifacts[name] = path
        return paper_terms, registry, evidence, artifacts

    def test_preferred_term_is_consistent_across_a_b_c(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = self._package(Path(tmp), "睡眠纺锤波")
            self.assertTrue(term_consistency.validate_consistency(*package)["passed"])

    def test_nonpreferred_term_in_b_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = self._package(Path(tmp), "sleep spindle 睡眠主轴")
            result = term_consistency.validate_consistency(*package)
            self.assertFalse(result["passed"])
            self.assertTrue(any(item["artifact"] == "B" for item in result["failures"]))


def make_docx(path: Path, text: str, *, dangling: bool = False) -> None:
    document = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body><w:p><w:r><w:t>' + text.replace("&", "&amp;").replace("<", "&lt;") +
        '</w:t></w:r></w:p></w:body></w:document>'
    )
    core = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:creator></dc:creator>'
        '<cp:lastModifiedBy></cp:lastModifiedBy><cp:keywords></cp:keywords>'
        '<dc:description></dc:description><dc:subject></dc:subject></cp:coreProperties>'
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document)
        archive.writestr("docProps/core.xml", core)
        if dangling:
            archive.writestr(
                "word/_rels/document.xml.rels",
                '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="x" Target="media/missing.png"/></Relationships>',
            )


class DeepReadingGateTests(unittest.TestCase):
    def _text(self) -> str:
        return "\n".join(deep_validator.TOP_LEVEL_HEADINGS + deep_validator.METHOD_MARKERS + deep_validator.RESULT_MARKERS + deep_validator.DISCUSSION_MARKERS)

    def test_renderer_failure_prevents_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            b = root / "B.docx"
            make_docx(b, self._text())
            (root / "claim_evidence_map.csv").write_text("claim,evidence\n", encoding="utf-8")
            (root / "audit_log.jsonl").write_text("", encoding="utf-8")
            with mock.patch.object(deep_validator, "_python_docx_readable", return_value=(True, "ok")), mock.patch.object(deep_validator, "_find_soffice", return_value=None):
                checks = deep_validator.validate_package(b, root)
            self.assertFalse(next(item for item in checks if item.code == "B:independent-render").passed)

    @unittest.skipIf(canvas is None, "reportlab unavailable")
    def test_valid_render_and_all_page_visual_qa_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            b = root / "B.docx"
            make_docx(b, self._text())
            (root / "claim_evidence_map.csv").write_text("claim,evidence\n", encoding="utf-8")
            (root / "audit_log.jsonl").write_text("", encoding="utf-8")
            pdf = root / "B.pdf"
            c = canvas.Canvas(str(pdf)); c.drawString(20, 800, "B"); c.showPage(); c.save()
            png_dir = root / "pages"; png_dir.mkdir(); (png_dir / "page-1.png").write_bytes(b"png")
            qa = root / "b_visual_qa.json"
            qa.write_text(json.dumps({
                "schema_version": 1, "renderer": "LibreOffice 25 headless", "wrong_page_count": False,
                "pages": [{"page": 1, "reviewed": True, "blank": False, "overflow": False,
                           "table_clipping": False, "orphan_heading": False, "missing_glyph": False}],
            }), encoding="utf-8")
            with mock.patch.object(deep_validator, "_python_docx_readable", return_value=(True, "ok")):
                checks = deep_validator.validate_package(b, root, rendered_pdf=pdf, png_dir=png_dir, visual_qa=qa)
            self.assertEqual([item.detail for item in checks if not item.passed], [])

    def test_dangling_ooxml_relationship_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); b = root / "B.docx"; make_docx(b, self._text(), dangling=True)
            failures = deep_validator._relationship_checks(b)
            self.assertTrue(any("dangling" in item for item in failures))


if __name__ == "__main__":
    unittest.main()
