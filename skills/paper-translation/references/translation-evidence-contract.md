# Translation Evidence Contract

Use inventory, ledger and issue evidence for every translation scope. `FULL_MIRROR` defaults to `EXACT_TEXT_FRAME` and activates the schema-v2 geometry/font contract below. These files answer different questions and cannot be replaced by a hand-written “QC passed” statement.

## 1. `source_inventory.json`

Exact mirror requires:

- `schema_version: 2`, `scope: FULL_MIRROR`, `layout_fidelity: EXACT_TEXT_FRAME`;
- `sources`: `source_id`, `role`, `page_count`, fixed `pdf_path` and availability;
- `pages`: source/output page, all five PDF boxes, rotation, unit/object/frame IDs;
- `units`: stable frame-level translation units;
- `objects`: every scientific figure/table with page `bbox_pt` and label frames.

Each table additionally records topology and every cell:

```json
{
  "object_id": "TAB-S1",
  "kind": "table",
  "bbox_pt": [72, 220, 520, 460],
  "table_structure": {
    "rows": 8,
    "columns": 5,
    "header_rows": 2,
    "merged_cells": 3,
    "footnotes": 2
  },
  "cells": [
    {
      "row": 1,
      "column": 1,
      "row_span": 1,
      "column_span": 2,
      "bbox_pt": [72, 430, 250, 460],
      "frame_id": "TF-S1-P003-T001-C001"
    }
  ]
}
```

Render DOCX SI once to fixed PDF before assigning page positions. Inspect rendered pages and DOCX drawing relationships so floating SI figures cannot disappear.

## 2. `text_frame_inventory.jsonl`

Every source text frame, table cell and figure label requires:

- `frame_id`, source page, `unit_id`, kind and reading order;
- bottom-left PDF `bbox_pt` and rotation;
- source font, font size, leading, weight, alignment and background;
- `translation_action: TRANSLATE | RETAIN_SOURCE`;
- an allowed `retain_reason` for retained frames;
- `reviewed: true` after visual source-page inspection.

Automatic extraction produces `reviewed: false` and `background: UNREVIEWED`. Those values must be corrected before plan creation. One exact ledger unit maps to exactly one source frame.

## 3. `translation_ledger.jsonl`

Exact rows retain the ordinary provenance fields and additionally require:

- exactly one `frame_id`;
- `source_text` and `translated_text`;
- actual `font_scale_used` from `0.95` through `1.00`;
- `fit_status: FIT` for completion;
- `untranslated_tokens`, each with token text and reason.

`OVERFLOW` is usable evidence but prevents `COMPLETE`. Do not claim overflow is solved by moving the frame, changing leading or adding a page.

## 4. `font_map.json`

Required exact settings:

```json
{
  "schema_version": 1,
  "cjk_font_family": "SimSun",
  "font_path": "C:\\Windows\\Fonts\\simsun.ttc",
  "ttc_face_index": 0,
  "fallback_allowed": false,
  "regular_mode": "embedded-subset",
  "bold_mode": "synthetic-stroke",
  "italic_mode": "synthetic-shear",
  "expected_pdf_font_name": "SimSun"
}
```

The font file itself is not committed. If it is absent or cannot be embedded, use `BLOCKED`; never silently select another CJK font.

## 5. `mirror_layout_plan.json`

Schema v2 maps every source page to exactly one output page and records:

- source/output page identity and all page boxes;
- every reviewed frame and replacement region;
- exact table-cell placements and scientific object IDs;
- `layout_strategy_used: exact-text-frame`;
- `extension_page: false`;
- actual font scale and fit result after rendering.

`render_checked` and render notes are diagnostic only. They are not completion evidence.

## 6. `translation_issues.jsonl`

Each issue requires `issue_id`, `status` and `completion_impact`. A SimSun absence is `BLOCKED`; an unresolved frame/background/overflow or untranslated label is normally `PROVISIONAL`.

## Independent completion check

```text
python scripts/validate_translation_package.py \
  --work-dir <work-dir> \
  --a-path <A.pdf> \
  --scope FULL_MIRROR \
  --layout-fidelity EXACT_TEXT_FRAME \
  --report <work-dir>/translation_validation.json
```

The validator generates `layout_diff.json` itself and recomputes page boxes, rotations, one-to-one mapping, replacement frames, table cells, embedded/CJK SimSun use, 95%-100% glyph sizing, English-token accounting and same-renderer pixels outside replacement frames. Do not edit either validation report.

Use the existing `source_manifest.json` for source identity. Do not add per-unit, per-page, per-object or font hashes.

## Legacy and non-exact scopes

Schema-v1 evidence remains readable as `LEGACY_STRUCTURAL`. It cannot be re-certified as `EXACT_TEXT_FRAME`. `MAIN_ONLY` and `ABSTRACT_ONLY` continue to use their existing content evidence without exact-layout files.
