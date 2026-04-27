---
name: techdebt-scan
description: Scan editable code for tech debt and anti-patterns specific to this repo (UNSET misuse, manual status-code checks, retry wrapping, dead code). Reports findings without applying fixes.
allowed-tools: Read, Grep, Glob, Bash(uv run poe quick-check), Bash(uv run poe fix), Bash(git diff*), Bash(git log*)
---

# /techdebt-scan — StatusPro tech-debt scan

## PURPOSE

Find anti-patterns, dead code, and code smells in editable files. Survey only — does not apply fixes. For active remediation, spawn the `code-modernizer` agent.

## CRITICAL

- **Never flag or scan generated files** — `statuspro_public_api_client/api/**/*.py`, `statuspro_public_api_client/models/**/*.py`, `statuspro_public_api_client/client.py` are output of regeneration
- **LSP-verify before flagging dead code** — run `LSP findReferences` on the symbol; pyright walks the real import graph (`from x import *`, aliased re-exports) that grep misses. Zero references = safe to flag.
- **LSP-verify before flagging `hasattr` rewrites** — run `LSP hover`. If the type points into an attrs model (`Unset | T`), the rewrite to `unwrap_unset` is safe. Plain Python class? It may be a real `hasattr` check — leave it.

## STANDARD PATH

### 1. Establish baseline

```bash
uv run poe quick-check
```

### 2. Scan editable files by category

Scan `statuspro_public_api_client/` (excluding generated paths above), `statuspro_mcp_server/`, `tests/`, `scripts/`:

- **Dead code** — unused imports/variables/functions/classes; verify with `LSP findReferences` before flagging
- **UNSET / helper anti-patterns** — `isinstance(_, type(UNSET))`, `hasattr` on attrs fields, manual `response.status_code == 200`, `value if value is not None else UNSET`
- **Architecture violations** — wrapping API methods with retry logic, broad `except Exception` without re-raise/log
- **Code smells** — too many parameters (extract dataclass), names shadowing built-ins, deeply nested conditionals, duplicate test-fixture logic
- **Missing best practices** — public functions without docstrings, async tests missing `@pytest.mark.asyncio`, fixtures that should be `scope="session"`

### 3. Auto-fix what's safe

```bash
uv run poe fix
```

### 4. Report

```
## Tech Debt Report

### Summary
- Dead code: N
- UNSET/helper anti-patterns: N
- Architecture violations: N
- Code smells: N
- Missing best practices: N

### HIGH (breaks conventions)
[file:line — current code → suggested fix]

### MEDIUM (code quality)
[...]

### LOW (nice to have)
[...]

### Improvements to CLAUDE.md
[Any new anti-patterns/pitfalls discovered worth documenting]
```

## EDGE CASES

- [Apply fixes, don't just survey] — Spawn `code-modernizer` agent with this report; it actively rewrites and runs `agent-check` between batches.
- [New anti-pattern found] — Add it to CLAUDE.md "Known Pitfalls" or "Anti-Patterns to Avoid" so future scans catch it earlier.

## RELATED

- `code-modernizer` agent — actively applies fixes for these categories
- CLAUDE.md "Known Pitfalls" + "Anti-Patterns to Avoid" — source of truth for project-specific debt
