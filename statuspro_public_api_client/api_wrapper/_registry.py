"""Data-driven registry mapping accessor names to generated API modules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResourceConfig:
    """Maps a logical resource to its generated API module functions.

    Attributes:
        module: Directory name under ``api/`` (e.g. ``"orders"``).
        get_one: Module name for single-resource GET, or ``None``.
        get_all: Module name for list GET, or ``None``.
        create: Module name for POST, or ``None``.
        update: Module name for PATCH/PUT, or ``None``.
        delete: Module name for DELETE, or ``None``.
    """

    module: str
    get_one: str | None = None
    get_all: str | None = None
    create: str | None = None
    update: str | None = None
    delete: str | None = None


# StatusPro has 7 endpoints. Only GET /orders, GET /orders/{id}, and GET /statuses
# fit cleanly into CRUD shape. The mutation endpoints (/status, /comment,
# /due-date, /bulk-status, /lookup, /viable-statuses) are endpoint-specific
# and are exposed via the domain helpers (client.orders, client.statuses).
RESOURCE_REGISTRY: dict[str, ResourceConfig] = {
    "orders": ResourceConfig(
        module="orders",
        get_one="get_order",
        get_all="list_orders",
    ),
    "statuses": ResourceConfig(
        module="statuses",
        get_all="get_statuses",
    ),
}
