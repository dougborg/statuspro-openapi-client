# StatusProClient Cookbook

Focused recipes for common StatusPro workflows. See the [guide](guide.md) for the
conceptual overview.

## List orders due in the next 7 days

```python
import asyncio
from datetime import datetime, timedelta, timezone

from statuspro_public_api_client import StatusProClient

async def main():
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=7)

    async with StatusProClient() as client:
        orders = await client.orders.list(
            exclude_cancelled=True,
            due_date_from=now.isoformat(),
            due_date_to=horizon.isoformat(),
        )
    for order in orders:
        print(f"{order.due_date} — {order.name} — {order.status.name if order.status else '—'}")

asyncio.run(main())
```

## Find an order by customer email + order number

```python
from statuspro_public_api_client import StatusProClient

async with StatusProClient() as client:
    order = await client.orders.lookup(number="1188", email="customer@example.com")
    print(order.id, order.status.name)
```

## Walk every order with a custom page size

```python
from statuspro_public_api_client import StatusProClient

async with StatusProClient(max_pages=500) as client:
    # per_page defaults to StatusPro's max (100) when omitted.
    all_orders = await client.orders.list()
    print(f"Total orders: {len(all_orders)}")
```

## Fetch a single page without auto-pagination

```python
async with StatusProClient() as client:
    first_page = await client.orders.list(page=1, per_page=50)
```

Passing an explicit `page` disables auto-pagination for that call.

## Cap total items collected

```python
async with StatusProClient() as client:
    httpx_client = client.get_async_httpx_client()
    response = await httpx_client.get(
        "/orders",
        params={"status_code": "st000002"},
        extensions={"max_items": 200},
    )
```

## Change an order's status safely

Call `/viable-statuses` first to confirm the target status is a valid transition from
the current state.

```python
from statuspro_public_api_client import StatusProClient
from statuspro_public_api_client.api.orders import update_order_status
from statuspro_public_api_client.models.update_order_status_request import (
    UpdateOrderStatusRequest,
)
from statuspro_public_api_client.utils import is_success

async def advance_to_shipped(order_id: int) -> bool:
    async with StatusProClient() as client:
        viable = await client.statuses.viable_for(order_id)
        shipped = next((s for s in viable if "ship" in (s.name or "").lower()), None)
        if shipped is None:
            print(f"No shipped-like status is a valid transition for order {order_id}")
            return False

        response = await update_order_status.asyncio_detailed(
            client=client,
            order=order_id,
            body=UpdateOrderStatusRequest(
                status_code=shipped.code,
                comment="Shipped via carrier.",
                public=True,
                email_customer=True,
            ),
        )
        return is_success(response)
```

## Add a public history comment

```python
from statuspro_public_api_client import StatusProClient
from statuspro_public_api_client.api.orders import add_order_comment
from statuspro_public_api_client.models.add_order_comment_request import (
    AddOrderCommentRequest,
)
from statuspro_public_api_client.utils import is_success, RateLimitError

async with StatusProClient() as client:
    try:
        response = await add_order_comment.asyncio_detailed(
            client=client,
            order=123,
            body=AddOrderCommentRequest(
                comment="Parts received, starting assembly.",
                public=True,
            ),
        )
        assert is_success(response)
    except RateLimitError:
        # /comment is limited to 5 requests / minute
        print("Rate-limited; try again shortly.")
```

## Bulk-update status for up to 50 orders

```python
from statuspro_public_api_client import StatusProClient
from statuspro_public_api_client.api.orders import bulk_update_order_status
from statuspro_public_api_client.models.bulk_status_update_request import (
    BulkStatusUpdateRequest,
)

async with StatusProClient() as client:
    ids = [6110375248088, 6110375248089, 6110375248090]
    response = await bulk_update_order_status.asyncio_detailed(
        client=client,
        body=BulkStatusUpdateRequest(
            order_ids=ids,
            status_code="st000003",
            email_customer=False,
        ),
    )
    # 202 Accepted: the update is queued and applied asynchronously.
    assert response.status_code == 202
```

## Load the full status catalog

```python
from statuspro_public_api_client import StatusProClient

async with StatusProClient() as client:
    statuses = await client.statuses.list()
    for s in statuses:
        print(f"{s.code:10}  {s.name}  ({s.color or '—'})")
```

## Handle validation errors

```python
from statuspro_public_api_client.utils import ValidationError

try:
    ...
except ValidationError as e:
    # e.validation_errors is dict[str, list[str]]
    for field, messages in e.validation_errors.items():
        for message in messages:
            print(f"{field}: {message}")
```

## Use `~/.netrc` instead of environment variables

```
# ~/.netrc
machine app.orderstatuspro.com
password your-api-key-here
```

```bash
chmod 600 ~/.netrc
```

The client will pick this up automatically if `STATUSPRO_API_KEY` is not set.
