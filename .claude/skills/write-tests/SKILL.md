---
name: write-tests
description: Write pytest tests using AAA pattern, project naming convention, and helper-based assertions (unwrap_as, unwrap_data, unwrap_unset). Delegates to the test-writer agent.
allowed-tools: Read, Edit, Write, Grep, Glob, Bash(uv run poe quick-check), Bash(uv run poe test), Bash(uv run poe test-coverage), Bash(uv run pytest *)
---

# /write-tests — Project test authoring

## PURPOSE

Add or expand pytest tests using StatusPro conventions. Spawns the `test-writer` agent for implementation; this skill defines the contract.

## CRITICAL

- **Never test generated files directly** — `api/`, `models/`, `client.py` are output of regeneration; test the helpers and transport that wrap them
- **Use project assertion helpers** — `unwrap_as` / `unwrap_data` / `unwrap_unset` / `is_success`; never `response.status_code == 200`, `isinstance(_, type(UNSET))`, or `hasattr` on attrs fields
- **Cover error paths** — every API integration needs assertions for 401 / 422 / 429 / 5xx via the typed exception hierarchy
- **No skipped or deleted tests** — if a test breaks, fix the code or the test, never `pytest.skip` or `noqa` to make CI green

## STANDARD PATH

### 1. Identify the target

If the user named a target, use it. Otherwise:

```bash
LSP documentSymbol on candidate files → inventory functions/classes
LSP findReferences on each → see real-world callers
```

Look for under-tested code in `statuspro_public_api_client/` (excluding generated paths), `statuspro_mcp_server/`.

### 2. Enumerate cases

For each function: empty inputs, boundary values, invalid types, None / UNSET handling, error conditions (401, 404, 422, 429, 5xx), concurrent access (async).

### 3. Spawn the test-writer agent

The agent applies the AAA pattern, the `test_<what>_<condition>_<expected>` naming convention, and project assertion helpers. It runs `uv run poe quick-check` after writing.

### 4. Verify

```bash
uv run poe test
uv run poe test-coverage
```

Core coverage must stay ≥ 87%.

## EDGE CASES

- [Async test] — must have `@pytest.mark.asyncio`. Don't forget the marker even when the test looks synchronous from inside.
- [HTTP mocking] — use `httpx.MockTransport` with shared fixtures from `conftest.py`. Don't reinvent mocking per test module.
- [Tabular cases] — use `@pytest.mark.parametrize` instead of duplicating bodies.
- [Test reveals undocumented API behavior] — update CLAUDE.md "Known Pitfalls" so the next session doesn't rediscover it.

## RELATED

- `test-writer` agent — runs the AAA loop, encodes naming and helper conventions
- `domain-advisor` agent — answers "which helper applies here?" mid-test
