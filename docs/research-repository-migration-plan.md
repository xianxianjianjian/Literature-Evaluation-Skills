# Research Archive Separation Plan

Status: planned; no automatic migration performed.

The current W36 research records are historically committed in the plugin repository. Moving them during a code hardening release would mix provenance rewriting with runtime changes and risks breaking the existing links.

## Proposed non-destructive sequence

1. Create a dedicated private research Git repository outside both the installed plugin and the current data root.
2. Copy only `knowledge/` and `weekly_reviews/` with Git history preserved where feasible; keep `work/`, source PDFs, DOCX and local handoff files outside public Git.
3. Validate W36 paths, C content, correction history and Zotero keys in the destination.
4. Set `workspace.json.research_git_root` to the verified destination.
5. Freeze the old repository paths with a migration pointer; remove nothing until the destination commit and remote are verified.

Until those steps are explicitly authorized and completed, W36 remains at its current paths and is labeled `migration required: yes`.
