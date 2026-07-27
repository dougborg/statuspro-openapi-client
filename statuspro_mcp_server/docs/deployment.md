# MCP Server Deployment Guide

This document describes how the StatusPro MCP Server is released and published to PyPI
using **release-please**, in manifest mode alongside the client and TS packages. See the
[main release guide](https://github.com/dougborg/statuspro-openapi-client/blob/main/docs/RELEASE.md)
for the full repo-wide process; this page covers what's specific to the MCP server.

## Overview

Releases are fully automated. You don't manually update version numbers or publish to
PyPI — merging a PR to `main` updates an aggregated release PR (across all three
packages), and merging _that_ PR is what actually creates the `mcp-v{version}` tag and
draft GitHub Release, which the tag-triggered `publish.yml` workflow then builds and
publishes from.

## How Releases Work

1. **Commits land on `main`** — release-please detects any commit touching
   `statuspro_mcp_server/` since the last `mcp-v*` release and reflects it in the
   aggregated release PR (path-based detection, not the `(mcp)` commit-scope filtering
   used before this migration — scopes are now cosmetic for changelog grouping only).
2. **The release PR proposes**: a version bump in `statuspro_mcp_server/pyproject.toml`,
   an updated `CHANGELOG.md`, and (via `release-pr-prepare.yml`) a synced `uv.lock` +
   client-dependency floor.
3. **Merging the release PR** creates tag `mcp-v{version}` and a **draft** GitHub
   Release at that commit.
4. **`publish.yml`'s `publish-mcp` job**, triggered by the `mcp-v*` tag: builds the
   wheel + sdist with `uv build --package statuspro-mcp-server`, builds the `.mcpb`
   bundle (`scripts/build_mcpb.py`), publishes to PyPI via OIDC, uploads both the Python
   and `.mcpb` artifacts to the still-draft release, then flips it to published.
5. **`publish-mcp-docker`** runs after `publish-mcp` succeeds and pushes a multi-arch
   image to `ghcr.io/dougborg/statuspro-mcp-server`.

## For Developers

### How to Trigger a Release

Write commits touching `statuspro_mcp_server/` using Conventional Commits:

```bash
# Feature (minor version bump)
git commit -m "feat(mcp): add search_products tool"

# Bug fix (patch version bump)
git commit -m "fix(mcp): correct stock level calculation"

# Breaking change (major version bump)
git commit -m "feat(mcp)!: redesign tool request models

BREAKING CHANGE: Tool request parameters now require explicit types"

# No release (documentation only)
git commit -m "docs(mcp): update README examples"
```

Merge your PR — release-please picks it up on the next push to `main` and reflects it in
the aggregated release PR. Merging that release PR is what actually ships the version.

### Which Commits Bump the MCP Version?

release-please partitions by **path**, not commit scope: any commit whose diff touches
`statuspro_mcp_server/` is eligible to bump the `mcp` component, based on its
conventional-commit type:

| Commit Type           | Release? | Version Bump        |
| --------------------- | -------- | ------------------- |
| `feat(mcp): ...`      | Yes      | MINOR (0.1.0→0.2.0) |
| `fix(mcp): ...`       | Yes      | PATCH (0.1.0→0.1.1) |
| `perf(mcp): ...`      | Yes      | PATCH (0.1.0→0.1.1) |
| `feat(mcp)!: ...`     | Yes      | MAJOR (0.1.0→1.0.0) |
| `docs`/`test`/`chore` | No       | No release          |

A commit touching both `statuspro_mcp_server/` and the repo root bumps both `client` and
`mcp` — this is new behavior versus the old scope-only filtering.

## Verify a Release

After a release is published (check
[GitHub Releases](https://github.com/dougborg/statuspro-openapi-client/releases)):

### 1. Check PyPI Page

Visit: https://pypi.org/project/statuspro-mcp-server/

Verify:

- New version is listed
- README renders correctly
- Project metadata is correct
- Installation command works

### 2. Test Installation from PyPI

```bash
# Create fresh test environment
cd /tmp
python3 -m venv test-pypi-install
source test-pypi-install/bin/activate

# Install from PyPI
pip install statuspro-mcp-server

# Verify installation
pip list | grep statuspro

# Test command (should require API key)
statuspro-mcp-server
# Expected: "STATUSPRO_API_KEY environment variable is required"

# Clean up
deactivate
rm -rf /tmp/test-pypi-install
```

### 3. Test with Claude Desktop

Update Claude Desktop config
(`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "statuspro": {
      "command": "uvx",
      "args": ["statuspro-mcp-server"],
      "env": {
        "STATUSPRO_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Desktop and verify:

- Server starts without errors
- Inventory tools appear in MCP tools list
- Tools work when invoked

## Manual Testing Before Release

Before merging a PR that will feed into a release, test locally:

### Run All Tests

```bash
cd statuspro_mcp_server

# Unit tests (fast)
uv run pytest tests/ -m "not integration"

# Integration tests (requires STATUSPRO_API_KEY in .env)
uv run pytest tests/ -m integration

# All tests
uv run pytest tests/
```

### Test Local Build

```bash
# From the repo root - uv build is workspace-aware and writes to the
# workspace root's dist/, not statuspro_mcp_server/dist/.
uv build --package statuspro-mcp-server

# Install locally (in a test venv)
cd /tmp
python3 -m venv test-local
source test-local/bin/activate
pip install /path/to/statuspro-openapi-client/dist/*.whl

# Test
statuspro-mcp-server --help

# Clean up
deactivate
rm -rf /tmp/test-local
```

### Test the `.mcpb` Bundle Build

```bash
npm install -g @anthropic-ai/mcpb   # once
uv run poe build-mcpb
```

## Emergency Manual Actions

If `publish.yml` fails partway through for a tag that already has a draft release, fix
the underlying failure and re-run the failed job — the release stays draft (and
therefore mutable) until `gh release edit --draft=false` succeeds, so nothing is lost by
retrying.

There is no supported way to force a release outside release-please's PR flow; manually
pushing a `mcp-v*` tag without a corresponding release-please-created draft release will
cause `publish.yml`'s `gh release upload`/`gh release edit` steps to fail (no release
exists for that tag).

## Troubleshooting

### Release Not Appearing After Merge

**Symptom**: PR merged but no MCP entry in the next release PR

**Causes**:

1. No `feat(mcp):`/`fix(mcp):`/`perf(mcp):`/breaking commits touching
   `statuspro_mcp_server/` since the last `mcp-v*` release
1. `release-please.yml` failed to run — check the Actions tab

**Solutions**:

- Check commit messages: `git log --oneline -- statuspro_mcp_server/`
- Review `release-please.yml` run logs

### PyPI Publish Failed

**Symptom**: Draft release created (tag exists) but PyPI publish failed

**Causes**:

1. PyPI Trusted Publisher misconfigured (must still have **no** `environment` set — see
   [RELEASE.md](https://github.com/dougborg/statuspro-openapi-client/blob/main/docs/RELEASE.md#trusted-publisher-environments-deviation-from-other-repos-in-this-migration))
1. Version already exists on PyPI (can't overwrite)
1. PyPI service outage

**Solutions**:

1. Check PyPI Trusted Publisher configuration (no environment, correct repo/workflow)
1. Check if version exists: https://pypi.org/project/statuspro-mcp-server/#history
1. Check PyPI status: https://status.python.org/
1. Re-run the failed `publish.yml` job — the tag and draft release persist

### Tests Failed in CI

**Symptom**: PR checks failing

**Solutions**:

1. Run tests locally: `uv run pytest tests/`
1. Check test output in GitHub Actions
1. Fix the issue and push a new commit

## Release Workflow Details

### release-please Configuration

The MCP server's component is declared in the repo root's `release-please-config.json`:

```jsonc
"statuspro_mcp_server": {
  "release-type": "python",
  "component": "mcp",
  "package-name": "statuspro-mcp-server",
  "changelog-path": "CHANGELOG.md"
}
```

### GitHub Workflows

- **`.github/workflows/release-please.yml`** — opens/updates the aggregated release PR;
  creates the `mcp-v{version}` tag + draft release on merge
- **`.github/workflows/release-pr-prepare.yml`** — keeps `uv.lock` and the MCP's
  `statuspro-openapi-client>=X` floor in sync with the release PR's proposed client
  version
- **`.github/workflows/publish.yml`** (`publish-mcp`, `publish-mcp-docker` jobs) —
  builds, publishes to PyPI + GHCR, and finalizes the release

### PyPI Trusted Publisher

Configured at: https://pypi.org/manage/project/statuspro-mcp-server/settings/publishing/

- **Owner**: `dougborg`
- **Repository**: `statuspro-openapi-client`
- **Workflow**: `publish.yml`
- **Job**: `publish-mcp`
- **Environment**: (none — deliberately left blank; see
  [RELEASE.md](https://github.com/dougborg/statuspro-openapi-client/blob/main/docs/RELEASE.md#trusted-publisher-environments-deviation-from-other-repos-in-this-migration))

## Version Numbering

This project uses semantic versioning with pre-release identifiers:

### Version Format: `MAJOR.MINOR.PATCH[-prerelease]`

- **MAJOR**: Breaking changes (`feat(mcp)!:` or `BREAKING CHANGE:`)
- **MINOR**: New features (`feat(mcp):`)
- **PATCH**: Bug fixes (`fix(mcp):`, `perf(mcp):`)

### Pre-release Phases:

- **Alpha** (0.1.0a1, 0.1.0a2): Early development, unstable, breaking changes expected
- **Beta** (0.1.0b1): Feature complete, testing, API stabilizing
- **RC** (0.1.0rc1): Release candidate, final testing
- **Stable** (0.1.0, 1.0.0): Production-ready release

## Checklist for Contributors

Before submitting a PR touching the MCP server:

- [ ] All tests pass locally: `uv run pytest tests/`
- [ ] Commit messages use `(mcp)` scope (for changelog readability)
- [ ] Commit messages follow conventional commits
- [ ] README updated if adding new features
- [ ] Integration tests added/updated if needed
- [ ] Breaking changes documented in commit body (if any)

After the release PR is merged:

- [ ] Check `publish.yml`'s `publish-mcp`/`publish-mcp-docker` runs succeeded
- [ ] Verify new version on PyPI
- [ ] Test installation from PyPI
- [ ] Check GitHub Release notes and attached assets (wheel, sdist, `.mcpb`)

## Related Documentation

- **Main Release Guide**:
  [docs/RELEASE.md](https://github.com/dougborg/statuspro-openapi-client/blob/main/docs/RELEASE.md)
  — full monorepo release process
- **Contributing**:
  [docs/CONTRIBUTING.md](https://github.com/dougborg/statuspro-openapi-client/blob/main/docs/CONTRIBUTING.md)
  — commit message format
- **MCP Documentation Index**:
  [docs/mcp-server/README.md](https://github.com/dougborg/statuspro-openapi-client/blob/main/statuspro_mcp_server/docs/README.md)
  — all MCP documentation

## Related Links

- **PyPI Project**: https://pypi.org/project/statuspro-mcp-server/
- **GitHub Repository**: https://github.com/dougborg/statuspro-openapi-client
- **GitHub Releases**:
  https://github.com/dougborg/statuspro-openapi-client/releases?q=mcp-v
- **Main Client**: https://pypi.org/project/statuspro-openapi-client/
