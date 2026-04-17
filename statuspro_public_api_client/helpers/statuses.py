"""Status helper facade — ergonomic wrappers around the generated status endpoints."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from statuspro_public_api_client.helpers.base import Base

if TYPE_CHECKING:
    from statuspro_public_api_client.domain import Status


class Statuses(Base):
    """Ergonomic status catalog operations."""

    async def list(self) -> builtins.list[Status]:
        """Return the full status catalog (``/statuses``)."""
        from statuspro_public_api_client.api.statuses import get_statuses
        from statuspro_public_api_client.domain import Status
        from statuspro_public_api_client.utils import unwrap_data

        response = await get_statuses.asyncio_detailed(client=self._client)
        raw = unwrap_data(response, default=[])
        return [Status.model_validate(s.to_dict()) for s in raw]

    async def viable_for(self, order_id: int) -> builtins.list[Status]:
        """Return statuses that are valid transitions from the order's current state."""
        from statuspro_public_api_client.api.orders import get_viable_statuses
        from statuspro_public_api_client.domain import Status
        from statuspro_public_api_client.utils import unwrap_data

        response = await get_viable_statuses.asyncio_detailed(
            client=self._client, order=order_id
        )
        raw = unwrap_data(response, default=[])
        return [Status.model_validate(s.to_dict()) for s in raw]
