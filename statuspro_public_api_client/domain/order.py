"""Domain models for StatusPro orders.

Hand-written Pydantic models for business logic, separate from the generated
attrs API models. Shapes mirror the OpenAPI ``Customer``, ``Status``,
``OrderListItem``, ``OrderResponse``, and ``OrderListMeta`` schemas.
"""

from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class _Frozen(BaseModel):
    """Immutable Pydantic base used for nested types that don't carry timestamps."""

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        extra="ignore",
    )


class Customer(_Frozen):
    """Customer details attached to an order."""

    name: str | None = None
    email: str | None = None
    locale: str | None = None


class OrderStatus(_Frozen):
    """The status currently set on an order (nested ``Status`` schema).

    Distinct from :class:`Status`, which is a top-level status definition
    returned by ``/statuses`` and includes ``color`` instead of transition
    metadata.
    """

    is_set: bool | None = None
    code: str | None = Field(None, description="8-char status code, e.g. 'st000002'")
    name: str | None = None
    public_name: str | None = None
    description: str | None = None
    public: bool | None = None
    set_at: AwareDatetime | None = None
    auto_change_at: AwareDatetime | None = None


class HistoryEntry(_Frozen):
    """One entry in an order's history timeline.

    Returned only by ``/orders/{id}`` (single-order detail), never on list
    pages. Covers status transitions (``status`` is set, ``comment`` may be
    set or empty) and free-form comments (``comment`` set, ``status`` usually
    not). The ``mail_log`` audit field on the underlying API is intentionally
    omitted — operational tooling rarely needs it and it's verbose.
    """

    event: str | None = None
    status: OrderStatus | None = None
    comment: str | None = None
    comment_is_public: bool | None = None
    created_at: AwareDatetime | None = None


class Order(_Frozen):
    """An order as returned by ``/orders`` list pages or ``/orders/{id}``."""

    id: int
    name: str | None = Field(None, description="Display name, e.g. '#1188'")
    order_number: str | None = None
    customer: Customer | None = None
    status: OrderStatus | None = None
    due_date: AwareDatetime | None = None
    due_date_to: AwareDatetime | None = None
    history_count: int | None = Field(
        None,
        description="Number of history entries; only present on list responses",
    )
    history: list[HistoryEntry] | None = Field(
        None,
        description="Full history timeline; only present on single-order detail responses",
    )


class PageMeta(_Frozen):
    """Pagination envelope returned alongside list endpoints.

    Matches the StatusPro ``OrderListMeta`` schema. ``current_page`` and
    ``last_page`` are used by the transport layer to auto-walk pages.
    """

    current_page: int
    last_page: int
    per_page: int
    total: int
    from_: int | None = Field(None, alias="from")
    to: int | None = None

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        extra="ignore",
        populate_by_name=True,
    )


__all__ = ["Customer", "HistoryEntry", "Order", "OrderStatus", "PageMeta"]
