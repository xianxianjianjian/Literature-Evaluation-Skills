# Zotero Live Validation Runbook

This runbook is the remaining bridge between Phase-7/8 mock/CI verification and a real Zotero Desktop production-validation claim.

Do **not** run it in GitHub Actions. Run it on the user's own computer with Zotero Desktop open.

## Purpose

Validate separately:

1. Phase-8 durable existing-parent local-file attachment;
2. Phase-7 bibliographic parent creation.

Keep these tests separate so a failure in one adapter does not obscure the other.

## Safety rules

- Use Zotero 10+.
- Enable Settings → Advanced → **Allow other applications on this computer to communicate with Zotero**.
- Use a disposable test parent and synthetic file for the first attachment test.
- Do not use a real Main/SI/A/B file until the synthetic test passes.
- Do not paste or record the Local API authorization key anywhere. The repository helper does not display it.
- If Zotero reports a different `Zotero-Server-ID`, stop and reconnect; do not continue with cached object identities.
- If any command returns `ATTACHMENT_CONFLICT`, do not overwrite/delete automatically.
- If a child key is returned with `ATTACHMENT_FILE_UPLOAD_INCOMPLETE`, preserve it for diagnosis/resume.

## 1. Check capability

From the repository root:

```bash
python scripts/zotero_bridge.py status
```

Expected for Phase-8 durable attachment:

- Local API reachable;
- Local API mode reports Zotero-10 write capability;
- a Server-ID is detectable;
- `attach` is implemented/enabled at the protocol-capability level.

This command does not prove that the user has granted write authorization yet.

## 2. Prepare a disposable parent

For the first attachment-only test, create a temporary bibliographic item manually in **My Library** with a unique title such as:

```text
Literature Evaluation V1 Zotero Local Attachment Smoke Test
```

Find its key:

```bash
python scripts/zotero_bridge.py find \
  --title "Literature Evaluation V1 Zotero Local Attachment Smoke Test"
```

Record the returned Zotero parent item key only for this local test session.

Using a manually created parent isolates Phase 8 from the Phase-7 Connector parent-create path.

## 3. Create a synthetic local PDF

Create it under ignored `work/` so it cannot be committed:

```bash
python -c "from pathlib import Path; p=Path('work/zotero-live-smoke.pdf'); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'%PDF-1.4\n% Literature Evaluation synthetic Zotero attachment smoke test\n')"
```

Do not use copyrighted paper content for this validation fixture.

## 4. Preview attachment — must not prompt or write

Replace `<PARENT_KEY>`:

```bash
python scripts/zotero_bridge.py attach \
  --parent-key <PARENT_KEY> \
  --file work/zotero-live-smoke.pdf \
  --name "[TEST] Literature Evaluation Local Attachment"
```

Expected:

```text
WRITE_CONFIRMATION_REQUIRED
```

and no Zotero authorization dialog, child item, or file write.

If preview causes a Zotero write prompt, stop: preview semantics are broken.

## 5. Perform the live write

```bash
python scripts/zotero_bridge.py attach \
  --parent-key <PARENT_KEY> \
  --file work/zotero-live-smoke.pdf \
  --name "[TEST] Literature Evaluation Local Attachment" \
  --yes
```

Zotero Desktop should display its local-write authorization dialog.

For a controlled multi-request smoke test, choosing **Always Allow** is convenient because one attachment requires multiple authorized write requests. If choosing one-time **Allow**, Zotero may prompt again for later write phases; the helper is designed to re-authorize as needed. Zotero rate-limits dialogs, so repeated one-time prompts can eventually return 429.

Expected final status:

```text
ATTACHED_AND_VERIFIED
```

The output should contain an attachment key, but **must not contain the Local API key**.

## 6. Verify the child from Zotero

List children:

```bash
python scripts/zotero_bridge.py children --parent-key <PARENT_KEY>
```

Then verify the returned attachment key:

```bash
python scripts/zotero_bridge.py verify --item-key <ATTACHMENT_KEY>
```

Confirm in the Zotero UI that:

- exactly one `[TEST] Literature Evaluation Local Attachment` child exists;
- it is under the intended parent;
- it opens as the synthetic PDF;
- the attachment key matches the helper output.

## 7. Idempotency rerun

Run the exact same `attach --yes` command again.

Expected:

```text
ALREADY_ATTACHED_AND_VERIFIED
```

There must still be exactly one same-title test attachment child. If a duplicate child appears, Phase 8 fails live validation.

## 8. Optional controlled interruption check

This is optional because deliberately interrupting a write can leave a child item behind.

If performed, verify that the next run reuses a same-title child whose MD5 is still empty and whose filename is empty or matches the requested file. It must not create a duplicate.

Do not intentionally create a conflicting same-title/different-file child unless you are comfortable resolving/deleting the test items manually afterward.

## 9. Phase-7 parent-create live test

Test parent creation separately after the Phase-8 attachment test passes.

First inspect the Connector target:

```bash
python scripts/zotero_bridge.py selected-target --writable
```

For the current Phase-7 implementation, keep the live smoke test in **My Library**. Group-library parent creation has a target-prefix verification ambiguity and is not part of the Phase-7 production claim.

Prepare synthetic metadata under ignored `work/`, for example `work/zotero-parent-smoke.json`, with a unique title and synthetic DOI, then preview:

```bash
python scripts/zotero_bridge.py create \
  --metadata work/zotero-parent-smoke.json
```

Expected: preview/no write.

Execute only after confirming the selected target:

```bash
python scripts/zotero_bridge.py create \
  --metadata work/zotero-parent-smoke.json \
  --yes
```

Expected:

```text
CREATED_AND_VERIFIED
```

Re-running the same create request should stop at duplicate detection rather than create another parent.

## 10. Cleanup

After validation, delete the synthetic test attachment/parent manually in Zotero if they are no longer needed, and remove the local fixture:

```bash
rm -f work/zotero-live-smoke.pdf work/zotero-parent-smoke.json
```

On Windows PowerShell, use the equivalent `Remove-Item` command.

If **Always Allow** was chosen only for testing, Zotero's remembered local write authorizations can be cleared later in Settings → Advanced.

## Pass criteria

Phase-8 live attachment validation passes only when all are true:

- preview caused no write/prompt;
- real write required local authorization;
- final status was `ATTACHED_AND_VERIFIED`;
- child key was observable under the intended parent;
- local file opened correctly from Zotero;
- rerun returned `ALREADY_ATTACHED_AND_VERIFIED`;
- rerun created no duplicate;
- no Local API key appeared in terminal output/logs/files.

Phase-7 parent-create live validation passes only when:

- target was explicitly inspected and kept in My Library;
- create returned `CREATED_AND_VERIFIED`;
- duplicate rerun was refused;
- the parent was observable in Zotero with the expected identity.

## After live validation

Only after these checks should `docs/v1-release-checklist.md` change the relevant live Zotero boxes from open to complete.

Real Main/SI/A/B attachment remains a later archive acceptance step and still requires the actual selected-paper source/output files.
