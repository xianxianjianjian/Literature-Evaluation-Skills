# Figures, Tables, and Supporting Information

Scientific data and source relationships must be preserved when localizing visual material.

## Tables

Translate titles, headers, labels, footnotes and explanatory text. Lock numerical cells and significance markers to the source and perform cell-by-cell numeric checks.

For wide or dense tables, prefer:

- line wrapping;
- landscape orientation;
- continuation tables;
- readable extension pages;

over unreadably small text.

Never recalculate or silently correct a source table during Translation. If an inconsistency is noticed, preserve the reported value and record an issue for later audit.

## Figures

### Data figures

Normally retain the original figure image/data layer. Do not alter:

- points;
- lines;
- axes/scales;
- error bars;
- color scales;
- significance markers;
- plotted numerical information.

Translate the caption and, when safe, provide a Chinese label map or localized overlay that does not change data.

### Conceptual / timeline / paradigm figures

A Chinese-labeled localization is allowed only when structural relations remain unchanged and the result is clearly identified as a localized version of the original figure.

Any explanatory redraw created for Deep Reading must instead be labeled:

`【根据原文重建，并非作者原图】`

and must not be presented as part of the author's original artwork.

## Supporting Information

Main Article and SI are one evidence package but retain separate source identities (`SRC-M1`, `SRC-S1`, ...).

Rules:

- use one shared paper terminology sheet;
- translate scientifically relevant SI by default for `FULL_MIRROR`;
- preserve a clear Main/SI boundary in A;
- keep page/source correspondence independently traceable for Main and each SI file;
- verify SI figures/tables visually rather than relying only on extracted text.

If expected SI is unavailable, Translation remains `PROVISIONAL` when the missing material may affect completeness or interpretation.

If SI arrives later, run `UPDATE_EXISTING`: set Translation `needs_update`, retranslate/re-QC the affected units and regenerate/reverify A; set Deep Reading `needs_update` when the new SI affects B/C evidence, and regenerate/reverify the affected B/C content as needed. A/B/C are outputs and do not themselves invent a separate `needs_update` state outside the workflow contract.
