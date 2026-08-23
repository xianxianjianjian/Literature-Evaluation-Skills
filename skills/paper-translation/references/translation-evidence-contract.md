# Translation Evidence Contract

Use the inventory, ledger and issue portions of this contract for every manifest translation scope before Translation/A is marked `COMPLETE`. `FULL_MIRROR` additionally requires the layout plan and page/object/table checks. The files below answer different questions and must not be replaced by a self-authored “QC passed” statement.

## 1. `source_inventory.json` — what exists in the source package?

Required root fields:

- `schema_version: 1`;
- `scope`: `FULL_MIRROR`, `MAIN_ONLY`, or `ABSTRACT_ONLY`;
- `sources`: source ID, role (`MAIN`/`SI`), fixed-render page count and availability status;
- `pages`: `source_id`, positive `source_page`, `unit_ids`, and `object_ids`;
- `units`: `unit_id`, `source_id`, `source_page`, and scientific-content `kind`;
- `objects`: every scientific figure/table with `object_id`, source locator, kind and label when present.

For tables, also record:

```json
{
  "table_structure": {
    "rows": 8,
    "columns": 5,
    "header_rows": 2,
    "merged_cells": 3,
    "footnotes": 2
  }
}
```

Do not inventory only text paragraphs. Inspect PDF page renders and DOCX relationships/drawings so inline and floating SI images cannot disappear. Render DOCX SI once to a fixed paginated PDF before assigning page locators.

## 2. `translation_ledger.jsonl` — what happened to every text unit?

Each line requires:

- `unit_id`, `source_id`, `source_page`, `section`, `unit_index`, `kind`;
- `source_status`;
- `translation_status`: `TRANSLATED` or `SOURCE_GAP`;
- `output_pages`: positive A page numbers;
- `issue_ids`.

`SOURCE_GAP` requires a `TRI-xxx` issue. A translated unit requires at least one output page. The ledger must cover exactly the units in the source inventory.

## 3. `mirror_layout_plan.json` — where did each page and object go?

Generate the initial plan with `scripts/mirror_pdf.py`. For every output page record:

- `output_page_number`;
- one or more `source_page_refs`;
- `placed_object_ids`;
- `table_placements`;
- layout strategy and extension relationship;
- `render_checked` plus a concrete comparison note.

For a native table, record output rows/columns/header rows and whether merged cells and footnotes were preserved. If a native grid cannot remain readable, use `source-image-with-translation-map` and confirm the Chinese header/footnote map is complete. Flattening cells into unrelated prose rows is not an allowed fallback.

## 4. `translation_issues.jsonl` — what remains unresolved?

Each issue requires `issue_id`, `status` (`OPEN`/`RESOLVED`) and `completion_impact` (`NONE`/`PROVISIONAL`/`BLOCKED`). An open consequential issue prevents Translation/A `COMPLETE`.

## Independent completion check

Run after A is rendered and visually compared:

```text
python scripts/validate_translation_package.py \
  --work-dir <data-root>/work/<paper_id> \
  --a-path <A.pdf> \
  --scope FULL_MIRROR \
  --report <data-root>/work/<paper_id>/translation_validation.json
```

The command recomputes inventory, ledger, source-page, object and table-topology coverage. Do not hand-write or edit `translation_validation.json`. Semantic fidelity and visual quality still require direct source/output comparison; the validator prevents those judgments from being made over an incomplete object/page set.

Use the existing `source_manifest.json` identity fields for source-version control. Do not add per-unit, per-page or per-object hashes.
