# C submission contract (v1.5.0)

Produce a submission-ready Chinese academic review from a validated B and Main Article. Keep B's full Main/SI audit, evaluator critique, redesign and evidence index intact. C is a selective review, not a miniature B.

## Public document

Use these level-2 headings in order: `期刊`, `发表日期`, `英文题目`, `中文题目`, `作者`, `原文地址`, `评阅人`, `Original Abstract`, `中文摘要`, `评论`. Reuse the canonical Chinese Abstract exactly. The public file must not show Zotero keys, source/audit IDs, B section references, validation or archive status, or an evidence/archive appendix.

Count only the visible text under `## 评论`: 800–1000 characters, preferably 850–950. Markdown syntax and whitespace do not count; Chinese, Latin letters, digits and visible punctuation do. Write 3–5 natural paragraphs without fixed labels. Cover (1) relevant background, gap and question, (2) design and 2–4 core results, (3) contribution and the uncertainty the authors themselves discuss, and (4) cautious field significance. Keep the result chain central; avoid a peer-review-style list of every possible confound.

## Evidence boundary

Default `source_scope=MAIN_VISIBLE_ONLY` and `critique_mode=author_only`. Every visible paper fact must be traceable to Main, including results repeated in SI. Do not insert SI-only results from B. Limitations in default C must be explicitly acknowledged in Main Discussion; keep evaluator-only critique in B. Use `author_plus_major` only when the user explicitly asks for a more critical review, and label the evaluator's judgment accurately. Use outside research only after its source is verified and its role is made explicit.

Build a private `<data-root>/work/<paper_id>/c_source_map.json` with one record per public paragraph. Each material claim needs an exact visible snippet, `source_class: MAIN`, and a Main source anchor. A limitation also needs `kind: limitation`, `author_acknowledged: true`, and a Main Discussion anchor. Add source-grounded `semantic_review` entries for `BACKGROUND_GAP_PASS`, `CORE_RESULT_CHAIN_PASS`, `MAIN_SOURCE_SCOPE_PASS`, `AUTHOR_LIMITATION_POLICY_PASS`, `NO_SI_ONLY_CLAIMS_PASS`, `FIELD_IMPLICATION_PASS`, `CLAIM_STRENGTH_PASS`, and `STYLE_NATURALNESS_PASS`, each with `status: PASS` and a specific evidence note. The map remains private.

Run `scripts/validate_c_review.py --c-path <C.md> --source-map <c_source_map.json>` and the canonical Abstract check in `validate_deliverables.py`. The script checks shape, length, public metadata and recorded provenance; the reviewer must compare the mapped claims with Main and judge whether background, core results, limitations, implications and prose are faithful and natural. Repeated `在于`, `对于`, `也`, or template transitions call for rewriting the logic, not simply substituting synonyms.

Markdown C has no physical indentation requirement. If C is rendered to DOCX/PDF, map `评论` paragraphs to `BODY_ZH`; keep field headings and Abstract labels unindented. Do not claim that Chinese justification comes from APA. Any generated English prose follows left-aligned APA-oriented styling, and generated references use a 0.5-inch hanging indent.

Do not apply the v1.5.0 length or submission profile retroactively to earlier C artifacts. Record a deliberate update if an older C is revised under this contract.
