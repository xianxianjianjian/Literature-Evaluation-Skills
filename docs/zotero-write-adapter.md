# Zotero Write Adapter — Phase 7 Integration Note

> **Historical design note.** This document records the Phase-7 parent-create adapter and the Connector-session limitation that was known at that stage. Phase 8 later adds a durable Zotero 10+ Local API existing-parent attachment route. For current attachment behavior, read [`zotero-local-attachments.md`](zotero-local-attachments.md) and `shared/zotero-policy.md`.

## Phase-7 source boundary

Zotero Desktop exposes local interfaces on port `23119`. Phase 7 deliberately used:

- `/api/...` for safe read-after-write identity checks;
- `/connector/...` for Connector save/import operations.

At that phase, the repository did not yet rely on the newer Zotero 10+ Local API write/full-upload contract. The earlier phrase “Local API is read-only” should therefore be read as a **Phase-7 implementation assumption**, not the current Phase-8 capability statement.

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

`scripts/zotero_bridge.py create` uses the Connector route:

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
7. With `--yes`, require Local API read verification and Connector availability.
8. Resolve and record the writable Connector target.
9. Pre-check for an existing parent by normalized DOI or exact title.
10. Refuse the write if a matching parent already exists.
11. POST to `/connector/saveItems` and require HTTP 201.
12. Re-query the Local API by the same stable identity.
13. Return `CREATED_AND_VERIFIED` only if exactly one matching parent is observable.

A request that returned HTTP 201 but cannot be uniquely verified is explicitly non-complete:

- `WRITE_SUCCEEDED_BUT_NOT_VERIFIED`, or
- `WRITE_SUCCEEDED_VERIFICATION_AMBIGUOUS`.

The workflow must not record Zotero ingest `COMPLETE` in either case.

## Why Connector `/saveAttachment` was not adopted as the generic archive route

Zotero exposes:

```text
POST /connector/saveAttachment
```

but this route is session-bound. Zotero resolves its parent through:

- a Connector `sessionID` created by `/connector/saveItems` or `/connector/saveSnapshot`;
- a Connector-side `parentItemID` supplied within that same save session.

Connector save sessions are intentionally short-lived. That makes the endpoint suitable for immediate attachments associated with a newly saved browser item, but not for the full Literature Evaluation lifecycle where:

- an existing parent may predate the current session;
- A/B may be generated much later than Main/SI;
- workflows must resume across sessions;
- archive completion must be keyed by durable Zotero item/attachment identities.

Phase 7 therefore did **not** expose Connector `/saveAttachment` as a generic existing-parent adapter. That decision remains valid.

## Phase-8 supersession: durable existing-parent attachment

The later Phase-8 audit identified Zotero 10+ Local API authorized writes and full file upload as the appropriate durable route. Phase 8 now implements:

```text
existing parent key
→ Local API attachment child
→ Local API full upload
→ same-server read-after-write
→ parent + filename + MD5 verification
```

This does not depend on a Connector session and therefore supports Main/SI/A/B at different points in the workflow.

See [`zotero-local-attachments.md`](zotero-local-attachments.md) for the current contract.

## Verification levels

Do not collapse these states:

```text
endpoint reachable
≠ authorization granted
≠ write accepted
≠ parent/child created
≠ file bytes registered
≠ identity verified
≠ full Zotero archive COMPLETE
```

## Testing status

Phase 7 automated tests verify parent-create payloads, creator schema, target resolution, no-write preview, duplicate refusal, HTTP 201 handling and post-write identity verification.

Phase 8 adds separate Local API attachment tests. Neither CI suite writes to the user's real Zotero Desktop library; live production validation remains a separate gate.

## Scope rule

These adapters are mechanical infrastructure only. They must never decide which paper should be selected, infer missing metadata, merge ambiguous records, silently replace attachments, or choose an academically preferred source version.
