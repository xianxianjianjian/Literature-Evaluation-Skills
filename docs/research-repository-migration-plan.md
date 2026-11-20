# Research Archive Separation Plan

Status: completed in v1.6.0 development (`knowledge/` and `weekly_reviews/` migrated to a dedicated standalone research Git repository; the plugin repository retains only clean workspace templates and sanitized legacy fixtures under `tests/fixtures/legacy/`).

The historical W33–W42 research records were previously committed in the plugin repository. They have now been separated into a standalone research Git repository with commit history preserved.

## Completed non-destructive sequence

1. Created a dedicated research Git repository outside both the installed plugin and the active data root.
2. Copied `knowledge/` and `weekly_reviews/` with Git history and commit SHAs preserved; kept `work/`, source PDFs, DOCX and local handoff files outside public Git.
3. Validated W36 paths, C content, correction history and Zotero keys in the destination.
4. Set `workspace.json.research_git_root` to the verified destination.
5. Replaced the plugin repository's root `knowledge/` and `weekly_reviews/` with clean workspace templates and sanitized regression fixtures under `tests/fixtures/legacy/`.
