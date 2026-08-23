from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import sanitize_docx_metadata as docx_metadata
import psychology_method_router as method_router
import validate_deliverables as deliverables
import validate_translation_package as translation
import workflow_state


class TranslationPackageTests(unittest.TestCase):
    def _package(self, root: Path) -> tuple[Path, Path]:
        work = root / "work"
        work.mkdir()
        a_path = root / "A.pdf"
        a_path.write_bytes(b"%PDF-1.4\nsynthetic mirror")
        units = [
            {"unit_id": "TU-M1", "source_id": "SRC-M1", "source_page": 1, "kind": "paragraph"},
            {"unit_id": "TU-S1", "source_id": "SRC-S1", "source_page": 1, "kind": "paragraph"},
        ]
        objects = [
            {"object_id": "FIG-1", "source_id": "SRC-M1", "source_page": 1, "kind": "figure"},
            {"object_id": "FIG-S1", "source_id": "SRC-S1", "source_page": 1, "kind": "figure"},
            {"object_id": "FIG-S2", "source_id": "SRC-S1", "source_page": 1, "kind": "figure"},
            {"object_id": "FIG-S3", "source_id": "SRC-S1", "source_page": 1, "kind": "figure"},
            {
                "object_id": "TAB-S1",
                "source_id": "SRC-S1",
                "source_page": 1,
                "kind": "table",
                "table_structure": {
                    "rows": 4,
                    "columns": 3,
                    "header_rows": 2,
                    "merged_cells": 1,
                    "footnotes": 1,
                },
            },
        ]
        inventory = {
            "schema_version": 1,
            "scope": "FULL_MIRROR",
            "sources": [
                {"source_id": "SRC-M1", "role": "MAIN", "page_count": 1, "status": "AVAILABLE"},
                {"source_id": "SRC-S1", "role": "SI", "page_count": 1, "status": "AVAILABLE"},
            ],
            "pages": [
                {"source_id": "SRC-M1", "source_page": 1, "unit_ids": ["TU-M1"], "object_ids": ["FIG-1"]},
                {
                    "source_id": "SRC-S1",
                    "source_page": 1,
                    "unit_ids": ["TU-S1"],
                    "object_ids": ["FIG-S1", "FIG-S2", "FIG-S3", "TAB-S1"],
                },
            ],
            "units": units,
            "objects": objects,
        }
        (work / translation.INVENTORY_FILE).write_text(
            json.dumps(inventory), encoding="utf-8"
        )
        ledger = [
            {
                "unit_id": unit["unit_id"],
                "source_id": unit["source_id"],
                "source_page": unit["source_page"],
                "section": "Body",
                "unit_index": index,
                "kind": unit["kind"],
                "source_status": "READABLE",
                "translation_status": "TRANSLATED",
                "output_pages": [index],
                "issue_ids": [],
            }
            for index, unit in enumerate(units, start=1)
        ]
        (work / translation.LEDGER_FILE).write_text(
            "".join(json.dumps(row) + "\n" for row in ledger), encoding="utf-8"
        )
        (work / translation.ISSUES_FILE).write_text("", encoding="utf-8")
        plan = {
            "schema_version": 1,
            "helper_scope": "V1_LAYOUT_HELPER_NOT_FULL_AUTOMATIC_RELAYOUT",
            "source_pdf": str((root / "source.pdf").resolve()),
            "output_pdf": str(a_path.resolve()),
            "strategy_order": ["strict-mirror", "adaptive-mirror", "readable-extension"],
            "requested_strategy": "strict-mirror",
            "page_count_planned": 2,
            "pages": [
                {
                    "page_number": 1,
                    "output_page_number": 1,
                    "source_page_label": "1",
                    "source_page_refs": [{"source_id": "SRC-M1", "source_page": 1}],
                    "text_blocks": [],
                    "figure_placeholders": [],
                    "table_placeholders": [],
                    "placed_object_ids": ["FIG-1"],
                    "table_placements": [],
                    "adaptive_font_sizing": {"initial_scale": 1.1, "minimum_font_pt": 8.5},
                    "layout_strategy_used": "strict-mirror",
                    "overflow_detected": False,
                    "extension_page": None,
                    "extension_of": None,
                    "render_checked": True,
                    "render_notes": ["source/output pair inspected"],
                },
                {
                    "page_number": 2,
                    "output_page_number": 2,
                    "source_page_label": "S1",
                    "source_page_refs": [{"source_id": "SRC-S1", "source_page": 1}],
                    "text_blocks": [],
                    "figure_placeholders": [],
                    "table_placeholders": [],
                    "placed_object_ids": ["FIG-S1", "FIG-S2", "FIG-S3", "TAB-S1"],
                    "table_placements": [
                        {
                            "object_id": "TAB-S1",
                            "mode": "native-grid",
                            "rows": 4,
                            "columns": 3,
                            "header_rows": 2,
                            "merged_cells_preserved": True,
                            "footnotes_present": True,
                        }
                    ],
                    "adaptive_font_sizing": {"initial_scale": 1.1, "minimum_font_pt": 8.5},
                    "layout_strategy_used": "adaptive-mirror",
                    "overflow_detected": False,
                    "extension_page": None,
                    "extension_of": None,
                    "render_checked": True,
                    "render_notes": ["source/output pair inspected"],
                },
            ],
            "layout_qc": {
                "render_required": True,
                "visual_inspection_required": True,
                "all_pages_checked": True,
                "status": "LAYOUT_QC_PASSED",
            },
        }
        (work / translation.PLAN_FILE).write_text(json.dumps(plan), encoding="utf-8")
        return work, a_path

    def _failed_codes(self, work: Path, a_path: Path) -> set[str]:
        return {
            check.code
            for check in translation.validate_package(work, a_path, "FULL_MIRROR")
            if not check.passed
        }

    def test_complete_main_and_complex_si_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work, a_path = self._package(Path(tmp))
            failures = self._failed_codes(work, a_path)
            self.assertEqual(failures, set())

    def test_missing_si_figure_fails_object_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work, a_path = self._package(Path(tmp))
            path = work / translation.PLAN_FILE
            plan = json.loads(path.read_text(encoding="utf-8"))
            plan["pages"][1]["placed_object_ids"].remove("FIG-S3")
            path.write_text(json.dumps(plan), encoding="utf-8")
            self.assertIn("layout:object-coverage", self._failed_codes(work, a_path))

    def test_flattened_table_fails_topology(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work, a_path = self._package(Path(tmp))
            path = work / translation.PLAN_FILE
            plan = json.loads(path.read_text(encoding="utf-8"))
            plan["pages"][1]["table_placements"][0]["rows"] = 12
            path.write_text(json.dumps(plan), encoding="utf-8")
            self.assertIn("layout:table-topology", self._failed_codes(work, a_path))

    def test_unmapped_source_page_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work, a_path = self._package(Path(tmp))
            path = work / translation.PLAN_FILE
            plan = json.loads(path.read_text(encoding="utf-8"))
            plan["pages"][1]["source_page_refs"] = [{"source_id": "SRC-M1", "source_page": 1}]
            path.write_text(json.dumps(plan), encoding="utf-8")
            self.assertIn("layout:source-page-coverage", self._failed_codes(work, a_path))

    def test_ledger_missing_source_page_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work, a_path = self._package(Path(tmp))
            path = work / translation.LEDGER_FILE
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            del rows[1]["source_page"]
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            failures = self._failed_codes(work, a_path)
            self.assertIn("ledger:schema", failures)
            self.assertIn("ledger:inventory-coverage", failures)

    def test_ledger_output_page_must_exist_in_layout_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work, a_path = self._package(Path(tmp))
            path = work / translation.LEDGER_FILE
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            rows[1]["output_pages"] = [99]
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            self.assertIn(
                "layout:ledger-output-pages",
                self._failed_codes(work, a_path),
            )

    def test_paper_without_figures_or_tables_can_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work, a_path = self._package(Path(tmp))
            inventory_path = work / translation.INVENTORY_FILE
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            inventory["objects"] = []
            for page in inventory["pages"]:
                page["object_ids"] = []
            inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

            plan_path = work / translation.PLAN_FILE
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            for page in plan["pages"]:
                page["placed_object_ids"] = []
                page["table_placements"] = []
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            self.assertEqual(self._failed_codes(work, a_path), set())

    def test_declared_source_page_count_must_match_inventory_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work, a_path = self._package(Path(tmp))
            path = work / translation.INVENTORY_FILE
            inventory = json.loads(path.read_text(encoding="utf-8"))
            inventory["sources"][1]["page_count"] = 2
            path.write_text(json.dumps(inventory), encoding="utf-8")
            self.assertIn(
                "inventory:page-count-coverage",
                self._failed_codes(work, a_path),
            )

    def test_completion_gate_requires_written_validation_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work, a_path = self._package(Path(tmp))
            checks = deliverables.check_translation_package(
                work,
                a_path,
                "FULL_MIRROR",
                True,
            )
            failed = {check.name for check in checks if not check.passed}
            self.assertEqual(failed, {"translation:validation-report"})


class DocxMetadataTests(unittest.TestCase):
    def _docx(self, path: Path) -> None:
        document = (
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body><w:p><w:commentRangeStart w:id="0"/><w:r><w:t>内容</w:t></w:r>'
            '<w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r></w:p></w:body></w:document>'
        )
        core = (
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            '<dc:creator>ChatGPT</dc:creator><cp:lastModifiedBy>python-docx</cp:lastModifiedBy>'
            '<cp:keywords>AI</cp:keywords><dc:description>Codex</dc:description></cp:coreProperties>'
        )
        app = '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>OpenAI</Application></Properties>'
        comments = '<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", document)
            archive.writestr("word/comments.xml", comments)
            archive.writestr("docProps/core.xml", core)
            archive.writestr("docProps/app.xml", app)

    def test_sanitize_removes_tool_metadata_and_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "B.docx"
            self._docx(path)
            docx_metadata.sanitize_docx(path)
            self.assertEqual(docx_metadata.validate_docx_metadata(path), [])
            with zipfile.ZipFile(path) as archive:
                self.assertNotIn("word/comments.xml", archive.namelist())
                core = archive.read("docProps/core.xml").decode("utf-8")
                for token in ("python-docx", "ChatGPT", "OpenAI", "Codex"):
                    self.assertNotIn(token, core)

    def test_explicit_author_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "B.docx"
            self._docx(path)
            docx_metadata.sanitize_docx(path, author="JYW23.26")
            self.assertEqual(
                docx_metadata.validate_docx_metadata(path, expected_author="JYW23.26"), []
            )


class TranslationScopeStateTests(unittest.TestCase):
    def test_new_manifest_defaults_to_full_mirror(self) -> None:
        data = workflow_state.initial_manifest("2026-W34")
        self.assertEqual(data["stages"]["translation"]["scope"], "FULL_MIRROR")

    def test_old_complete_manifest_requires_scope_before_completion(self) -> None:
        data = workflow_state.initial_manifest("2026-W34")
        data["paper_id"] = "paper"
        data["stages"]["translation"]["status"] = "COMPLETE"
        del data["stages"]["translation"]["scope"]
        with self.assertRaises(workflow_state.WorkflowStateError):
            workflow_state.validate_manifest(data)


class PsychologyMethodRoutingTests(unittest.TestCase):
    def test_observational_fmri_routes_jars_strobe_and_cobidas(self) -> None:
        result = method_router.select_modules(
            {"designs": ["observational", "cross_sectional"], "modalities": ["fmri"]}
        )
        modules = {item["module_id"] for item in result["modules"]}
        self.assertEqual(
            modules,
            {"APA-JARS-QUANT", "STROBE", "COBIDAS-MRI"},
        )
        self.assertEqual(result["scoring"], "NONE")

    def test_cross_sectional_mediation_gets_temporal_warning(self) -> None:
        result = method_router.select_modules(
            {"designs": ["cross_sectional"], "analyses": ["mediation"]}
        )
        modules = {item["module_id"] for item in result["modules"]}
        self.assertIn("MEDIATION-SEM-TEMPORALITY", modules)
        self.assertTrue(result["warnings"])

    def test_qualitative_and_mixed_methods_route_separately(self) -> None:
        qualitative = method_router.select_modules({"designs": ["qualitative"]})
        self.assertEqual(
            {item["module_id"] for item in qualitative["modules"]},
            {"APA-JARS-QUAL"},
        )
        mixed = method_router.select_modules({"designs": ["mixed_methods"]})
        self.assertEqual(
            {item["module_id"] for item in mixed["modules"]},
            {"APA-MMARS", "APA-JARS-QUAL", "APA-JARS-QUANT"},
        )
        self.assertNotIn(
            "exact p value when reported",
            qualitative["interpretation_requirements"],
        )
        self.assertIn(
            "integration-point and joint-inference consistency",
            mixed["interpretation_requirements"],
        )

    def test_result_interpretation_is_not_p_value_only(self) -> None:
        result = method_router.select_modules({"designs": ["experimental"]})
        requirements = set(result["interpretation_requirements"])
        self.assertIn("estimate and direction", requirements)
        self.assertIn("uncertainty interval", requirements)
        self.assertIn("effect size and scientific meaning", requirements)
        self.assertIn("sample-size justification", requirements)


if __name__ == "__main__":
    unittest.main()
