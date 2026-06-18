---
name: confluence-api
description: Direct Confluence REST API access via the atlassian-python-api library. Use when updating large Confluence pages where the MCP updateConfluencePage tool would require re-emitting the full body (orders of magnitude slower than the diff-based approach this skill enables). Also use for creating pages programmatically, fetching page bodies to local files for offline editing, or any Confluence operation paired with the Edit tool on a local body file. Triggers: "use the confluence api", "update via the api directly", "fast confluence publish", "bypass mcp for confluence", "fetch the page body locally".
---

# confluence-api

Direct REST API access to Confluence Cloud. Bypasses the MCP `updateConfluencePage` tool's full-body round-trip — pair with the `Edit` tool on a local body file for fast incremental publishes. (Jira will get its own sibling `jira-api` skill — not yet implemented; the shared client at `plugins/atlassian/lib/_client.py` already supports it.)

## When to use

- Updating a Confluence page where the body is large (>2K tokens) and changes are localized — bypassing MCP saves minutes per publish.
- Creating new pages programmatically.
- Fetching page body to a local file for offline editing.
- Any operation where you'd otherwise re-emit the full page body through me.

## When NOT to use

- One-off small page edits — MCP's `updateConfluencePage` is simpler when the whole body fits comfortably in one response.
- Page operations needing ADF-specific macros not expressible in wiki markup (use the UI or the MCP tool).
- Jira ops — use the (future) `jira-api` skill; not implemented yet.

## Prerequisites

**Env vars** (set in your shell rc, e.g. `~/.zshenv` so non-interactive shells inherit them):

| Var | Example | Notes |
|---|---|---|
| `ATLASSIAN_BASE_URL` | `https://YOUR-DOMAIN.atlassian.net` | Atlassian Cloud root, no `/wiki` |
| `ATLASSIAN_EMAIL` | `you@example.com` | Atlassian account email |
| `ATLASSIAN_API_TOKEN` | `ATATT...` | Created at https://id.atlassian.com/manage-profile/security/api-tokens |

**Dependencies:**

```bash
pip3 install --user -r requirements.txt
```

## Usage

```bash
# Fetch a page (prints metadata; --out writes storage-format body to a file)
python3 assets/confluence.py get --page-id <page-id> --out body.html

# Create a new page in a space (always sets wide layout via full_width=True)
python3 assets/confluence.py create \
  --space-key '<space-key>' \
  --title "My Page" \
  --body-file body.html \
  [--parent-id <id>] \
  [--from-markdown]

# Update an existing page (defaults to storage format and wide layout)
python3 assets/confluence.py update \
  --page-id <page-id> \
  --body-file body.html \
  [--title "..."] \
  [--message "version comment"] \
  [--keep-appearance]

# Update treating the body as wiki/markdown (Confluence converts to storage)
python3 assets/confluence.py update \
  --page-id <page-id> \
  --body-file body.md \
  --from-markdown

# Move a page under a new parent (re-parent within a space)
python3 assets/confluence.py move \
  --page-id <page-id> \
  --space-key '<space-key>' \
  --target-id <new-parent-id> \
  [--position append|above|below]

# Delete (trash) a page
python3 assets/confluence.py delete \
  --page-id <page-id> \
  [--recursive]
```

## Pairing with the Edit tool

Workflow that makes large-page updates fast:

1. **Seed the local body file once** — `python3 confluence.py get --page-id <id> --out body.html`
2. **Edit incrementally** — use the `Edit` tool on `body.html` to change only the lines that need changing (Edit sends only diffs, not the full body).
3. **Push** — `python3 confluence.py update --page-id <id> --body-file body.html`

This converts a multi-minute full-body round-trip into ~1-2 seconds because the only output tokens I emit are the diff inside `Edit`, not the entire page body.

## Body format

- **Storage format** (default) — Confluence's native XHTML-like format with macros. Round-trips cleanly from a `get` to an `update`.
- **`--from-markdown` flag** — sends `representation='wiki'`. Confluence parses common wiki/markdown syntax (headings, lists, tables, code fences) and converts to storage server-side. Some markdown features may lose fidelity vs storage format.
- For maximum fidelity, work in storage format (especially after the first `get` seeds the file).

## Page width (content-appearance)

The `atlassian-python-api` library writes a `content-appearance` value on every `update_page` / `create_page` call — defaulting to `fixed-width` unless `full_width=True` is passed. The skill uses this parameter so the appearance write is bundled into the same PUT as the body, with no extra API calls.

How the skill handles it:

- **`create`** always passes `full_width=True` → new pages render wide.
- **`update` default**: passes `full_width=True` → page renders wide after the update. No extra API calls, no race conditions.
- **`update --keep-appearance`**: reads the current appearance pre-update (one GET); if either `-draft` or `-published` is `"max"` or `"full-width"`, passes `full_width=True`; otherwise `full_width=False`. Lets you preserve a page that was deliberately set narrow.

Storage values for appearance:

- The UI writes `"max"` for wide layout.
- The library writes `"full-width"` for the same wide layout.
- Both render identically; the skill treats both as "wide" when deciding whether to preserve.

## Future: Jira

The shared client `plugins/atlassian/lib/_client.py` reads `ATLASSIAN_EMAIL` + `ATLASSIAN_API_TOKEN` (shared between Confluence and Jira) and already exposes a `jira_client()`. The planned extension is a separate `jira-api` skill alongside this one — its own `jira.py` script importing the same `lib/_client.py`, with `get`/`create`/`update`/`comment`/`transition` subcommands. Not yet implemented; see `plugins/atlassian/TODO.md`.
