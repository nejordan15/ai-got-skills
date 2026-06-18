# ai-got-skills

A personal [Claude Code](https://docs.claude.com/en/docs/claude-code) **plugin marketplace**. Installing a plugin from here makes its skills available in Claude Code from *any* directory — no per-project copying or symlinking.

- **Marketplace:** `ai-got-skills` (this repo)
- **Plugins:** `atlassian` (more later)

## Plugins

### atlassian

Direct REST API access to Atlassian Cloud — a faster, more accurate alternative to the Atlassian MCP. Confluence is implemented today; Jira is planned (the shared client already supports it).

- **Skill:** `confluence-api` (invoke as `/atlassian:confluence-api`; Claude also triggers it automatically by description)
- **Manifest:** [`plugins/atlassian/skills/confluence-api/SKILL.md`](plugins/atlassian/skills/confluence-api/SKILL.md)
- **Shared client:** [`plugins/atlassian/lib/_client.py`](plugins/atlassian/lib/_client.py) — common auth/REST setup, reused by future skills (e.g. `jira-api`; see [`TODO.md`](plugins/atlassian/TODO.md))

**Why it exists:** the standard MCP path requires Claude to emit the entire page body on every update. On a 50 KB page that's many minutes of model output per edit. This skill writes via Atlassian's REST API directly from a local body file, so Claude only emits the diff (via the `Edit` tool). The result is roughly an order-of-magnitude speedup on large-page updates and exact preservation of Confluence-native macros (info panels, table widths, code-block widths) that the MCP path flattens.

## Install

### 1. Clone

```bash
git clone <this-repo-url> ~/personaldev/ai-got-skills
```

### 2. Register the marketplace and install the plugin

Either declaratively (recommended — survives reinstalls) by adding to `~/.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "atlassian@ai-got-skills": true
  },
  "extraKnownMarketplaces": {
    "ai-got-skills": {
      "source": {
        "source": "directory",
        "path": "/absolute/path/to/ai-got-skills"
      }
    }
  }
}
```

…or via the CLI:

```bash
claude plugin marketplace add /absolute/path/to/ai-got-skills
claude plugin install atlassian@ai-got-skills
```

Confirm it's enabled at user scope:

```bash
claude plugin list | grep atlassian   # → atlassian@ai-got-skills … ✔ enabled
```

### 3. Install the Python dependency and set credentials

```bash
pip3 install --user -r plugins/atlassian/skills/confluence-api/requirements.txt
```

Set three environment variables in your shell rc (use `~/.zshenv` so non-interactive shells pick them up too):

```bash
export ATLASSIAN_BASE_URL="https://YOUR-DOMAIN.atlassian.net"
export ATLASSIAN_EMAIL="you@example.com"
export ATLASSIAN_API_TOKEN="..."   # https://id.atlassian.com/manage-profile/security/api-tokens
```

### Prefer the skill over the Atlassian MCP

To make Claude reach for this skill instead of the `mcp__*_Atlassian__*` tools for Confluence work, add a note to your `~/.claude/CLAUDE.md`:

> Prefer the `confluence-api` skill (`atlassian@ai-got-skills`) over the Atlassian MCP for Confluence — it's faster and more accurate. Fall back to the MCP only for ADF-specific macros or trivial small edits.

## Standalone CLI use (no Claude Code required)

The skill's Python script is a normal CLI — use it directly from any shell:

```bash
SKILL=plugins/atlassian/skills/confluence-api/assets

# Fetch a page body to a local file
python3 $SKILL/confluence.py get --page-id <page-id> --out body.html

# Create a new page
python3 $SKILL/confluence.py create \
  --space-key '<space-key>' \
  --title "My Page" \
  --body-file body.html

# Update an existing page
python3 $SKILL/confluence.py update \
  --page-id <page-id> \
  --body-file body.html \
  --message "what changed"
```

See [`SKILL.md`](plugins/atlassian/skills/confluence-api/SKILL.md) for the full CLI surface, including `--from-markdown` and `--keep-appearance`.

## Layout

```
ai-got-skills/
├── .claude-plugin/
│   └── marketplace.json              ← marketplace catalog
└── plugins/
    └── atlassian/
        ├── .claude-plugin/
        │   └── plugin.json           ← plugin manifest (name, version, …)
        ├── lib/
        │   └── _client.py            ← shared auth/REST client (used by all skills)
        ├── TODO.md                   ← planned work (e.g. jira-api skill)
        ├── tests/
        │   ├── test_client.py        ← happy-path tests for lib/_client.py
        │   └── test_confluence.py    ← happy-path tests for the CLI (mocked client)
        └── skills/
            └── confluence-api/
                ├── SKILL.md          ← invocation manifest for Claude Code
                ├── requirements.txt  ← Python deps for the skill's scripts
                └── assets/
                    └── confluence.py ← imports ../../lib/_client.py
```

## Contributing / extending

- **Add a skill to an existing plugin:** create `plugins/<plugin>/skills/<name>/SKILL.md` with YAML frontmatter (`name` + `description`); put helper scripts under `assets/`. It's discovered automatically under the plugin's `skills/` dir.
- **Add a new plugin:** create `plugins/<name>/.claude-plugin/plugin.json`, then add an entry to `.claude-plugin/marketplace.json` with `source: "./plugins/<name>"`.
- **After editing:** because the marketplace source is a local `directory`, run `claude plugin marketplace update ai-got-skills` if a change doesn't show up in a new session (plugins are cached on install).

### Tests

Happy-path unit tests use stdlib `unittest` with the Confluence client mocked — no network, no `atlassian-python-api` install required. Run from the plugin root:

```bash
cd plugins/atlassian
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE) — use, modify, redistribute freely; no warranty.
