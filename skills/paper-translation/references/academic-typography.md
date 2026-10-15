# Academic paragraph and bilingual typography

Use `paragraph_styles.py` as the shared role-to-style engine for generated A/B/C content. Do not implement one-off indentation rules inside individual text boxes or document writers.

## Chinese project style and APA reference style

Chinese body prose uses this project's reading style: justified alignment, a first-line indent of two Chinese ems, and consistent paragraph/line spacing. This is a project rule, not an APA rule.

APA 7-oriented English prose uses left alignment and a 0.5-inch first-line indent when the deliverable is being reformatted. Skill-generated reference entries use left alignment and a 0.5-inch hanging indent. Never apply the Chinese body first-line indent to titles, headings, captions, table cells, lists, references, block quotes or footnotes. Abstract indentation follows the target deliverable; the shared default uses no first-line indent.

APA-oriented reformatting applies to generated B/C documents, Structural Mirror output and newly generated English explanatory prose. In `EXACT_TEXT_FRAME`, the Version of Record geometry remains authoritative.

## Role map

- `BODY_ZH`: justify; first line 2em.
- `BODY_EN`: left; first line 0.5 inch.
- `ABSTRACT_ZH`: justify; no default first-line indent.
- `ABSTRACT_EN`: left; no default first-line indent.
- `HEADING`, `CAPTION`, `TABLE_CELL`, `FOOTNOTE`: role-specific alignment; no body indent.
- `REFERENCE_APA`: left; 0.5-inch hanging indent.

## Exact Mirror priority and exceptions

For Chinese `BODY` frames, first find a source-safe font scale and leading that fit the reviewed rectangle. Apply justification and 2em indentation only if they still fit at that same scale. Never reduce font size, change column width, move a figure, compress leading below the accepted range, add a page or drop content to satisfy paragraph styling.

When the preferred paragraph style would add a line or overflow, retain the source-frame alignment/indentation and write a `LAYOUT_EXCEPTION` with frame ID, reason and fallback. A documented exception is acceptable only when overflow and clipping remain false.

Priority: content completeness, page geometry, paragraph preference.

## Bilingual typography

Use full-width Chinese punctuation in Chinese prose and one consistent CJK/Latin spacing policy. Remove accidental spaces around Chinese punctuation and between adjacent Chinese text; keep English word boundaries, DOI, variable names, abbreviations, units and statistical expressions intact. Valid examples include `p = .032`, `r = .46`, `F(1, 38) = 5.21`, and `95% CI [0.12, 0.45]`.

Validate generated paragraph records with `validate_paragraph_styles.py`. Required gates are `PARAGRAPH_ALIGNMENT_PASS`, `FIRST_LINE_INDENT_PASS`, `BILINGUAL_TYPOGRAPHY_PASS`, `APA_REFERENCE_FORMAT_PASS`, and `STYLE_ROLE_MAPPING_PASS`. Existing overflow, clipping, page-count and text-layer gates remain independent and mandatory.
