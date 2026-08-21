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

Do not bypass paywalls, institutional authentication, download restrictions, or other access controls.

## 3. Attachment labels

Use the shared Zotero naming contract:

```text
[ORIGINAL] Main Article
[SUPPLEMENT] <descriptive name>
```

Later phases add:

```text
[A] 中文全文翻译镜像版
[B] 文献研究笔记·完整精读版
```

After attachment, verify the returned parent/attachment identity rather than treating a submitted request as success.

## 4. Current Phase 2 capability boundary

The repository's `scripts/zotero_bridge.py` implements Zotero Desktop Local API reads (`status`, `find`, `children`, `verify`). The Local API is read-only.

`create` and `attach` remain explicit write interfaces that may be unavailable in the current runtime. If a verified write-capable Zotero route is available, use it. If not, **do not fake successful ingest**.

Instead:

1. stage the selected Main/SI files under `work/<paper_id>/handoff/`;
2. add concrete entries to `pending_zotero_actions` in the weekly manifest;
3. record the expected parent identity and attachment labels;
4. set the relevant Search/output state to `PROVISIONAL` until ingest is verified.

A temporary Zotero write limitation does not invalidate the completed academic search decision, but it prevents the archive from being described as fully complete.

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

After final confirmation, append the selected paper decision to `knowledge/selection_log.csv`. Do not write to `reading_history.csv`; that file is reserved for papers that later complete Deep Reading.

Do not bulk-import all search candidates into Zotero.