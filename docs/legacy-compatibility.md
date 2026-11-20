# Legacy Compatibility Guarantees

Literature-Evaluation-Skills preserves backward readability for historical manifests, archives, terminology registries, and validation reports without weakening active contract requirements.

## 1. Workflow Manifests & Translation Profiles

- **Pre-v1.2 manifests without `stages.translation.scope`**: remain readable during load/normalization, but an explicit `scope` must be recorded before Translation can transition to `COMPLETE`.
- **Pre-v1.3 manifests without `layout_fidelity`**: normalize to legacy `STRUCTURAL_MIRROR` (`Strict Mirror → Adaptive Mirror → Readable Extension`) so historical structural-mirror deliverables remain valid without being misclassified as `EXACT_TEXT_FRAME`.
- **v1.4.1 / v1.4.2 stage separation**: `source_package`, `source_archive`, and `output_archive` remain distinct stage and archive records. Loading a historical manifest never mutates or rewrites the file on disk.

## 2. Deliverable Contracts (A / B / C)

- **A residual threshold (pre-v1.4.2 vs v1.4.2+)**: the legacy four-word English residual threshold applies only to historical pre-v1.4.2 reports. Active `EXACT_TEXT_FRAME` validation rejects any unapproved source-matched English token in translatable roles.
- **B archive export binding (pre-v1.5.0 vs v1.5.0+)**: pre-v1.5.0 manifests and reports without SHA-256 `content_bindings` or `archive:B-PDF-export` remain readable under their recorded `contract_version`. Active v1.5.0+ archive closure requires full SHA-256 content binding from DOCX → independent PDF render → visual QA → Zotero attachment.
- **C comment length and source map (v1.4.x vs v1.5.0+)**:
  - Historical `1.4.1` / `1.4.2` manifests use `submission_contract.weekly_review.minimum_comment_chars` when recorded in the manifest, falling back to the historical `500` Chinese-character minimum.
  - Active `1.5.0+` work requires `800–1000` effective visible characters in `## 评论`, Main-visible evidence, author-acknowledged limitations by default, and an attributable `c_source_map.json`.

## 3. Zotero Attachment Naming (v1 vs v2)

- **Naming v1 (historical)**: `pdf` / `SI` / `A翻译` / `B精读` (or bracketed `[A]` / `[B]` titles). Specifications without `naming_version` continue to validate under Naming v1.
- **Naming v2 (active default)**: `Main Article` / `Support Information` / `A-Translation` / `B-DeepReading` / `SI-Video-n` / `SI-Data-n` (`naming_version: 2`). Upgrading existing Zotero titles via `zotero_bridge.py normalize-titles` defaults to preview-only and requires explicit authorization (`--yes`).

## 4. Terminology Registry Schema (16-column vs 24-column)

- Historical 16-column `terminology_registry.csv` files (`Discipline`, `Subfield`, etc.) remain readable by `terminology_registry.py` and `validate_deliverables.py`, and upgrade non-destructively to the 24-column v1.5+ schema (`Domain`, `Subdomain`, `Operational_Use`, `Usage_Count`, etc.) on the next registry write while preserving `Evidence_IDs` and correction history.
