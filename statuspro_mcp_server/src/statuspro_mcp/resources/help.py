"""MCP resource: tool reference and workflow guide for StatusPro."""

from __future__ import annotations

from fastmcp import FastMCP

_HELP_MARKDOWN = """\
# StatusPro MCP Server — Tool Reference

## Orders

| Tool | Endpoint | Purpose |
| ---- | -------- | ------- |
| `list_orders` | `GET /orders` | Paginated list with filters (search, status, tags, due-date range). Auto-paginates. `search` matches order number, name, or customer fields — use it to find an order from just an order number. |
| `get_order` | `GET /orders/{id}` | Full detail for one order, including history. |
| `get_viable_statuses` | `GET /orders/{id}/viable-statuses` | Valid status transitions for the order's current state. |
| `update_order_status` | `POST /orders/{id}/status` | Change status. Two-step confirm. |
| `add_order_comment` | `POST /orders/{id}/comment` | Add a history comment. Two-step confirm. 5/min. |
| `update_order_due_date` | `POST /orders/{id}/due-date` | Change due date / date range. Two-step confirm. |
| `bulk_update_order_status` | `POST /orders/bulk-status` | Update up to 50 orders in one request. Two-step confirm. 5/min. |

## Statuses

| Tool | Endpoint | Purpose |
| ---- | -------- | ------- |
| `list_statuses` | `GET /statuses` | Full status catalog for the account. |

## Resources

- `statuspro://statuses` — JSON list of all defined statuses (cached read).
- `statuspro://help` — this document.

## Recommended workflow for status changes

```
get_order(order_id)                 # confirm you're targeting the right order
get_viable_statuses(order_id)       # discover the valid transitions
update_order_status(
    order_id=…, status_code=…,
    confirm=False,                  # preview
)
update_order_status(…, confirm=True)  # apply
```

## Rate limits

StatusPro documents rate limits per-endpoint in its OpenAPI description (not
in response headers). The client retries 429s with exponential backoff.

- Most endpoints: 60 requests/minute.
- `add_order_comment`, `bulk_update_order_status`: 5 requests/minute.
"""


def register_resources(mcp: FastMCP) -> None:
    """Register the ``statuspro://help`` resource."""

    @mcp.resource(
        uri="statuspro://help",
        name="Tool reference",
        description="Tool reference and recommended workflows for the StatusPro MCP server.",
        mime_type="text/markdown",
    )
    async def help_resource() -> str:
        return _HELP_MARKDOWN
