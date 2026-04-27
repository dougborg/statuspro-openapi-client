---
name: code-review
description: Review the current branch for correctness, security, architecture, and project conventions before opening a PR. Delegates to the code-reviewer agent and adds StatusPro-specific checks.
allowed-tools: Read, Grep, Glob, Bash(git diff*), Bash(git log*), Bash(git show*), Bash(uv run poe check)
---

# /code-review — StatusPro branch review

## PURPOSE

Review current branch vs `main` for shippability — catch bugs, anti-patterns, and architecture violations before PR.

## CRITICAL

- **No edits to generated files** — `api/**/*.py`, `models/**/*.py`, `client.py` must come from regeneration, never manual edits
- **UNSET / helper compliance** — flag any `isinstance(_, type(UNSET))`, `hasattr` on attrs fields, manual `response.status_code == 200`, or wrapping API calls with retries (resilience is at the transport layer)
- **Help-resource sync** — if MCP tool parameters changed, `statuspro_mcp_server/.../resources/help.py` must be updated
- **Validation must pass** — `uv run poe check` must be green before approving; failures are BLOCKING

## STANDARD PATH

### 1. Classify the change

- **Type:** feature / fix / refactor / spec / config / docs
- **Risk:** low (cosmetic) / medium (new feature) / high (spec, transport, auth, breaking)
- **Packages affected:** client / mcp / typescript / cross-cutting

### 2. Run the upstream code-reviewer agent

Delegate the 6-dimension review (correctness, design, readability, performance, testing, security) to the `code-reviewer` agent. Pass it the diff range:

```bash
git diff main...HEAD
```

### 3. Run StatusPro-specific checks (in addition to agent output)

- Generated-file edits in `api/`, `models/`, `client.py` — if present, verify they came from `uv run poe regenerate-client` + `uv run poe generate-pydantic`
- UNSET / helper anti-patterns from CLAUDE.md "Known Pitfalls"
- Transport-layer resilience: no per-call retry/pagination wrappers
- Coverage: `uv run poe test-coverage` ≥ 87% on core
- ADR present for architectural decisions in `docs/adr/`

### 4. Validate

```bash
uv run poe check
```

Any failure is BLOCKING.

### 5. Report

Use `code-reviewer` output structure (BLOCKING / SUGGESTION / NITPICK with `file:line` references). Append the StatusPro-specific findings under their own subsection.

## EDGE CASES

- [Spec change] — Verify the local spec at `docs/statuspro-openapi.yaml` is consistent (consider spawning `spec-auditor`); confirm both `regenerate-client` and `generate-pydantic` ran.
- [Function signature changed] — Use `LSP findReferences` (or `LSP incomingCalls`) on the changed function to enumerate callers and confirm each still works with new semantics.
- [No diff vs main] — Stop and tell the user there's nothing to review.

## RELATED

- `code-reviewer` agent — does the heavy lifting; this skill adds StatusPro context
- `pr-preparer` agent — process readiness (commit format, coverage threshold, generated-file integrity)
- `domain-advisor` agent — answers "which pattern applies here?" questions during review
