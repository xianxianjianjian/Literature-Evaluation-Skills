# Workspace and Plugin Resource Contract

## Two roots

The installed plugin and the user's research data have different lifecycles and must remain separate.

- **Plugin root**: the directory containing `.codex-plugin/plugin.json`. Treat `skills/`, `shared/`, `scripts/`, and `assets/` below this root as read-only installed resources.
- **Data root**: the writable research workspace containing `workspace.json`, `knowledge/`, `weekly_reviews/`, and `work/`.

Never write user state, downloaded sources, translations, notes, or registry updates into the installed plugin root.

## Data-root resolution

Resolve the data root in this order:

1. an explicit `--workspace-root <path>` supplied to a helper;
2. `LITERATURE_EVALUATION_HOME` when it is non-empty;
3. an already initialized `.literature-evaluation/workspace.json` discovered from the current directory upward;
4. `.literature-evaluation/` below the containing Git project root when one can be identified;
5. `.literature-evaluation/` below the current working directory.

An explicit or environment-provided path is the data root itself. The upward discovery rule prevents a project from accidentally creating multiple Literature Evaluation workspaces when Codex starts from different subdirectories.

## Initialization

Before the first write, run the plugin-root helper:

```text
python <plugin-root>/scripts/init_workspace.py [--workspace-root <data-root>]
```

Initialization is idempotent and never overwrites an existing file. Use `--migrate-from <legacy-root>` to copy the legacy root-level `knowledge/`, `weekly_reviews/`, and `work/` trees. Use `--dry-run` first when migrating valuable records.

The migration source and destination must be separate, non-overlapping directory trees. If initialization or migration reports a content conflict, stop and ask the user to reconcile it. Do not choose one version automatically.

## Writable layout

All operational paths are relative to `<data-root>`:

```text
<data-root>/
|-- workspace.json
|-- knowledge/
|-- weekly_reviews/
`-- work/
```

`knowledge/` and `weekly_reviews/` are eligible for version control. `work/`, PDFs, DOCX files, and other large or local handoff artifacts are ignored by the template `.gitignore`.

`knowledge/submission_profile.yaml` intentionally uses a JSON-compatible YAML representation so the V1 helper layer can remain standard-library-only. Treat it as a structured configuration file rather than free-form YAML unless a future version adds a dedicated YAML parser.

## Script invocation

Resolve helper scripts from the plugin root, not from the current workspace. Pass data files explicitly, or pass `--plugin-root` and `--workspace-root` to repository-wide validation. The legacy `--repo-root` validator option remains compatible for development checkouts where plugin resources and data share one root.
