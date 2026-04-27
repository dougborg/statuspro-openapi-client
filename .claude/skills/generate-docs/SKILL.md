---
name: generate-docs
description: Generate or update docstrings, ADRs, READMEs, cookbook recipes, and user guides. Knows about MCP help-resource drift and ADR numbering scheme.
allowed-tools: Read, Edit, Write, Grep, Glob, Bash(uv run poe format), Bash(uv run poe docs-build), Bash(ls *), Bash(git log *)
---

# /generate-docs — Project documentation

## PURPOSE

Add or update documentation for code, architecture decisions, and usage patterns. Knows StatusPro's doc layout (ADRs, MkDocs guides, cookbook, MCP help resource).

## CRITICAL

- **MCP help-resource drift is silent** — when adding/changing MCP tool parameters, also update `statuspro_mcp_server/.../resources/help.py`. The hardcoded help content does not auto-sync from tool signatures.
- **ADR numbering is sequential** — find the next number with `ls docs/adr/*.md | grep -o '[0-9]\{4\}' | sort -n | tail -1`. Then update `docs/adr/README.md` index.
- **Code examples must be tested** — every snippet in cookbook recipes or guides must be a real, working example. Don't invent untested code.
- **Format markdown** — `uv run poe format` (88-char lines, ATX headers).

## STANDARD PATH

### 1. Identify what's needed

| Doc type        | Location                      | When                                      |
| --------------- | ----------------------------- | ----------------------------------------- |
| Docstring       | inline (Google style)         | Public functions/classes/modules added    |
| ADR             | `docs/adr/NNNN-*.md`          | Architectural decision made               |
| Cookbook recipe | `docs/COOKBOOK.md`            | New usage pattern worth sharing           |
| User guide      | `docs/*.md`                   | Complex feature needs walkthrough         |
| README          | package root                  | New package or major surface change       |
| MCP help        | `statuspro_mcp_server/.../resources/help.py` | MCP tool params changed |

### 2. Write following the templates

Docstring (Google style):

```python
def unwrap_as(response: Response, expected_type: type[T]) -> T:
    """Extract and validate a parsed response as the expected type.

    Args:
        response: The HTTP response to unwrap.
        expected_type: The type to validate the parsed response against.

    Returns:
        The parsed response cast to the expected type.

    Raises:
        AuthenticationError: If the response is 401 Unauthorized.
        ValidationError: If the response is 422 Unprocessable Entity.
        APIError: For other non-success status codes.
    """
```

ADR: copy `docs/adr/template.md` to `docs/adr/<next-number>-<slug>.md`; update `docs/adr/README.md` index.

### 3. Verify

```bash
uv run poe format
uv run poe docs-build  # only if updating MkDocs content
```

## EDGE CASES

- [Adding/changing MCP tool] — update help-resource as part of the same change. Out-of-sync help is a known pitfall.
- [ADR contradicts existing one] — supersede with `Status: Superseded by ADR-NNNN` in the old ADR.
- [Existing docs are wrong while writing new ones] — fix what's there as part of the work; don't ship new docs that conflict with old.

## RELATED

- CLAUDE.md "Detailed Documentation" table — full inventory of project docs
- `docs/adr/README.md` — ADR index, must be updated after creating an ADR
