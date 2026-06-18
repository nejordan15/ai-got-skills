# ai-got-skills — TODO (marketplace level)

Plugin-specific tasks live in each plugin's own TODO, e.g. `plugins/atlassian/TODO.md`.

## Consider adding explicit versioning

Right now **`version` is intentionally omitted** from `.claude-plugin/marketplace.json` and
`plugins/atlassian/.claude-plugin/plugin.json`. With no `version`, Claude Code resolves a plugin's
version from its **git commit SHA**, so:

- Every merge to `main` is a new version. Consumers get it on the next `claude plugin marketplace
  update` (or automatically at startup if they enabled `autoUpdate`). No release chore for us.

### What adding a `version` would mean (the caveat)

Setting a `version` string **pins** consumers: they stay on their cached copy and receive **nothing
new** until the string changes — *even if they pull and run `marketplace update`*. So adopting
versioning turns "merge to main" into a two-part release: **merge code _and_ bump the version**.

If we go this way:

- [ ] Decide the model:
  - **Auto-bump (Option B):** a workflow on push to `main` (after CI) bumps `version` in
    `marketplace.json` and commits it. Caveat: the push must pass branch protection, so it needs a
    **PAT or GitHub App token** (not the default `GITHUB_TOKEN`), plus a loop guard
    (`paths-ignore` / `[skip ci]`) so the bump commit doesn't re-trigger CI endlessly.
  - **Tagged release channels (Option C):** tag releases in CI and point the marketplace entry's
    `ref` at a channel (e.g. `latest` vs `vN`); consumers pin the channel they want.
- [ ] Set `version` in **one place only** — the marketplace entry *or* `plugin.json`, never both
  (`plugin.json` wins silently and can mask the other).
- [ ] Use semver and keep a short changelog/release notes.

### When it's worth doing

Adopt versioning once there are external consumers who need **stable, intentional releases** or a
**stable-vs-latest** distinction. Until then, SHA-tracked (no `version`) is simpler and matches the
"merge to main ⇒ users update" goal with zero release overhead.
