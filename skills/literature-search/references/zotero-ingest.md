# Zotero Ingest

Zotero ingest happens only after the user explicitly confirms the final focal paper. That confirmation authorizes ordinary identity matching, legal-access source retrieval, parent creation when supported, and attachment of Main/SI without repeated permission prompts, except for duplicate ambiguity, DOI/title conflict, unresolved version conflict, or a true technical blocker.

## 1. Match before creating

Prefer parent matching in this order:

1. normalized DOI;
2. exact/near-exact title plus author/year context;
3. other stable bibliographic fields when DOI is absent.

Use `scripts/zotero_bridge.py find` and `children` for safe read-only checks when Zotero Desktop Local API is available.

Stop for user or operator resolution when there is:

- more than one plausible parent;
- DOI/title disagreement;
- conflicting Version of Record/preprint identity;
- uncertainty about whether two records are duplicates.

Do not create duplicate parents merely because an existing item lacks an attachment.

## 2. Preferred source package

Prefer Version of Record metadata and legally accessible sources. Retrieve and record, when discoverable:

- Main Article;
- all Supporting Information/supplementary files relevant to the article;
- correction/erratum material;
- version/status information.

Do not bypass paywalls, institutional authentication, download restrictions, or other access controls. Source-text reuse in public Git must also follow `shared/data-format-policy.md`; access to a webpage is not automatic permission to republish its text.

## 3. Attachment labels

Use the shared Zotero naming contract:

```text
[ORIGINAL] Main Article
[SUPPLEMENT] <descriptive name>
```

Later stages add:

```text
[A] 中文全文翻译镜像版
[B] 文献研究笔记·完整精读版
```

After any write, verify the actual parent/attachment identity rather than treating a submitted request or HTTP success code as archive success.

## 4. V1 capability boundary

`scripts/zotero_bridge.py` exposes truthful capability status:

- Zotero Desktop Local API under `/api/` is read-only and supports `status`, `find`, `children`, and `verify`;
- the Zotero Connector server can be probed separately;
- `create` and `attach` are declared workflow interfaces but **must not report success until a supported write adapter has been implemented and verified in the target runtime**.

Connector availability alone is not proof that the repository helper can safely perform the exact requested parent/file write.

When no verified write route exists:

1. if a local working runtime exists, stage acquired Main/SI files under `work/<paper_id>/handoff/`;
2. append concrete records to `workflow_manifest.yaml.pending_zotero_actions` (the bridge `pending` command may prepare the record but does not write Zotero);
3. record the expected parent identity, source id and attachment label;
4. keep Search `PROVISIONAL` when Zotero/archive completion is the only remaining gap;
5. verify and clear each pending action only after the real Zotero parent/attachment is observable.

If the source files themselves are unavailable, record that source blocker separately; a Zotero outage and a source-availability failure are not the same condition.

A temporary Zotero write limitation does not invalidate an otherwise defensible Search selection, but it prevents the archive from being described as fully complete.

## 5. `selected_paper.yaml`

Store under `work/<paper_id>/selected_paper.yaml` and include at least:

- `schema_version`;
- `paper_id`;
- title;
- authors;
- journal;
- DOI;
- year and online date when known;
- publication status/version;
- weekly role (`Primary` when selected from the weekly workflow);
- user-confirmation date;
- Quality Gate;
- weighted-score summary;
- selection rationale;
- known cautions;
- Zotero parent key or `null`;
- ingest status.

Unknown source fields must remain `null`; do not infer them from common publishing practice.

## 6. `source_manifest.json`

Create/update `work/<paper_id>/source_manifest.json`. Each source record should preserve:

- stable source id such as `SRC-M1` / `SRC-S1`;
- source type;
- bibliographic/version identity;
- origin URL or repository/publisher source when appropriate;
- acquired/checked date;
- local staging path only as a temporary locator, never identity;
- availability/status;
- checksum when available/useful;
- Zotero attachment key or `null`;
- known gap or verification note.

Main, every Supplement, and correction material should be separate source records.

## 7. Selection history

After final confirmation, append the selected paper decision to `knowledge/selection_log.csv`. Do not write to `reading_history.csv`; that file is reserved for papers that later genuinely complete Deep Reading.

Do not bulk-import all search candidates into Zotero.
