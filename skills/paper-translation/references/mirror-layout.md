# Mirror Layout

A is a readable Chinese mirror PDF that preserves scientific page/structure relationships. It is not required to reproduce publisher typography pixel-for-pixel.

## Priority order

When layout tradeoffs are necessary, prioritize:

1. page correspondence;
2. section/structural correspondence;
3. nearby figure/table placement;
4. paragraph correspondence;
5. line correspondence.

Readability must not be sacrificed merely to preserve line-level similarity.

## Escalation strategy

Use the frozen three-level sequence:

1. **Strict Mirror** — preserve the original page, column structure and nearby figure/table placement where natural.
2. **Adaptive Mirror** — allow moderate font, spacing, column-width and local object-placement changes while keeping page/structure correspondence.
3. **Readable Extension** — add a continuation/extension page when the Chinese translation cannot fit readably.

## Chinese typography

Chinese is often more compact than English. When appropriate, begin around `105%–115%` of the source visual body-font size and adjust according to actual occupancy.

Do not mechanically preserve a small English font when the Chinese page has excessive empty space. Conversely, do not force ordinary Chinese body text below approximately `8.5 pt` merely to keep the page count identical. `8.5 pt` is an extreme safety floor, not a target. Use Readable Extension instead of further compression.

## Columns and special objects

Preserve single/double-column structure by default, with local exceptions for wide tables, full-width figures, equations or other scientific objects.

Publisher decorative elements, advertisements and non-scientific branding are lower priority than readable scientific content and source correspondence.

## Overflow and extension tracking

Every detected overflow or extension decision should be traceable in the layout plan or translation issue log. An extension page must identify which source page/section it continues so reverse mapping remains possible.