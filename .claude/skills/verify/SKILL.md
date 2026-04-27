---
name: verify
description: Skeptically verify that an implementation actually works — exercise the feature, run validation tiers, check coverage, confirm new code is wired up. Delegates to the verifier agent.
allowed-tools: Read, Grep, Glob, Bash(git status), Bash(git diff*), Bash(git log*), Bash(uv run poe quick-check), Bash(uv run poe agent-check), Bash(uv run poe check), Bash(uv run poe full-check), Bash(uv run poe test), Bash(uv run poe test-coverage)
---

# /verify — Skeptical implementation check

## PURPOSE

Prove the implementation works with evidence — not assumptions. Catches "compiles but doesn't actually run" failures the test suite can miss.

## CRITICAL

- **Trust evidence, not claims** — run every command, read every file, check every output. Never accept "should work" without proof.
- **Exercise the feature first** — before checking infrastructure, actually invoke the new MCP tool / API method / fixed code path
- **Use `LSP findReferences` on new symbols** — zero callers means it's not wired up, even if imported
- **Generated files must be intact** — if `api/`, `models/`, or `client.py` changed, both `regenerate-client` and `generate-pydantic` must have run

## STANDARD PATH

### 1. Pick the validation tier

| Tier | Cmd                       | When                                  |
| ---- | ------------------------- | ------------------------------------- |
| 1    | `uv run poe quick-check`  | During iterative development          |
| 2    | `uv run poe agent-check`  | Before committing                     |
| 3    | `uv run poe check`        | Before opening PR                     |
| 4    | `uv run poe full-check`   | Before requesting review              |

Use Tier 3 by default for verification. If the change is small and isolated, Tier 2 is enough.

### 2. Exercise the feature

- New MCP tool → invoke via test harness or MCP inspector
- New API method → make a test call (or via integration test)
- Bug fix → reproduce the original scenario; confirm it no longer fails
- Behavior change → demonstrate old vs new

### 3. Run the verifier agent

Delegate the systematic checklist to the `verifier` agent. It walks: code exists, code works (validation tier passes), code is complete (no TODO stubs), code is integrated (`LSP findReferences` on new public symbols), generated-files intact, coverage maintained, regression check.

### 4. Confirm

- Validation tier passes clean (no warnings)
- New public functions/classes have callers (or are intentionally part of a public API surface)
- Coverage on core ≥ 87%
- No tests skipped or deleted unintentionally

### 5. Report

```
## Verification Report
### Status: PASS | FAIL
### Verified
- [item]: [evidence: command output, file:line, test count]
### Failed
- [item]: [what's wrong, what to fix]
### Recommendations
- [improvements noticed]
```

## EDGE CASES

- [Coverage decreased] — identify which file lost coverage and why; document if the loss is acceptable (e.g. removed dead code) or fix.
- [Tests passed but feature doesn't actually work] — the feature exercise step (§2) caught it; otherwise verification is incomplete.
- [Verification reveals a doc gap] — fix CLAUDE.md or relevant guide as part of the verification work, not later.

## RELATED

- `verifier` agent — runs the full systematic checklist
- `pr-preparer` agent — checks process readiness (commit format, coverage threshold)
- `code-reviewer` agent — assesses code quality, not just whether it works
