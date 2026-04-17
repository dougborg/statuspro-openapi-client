# ADR-0016: Tool Interface Pattern

## Status

Accepted

Date: 2025-01-11 (updated 2026-04-17 for StatusPro fork — examples replaced,
core decision unchanged)

## Context

MCP tools need consistent, type-safe interfaces for requests and responses.
We needed to decide:

- How to structure tool parameters (flat vs nested)
- How to handle validation
- How to represent responses (structured vs string)
- How to integrate with FastMCP
- How to handle user confirmation for destructive operations

## Decision

We adopt the **Pydantic parameter annotations** pattern combined with **FastMCP
Elicitation** for destructive operations. StatusPro's tools are small enough
that we use Pydantic `Field()` on each parameter directly rather than a
nested request model + `Unpack()` decorator; the Katana parent project used
the Unpack pattern for its larger request bodies and we kept the decorator
infrastructure (`unpack.py`) as an option.

### Pattern components

#### 1. Per-parameter annotations (typical StatusPro tool)

```python
@mcp.tool(
    name="update_order_status",
    description="Change an order's status. Two-step confirm.",
)
async def update_order_status(
    context: Context,
    order_id: int,
    status_code: Annotated[
        str, Field(description="8-char status code, e.g. 'st000003'")
    ],
    comment: Annotated[str | None, Field(description="Optional history comment")] = None,
    public: Annotated[bool, Field(description="Visible to the customer")] = False,
    email_customer: bool = True,
    email_additional: bool = True,
    confirm: Annotated[bool, Field(description="Must be true to apply the change")] = False,
) -> dict[str, Any]:
    ...
```

#### 2. Request model + Unpack decorator (for complex bodies)

When a request has many fields or nested structure, wrap it in a Pydantic
model and use the `@unpack_pydantic_params` decorator (still available via
`statuspro_mcp/unpack.py`):

```python
class BulkStatusUpdateRequest(BaseModel):
    order_ids: list[int] = Field(..., min_length=1, max_length=50)
    status_code: str
    comment: str | None = None
    public: bool = False
    email_customer: bool = True
    confirm: bool = False

@unpack_pydantic_params
async def bulk_update_order_status(
    request: Annotated[BulkStatusUpdateRequest, Unpack()],
    context: Context,
) -> dict[str, Any]:
    ...
```

#### 3. Response shape

StatusPro tools return plain dicts. The mutation tools follow this shape:

```python
{
    "confirmed": bool,
    "success": bool,
    "status_code": int,    # HTTP status from the API
    # For bulk ops:
    "note": "Bulk updates are queued and processed asynchronously.",
}
```

Non-mutation tools return typed Pydantic responses (e.g. `list[OrderSummary]`,
`list[StatusEntry]`).

#### 4. Elicitation pattern (safety-critical operations)

For destructive operations, we use FastMCP's elicitation to request user
confirmation:

```python
# Preview mode (confirm=false) — show what would happen
if not confirm:
    return {"preview": preview, "confirmed": False}

# Request user confirmation via elicitation
result = await require_confirmation(
    context,
    f"Change order {order_id} status to {status_code}?",
)
if result is not ConfirmationResult.CONFIRMED:
    return {"preview": preview, "confirmed": False, "result": result.value}

# User confirmed — proceed with the API call
response = await update_order_status_api.asyncio_detailed(...)
return {"confirmed": True, "success": is_success(response), ...}
```

#### 5. Shared schemas

Common schemas live in `statuspro_mcp/tools/schemas.py` so every mutation
tool reuses the same confirmation flow:

```python
# statuspro_mcp/tools/schemas.py
class ConfirmationSchema(BaseModel):
    """Schema for user confirmation elicitation."""
    confirm: bool = Field(..., description="Confirm the action (true to proceed)")


async def require_confirmation(context: Context, message: str) -> ConfirmationResult:
    ...
```

### Benefits

- **Type safety**: Pydantic validates all inputs at runtime
- **Documentation**: Field descriptions are self-documenting
- **IDE support**: Autocomplete and type checking work perfectly
- **Testability**: Easy to mock and test with Pydantic models
- **Consistency**: All mutation tools follow the same two-step confirm pattern
- **Safety**: Destructive operations require explicit user confirmation
- **DRY**: Shared `require_confirmation` helper across every mutation tool

## Consequences

### Positive

- Type-safe tool interfaces prevent runtime errors
- Self-documenting parameters improve developer experience
- Validation errors are clear and actionable
- Elicitation prevents accidental destructive operations
- Shared helpers ensure consistency across tools

### Negative

- Per-parameter `Annotated[...]` annotations are verbose for wide signatures
- Unpack decorator adds complexity where it's used
- Elicitation adds an extra round-trip for confirmed operations

### Neutral

- Elicitation pattern only used for destructive operations (4 of 9 tools)
- Preview-then-confirm means every mutation is at minimum a two-call flow

## Alternatives considered

### Alternative 1: Flat untyped parameters

```python
async def update_order_status(
    order_id: int,
    status_code: str,
    comment: str | None,    # ❌ No Field description
    ...
    context: Context,
) -> dict:
    ...
```

**Why rejected**: No validation, tool schemas lose field descriptions the
model sees, harder to keep tools consistent.

### Alternative 2: Dictionary-based

```python
async def update_order_status(
    params: dict,    # ❌ No type safety
    context: Context,
) -> dict:
    ...
```

**Why rejected**: No IDE support, no validation, no documentation.

### Alternative 3: Manual confirmation via response field (no elicitation)

```python
async def update_order_status(...) -> dict:
    if not confirmed:
        return {"status": "pending", "confirmation_required": True}
    # Otherwise apply
```

**Why rejected**: Two round trips, harder to use, no built-in UI integration
for preview/confirm in Claude Desktop.

## Implementation examples

Mutation tools using this pattern (all follow two-step confirm with elicitation):

- `update_order_status`
- `add_order_comment`
- `update_order_due_date`
- `bulk_update_order_status`

Read-only tools (no elicitation):

- `list_orders`, `get_order`, `lookup_order`, `list_statuses`, `get_viable_statuses`

## References

- [ADR-0011: Pydantic Domain Models](../../statuspro_public_api_client/docs/adr/0011-pydantic-domain-models.md)
- [ADR-0017: Automated Tool Documentation](0017-automated-tool-documentation.md)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp) — Elicitation pattern
