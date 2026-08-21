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

`scripts/zotero_bridge.py` exposes per-operation capability rather than one generic “Zotero write works” flag.

### Read path

Zotero Desktop Local API under `/api/` remains read-only and supports:

- `status`;
- `find`;
- `children`;
- `verify`.

### Parent create path

Bibliographic parent creation is implemented through the Zotero Connector server's official `/connector/saveItems` route.

Required safety sequence:

1. prepare structured metadata; do not guess creator parsing or missing bibliographic fields;
2. `find` by normalized DOI or exact title before writing;
3. refuse a duplicate/ambiguous parent;
4. execute `create --metadata <file> --yes` only when the write is already authorized;
5. require Connector HTTP 201;
6. search the read-only Local API again by DOI/title;
7. only one verified matching parent may be recorded as `CREATED_AND_VERIFIED` with its item key.

A successful POST without a unique post-write identity check is **not** ingest completion.

### Attachment path

Local-file attachment to an existing parent is still explicitly unsupported by the repository helper:

`LOCAL_FILE_ATTACH_ROUTE_NOT_IMPLEMENTED_OR_VERIFIED`

Do not invent an undocumented Connector/plugin request in order to attach Main/SI/A/B. Parent creation and attachment capability are separate gates.

When attachment capability is unavailable:

1. retain any already verified parent key;
2. if a local working runtime exists, stage acquired Main/SI files under `work/<paper_id>/handoff/`;
3. append concrete attachment records to `workflow_manifest.yaml.pending_zotero_actions`;
4. record expected source IDs and attachment labels;
5. keep the relevant archive state `PROVISIONAL` until each attachment is actually observable and verified.

If the source files themselves are unavailable, record that source blocker separately; a Zotero attachment limitation and a source-availability failure are not the same condition.

A temporary Zotero limitation does not invalidate an otherwise defensible Search selection, but it prevents the archive from being described as fully complete.

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
