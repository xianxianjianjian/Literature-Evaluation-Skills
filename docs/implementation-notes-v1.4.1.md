# v1.4.1 Implementation Notes

The renderer now wraps semantic tokens instead of a flattened whitespace stream. It keeps explicit paragraph breaks, renders citations and scientific exponents using PDF text rise, removes unconstrained character spacing, and chooses a role-appropriate font/leading candidate by source-relative used height.

The validator remains independent from renderer assertions. Visible-English audit rasterizes both source and output pages, crops the same reviewed frame, OCRs both, and fails only when an unapproved source-English sequence of at least four substantive words survives in the output. URLs, DOI lines, declared acronyms and group codes are preserved by policy rather than treated as untranslated prose.

The Yuksel 2025 regression uses all 21 Main/SI pages. Its rebuilt A passed 30 independent checks: numeric integrity, frame closure, visible-English audit, typography evidence, page/box geometry, CJK font containment, leading, tables/figures and outside-frame pixel invariance.

## Verification

- 187 unit and regression tests pass.
- The source tree passes 91 repository/deliverable checks.
- The final bundle and installed `1.4.1` cache each pass 92 plugin/workspace checks, including presence of all three new runtime scripts.
- A versioned local bundle and ZIP were built under the ignored `dist/` directory and installed into the `1.4.1` plugin cache.
