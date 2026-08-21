# Zotero Ingest

Zotero is the preferred long-term archive after the user confirms the final focal paper, but V1 Search completion does not depend on a specific Zotero write transport. Final-paper confirmation authorizes ordinary identity matching, legal-access source retrieval, normal archive actions, and selected-paper/source records without repeated permission prompts.

## 1. Match before creating

Prefer parent matching in this order:

1. normalized DOI;
2. exact/near-exact title plus author/year context;
3. other stable bibliographic fields when DOI is absent.

Use `scripts/zotero_bridge.py find` and `children` for safe checks when Zotero Desktop is available.

Stop for user/operator resolution when there is:

- more than one plausible parent;
- DOI/title disagreement;
- conflicting Version of Record/preprint identity;
- uncertainty about whether two records are duplicates.

Do not create duplicate parents merely because an existing item lacks an attachment.

## 2. Preferred source package

Prefer Version of Record metadata and legally accessible sources. Retrieve and record, when discoverable:

- Main Article;
- all scientifically relevant Supporting Information;
- correction/erratum material;
- version/status information.

Do not bypass paywalls, institutional authentication, download restrictions, or other access controls. Source-text reuse in public Git must follow `shared/data-format-policy.md`.

The academic handoff depends on this source package, not on whether Zotero already contains it.

## 3. Attachment labels

Preferred labels:

```text
[ORIGINAL] Main Article
[SUPPLEMENT] <descriptive name>
[A] 中文全文翻译镜像版
[B] 文献研究笔记·完整精读版
```

After any automatic or manual write, verify the actual parent/attachment identity rather than treating a submitted request, UI action or HTTP success code as archive success.

## 4. Current automatic archive helpers

The repository retains Zotero automation as an optional enhancement.

### Parent create

`scripts/zotero_bridge.py create` currently uses the verified Connector `/connector/saveItems` route with duplicate checks and post-write identity verification. Its group-library/target-unification limitations are documented future optimizations, not Search release blockers.

### Zotero 10+ durable attachment

`scripts/zotero_bridge.py attach` contains a Zotero 10+ Local API existing-parent attachment implementation with preview/`--yes`, Server-ID binding, local authorization, upload verification, MD5/parent/filename checks, idempotency and conflict refusal.

This path is protocol/mock/CI tested but still requires real desktop live validation before it should be called universally production-validated.

V1 therefore supports three operational archive modes:

1. verified automatic archive when the environment supports it;
2. manual Zotero parent/attachment followed by verification;
3. deferred archive using `pending_zotero_actions` and handoff files.

None of these modes changes the academic selection result.

## 5. Archive pending path

When Zotero Desktop, write authorization, compatible Local API, or automatic routing is unavailable:

1. retain any already verified parent/attachment keys;
2. stage acquired Main/SI/A/B under `work/<paper_id>/handoff/` when a local runtime exists;
3. append concrete unresolved records to `workflow_manifest.yaml.pending_zotero_actions`;
4. record expected source IDs and attachment labels;
5. continue downstream academic work if the actual source evidence is available;
6. later reconcile automatically or manually and clear each verified pending action.

A Zotero-only pending action **does not make Search `PROVISIONAL`**. Search status is determined by search/selection/source-package completeness.

If a source file itself is unavailable, record that as a separate source blocker; source unavailability may legitimately make Search/Translation/Deep Reading provisional or blocked.

## 6. Academic versus archive completion

### Search academic completion

Search can be `COMPLETE` once the user-confirmed paper, identity/version, search record, selection rationale and source/package handoff are sufficiently resolved for downstream work.

### Zotero archive completion

A stricter archive closure requires the intended parent/attachments to be observable and verified and all relevant pending actions cleared.

Report these separately. Never say “saved to Zotero” unless verified, but never call a completed Search academically incomplete solely because Zotero automation is pending.

## 7. `selected_paper.yaml`

Store under `work/<paper_id>/selected_paper.yaml` and include at least:

- `schema_version`;
- `paper_id`;
- title;
- authors;
- journal;
- DOI;
- year and online date when known;
- publication status/version;
- weekly role;
- user-confirmation date;
- Quality Gate;
- weighted-score summary;
- selection rationale;
- known cautions;
- Zotero parent key or `null`;
- archive/ingest status.

Unknown source fields must remain `null`; do not infer them from common publishing practice.

## 8. `source_manifest.json`

Create/update `work/<paper_id>/source_manifest.json`. Each source record should preserve:

- stable source id such as `SRC-M1` / `SRC-S1`;
- source type;
- bibliographic/version identity;
- origin URL or repository/publisher source when appropriate;
- acquired/checked date;
- local staging path only as a temporary locator, never identity;
- availability/status;
- checksum when useful;
- Zotero attachment key or `null`;
- known gap or verification note.

Main, each Supplement, and correction material should be separate source records.

## 9. Selection history

After final confirmation, append the selected paper decision to `knowledge/selection_log.csv`. Do not write to `reading_history.csv` until Deep Reading genuinely reaches academic completion.

Do not bulk-import all search candidates into Zotero.
