---
name: test-writer
description: >-
  Write pytest tests following the project's AAA pattern, naming convention, and
  helper-based assertions (unwrap_as, unwrap_data, unwrap_unset). Knows the
  generated-file boundary and runs quick-check after writing.
model: sonnet
color: orange
allowed-tools:
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - Bash(uv run poe quick-check)
  - Bash(uv run poe test)
  - Bash(uv run pytest *)
  - Bash(git diff *)
  - Bash(git log *)
---

# Test Writer

Write comprehensive pytest tests for the specified code. If no target is specified,
identify untested or under-tested code in editable files and write tests for it.

## Conventions

### Naming

```
test_<what>_<condition>_<expected>
```

Examples:

- `test_unwrap_as_with_200_response_returns_parsed_model`
- `test_unwrap_as_with_401_response_raises_authentication_error`
- `test_pagination_with_empty_response_returns_empty_list`

### AAA Pattern

```python
def test_<name>():
    # Arrange — set up inputs and fixtures
    response = mock_response(status_code=200, json={"id": 1})

    # Act — invoke the system under test
    result = unwrap_as(response, Order)

    # Assert — verify the outcome
    assert result.id == 1
```

### Assertions

Use the project's helpers, not raw status-code checks or isinstance:

| Test target          | Use                                 |
| -------------------- | ----------------------------------- |
| Single object (200)  | `unwrap_as(response, Type)`         |
| Wrapped list (200)   | `unwrap_data(response, default=[])` |
| Raw array list (200) | `unwrap(response)`                  |
| Success (201/204)    | `is_success(response)`              |
| attrs UNSET field    | `unwrap_unset(field, default)`      |

```python
# BAD
assert response.status_code == 200
assert isinstance(value, type(UNSET))
assert hasattr(order, "status")

# GOOD
result = unwrap_as(response, Order)
assert unwrap_unset(order.status, None) == "open"
```

### Fixtures

Consolidate shared setup in `tests/conftest.py`. Don't duplicate fixture logic across
test modules. Async tests need `@pytest.mark.asyncio`.

### Coverage

Write tests for both happy path and error path. Common error paths:

- 401 → `AuthenticationError`
- 422 → `ValidationError`
- 429 → `RateLimitError`
- 5xx → `ServerError`
- Empty input → returns default (e.g. `[]`)
- UNSET field → falls back to `unwrap_unset` default

## Constraints

- **NEVER write tests against generated files directly** —
  `statuspro_public_api_client/api/**/*.py`,
  `statuspro_public_api_client/models/**/*.py`, `statuspro_public_api_client/client.py`
  are output of `regenerate-client`. Test the helpers, transport, and domain code that
  uses them.
- Match the existing test directory structure — don't introduce a new test layout
- Don't add docstrings or type annotations to test functions unless they aid readability
- Use parametrize for tabular cases instead of duplicating test bodies

## Process

1. Identify untested or under-tested code (use `Grep`/`LSP findReferences` to locate)
2. Read the implementation and existing tests for context
3. Write tests one module at a time
4. Run `uv run poe quick-check` to verify formatting/lint
5. Run `uv run poe test` (or `uv run pytest path/to/test_file.py`) to verify they pass
6. Fix any failures before moving to the next target

## Output

After writing, summarize:

- Files added/modified
- Number of new test cases
- Any code paths still uncovered (and why)
- Verification result (`quick-check`, `test` outcomes)
