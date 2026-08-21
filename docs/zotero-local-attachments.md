# Zotero 10+ Local Attachments — Phase 8 Integration Note

This document defines the durable local-file attachment adapter introduced on `phase-8-zotero-local-attachments`.

It extends the Phase-7 parent-create work. It does **not** change paper selection or academic-analysis rules.

## Why Phase 8 exists

The literature-evaluation workflow needs to attach files to a Zotero parent over a long lifecycle:

```text
selected paper
→ Main/SI ingest
→ later A translation PDF
→ later B deep-reading DOCX
```

The Connector `/connector/saveAttachment` route is tied to a short-lived Connector save session and a Connector-side parent id. That is appropriate for immediate browser-save attachments but not for a resumable existing-parent archive that may continue much later.

Zotero 10+ Local API v3 provides the durable path needed by this workflow: authorized local item writes plus the full file-upload protocol, all against the local Zotero database.

## Runtime requirements

Durable attachment requires:

- Zotero 10+ Desktop;
- Local API enabled in Zotero;
- port `23119` reachable locally;
- Local API discovery response containing `Zotero-Server-ID`;
- a writable target library for the requested parent;
- the user allowing the local write request when Zotero presents the authorization prompt.

The helper does not use or require a zotero.org cloud API key.

## Authorization and secret handling

The write flow calls:

```text
POST /api/local/authorize
```

with the current `Zotero-Server-ID` and the application name.

Rules:

- authorization happens in Zotero Desktop;
- the returned Local API key exists only in process memory;
- the helper never prints it;
- the helper never writes it to Git, YAML, JSON, CSV, `.env`, logs, or pending actions;
- a temporary/non-remembered key is treated as single-use and discarded after a successful write request;
- a remembered key may remain only inside the running process;
- HTTP 401 permits one re-authorization attempt;
- HTTP 412 or a changed `Zotero-Server-ID` stops the operation and requires reconnecting to the current Zotero database.

## Existing-parent attachment flow

`scripts/zotero_bridge.py attach` uses `scripts/zotero_local_archive.py` and `scripts/zotero_local_write.py`.

The normal durable flow is:

```text
1. calculate local file descriptor
2. connect and capture Zotero-Server-ID
3. verify parent is a top-level bibliographic item
4. inspect existing same-label child attachments
5. create or safely reuse an attachment child
6. obtain Local API write authorization
7. request file-upload authorization
8. upload bytes to the returned local upload URL
9. register uploadKey
10. read attachment back using the same Zotero-Server-ID
11. verify parent + filename + MD5
12. return verified attachment key
```

The default library prefix is `users/0`. A group library may be addressed with `groups/<numeric-group-id>` only when that target is intentionally selected and writable.

## Preview versus real write

Preview mode:

```bash
python scripts/zotero_bridge.py attach \
  --parent-key <KEY> \
  --file <PATH> \
  --name "[ORIGINAL] Main Article"
```

Preview calculates local file metadata but does not connect to Zotero, request authorization, create a child, or upload bytes.

Actual write:

```bash
python scripts/zotero_bridge.py attach \
  --parent-key <KEY> \
  --file <PATH> \
  --name "[ORIGINAL] Main Article" \
  --yes
```

The workflow's earlier final-paper confirmation may already authorize normal Main/SI/A/B archival actions, but the CLI still requires `--yes` as a mechanical write boundary.

## Idempotency and resume semantics

The adapter uses the requested Zotero child title as an archive slot and compares file identity before writing.

### `NEW`

No same-title attachment child exists. Create a new imported-file child and upload the file.

### `ALREADY_VERIFIED`

A single same-title child already has the same filename and MD5. Do not rewrite anything. Return:

```text
ALREADY_ATTACHED_AND_VERIFIED
```

with its existing attachment key.

### `REUSE_PARTIAL`

A single same-title imported-file child exists but has no filename and no MD5, consistent with an interrupted run after child creation but before file registration. Reuse that child key and continue the upload instead of creating a duplicate.

### `CONFLICT`

Stop without overwrite when:

- multiple same-title attachments exist;
- the same-title child has an unexpected structural identity;
- the same-title attachment points to a different filename/MD5.

Return `ATTACHMENT_CONFLICT`; operator/user resolution is required before replacing or deleting anything.

## Full-upload contract

For a child attachment item, the helper follows the Zotero v3 full-upload pattern:

1. `POST /items/<attachmentKey>/file` with `md5`, `filename`, `filesize`, `mtime` and `If-None-Match: *`;
2. if the file is not already present, POST the bytes using the returned `url`, `prefix`, `suffix`, `contentType`, and `uploadKey`;
3. register the returned `uploadKey` with another POST to `/items/<attachmentKey>/file`;
4. read the attachment item back and verify metadata.

When Zotero reports the file already exists, the byte upload/registration portion can be skipped, but post-write/read verification is still required.

## Verification contract

A successful upload request is insufficient. Completion requires all of:

- item type is `attachment`;
- `parentItem` equals the requested parent key;
- link mode is imported-file compatible;
- `filename` equals the local file name;
- Zotero `md5` equals the local file MD5;
- the verification read is bound to the same `Zotero-Server-ID` discovered at connection time.

Only then may the workflow use the attachment key as verified archive evidence.

## Incomplete writes

If an attachment child is created or reused but file upload/verification fails, return:

```text
ATTACHMENT_FILE_UPLOAD_INCOMPLETE
```

and include the attachment key. The workflow should preserve that key as a recovery hint and leave the relevant archive action pending/PROVISIONAL.

The next run may reuse a genuinely empty child. The adapter does not silently delete failed children, because deletion is a separate destructive operation and may require operator review.

## File and privacy boundaries

- Main/SI/A/B bytes are sent to the user's local Zotero endpoint; they are not committed to Git by this adapter.
- Local API authorization secrets are not persisted.
- The project helper currently applies a 256 MiB single-file safety limit. This is a project-side guardrail, not a statement of Zotero's official maximum upload size.
- Research files remain excluded by `.gitignore`.

## Current validation level

**Code/protocol/mock validation: PASS on the Phase-8 CI line.**

Automated tests cover:

- Server-ID discovery;
- authorization handling and temporary-key disposal;
- one reauthorization attempt after 401;
- Server-ID mismatch rejection;
- attachment child schema;
- MD5/filesize/mtime calculation;
- upload authorization, byte upload, upload-key registration;
- parent/filename/MD5 verification;
- idempotent exact match;
- interrupted-child reuse;
- conflict refusal;
- incomplete-upload recovery metadata;
- preview mode with no Zotero contact.

**Live production validation: OPEN.**

GitHub Actions cannot display the user's Zotero Desktop authorization dialog or write to the user's local library. Before calling the adapter production-validated, run a controlled local Zotero 10+ test and verify the resulting parent/child/file in Zotero.

## Relationship to Phase 7

`docs/zotero-write-adapter.md` records the Phase-7 decision and Connector limitations discovered at that time. Phase 8 supersedes only its conclusion that durable generic attachment was unavailable: Zotero 10+ Local API now provides the durable existing-parent route. The Phase-7 parent-create implementation remains active unless a later phase explicitly migrates it.
