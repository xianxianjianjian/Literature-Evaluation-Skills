# Zotero Write Adapter — V1 Integration Note

This note defines the implemented and unimplemented Zotero write operations for the isolated `phase-7-zotero-write-adapter` branch.

## Source-of-truth boundary

Zotero Desktop exposes two relevant local interfaces on port `23119`:

- `/api/...`: Zotero Web API v3-compatible local interface, **read-only**;
- `/connector/...`: Connector server routes used for desktop write/import workflows.

The repository does not treat “Connector is reachable” as proof that every desired write is supported.

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
4. Refuse attachment data inside parent creation.
5. Without `--yes`, output a preview only and perform no Zotero probe/write.
6. With `--yes`, require both Local API and Connector availability.
7. Pre-check for an existing parent by normalized DOI or exact title.
8. Refuse the write if a matching parent already exists.
9. POST to `/connector/saveItems` and require HTTP 201.
10. Re-query the read-only Local API by the same stable identity.
11. Return `CREATED_AND_VERIFIED` only if exactly one matching parent is observable.

A request that returned HTTP 201 but cannot be uniquely verified is explicitly non-complete:

- `WRITE_SUCCEEDED_BUT_NOT_VERIFIED`, or
- `WRITE_SUCCEEDED_VERIFICATION_AMBIGUOUS`.

The workflow must not record Zotero ingest `COMPLETE` in either case.

## Not implemented: local-file attachment

The required archive operations include attaching local Main/SI/A/B files to an existing parent. The current repository deliberately does **not** implement this until a documented and tested route is available for the exact operation.

Current status:

```text
LOCAL_FILE_ATTACH_ROUTE_NOT_IMPLEMENTED_OR_VERIFIED
```

The `attach` CLI only reports this capability gap. It does not send a speculative request.

Use `pending_zotero_actions` for Main/SI/A/B attachment work until the adapter is implemented and live-verified.

## Verification levels

Do not collapse these states:

```text
Connector reachable
≠ request accepted
≠ parent created
≠ parent identity verified
≠ file attachment created
≠ full Zotero archive COMPLETE
```

The V1 archive completion gate still requires the applicable verified Main/SI/A/B attachment keys.

## Testing

Phase 7 automated tests use mocks and synthetic metadata only. They verify:

- metadata-to-Connector payload construction;
- free-text creator rejection;
- attachment payload rejection;
- preview/no-write behavior without `--yes`;
- duplicate pre-check;
- HTTP 201 + unique post-write match → verified success;
- HTTP 201 + no/ambiguous post-write match → non-complete;
- attachment remains explicitly unsupported.

These tests do not modify a real Zotero library. A live test in the user's local Zotero Desktop environment is still required before calling the parent-create adapter production-validated.

## Scope rule

This adapter is mechanical infrastructure only. It must never decide which paper should be selected, infer missing metadata, merge ambiguous records, or choose an academically preferred source version.
