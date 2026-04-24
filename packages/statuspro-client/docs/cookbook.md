# Cookbook: Common Patterns (TypeScript)

Ready-to-use recipes for the StatusPro TypeScript client. See the [guide](guide.md) for
the conceptual overview.

## Contents

- [List orders with filters](#list-orders-with-filters)
- [Look up an order by number + email](#look-up-an-order-by-number--email)
- [Get one order with full detail](#get-one-order-with-full-detail)
- [Change an order's status safely](#change-an-orders-status-safely)
- [Add a public comment](#add-a-public-comment)
- [Push back a due date](#push-back-a-due-date)
- [Bulk-update up to 50 orders](#bulk-update-up-to-50-orders)
- [Load the full status catalog](#load-the-full-status-catalog)
- [Pagination: one page vs. all pages](#pagination-one-page-vs-all-pages)
- [Testing patterns](#testing-patterns)

## List orders with filters

```typescript
import { StatusProClient, listOrders } from "statuspro-client";

const client = await StatusProClient.create();

const { data } = await listOrders({
  client: client.sdk,
  query: {
    status_code: "st000002",
    exclude_cancelled: true,
    due_date_to: "2026-03-08T00:00:00+00:00",
    per_page: 50,
  },
});

for (const order of data?.data ?? []) {
  console.log(`${order.name}: ${order.status?.name ?? "—"}`);
}
```

## Look up an order by number + email

```typescript
import { lookupOrder } from "statuspro-client";

const { data: order } = await lookupOrder({
  client: client.sdk,
  query: { number: "1188", email: "customer@example.com" },
});

if (order) {
  console.log(`Order ${order.id}: ${order.status?.name}`);
}
```

## Get one order with full detail

```typescript
import { getOrder } from "statuspro-client";

const { data: order } = await getOrder({
  client: client.sdk,
  path: { order: 6110375248088 },
});

if (order) {
  console.log(`${order.name} — ${order.history?.length ?? 0} history entries`);
}
```

## Change an order's status safely

Call `/viable-statuses` first to confirm the target status is a valid transition.

```typescript
import { getViableStatuses, updateOrderStatus } from "statuspro-client";

async function advanceToShipped(orderId: number): Promise<boolean> {
  const { data: viable } = await getViableStatuses({
    client: client.sdk,
    path: { order: orderId },
  });

  const shipped = viable?.find((s) => (s.name ?? "").toLowerCase().includes("ship"));
  if (!shipped) {
    console.warn(`No shipped-like status is a valid transition for order ${orderId}`);
    return false;
  }

  const { response } = await updateOrderStatus({
    client: client.sdk,
    path: { order: orderId },
    body: {
      status_code: shipped.code,
      comment: "Shipped via carrier.",
      public: true,
      email_customer: true,
    },
  });
  return response.ok;
}
```

## Add a public comment

```typescript
import { addOrderComment, RateLimitError, parseError } from "statuspro-client";

const { response } = await addOrderComment({
  client: client.sdk,
  path: { order: 123 },
  body: { comment: "Parts received, starting assembly.", public: true },
});

if (!response.ok) {
  const error = parseError(response, await response.json());
  if (error instanceof RateLimitError) {
    // /comment is limited to 5/min
    console.warn("Rate-limited; try again shortly.");
  }
}
```

## Push back a due date

```typescript
import { setOrderDueDate } from "statuspro-client";

await setOrderDueDate({
  client: client.sdk,
  path: { order: 123 },
  body: { due_date: "2026-03-13T17:00:00+00:00" },
});
```

## Bulk-update up to 50 orders

```typescript
import { bulkUpdateOrderStatus } from "statuspro-client";

const { response } = await bulkUpdateOrderStatus({
  client: client.sdk,
  body: {
    order_ids: [6110375248088, 6110375248089, 6110375248090],
    status_code: "st000003",
    email_customer: false,
  },
});

// 202 Accepted: the update is queued and applied asynchronously.
console.log(`Bulk status code: ${response.status}`);
```

## Load the full status catalog

```typescript
import { getStatuses } from "statuspro-client";

const { data: statuses } = await getStatuses({ client: client.sdk });

for (const s of statuses ?? []) {
  console.log(`${s.code.padEnd(10)}  ${s.name}  (${s.color ?? "—"})`);
}
```

## Pagination: one page vs. all pages

```typescript
// Auto-paginated (default) — collects every page of /orders
const all = await client.get("/orders");
const { data: allOrders, pagination } = await all.json();
console.log(
  `${pagination.total_items} orders across ${pagination.collected_pages} pages`,
);

// Single page — explicit `page` disables auto-pagination
const single = await client.get("/orders", { page: 1, per_page: 25 });
const { data: firstPage, meta } = await single.json();
console.log(`Page ${meta.current_page}/${meta.last_page}`);
```

## Testing patterns

Mock the fetch layer rather than the SDK:

```typescript
import { describe, it, expect, beforeEach, vi } from "vitest";
import { StatusProClient } from "statuspro-client";

describe("my app", () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({
        data: [
          {
            id: 1,
            name: "#1001",
            order_number: "1001",
            customer: { name: "Test", email: "test@example.com" },
            status: { code: "st000002", name: "In Production" },
          },
        ],
        meta: {
          current_page: 1,
          last_page: 1,
          per_page: 100,
          total: 1,
          from: 1,
          to: 1,
        },
      }),
    } as Response);
  });

  it("lists orders", async () => {
    const client = StatusProClient.withApiKey("test-key");
    const response = await client.get("/orders");
    const { data } = await response.json();
    expect(data).toHaveLength(1);
    expect(data[0].status.code).toBe("st000002");
  });
});
```

See the [testing guide](testing.md) for the full testing strategy.
