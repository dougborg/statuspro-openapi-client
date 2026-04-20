# StatusPro MCP Server — Workflow Examples

Typical natural-language flows you can try with Claude Desktop once the
server is connected. Each example shows the underlying tool sequence.

> **Tip**: the `statuspro://help` resource surfaces the same information
> from inside the MCP client.

## Looking up an order

```
User: "Find order 1188 for customer@example.com"

Model:
  lookup_order(number="1188", email="customer@example.com")
  → Order 6110375248088 — "#1188" — Status: "In Production"
```

## Listing orders by state

```
User: "Show me orders currently in production that are due this week"

Model:
  list_orders(
    status_code="st000002",
    exclude_cancelled=True,
    due_date_to="2026-03-08T00:00:00+00:00",
    per_page=50,
  )
  → [<20 OrderSummary entries>]
```

## Changing one order's status (two-step confirm)

```
User: "Mark order 6110375248088 as shipped and notify the customer"

Model:
  # 1. Verify the target status is reachable.
  get_viable_statuses(order_id=6110375248088)
  → [..., Status(code="st000003", name="Shipped"), ...]

  # 2. Preview — confirm=False returns a preview, no write.
  update_order_status(
    order_id=6110375248088,
    status_code="st000003",
    comment="Shipped via UPS — tracking 1Z999AA10123456784",
    public=True,
    email_customer=True,
    confirm=False,
  )
  → {"preview": {...}, "confirmed": False}

  # 3. Execute — confirm=True triggers an elicit for explicit user approval.
  update_order_status(..., confirm=True)
  → {"confirmed": True, "success": True, "status_code": 200}
```

## Adding a customer-visible comment

```
User: "Post a public update on order 6110375248088 saying the parts arrived"

Model:
  add_order_comment(
    order_id=6110375248088,
    comment="Parts received — assembly starts tomorrow.",
    public=True,
    confirm=False,
  )
  → preview

  add_order_comment(..., confirm=True)
  → {"confirmed": True, "success": True, "status_code": 200}
```

The `/comment` endpoint is rate-limited to **5 requests/minute**.

## Pushing back a due date

```
User: "Slip order 6110375248088's due date to next Friday"

Model:
  update_order_due_date(
    order_id=6110375248088,
    due_date="2026-03-13T17:00:00+00:00",
    confirm=False,
  )
  → preview

  update_order_due_date(..., confirm=True)
```

## Bulk status update (up to 50 orders)

```
User: "Mark these 25 orders as shipped without emailing customers"

Model:
  bulk_update_order_status(
    order_ids=[...25 ids...],
    status_code="st000003",
    email_customer=False,
    confirm=False,
  )
  → preview (one preview dict, lists all 25)

  bulk_update_order_status(..., confirm=True)
  → {"confirmed": True, "success": True, "status_code": 202,
     "note": "Bulk updates are queued and processed asynchronously."}
```

`/bulk-status` returns **202 Accepted** — the updates are queued and applied
in the background. It's also rate-limited to **5 requests/minute**.

## Listing all statuses

```
User: "What statuses are configured on this account?"

Model:
  list_statuses()
  → [
      {code: "st000001", name: "Order Received", color: "gray"},
      {code: "st000002", name: "In Production", color: "pink"},
      {code: "st000003", name: "Shipped",       color: "green"},
      ...
    ]
```

Or browse the `statuspro://statuses` resource for a cached JSON snapshot.
