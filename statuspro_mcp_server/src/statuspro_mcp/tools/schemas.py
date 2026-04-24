"""Shared schemas for StatusPro MCP tools.

This module contains Pydantic models and helpers that are shared across multiple
tool modules to ensure consistency and avoid duplication.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from fastmcp import Context
from pydantic import BaseModel, Field


class ConfirmationSchema(BaseModel):
    """Schema for user confirmation via elicitation.

    This schema is used with FastMCP's `ctx.elicit()` to request explicit
    user confirmation before executing destructive operations.

    Attributes:
        confirm: Boolean indicating whether the user confirms the action
    """

    confirm: bool = Field(..., description="Confirm the action (true to proceed)")


class ConfirmationResult(StrEnum):
    """Result of a confirmation request."""

    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    DECLINED = "declined"


async def require_confirmation(context: Context, message: str) -> ConfirmationResult:
    """Request user confirmation via elicitation.

    Encapsulates the common elicitation pattern used across all confirm-mode tools.

    Args:
        context: FastMCP context for elicitation
        message: Confirmation message to display

    Returns:
        ConfirmationResult indicating user's decision
    """
    elicit_result = await context.elicit(message, ConfirmationSchema)

    if elicit_result.action != "accept":
        return ConfirmationResult.CANCELLED

    if not elicit_result.data.confirm:
        return ConfirmationResult.DECLINED

    return ConfirmationResult.CONFIRMED


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
    """Full order record including the history timeline.

    Returned by ``get_order`` — extends ``OrderSummary`` with the fields that
    aren't useful in list views.
    """

    due_date_to: str | None = None
    history: list[HistoryEntry] = Field(default_factory=list)


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
    executing it."""

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


class StatusChangeResult(BaseModel):
    """Execution result returned when ``update_order_status`` is called with
    ``confirm=True``."""

    action: Literal["update_order_status"] = "update_order_status"
    confirmed: Literal[True] = True
    order_id: int
    new_status_code: str
    success: bool
    http_status: int
    message: str | None = None


__all__ = [
    "ConfirmationResult",
    "ConfirmationSchema",
    "HistoryEntry",
    "OrderDetail",
    "OrderList",
    "OrderSummary",
    "StatusChangePreview",
    "StatusChangeResult",
    "StatusEntry",
    "ViableStatusesResponse",
    "require_confirmation",
]
