"""Order helper facade — ergonomic wrappers around the generated order endpoints."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Any

from statuspro_public_api_client.helpers.base import Base

if TYPE_CHECKING:
    from statuspro_public_api_client.domain import Order


class Orders(Base):
    """Ergonomic order operations that return domain ``Order`` models."""

    async def list(
        self,
        *,
        search: str | None = None,
        status_code: str | None = None,
        tags: builtins.list[str] | None = None,
        tags_any: builtins.list[str] | None = None,
        financial_status: builtins.list[str] | None = None,
        fulfillment_status: builtins.list[str] | None = None,
        exclude_cancelled: bool | None = None,
        due_date_from: str | None = None,
        due_date_to: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> builtins.list[Order]:
        """List orders. Auto-paginates when ``page`` is not set."""
        from statuspro_public_api_client.api.orders import list_orders
        from statuspro_public_api_client.domain import Order
        from statuspro_public_api_client.utils import unwrap_data

        kwargs: dict[str, Any] = {
            "client": self._client,
            "search": search,
            "status_code": status_code,
            "tags": tags,
            "tags_any": tags_any,
            "financial_status": financial_status,
            "fulfillment_status": fulfillment_status,
            "exclude_cancelled": exclude_cancelled,
            "due_date_from": due_date_from,
            "due_date_to": due_date_to,
            "page": page,
            "per_page": per_page,
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        response = await list_orders.asyncio_detailed(**kwargs)
        raw_orders = unwrap_data(response, default=[])
        return [Order.model_validate(o.to_dict()) for o in raw_orders]

    async def get(self, order_id: int) -> Order:
        """Get a single order by id."""
        from statuspro_public_api_client.api.orders import get_order
        from statuspro_public_api_client.domain import Order
        from statuspro_public_api_client.models.order_response import OrderResponse
        from statuspro_public_api_client.utils import unwrap_as

        response = await get_order.asyncio_detailed(client=self._client, order=order_id)
        raw = unwrap_as(response, OrderResponse)
        return Order.model_validate(raw.to_dict())

    async def lookup(self, *, number: str, email: str) -> Order:
        """Look up an order by order number and customer email."""
        from statuspro_public_api_client.api.orders import lookup_order
        from statuspro_public_api_client.domain import Order
        from statuspro_public_api_client.models.order_response import OrderResponse
        from statuspro_public_api_client.utils import unwrap_as

        response = await lookup_order.asyncio_detailed(
            client=self._client, number=number, email=email
        )
        raw = unwrap_as(response, OrderResponse)
        return Order.model_validate(raw.to_dict())
