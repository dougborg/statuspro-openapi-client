# Release Process

This repository uses **[release-please](https://github.com/googleapis/release-please) in
manifest mode** to independently version three packages from a single, aggregated
release PR:

1. **statuspro-openapi-client** (component `client`) — the Python API client, at the
   repo root
1. **statuspro-mcp-server** (component `mcp`) — the Model Context Protocol server, in
   `statuspro_mcp_server/`
1. **statuspro-client** (component `ts`) — the TypeScript client, in
   `packages/statuspro-client/`

Configuration lives in `release-please-config.json` and `.release-please-manifest.json`
at the repo root. (Not linked: they sit outside the docs tree, and mkdocs runs in strict
mode.)

## How releases work

### 1. Every push to `main` updates one Release PR

`.github/workflows/release-please.yml` runs on every push to `main`. It never pushes to
`main` itself — it only opens or updates **one aggregated pull request** covering every
package that has releasable commits since its last release
(`separate-pull-requests: false`). That PR:

- bumps `version` in each changed package's manifest (`pyproject.toml` / `package.json`)
- updates each package's changelog
- updates `.release-please-manifest.json`

Because change detection is **path-based** (which files a commit touches), not
**scope-based** (a `(client)`/`(mcp)`/`(ts)` prefix in the commit message), a commit
that touches both `statuspro_mcp_server/` and the repo root will bump both packages.
Commit scopes are still worth using for readability and changelog grouping, but they are
no longer load-bearing for version-bump decisions the way they were under
python-semantic-release.

### 2. A second workflow keeps the release PR internally consistent

`.github/workflows/release-pr-prepare.yml` runs on the release PR branch only (never on
`main`). It:

- resyncs `uv.lock` to whatever versions release-please just bumped
- keeps `statuspro_mcp_server/pyproject.toml`'s `statuspro-openapi-client>=X` floor
  equal to the client version this PR proposes, so the MCP package's declared dependency
  is always installable

Both changes are pushed as an extra commit on the release PR branch, so they land
**atomically with the version bump** when the PR is merged — never as a follow-up push
to `main`.

### 3. Merging the release PR creates tags and draft GitHub Releases

When the release PR merges, `release-please.yml` runs once more (still triggered by the
push to `main` the merge produces), notices the PR was just merged, and creates a tag +
draft GitHub Release for every package that changed, all at that single merge commit:

- `client-vX.Y.Z`
- `mcp-vX.Y.Z`
- `ts-vX.Y.Z`

Releases are created as **drafts** (`"draft": true` in the config). Draft releases can
still accept asset uploads; once a release is published it becomes
[immutable](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
and permanently rejects new assets. See step 4.

### 4. Each tag triggers a build-and-publish job

`.github/workflows/publish.yml` triggers only on `client-v*` / `mcp-v*` / `ts-v*` tag
pushes — never on a `main` push. For the matching component it:

1. builds the package/tarball (the MCP job also builds the `.mcpb` bundle)
1. publishes to the registry (PyPI or npm) via **OIDC** — no stored tokens
1. uploads the build artifact(s) to the still-draft GitHub Release
1. flips the release to published (`gh release edit --draft=false`)

The MCP job additionally builds and pushes a multi-arch Docker image to
`ghcr.io/dougborg/statuspro-mcp-server` after its PyPI publish succeeds.

This ordering — build, publish to registry, attach assets, _then_ finalize the release —
means the release is never finalized before its assets exist, so nothing is ever lost to
the immutability rule.

## Trusted Publisher environments (deviation from other repos in this migration)

`publish.yml`'s jobs deliberately declare **no** `environment:`. statuspro's existing
PyPI Trusted Publishers for `statuspro-openapi-client` and `statuspro-mcp-server` were
registered with the environment field blank, matching the old `release.yml`'s
`publish-client-pypi`/`publish-mcp-pypi` jobs, which never set `environment:` either.
PyPI includes the environment name in the OIDC claim it checks against the registered
Trusted Publisher, so adding `environment:` here — without first re-registering the
Trusted Publishers on PyPI to expect it — would make the already-working publishers stop
matching and break every future release. If dedicated environments are wanted later,
register them as Trusted Publishers on PyPI first, then add `environment:` to the
corresponding jobs.

## Manual prerequisites before the first TS release

**No npm Trusted Publisher exists yet for `statuspro-client`** — the TS client has never
been published (no `ts-v*` tag exists). Until one is registered, `publish-ts` will fail
its registry-publish step. Configure, before merging a release PR that bumps the `ts`
component:

- npm Trusted Publisher for `statuspro-client`, workflow `publish.yml`, job `publish-ts`

The PyPI Trusted Publishers for the client and MCP packages already exist and require no
changes.

## Commit message format

Conventional Commits still drive **what kind of** bump happens (`feat` → minor,
`fix`/`perf` → patch, `!`/`BREAKING CHANGE` → major); scopes remain useful for changelog
readability. Which **package(s)** get bumped is now determined by which paths a commit
touches, not by its scope:

```bash
git commit -m "feat(client): add helper for archived orders"       # bumps client
git commit -m "fix(mcp): correct stock level calculation"          # bumps mcp
git commit -m "feat(ts): export pagination helpers"                # bumps ts
git commit -m "docs: update contributing guide"                    # bumps nothing
```

## Tag format

Tags carry an explicit component prefix, matching the format used before this migration
(`include-component-in-tag: true`), so existing tag history is continuous:

- `client-v0.1.0`, `client-v0.2.0`, …
- `mcp-v0.1.0`, …
- `ts-v0.1.0`, …

## Troubleshooting

### No release PR appears after merging a PR to `main`

Check that at least one commit since the last release touches a path release-please
watches (`.`, `statuspro_mcp_server/`, or `packages/statuspro-client/`) with a
`feat`/`fix`/`perf`/breaking-change commit. `docs:`/`chore:`/`test:` commits do not
trigger a release-worthy change on their own.

### The release PR's `uv.lock` or MCP pin looks stale

Check the `release-pr-prepare.yml` run for that PR — it runs on every push to the PR
branch (including release-please's own force-pushes) and should show a
`chore(release): sync uv.lock and MCP client pin` commit if anything needed resyncing.

### Publish job failed with a PyPI/npm auth error

For npm: almost certainly the Trusted Publisher prerequisite above hasn't been
configured yet. For PyPI: check that the Trusted Publisher on PyPI still has no
`environment` set — if one was added there without a matching `environment:` here (or
vice versa), the OIDC claim will stop matching.

### Release created but no assets attached

The publish job for that component failed _before_ the "attach assets" step (usually the
registry publish itself). Fix the underlying failure and re-run — the release stays in
draft state (and therefore mutable) until the workflow successfully reaches
`gh release edit --draft=false`.

## Further reading

- [release-please manifest-releaser docs](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [npm Trusted Publishers](https://docs.npmjs.com/trusted-publishers)
- [GitHub Docs: Immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
