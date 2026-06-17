# ai-got-skills

A collection of personal [Claude Code](https://docs.claude.com/en/docs/claude-code) skills. Each one is self-contained under `.claude/skills/<skill-name>/` and can be dropped into any Claude Code project or symlinked from `~/.claude/skills/`.

## Skills

### atlassian-api

Direct REST API access to Atlassian Cloud (Confluence; Jira architecture-ready for later). Bypasses the MCP `updateConfluencePage` tool's full-body round-trip — pair with Claude Code's `Edit` tool on a local body file for fast incremental publishes on large Confluence pages.

See [`.claude/skills/atlassian-api/SKILL.md`](.claude/skills/atlassian-api/SKILL.md) for the full skill manifest.

**Why it exists:** the standard MCP path requires Claude to emit the entire page body on every update. On a 50 KB page that's many minutes of model output per edit. This skill writes via Atlassian's REST API directly from a local body file, so Claude only emits the diff (via the `Edit` tool). The result is roughly an order-of-magnitude speedup on large-page updates and exact preservation of Confluence-native macros (info panels, table widths, code-block widths) that the MCP path flattens.

## Install

Clone this repo somewhere, then either symlink the skill into a project's `.claude/skills/` or into your global `~/.claude/skills/`:

```bash
git clone <this-repo-url> ~/path/to/ai-got-skills
cd ~/path/to/ai-got-skills

# Option A — make available to ALL Claude Code projects (recommended):
ln -s "$PWD/.claude/skills/atlassian-api" ~/.claude/skills/atlassian-api

# Option B — drop into one specific project:
ln -s "$PWD/.claude/skills/atlassian-api" /path/to/your/project/.claude/skills/atlassian-api

# Install the Python dependency the skill's CLI uses:
pip3 install --user -r .claude/skills/atlassian-api/requirements.txt
```

Then set three environment variables in your shell rc (e.g. `~/.zshenv` so non-interactive shells pick them up too):

```bash
export ATLASSIAN_BASE_URL="https://YOUR-DOMAIN.atlassian.net"
export ATLASSIAN_EMAIL="you@example.com"
export ATLASSIAN_API_TOKEN="..."   # https://id.atlassian.com/manage-profile/security/api-tokens
```

## Standalone CLI use (no Claude Code required)

The skill's Python script is a normal CLI — you can use it directly from any shell:

```bash
SKILL=.claude/skills/atlassian-api/assets

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

See the skill's [SKILL.md](.claude/skills/atlassian-api/SKILL.md) for the full CLI surface, including `--from-markdown` and `--keep-appearance`.

## Layout

```
ai-got-skills/
└── .claude/
    └── skills/
        └── <skill-name>/
            ├── SKILL.md           ← invocation manifest for Claude Code
            ├── requirements.txt   ← Python deps for the skill's scripts
            └── assets/            ← scripts the skill invokes
```

## Contributing / extending

Adding a new skill: create `.claude/skills/<name>/SKILL.md` with a YAML frontmatter `name` + `description`, then put any helper scripts under `assets/`. See `atlassian-api/SKILL.md` as a template.

## License

[MIT](LICENSE) — use, modify, redistribute freely; no warranty.
