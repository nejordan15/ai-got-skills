# atlassian plugin — TODO

## Add a `jira-api` skill

Mirror the `confluence-api` skill for Jira, sharing the common client.

- [ ] Create `skills/jira-api/SKILL.md` (name `jira-api`; description with Jira-specific triggers).
- [ ] Create `skills/jira-api/assets/jira.py` — import the shared client from the plugin lib:
      `sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "lib"))` then `from _client import jira_client`.
- [ ] Implement subcommands: `get`, `create`, `update`, `comment`, `transition`.
- [ ] `lib/_client.py` already exposes `jira_client()` and reads the shared `ATLASSIAN_*` env vars — no client changes expected.

## Cleanup to do when jira-api lands

- [ ] Promote `skills/confluence-api/requirements.txt` to a single plugin-level `requirements.txt` (the shared `atlassian-python-api` dep belongs with `lib/`, not one skill). Update both SKILL.md files and the README install step to point at it.

## Possible future cleanup: unify the Confluence backends

`skills/confluence-api/assets/` currently has two backends: `pages.py` (via the
`atlassian-python-api` library) and `folders.py` (raw v2 REST, because the library
doesn't wrap the folder content type). A future refactor could collapse both onto a
single hand-written client in `lib/` and drop the library dependency — not worth it
yet.

## Notes

- Keep both skills in the **one** `atlassian` plugin (one version, one install). Don't split into separate plugins.
- Shared code stays in `lib/`; reaching outside the plugin dir breaks plugin caching.
