# Zotero Ingest

Zotero ingest happens only after the user explicitly confirms the final focal paper. That confirmation authorizes ordinary identity matching, legal-access source retrieval, parent creation when supported, and attachment of Main/SI without repeated permission prompts, except for duplicate ambiguity, DOI/title conflict, unresolved version conflict, attachment conflict, denied local authorization, or a true technical blocker.

## 1. Match before creating

Prefer parent matching in this order:

1. normalized DOI;
2. exact/near-exact title plus author/year context;
3. other stable bibliographic fields when DOI is absent.

Use `scripts/zotero_bridge.py find` and `children` for safe checks when Zotero Desktop Local API is available.

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

Zotero Desktop Local API supports normal item reads used by:

- `status`;
- `find`;
- `children`;
- `verify`.

On Zotero 10+, the same Local API also exposes an authorized write/full-upload path. Durable attachment work must first confirm the presence of `Zotero-Server-ID`; older/unverified local environments remain read-only for this workflow.

### Parent create path

Bibliographic parent creation retains the verified Phase-7 Connector route `/connector/saveItems`.

Required safety sequence:

1. prepare structured metadata; do not guess creator parsing or missing bibliographic fields;
2. `find` by normalized DOI or exact title before writing;
3. refuse a duplicate/ambiguous parent;
4. inspect/resolve the Connector save target;
5. execute `create --metadata <file> --yes` only when the write is already authorized by workflow context;
6. require Connector HTTP 201;
7. search the Local API again by DOI/title;
8. only one verified matching parent may be recorded as `CREATED_AND_VERIFIED` with its item key.

A successful POST without a unique post-write identity check is **not** ingest completion.

### Zotero 10+ durable attachment path

For an existing parent, Main/SI/A/B attachment uses Zotero 10+ Local API full upload, not the short-lived Connector `/saveAttachment` session route.

Normal command form:

```bash
python scripts/zotero_bridge.py attach \
  --parent-key <ZOTERO_PARENT_KEY> \
  --file <LOCAL_FILE> \
  --name "[ORIGINAL] Main Article" \
  --yes
```

Default library is `users/0`. Use `--library-prefix groups/<id>` only when the target group is explicitly known and writable.

Safety sequence:

1. without `--yes`, calculate only the local file descriptor/preview; do not contact Zotero for authorization or write;
2. with `--yes`, discover the current Zotero 10+ `Zotero-Server-ID`;
3. verify that `parent_key` is a top-level bibliographic item in that same local database;
4. inspect existing child attachments with the requested label;
5. if title + filename + MD5 already match, return `ALREADY_ATTACHED_AND_VERIFIED` without rewriting;
6. if a same-title child is an empty interrupted shell, reuse that key and resume upload;
7. if same-title children are ambiguous or point to a different file, stop as `ATTACHMENT_CONFLICT`; never silently overwrite;
8. otherwise create an imported-file child under the parent;
9. request Local API write authorization in Zotero Desktop; the key must remain process-local and never enter Git/logs/manifests;
10. execute the documented full-upload authorization → byte upload → upload-key registration sequence;
11. read the attachment back using the same `Zotero-Server-ID` and require parent, filename and MD5 agreement;
12. only then return `ATTACHED_AND_VERIFIED` and record the attachment key.

If the child exists but file upload/verification fails, record `ATTACHMENT_FILE_UPLOAD_INCOMPLETE` plus the returned child key so a later run can resume. Do not mark the archive COMPLETE.

### Authorization behavior

Zotero Desktop controls Local API write permission. If the user denies authorization, or the environment does not expose Zotero 10+ write capability, preserve pending actions and stop cleanly.

The helper does not persist the Local API key. Temporary single-use authorization is discarded after the successful write request; a remembered authorization may be reused only within the running process. A `Zotero-Server-ID` mismatch invalidates the active archive operation and requires reconnecting before any further write.

## 5. Downgrade / pending path

When the required source file, Zotero Desktop, write authorization, or compatible Local API is unavailable:

1. retain any already verified parent/attachment keys;
2. if a local working runtime exists, stage acquired Main/SI/A/B files under `work/<paper_id>/handoff/`;
3. append concrete unresolved records to `workflow_manifest.yaml.pending_zotero_actions`;
4. record expected source IDs and attachment labels;
5. keep the affected archive state `PROVISIONAL` until each required attachment is actually observable and verified.

If the source files themselves are unavailable, record that source blocker separately; a Zotero capability failure and a source-availability failure are not the same condition.

A temporary Zotero limitation does not invalidate an otherwise defensible Search selection, but it prevents the archive from being described as fully complete.

## 6. `selected_paper.yaml`

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

## 7. `source_manifest.json`

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

## 8. Selection history

After final confirmation, append the selected paper decision to `knowledge/selection_log.csv`. Do not write to `reading_history.csv`; that file is reserved for papers that later genuinely complete Deep Reading.

Do not bulk-import all search candidates into Zotero.
