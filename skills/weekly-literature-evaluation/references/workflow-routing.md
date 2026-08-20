# Workflow Routing

Read the weekly manifest and inspect referenced artifacts before choosing a route.

| Request or state | Route |
| --- | --- |
| Full weekly workflow | Topic Gate → Search → Paper Gate → Translation → Deep Reading → verify A/B/C |
| Search only | Invoke `literature-search`; stop after its requested completion boundary |
| Translation only | Run Minimal Intake when Search artifacts are absent, then invoke `paper-translation` |
| Deep Reading only | Run Minimal Intake when needed, then invoke `paper-deep-reading`; A is optional input, never a prerequisite |
| Resume | Start at the first stage not `COMPLETE`, unless an earlier stage has `needs_update: true` |
| `needs_update: true` | Read `update_reason`, check source changes, and route only the affected stage plus downstream consumers |
| `PROVISIONAL` | Continue from the named evidence/system gap; preserve provisional outputs until replacements verify |
| Zotero unavailable | Continue safe local work, stage handoff under `work/<paper_id>/handoff/`, and record `pending_zotero_actions` |

## Resume examples

```text
Search COMPLETE
Translation COMPLETE
Deep Reading NOT_STARTED
→ resume at Deep Reading
```

```text
Translation COMPLETE + needs_update: true
update_reason: new Supplement
→ re-open Translation source coverage, then route affected Deep Reading sections
```

```text
Deep Reading PROVISIONAL
reason: cited Supplement unavailable
→ preserve B/C status as provisional and resume evidence audit when the Supplement appears
```

## Gate behavior

Use `WAITING_USER` only for topic confirmation or final-paper confirmation in the ordinary weekly workflow. Direct specialist requests can arrive with the relevant choice already supplied and should not recreate an unnecessary Gate.
