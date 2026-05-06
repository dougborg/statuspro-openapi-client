"""Shared schemas for StatusPro MCP tools.

This module contains Pydantic models that are shared across multiple tool
modules to ensure consistency and avoid duplication.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class OrderSummary(BaseModel):
    """Human-readable subset of fields from an order, for tool responses."""

    id: int
    name: str | None = None
    order_number: str | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    status_code: str | None = None
    status_name: str | None = None
    due_date: str | None = None


class HistoryEntry(BaseModel):
    """One entry in an order's history timeline.

    Covers two cases: status transitions (``status_code``/``status_name`` set) and
    free-form comments (``comment`` set, ``status_code`` usually None).
    """

    event: str | None = None
    status_code: str | None = None
    status_name: str | None = None
    comment: str | None = None
    comment_is_public: bool | None = None
    created_at: str | None = None


class OrderDetail(OrderSummary):
    """Full order record including the (possibly truncated) history timeline.

    Returned by ``get_order`` — extends ``OrderSummary`` with the fields that
    aren't useful in list views. The ``history`` array is truncated to the
    most recent ``history_limit`` entries when the order has many; callers
    should check ``history_truncated`` and use ``get_order_history`` to page
    through older entries when set.
    """

    due_date_to: str | None = None
    history: list[HistoryEntry] = Field(default_factory=list)
    history_truncated: bool = Field(
        default=False,
        description="True when older history entries were omitted; "
        "use get_order_history to page through them.",
    )
    history_total_count: int = Field(
        default=0,
        description="Total number of history entries on the order; "
        "len(history) <= history_total_count.",
    )


class OrderHistoryPage(BaseModel):
    """One page of history entries returned by ``get_order_history``."""

    order_id: int
    page: int
    per_page: int
    total: int
    total_pages: int
    entries: list[HistoryEntry]


class BatchOrderResult(BaseModel):
    """One entry in a batch order-fetch response.

    Either ``order`` is set (the lookup succeeded) or ``error`` is set
    (the lookup failed — order id not found, ambiguous match, etc.).
    Callers should iterate the batch and partition by which field is set.
    """

    order_id: int | None = Field(
        default=None,
        description="The order id if known. May be None for lookup-by-number where no id was resolved.",
    )
    requested: str = Field(
        ...,
        description=(
            "What the caller passed in (id as a string, or order_number). "
            "Echoed back so callers can join results to their input list."
        ),
    )
    order: OrderSummary | None = None
    error: str | None = Field(
        default=None,
        description="Set when the lookup failed; describes why (not_found, ambiguous, etc.).",
    )


class BatchOrderResponse(BaseModel):
    """Wrapper for batch order-fetch responses, typed for make_tool_result.

    Failures in a batch can be due to several causes (404 not-found,
    ambiguous match in `lookup_orders_batch`, transport errors, rate-limit
    exhaustion). The response splits these into ``not_found_count`` (only
    explicit not-found / no-exact-match cases) and ``error_count`` (all
    other failures, like transport / ambiguous). A row's ``error`` field
    starts with one of: ``not_found``, ``ambiguous``, or the exception
    class name for transport-level failures.
    """

    requested_count: int
    found_count: int = Field(..., description="Rows where ``order`` is set.")
    not_found_count: int = Field(
        0,
        description="Rows whose error starts with ``not_found`` (no exact match).",
    )
    error_count: int = Field(
        0,
        description=(
            "Rows whose error is anything OTHER than not_found — ambiguous "
            "matches, transport errors, etc. Sum of (found + not_found + "
            "error) equals ``requested_count``."
        ),
    )
    results: list[BatchOrderResult]


class StatusCount(BaseModel):
    """One row in the active-orders summary."""

    status_code: str | None = None
    status_name: str | None = None
    count: int


class ActiveOrdersSummary(BaseModel):
    """One-shot summary across all active (non-cancelled) orders.

    Built client-side by issuing one ``list_orders`` call per status code
    plus one each for the financial-status and fulfillment-status enums
    that are populated. The response is small but the underlying calls
    are not free — count this as 8-12 read requests internally.
    """

    total_active: int = Field(..., description="Total non-cancelled orders.")
    by_status: list[StatusCount]
    by_financial_status: dict[str, int] = Field(
        default_factory=dict,
        description="financial_status enum value -> count of matching orders.",
    )
    by_fulfillment_status: dict[str, int] = Field(
        default_factory=dict,
        description="fulfillment_status enum value -> count of matching orders.",
    )
    no_status_count: int = Field(
        0,
        description="Active orders with no workflow status assigned (newly created, unstaged).",
    )


class OrderList(BaseModel):
    """Wrapper for list_orders responses, typed for make_tool_result."""

    orders: list[OrderSummary]
    total: int
    filters: dict[str, Any] = Field(default_factory=dict)


class StatusEntry(BaseModel):
    """Human-readable status record for tool responses."""

    code: str = Field(..., description="8-char status code, e.g. 'st000002'")
    name: str | None = None
    description: str | None = None
    color: str | None = None


class ViableStatusesResponse(BaseModel):
    """Wrapper for get_viable_statuses responses, typed for make_tool_result."""

    order_id: int
    statuses: list[StatusEntry]


class StatusChangePreview(BaseModel):
    """Preview payload returned when ``update_order_status`` is called with
    ``confirm=False``. Describes the change that *would* happen, without
    executing it.

    The preview branch self-validates the requested transition against
    ``GET /orders/{id}/viable-statuses``. When ``valid`` is ``False``, the
    Confirm button on the Prefab UI is replaced with a warning surfacing
    the list of ``viable_status_codes`` so the agent can self-correct
    without a separate ``get_viable_statuses`` round-trip.
    """

    action: Literal["update_order_status"] = "update_order_status"
    confirmed: Literal[False] = False
    order_id: int
    current_status_code: str | None = None
    current_status_name: str | None = None
    new_status_code: str
    new_status_name: str | None = None
    comment: str | None = None
    public: bool
    email_customer: bool
    email_additional: bool
    valid: bool = Field(
        default=True,
        description=(
            "True when new_status_code is a viable transition from the "
            "current state (per GET /orders/{id}/viable-statuses). When "
            "False, the Prefab UI hides the Confirm button and surfaces "
            "viable_status_codes; the agent can still call the tool with "
            "confirm=True directly, in which case the API will likely 422."
        ),
    )
    viable_status_codes: list[str] = Field(
        default_factory=list,
        description="Status codes that ARE viable transitions, for self-correction.",
    )

    def recipients_text(self) -> str:
        """Human-readable list of who will receive notification emails."""
        recipients: list[str] = []
        if self.email_customer:
            recipients.append("customer")
        if self.email_additional:
            recipients.append("additional contacts")
        return ", ".join(recipients) or "nobody"


class StatusChangeResult(BaseModel):
    """Execution result for ``update_order_status`` after the confirm step.

    ``confirmed`` is always ``True`` here — the model is only constructed
    after the API call has been issued. The host gates user-confirmation via
    the ``destructiveHint`` annotation; there's no in-band declined path
    that produces this shape.
    """

    action: Literal["update_order_status"] = "update_order_status"
    confirmed: Literal[True] = True
    order_id: int
    new_status_code: str
    success: bool
    http_status: int


class CommentResult(BaseModel):
    """Execution result for ``add_order_comment``. See ``StatusChangeResult``
    for ``confirmed`` semantics."""

    action: Literal["add_order_comment"] = "add_order_comment"
    confirmed: Literal[True] = True
    order_id: int
    success: bool
    http_status: int


class DueDateChangeResult(BaseModel):
    """Execution result for ``update_order_due_date``. See
    ``StatusChangeResult`` for ``confirmed`` semantics."""

    action: Literal["update_order_due_date"] = "update_order_due_date"
    confirmed: Literal[True] = True
    order_id: int
    new_due_date: str
    new_due_date_to: str | None = None
    success: bool
    http_status: int


class BulkStatusChangeResult(BaseModel):
    """Execution result for ``bulk_update_order_status``. See
    ``StatusChangeResult`` for ``confirmed`` semantics."""

    action: Literal["bulk_update_order_status"] = "bulk_update_order_status"
    confirmed: Literal[True] = True
    order_count: int
    target_status_code: str
    success: bool
    http_status: int
    note: str | None = None


class CommentPreview(BaseModel):
    """Preview payload for ``add_order_comment`` with ``confirm=False``.

    Includes the current ``order_summary`` so the preview UI can show
    "you are about to comment on order #1188 (In Production)" rather than
    just an opaque order id.
    """

    action: Literal["add_order_comment"] = "add_order_comment"
    confirmed: Literal[False] = False
    order_id: int
    order_summary: OrderSummary
    comment: str
    public: bool


class DueDateChangePreview(BaseModel):
    """Preview payload for ``update_order_due_date`` with ``confirm=False``.

    Surfaces the current vs. proposed due_date side-by-side via the order
    summary plus the proposed new values.
    """

    action: Literal["update_order_due_date"] = "update_order_due_date"
    confirmed: Literal[False] = False
    order_id: int
    order_summary: OrderSummary
    current_due_date: str | None = None
    current_due_date_to: str | None = None
    new_due_date: str
    new_due_date_to: str | None = None


class BulkStatusChangePreview(BaseModel):
    """Preview payload for ``bulk_update_order_status`` with ``confirm=False``.

    Lists every order id that will be affected (capped at 50 by the API),
    the target status code/name, and notification flags. We don't expand
    each order_id to a full summary — that would be N round-trips today;
    once the ``id[]`` batch fetch lands the UI can be enriched.
    """

    action: Literal["bulk_update_order_status"] = "bulk_update_order_status"
    confirmed: Literal[False] = False
    order_ids: list[int]
    order_count: int
    target_status_code: str
    target_status_name: str | None = None
    comment: str | None = None
    public: bool
    email_customer: bool
    email_additional: bool

    def recipients_text(self) -> str:
        """Human-readable list of who will receive notification emails.

        Mirrors ``StatusChangePreview.recipients_text`` so the UI builders
        can share rendering logic.
        """
        recipients: list[str] = []
        if self.email_customer:
            recipients.append("customer")
        if self.email_additional:
            recipients.append("additional contacts")
        return ", ".join(recipients) or "nobody"


__all__ = [
    "ActiveOrdersSummary",
    "BatchOrderResponse",
    "BatchOrderResult",
    "BulkStatusChangePreview",
    "BulkStatusChangeResult",
    "CommentPreview",
    "CommentResult",
    "DueDateChangePreview",
    "DueDateChangeResult",
    "HistoryEntry",
    "OrderDetail",
    "OrderHistoryPage",
    "OrderList",
    "OrderSummary",
    "StatusChangePreview",
    "StatusChangeResult",
    "StatusCount",
    "StatusEntry",
    "ViableStatusesResponse",
]
