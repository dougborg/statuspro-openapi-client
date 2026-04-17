"""Ergonomic helper facades for the StatusPro API client.

These classes wrap the generated API with domain-specific methods that reduce
boilerplate for common workflows. Each helper is accessed as an attribute on
``StatusProClient`` (e.g. ``client.orders.list(...)``).

Example:
    >>> async with StatusProClient() as client:
    ...     orders = await client.orders.list(per_page=50)
    ...     statuses = await client.statuses.list()
"""

from statuspro_public_api_client.helpers.base import Base
from statuspro_public_api_client.helpers.orders import Orders
from statuspro_public_api_client.helpers.statuses import Statuses

__all__ = [
    "Base",
    "Orders",
    "Statuses",
]
