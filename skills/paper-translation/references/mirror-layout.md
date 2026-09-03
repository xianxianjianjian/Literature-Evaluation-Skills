# Mirror Layout

`FULL_MIRROR` controls translation coverage. Its default layout fidelity is `EXACT_TEXT_FRAME`: preserve the publisher page as a fixed canvas and replace only reviewed source text frames with Chinese.

## Exact text-frame invariant

For each Main/SI page preserve:

- page order, count, rotation, MediaBox, CropBox, TrimBox, BleedBox and ArtBox;
- columns, headers, footers, rules, backgrounds, figures, tables and object positions;
- each source text-frame rectangle, alignment, color, leading and visual weight;
- one source page to one output page, with no extension pages.

Do not treat a visually similar reflow, a page-wide white panel, a translated appendix, or a source-image-plus-translation-map as exact mirror output.

## SimSun typography

Chinese glyphs must use the locally installed `SimSun` face from `simsun.ttc`, embedded as a PDF subset. Font fallback is forbidden. Preserve ordinary/bold/italic intent through SimSun regular, synthetic stroke, and synthetic shear.

For each frame, keep the source font size first, then try exactly:

`1.00 → 0.99 → 0.98 → 0.97 → 0.96 → 0.95`

Do not change the source frame, leading, paragraph spacing, column width or page geometry. Do not compress tracking. If the faithful concise translation still does not fit at `0.95`, create a `TRI-xxx` layout issue and keep A `PROVISIONAL`.

## Required production chain

1. Fix-render every source, including DOCX SI, to paginated PDF.
2. Build schema-v2 `source_inventory.json` with page boxes, objects and table cells.
3. Run `extract_text_frames.py`, then visually review every candidate. Correct reading order, kind, bounding box, background and translation action; `reviewed: false` cannot enter a plan.
4. Mark author names, references, formulas, identifiers and logos `RETAIN_SOURCE` with an allowed reason. Translate affiliations, captions, headings, body, table text and figure labels unless a source gap is logged.
5. Create strict `font_map.json`:

```text
python scripts/mirror_pdf.py create-font-map \
  --font-path C:\Windows\Fonts\simsun.ttc \
  --output <work-dir>/font_map.json
```

6. Create the exact plan:

```text
python scripts/mirror_pdf.py create-plan \
  --source-inventory <work-dir>/source_inventory.json \
  --text-frame-inventory <work-dir>/text_frame_inventory.jsonl \
  --font-map <work-dir>/font_map.json \
  --output <work-dir>/mirror_layout_plan.json \
  --output-pdf <A.pdf> \
  --layout-fidelity EXACT_TEXT_FRAME \
  --cjk-font-family SimSun \
  --minimum-font-scale 0.95
```

7. Render only through:

```text
python scripts/render_exact_mirror.py --work-dir <work-dir> --output <A.pdf>
```

Uniform backgrounds may use a frame-sized fill. Non-uniform backgrounds require a reviewed clean patch restricted to that frame. If a clean patch would erase a data mark, line, image or decoration, stop that frame as `PROVISIONAL`.

8. Render and visually compare every page. Human notes help diagnose problems but do not satisfy validation.
9. Run `validate_translation_package.py`; it independently generates `layout_diff.json` and checks page geometry, SimSun embedding/CJK use, frame containment, table cells, English-token accounting and pixels outside replacement regions.

## Tables and figures

Exact tables use `exact-cells`: retain the source grid and numeric data, then translate each textual cell in its original cell frame. Image-map fallback, flattened prose and continuation tables are forbidden.

Retain figure data pixels. Replace each translatable embedded label only within its reviewed label frame. Every pixel outside figure-label frames must remain unchanged.

## Explicit structural mirror

Use `STRUCTURAL_MIRROR` only when the user asks for readable structural correspondence rather than original-position replacement. In that mode the legacy escalation may be used:

`Strict Mirror → Adaptive Mirror → Readable Extension`

Name and report that artifact as a structural mirror. Never use it as evidence that `EXACT_TEXT_FRAME` passed.
