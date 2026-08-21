# Zotero Write Adapter — V1 Integration Note

This note defines the implemented and unimplemented Zotero write operations for the isolated `phase-7-zotero-write-adapter` branch.

## Source-of-truth boundary

Zotero Desktop exposes two relevant local interfaces on port `23119`:

- `/api/...`: Zotero Web API v3-compatible local interface, **read-only**;
- `/connector/...`: Connector server routes used for desktop save/import workflows.

The repository does not treat “Connector is reachable” as proof that every desired write is supported.

## Implemented: selected save target

Before an actual parent write, the helper can inspect the Connector save target through:

```text
POST /connector/getSelectedCollection
```

`selected-target` reports the active library/collection and its editability. `selected-target --writable` requests the writable target that Zotero would use for saving and exposes:

- library id/name;
- collection id/name;
- bibliographic editability;
- file editability.

`create --yes` resolves this writable target before the write and includes it in the result, so the destination is not an invisible side effect.

## Implemented: bibliographic parent creation

`scripts/zotero_bridge.py create` uses the documented Connector route:

```text
POST /connector/saveItems
Content-Type: application/json
X-Zotero-Connector-API-Version: 3
```

The payload is deliberately limited to a bibliographic item with an empty `attachments` list and an explicit source `uri`.

### Safety sequence

1. Load structured metadata JSON.
2. Require a non-empty title and explicit provenance through `source_uri`, URL, or DOI.
3. Require structured creator objects; do not parse free-text author strings heuristically.
4. Normalize institutional creators to Zotero's single-field creator form (`lastName` + `fieldMode: 1`).
5. Refuse attachment data inside parent creation.
6. Without `--yes`, output a preview only and perform no Zotero probe/write or target-resolution request.
7. With `--yes`, require both Local API and Connector availability.
8. Resolve and record the writable Connector target.
9. Pre-check for an existing parent by normalized DOI or exact title.
10. Refuse the write if a matching parent already exists.
11. POST to `/connector/saveItems` and require HTTP 201.
12. Re-query the read-only Local API by the same stable identity.
13. Return `CREATED_AND_VERIFIED` only if exactly one matching parent is observable.

A request that returned HTTP 201 but cannot be uniquely verified is explicitly non-complete:

- `WRITE_SUCCEEDED_BUT_NOT_VERIFIED`, or
- `WRITE_SUCCEEDED_VERIFICATION_AMBIGUOUS`.

The workflow must not record Zotero ingest `COMPLETE` in either case.

## Why generic local-file attachment is still not implemented

Zotero does expose an official Connector route:

```text
POST /connector/saveAttachment
```

However, this route is **session-bound**, not a generic “existing Zotero item key + local file” API. Zotero's implementation resolves the parent through a Connector save session using:

- `sessionID` created by `/connector/saveItems` or `/connector/saveSnapshot`;
- a Connector-side `parentItemID` that was supplied in that same session.

The Connector SessionManager is designed to garbage-collect old save sessions (normally around 10 minutes, shorter when many sessions exist). This can support immediate attachments associated with a just-created Connector item, but it is not a durable mechanism for the complete Literature Evaluation lifecycle:

- an already-existing Zotero parent may not belong to such a session;
- A and B may be generated much later than Main/SI;
- the workflow must support resume across sessions/chats/machines;
- archive completion requires verifiable attachment keys, not dependence on a transient Connector session.

Therefore the generic V1 `attach` interface remains deliberately disabled:

```text
LOCAL_FILE_ATTACH_ROUTE_NOT_IMPLEMENTED_OR_VERIFIED
```

This is a capability boundary, not a claim that Zotero has no attachment endpoint. The repository is refusing to present a short-lived session route as a durable existing-parent attachment adapter.

Use `pending_zotero_actions` for Main/SI/A/B attachment work until a durable adapter is implemented and live-verified.

## Verification levels

Do not collapse these states:

```text
Connector reachable
≠ writable target resolved
≠ request accepted
≠ parent created
≠ parent identity verified
≠ file attachment created
≠ attachment identity verified
≠ full Zotero archive COMPLETE
```

The V1 archive completion gate still requires the applicable verified Main/SI/A/B attachment keys.

## Testing

Phase 7 automated tests use mocks and synthetic metadata only. They verify:

- metadata-to-Connector payload construction;
- personal and institutional creator normalization;
- free-text creator rejection;
- attachment payload rejection;
- selected-target resolution and non-editable-target rejection;
- preview/no-write behavior without `--yes`;
- duplicate pre-check;
- HTTP 201 + unique post-write match → verified success;
- HTTP 201 + no/ambiguous post-write match → non-complete;
- generic attachment remains explicitly unsupported.

These tests do not modify a real Zotero library. A live test in the user's local Zotero Desktop environment is still required before calling the parent-create adapter production-validated.

## Scope rule

This adapter is mechanical infrastructure only. It must never decide which paper should be selected, infer missing metadata, merge ambiguous records, or choose an academically preferred source version.
