# Contributing

How to extend this marketplace and run its checks. See the [README](README.md) for install and usage.

## Extending

- **Add a skill to an existing plugin:** create `plugins/<plugin>/skills/<name>/SKILL.md` with YAML frontmatter (`name` + `description`); put helper scripts under `assets/`. It's discovered automatically under the plugin's `skills/` dir.
- **Add a new plugin:** create `plugins/<name>/.claude-plugin/plugin.json`, then add an entry to `.claude-plugin/marketplace.json` with `source: "./plugins/<name>"`.
- **After editing:** because the marketplace source is a local `directory`, run `claude plugin marketplace update ai-got-skills` if a change doesn't show up in a new session (plugins are cached on install).

## Tests

Use the `Makefile` from the repo root:

```bash
make unit          # happy-path unit tests — mocked client, no network
make integration   # live Confluence lifecycle test (see below)
make lint          # ruff (pip3 install --user -r requirements-dev.txt)
```

CI (`.github/workflows/ci.yml`) runs `make lint` and `make unit` on every pull request. The integration test is never run in CI — it requires real credentials and mutates Confluence.

**Unit tests** use stdlib `unittest` with the Confluence client mocked — no network, no `atlassian-python-api` install required.

**Integration test** runs the full lifecycle against a real Confluence instance — create → update → read → move → delete (it really creates and deletes pages, then cleans up). It's skipped unless these env vars are set:

| Var | Purpose |
|---|---|
| `ATLASSIAN_BASE_URL`, `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN` | Same credentials the skill uses |
| `INTEGRATION_TEST_SPACE` | A space key you can write to (e.g. `DOCS` or a personal space like `~012345`) |

Set the space key inline, or put it in a gitignored `local-integration-tests.env` at the repo root (the `integration` target sources it automatically if present):

```bash
# local-integration-tests.env  (gitignored)
INTEGRATION_TEST_SPACE='~012345'   # quote it — keeps the shell from expanding a leading ~
```

```bash
make integration                      # uses local-integration-tests.env if present
INTEGRATION_TEST_SPACE=DOCS make integration   # or set it inline
```
