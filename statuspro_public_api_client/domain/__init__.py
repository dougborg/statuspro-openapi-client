"""Pydantic domain models for StatusPro entities.

Hand-written domain models representing business entities from the StatusPro API,
separate from the generated attrs API request/response models. Use these for
business logic, validation, and ergonomic access to API data.

Example:
    ```python
    from statuspro_public_api_client import StatusProClient
    from statuspro_public_api_client.domain import Order

    async with StatusProClient() as client:
        orders = await client.orders.list(per_page=50)
        for order in orders:
            print(f"{order.name}: {order.status.name}")
    ```
"""

from .base import StatusProBaseModel
from .converters import to_unset, unwrap_unset
from .order import Customer, Order, OrderStatus, PageMeta
from .status import Status

__all__ = [
    "Customer",
    "Order",
    "OrderStatus",
    "PageMeta",
    "Status",
    "StatusProBaseModel",
    "to_unset",
    "unwrap_unset",
]
