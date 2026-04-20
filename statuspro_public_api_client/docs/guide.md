# StatusProClient Guide

The **StatusProClient** is the Python client for the [StatusPro
API](https://app.orderstatuspro.com/api/v1). It extends
`openapi-python-client`'s generated `AuthenticatedClient` with an httpx
transport stack that adds automatic retries, rate-limit awareness,
auto-pagination, and log sanitization — every endpoint inherits these for free.

The StatusPro API has seven endpoints covering order status lookup and
update. This guide covers using the client against that surface.

## Installation

```bash
pip install statuspro-openapi-client
```

```bash
# .env
STATUSPRO_API_KEY=your-api-key-here
STATUSPRO_BASE_URL=https://app.orderstatuspro.com/api/v1  # optional
```

## Quick Start

```python
import asyncio
from statuspro_public_api_client import StatusProClient

async def main():
    async with StatusProClient() as client:
        # High-level helper: returns Pydantic Order domain models
        orders = await client.orders.list(per_page=25)
        for order in orders:
            print(f"{order.name}: {order.status.name if order.status else '(none)'}")

asyncio.run(main())
```

The helper methods on `client.orders` and `client.statuses` return hand-written
Pydantic domain models (see `domain/`). If you want the raw attrs models
instead, call the generated API modules directly and pass `client` through:

```python
from statuspro_public_api_client import StatusProClient
from statuspro_public_api_client.api.orders import list_orders
from statuspro_public_api_client.utils import unwrap_data

async with StatusProClient() as client:
    response = await list_orders.asyncio_detailed(client=client, per_page=25)
    orders = unwrap_data(response, default=[])  # list of OrderListItem (attrs)
```

## Authentication

The client resolves the API key in this order:

1. `api_key=` constructor argument
1. `STATUSPRO_API_KEY` environment variable (including `.env` via python-dotenv)
1. `~/.netrc` entry matching the base-URL hostname:

```
machine app.orderstatuspro.com
password your-api-key-here
```

Run `chmod 600 ~/.netrc` to keep the file private; the client warns if
permissions are looser.

## Resilience

Every call through `StatusProClient` automatically gets:

### Retries

| Trigger               | Retried?                          |
| --------------------- | --------------------------------- |
| Network errors        | Yes (exponential backoff)         |
| 429 Too Many Requests | Yes — all methods, including POST |
| 502 / 503 / 504       | Yes — idempotent methods only     |
| Other 4xx             | No                                |

```python
async with StatusProClient(max_retries=5) as client:
    # POST/PATCH retry on 429; GET/PUT/DELETE retry on 429 + 5xx
    ...
```

### Rate-limit awareness

StatusPro documents rate limits (60/min on most endpoints, 5/min on
`/comment` and `/bulk-status`) but doesn't currently surface them in response
headers. The client's retry transport checks for `Retry-After` and falls
back to exponential backoff when it's missing.

### Auto-pagination

`GET /orders` is paginated. With auto-pagination (on by default for GET
requests without an explicit `page` parameter), the client walks every page
up to `meta.last_page` and returns the combined `data` array:

```python
async with StatusProClient(max_pages=200) as client:
    # Fetches every page automatically
    orders = await client.orders.list(status_code="st000002")
    print(f"Got {len(orders)} orders in production")
```

To fetch a single page, pass `page=` explicitly — that disables auto-
pagination for the call:

```python
page_two = await client.orders.list(page=2, per_page=50)
```

Cap the total items collected with the `max_items` extension on the raw
httpx client:

```python
async with StatusProClient() as client:
    httpx_client = client.get_async_httpx_client()
    response = await httpx_client.get(
        "/orders",
        extensions={"max_items": 200},
    )
```

**Raw-array endpoints** (`/statuses`, `/orders/{id}/viable-statuses`) are
not paginated — they return a flat JSON array and the transport passes them
through unchanged.

### Sensitive-data redaction

The client scrubs Authorization headers and any field matching common secret
patterns (`api_key`, `password`, `email`, `token`, etc.) from structured log
output.

## Response Handling

Use the helpers in `statuspro_public_api_client.utils` instead of writing
status-code checks by hand.

```python
from statuspro_public_api_client.utils import (
    unwrap,
    unwrap_as,
    unwrap_data,
    is_success,
)
```

| Helper        | When to use                                               |
| ------------- | --------------------------------------------------------- |
| `unwrap`      | Single-object response; raises typed exception on 4xx/5xx |
| `unwrap_as`   | Same but asserts the parsed body is a specific type       |
| `unwrap_data` | Wrapped list responses (`{"data": [...], "meta": {...}}`) |
| `is_success`  | 2xx check for POST endpoints that return no body          |

Typed exceptions raised by `unwrap()`:

| Exception             | HTTP Status                          |
| --------------------- | ------------------------------------ |
| `AuthenticationError` | 401                                  |
| `ValidationError`     | 422 (with `.validation_errors` dict) |
| `RateLimitError`      | 429                                  |
| `ServerError`         | 5xx                                  |
| `APIError`            | other 4xx (400, 403, 404, ...)       |

```python
from statuspro_public_api_client import StatusProClient
from statuspro_public_api_client.api.orders import get_order
from statuspro_public_api_client.models.order_response import OrderResponse
from statuspro_public_api_client.utils import unwrap_as, ValidationError

async with StatusProClient() as client:
    try:
        response = await get_order.asyncio_detailed(client=client, order=123)
        order = unwrap_as(response, OrderResponse)
        print(order.name, order.status.name)
    except ValidationError as e:
        print("Validation failed:", e.validation_errors)
```

## Domain Models

Hand-written Pydantic models live in `statuspro_public_api_client.domain`:

- `Order`, `OrderStatus`, `Customer`, `PageMeta` (orders)
- `Status` (status definitions)
- `StatusProBaseModel` (frozen, ignores unknown fields)

These are separate from the generated attrs models and are intended for
business-logic code, validation, and ETL. Convert between them with the
helpers in `statuspro_public_api_client.domain.converters`:

- `unwrap_unset(value, default)` — unwrap `UNSET` / `None` to a default.
- `to_unset(value)` — convert `None` to `UNSET` when building a request.

## Common Workflows

### List all orders, filtered

```python
async with StatusProClient() as client:
    overdue = await client.orders.list(
        exclude_cancelled=True,
        due_date_to="2026-03-01T00:00:00+00:00",
    )
    for order in overdue:
        print(f"{order.name} ({order.customer.email if order.customer else '—'})")
```

### Change one order's status

```python
from statuspro_public_api_client.api.orders import update_order_status
from statuspro_public_api_client.models.update_order_status_request import (
    UpdateOrderStatusRequest,
)
from statuspro_public_api_client.utils import is_success

async with StatusProClient() as client:
    viable = await client.statuses.viable_for(order_id=123)
    assert any(s.code == "st000003" for s in viable), "Not a valid transition"

    response = await update_order_status.asyncio_detailed(
        client=client,
        order=123,
        body=UpdateOrderStatusRequest(
            status_code="st000003",
            comment="Shipped via UPS tracking 1Z...",
            public=True,
            email_customer=True,
        ),
    )
    assert is_success(response)
```

### Bulk-update up to 50 orders

```python
from statuspro_public_api_client.api.orders import bulk_update_order_status
from statuspro_public_api_client.models.bulk_status_update_request import (
    BulkStatusUpdateRequest,
)

async with StatusProClient() as client:
    response = await bulk_update_order_status.asyncio_detailed(
        client=client,
        body=BulkStatusUpdateRequest(
            order_ids=[6110375248088, 6110375248089, 6110375248090],
            status_code="st000003",
            email_customer=False,
        ),
    )
    # Bulk updates are queued asynchronously; a 202 Accepted is success.
    assert response.status_code == 202
```

## Configuration Reference

| Constructor arg  | Default                                 | Notes                                              |
| ---------------- | --------------------------------------- | -------------------------------------------------- |
| `api_key`        | env / `.env` / netrc                    | Raises if not resolvable                           |
| `base_url`       | `https://app.orderstatuspro.com/api/v1` | Or `STATUSPRO_BASE_URL` env var                    |
| `timeout`        | `30.0`                                  | Per-request seconds                                |
| `max_retries`    | `5`                                     | Retry attempts before giving up                    |
| `max_pages`      | `100`                                   | Cap on auto-pagination walk                        |
| `logger`         | module logger                           | Any logger with `debug/info/warning/error`         |
| `**httpx_kwargs` | —                                       | Forwarded to the transport (http2, limits, verify) |
