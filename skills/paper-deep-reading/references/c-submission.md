# C submission contract (v1.5.0)

Produce a submission-ready Chinese academic review from a validated B and Main Article. Keep B's full Main/SI audit, evaluator critique, redesign and evidence index intact. C is a selective review, not a miniature B.

## Public document

Use these level-2 headings in order: `期刊`, `发表日期`, `英文题目`, `中文题目`, `作者`, `原文地址`, `评阅人`, `Original Abstract`, `中文摘要`, `评论`. Reuse the canonical Chinese Abstract exactly. The public file must not show Zotero keys, source/audit IDs, B section references, validation or archive status, or an evidence/archive appendix.

Count only the visible text under `## 评论`: 800–1000 characters, preferably 850–950. Markdown syntax and whitespace do not count; Chinese, Latin letters, digits and visible punctuation do. Write 3–5 natural paragraphs without fixed labels. Cover (1) relevant background, gap and question, (2) design and 2–4 core results, (3) contribution and the uncertainty the authors themselves discuss, and (4) cautious field significance. Keep the result chain central; avoid a peer-review-style list of every possible confound.

## Evidence boundary

Default `source_scope=MAIN_VISIBLE_ONLY` and `critique_mode=author_only`. Every visible paper fact must be traceable to Main, including results repeated in SI. Do not insert SI-only results from B. Limitations in default C must be explicitly acknowledged in Main Discussion; keep evaluator-only critique in B. Use `author_plus_major` only when the user explicitly asks for a more critical review, and label the evaluator's judgment accurately. Use outside research only after its source is verified and its role is made explicit.

Build a private `<data-root>/work/<paper_id>/c_source_map.json` with one record per public paragraph. Each material claim needs a unique `claim_id`, an exact visible snippet, `source_class: MAIN`, and a structured `source_anchor` containing Main `source_id`, `sha256`, one-based `page`/`block`, and an exact original `quote`. An optional `section` must match the generated index's actual heading context. A limitation also needs `kind: limitation`, `author_acknowledged: true`, and `section: discussion` or `limitations`. The validator extracts the index itself from a READY verified `source_manifest.json`, checks current Main bytes against its recorded SHA-256, and compares Main DOI/title/version and map identity. An embedded or invented index is never trusted. The map remains private.

The map records `paper_id`, `workflow_id`, `contract_version: 1.5.0`, `doi`, `source_id`, Main `sha256`, `version`, and `source_scope: MAIN_VISIBLE_ONLY`. Add source-grounded `semantic_review` entries for `BACKGROUND_GAP_PASS`, `CORE_RESULT_CHAIN_PASS`, `MAIN_SOURCE_SCOPE_PASS`, `AUTHOR_LIMITATION_POLICY_PASS`, `NO_SI_ONLY_CLAIMS_PASS`, `FIELD_IMPLICATION_PASS`, `CLAIM_STRENGTH_PASS`, and `STYLE_NATURALNESS_PASS`, each with `status`, a specific evidence note, and checked `claim_ids`.

An actual human academic reviewer supplies `signoff`: `reviewer`, timezone-bearing ISO `reviewed_at`, `main_sha256`, SHA-256 of the exact extracted comment body as UTF-8 (`comment_sha256`), `all_material_claims_reviewed: true`, the exact reviewed `semantic_review`, and one judgment per claim. Each judgment includes `claim_id`, `status`, a substantive `reason`, SHA-256 of the exact claim text (`claim_text_sha256`), and the exact reviewed `source_anchor`. Preserve rejected judgments and their reasons. Locating a quotation proves only source presence; the reviewer must judge direction, causal strength, attribution, relevance, and coverage. A generated PASS, placeholder signer, or `evidence: reviewed` cannot substitute for this review. Missing signatures or unextractable Main require REVIEW_REQUIRED/PROVISIONAL; provide reviewed source-bound OCR through the existing source workflow before retrying, rather than silently skipping.

The existing `critique_mode: author_plus_major` exception remains available only on the user's explicit request. Record `critique_approval` with reviewer, reviewed_at and reason; copy the exact approval into signoff. Map evaluator additions as `kind: evaluator_critique`, `attribution: reviewer`, with their real Main premise. Do not mark them author-acknowledged limitations.

Run `scripts/validate_c_review.py --c-path <C.md> --source-map <c_source_map.json> --source-manifest <source_manifest.json> --manifest <workflow_manifest.yaml> --index-report <private-main-index.json> --report <c_validation.json>` and the canonical Abstract check in `validate_deliverables.py` (supply `--source-manifest`). The script checks shape, length, public metadata, actual source location and an attributable source-bound review record; it cannot automatically certify academic semantics. Repeated `在于`, `对于`, `也`, or template transitions call for rewriting the logic, not simply substituting synonyms.

Markdown C has no physical indentation requirement. If C is rendered to DOCX/PDF, map `评论` paragraphs to `BODY_ZH`; keep field headings and Abstract labels unindented. Do not claim that Chinese justification comes from APA. Any generated English prose follows left-aligned APA-oriented styling, and generated references use a 0.5-inch hanging indent.

Do not apply the v1.5.0 length or submission profile retroactively to earlier C artifacts. Record a deliberate update if an older C is revised under this contract.
