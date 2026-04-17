"""MCP tools for StatusPro orders.

7 tools mapping to the ``/orders*`` endpoints. Mutations use a two-step confirm
pattern: call with ``confirm=False`` to see a preview, then ``confirm=True`` to
execute (the client host elicits explicit user approval via ``ctx.elicit``).
"""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from statuspro_mcp.services import get_services
from statuspro_mcp.tools.schemas import ConfirmationResult, require_confirmation


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


def _to_summary(order: Any) -> OrderSummary:
    """Convert a domain Order or attrs model to an OrderSummary."""
    customer = getattr(order, "customer", None)
    status = getattr(order, "status", None)
    due_date = getattr(order, "due_date", None)
    return OrderSummary(
        id=order.id,
        name=getattr(order, "name", None),
        order_number=getattr(order, "order_number", None),
        customer_name=getattr(customer, "name", None) if customer else None,
        customer_email=getattr(customer, "email", None) if customer else None,
        status_code=getattr(status, "code", None) if status else None,
        status_name=getattr(status, "name", None) if status else None,
        due_date=str(due_date) if due_date else None,
    )


def register_tools(mcp: FastMCP) -> None:
    """Register order-related tools with the FastMCP server."""

    @mcp.tool(
        name="list_orders",
        description="List orders with optional filters. Auto-paginates when page is unset.",
    )
    async def list_orders(
        context: Context,
        search: Annotated[str | None, Field(description="Full-text search")] = None,
        status_code: Annotated[
            str | None, Field(description="Filter to one status code")
        ] = None,
        tags: Annotated[
            list[str] | None, Field(description="Must match all tags")
        ] = None,
        tags_any: Annotated[
            list[str] | None, Field(description="Match any of these tags")
        ] = None,
        financial_status: list[str] | None = None,
        fulfillment_status: list[str] | None = None,
        exclude_cancelled: Annotated[
            bool | None, Field(description="Exclude cancelled orders")
        ] = None,
        due_date_from: Annotated[
            str | None, Field(description="ISO 8601 lower bound on due_date")
        ] = None,
        due_date_to: Annotated[
            str | None, Field(description="ISO 8601 upper bound on due_date")
        ] = None,
        page: Annotated[
            int | None, Field(description="Specific page; disables auto-pagination")
        ] = None,
        per_page: Annotated[
            int | None, Field(description="Items per page (max 100)")
        ] = None,
    ) -> list[OrderSummary]:
        services = get_services(context)
        orders = await services.client.orders.list(
            search=search,
            status_code=status_code,
            tags=tags,
            tags_any=tags_any,
            financial_status=financial_status,
            fulfillment_status=fulfillment_status,
            exclude_cancelled=exclude_cancelled,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            page=page,
            per_page=per_page,
        )
        return [_to_summary(o) for o in orders]

    @mcp.tool(
        name="get_order",
        description="Fetch full details for one order by id (with history).",
    )
    async def get_order(
        context: Context,
        order_id: Annotated[int, Field(description="StatusPro order id")],
    ) -> OrderSummary:
        services = get_services(context)
        order = await services.client.orders.get(order_id)
        return _to_summary(order)

    @mcp.tool(
        name="lookup_order",
        description="Look up an order by order number + customer email.",
    )
    async def lookup_order(
        context: Context,
        number: Annotated[
            str, Field(description="Order number, e.g. '1188' or '#1188'")
        ],
        email: Annotated[str, Field(description="Customer email address")],
    ) -> OrderSummary:
        services = get_services(context)
        order = await services.client.orders.lookup(number=number, email=email)
        return _to_summary(order)

    @mcp.tool(
        name="update_order_status",
        description=(
            "Change an order's status. Two-step confirm: call with confirm=false "
            "to preview; confirm=true runs the update."
        ),
    )
    async def update_order_status(
        context: Context,
        order_id: int,
        status_code: Annotated[
            str, Field(description="8-char status code, e.g. 'st000002'")
        ],
        comment: Annotated[
            str | None, Field(description="Optional history comment")
        ] = None,
        public: Annotated[
            bool, Field(description="Make the comment visible to the customer")
        ] = False,
        email_customer: Annotated[
            bool, Field(description="Send the customer a status email")
        ] = True,
        email_additional: Annotated[
            bool, Field(description="Send additional notification emails")
        ] = True,
        confirm: Annotated[
            bool, Field(description="Must be true to apply the change")
        ] = False,
    ) -> dict[str, Any]:
        services = get_services(context)

        preview = {
            "action": "update_order_status",
            "order_id": order_id,
            "status_code": status_code,
            "comment": comment,
            "public": public,
            "email_customer": email_customer,
            "email_additional": email_additional,
        }

        if not confirm:
            return {"preview": preview, "confirmed": False}

        result = await require_confirmation(
            context,
            f"Change order {order_id} status to {status_code}?",
        )
        if result is not ConfirmationResult.CONFIRMED:
            return {"preview": preview, "confirmed": False, "result": result.value}

        from statuspro_public_api_client.api.orders import (
            update_order_status as update_order_status_api,
        )
        from statuspro_public_api_client.models.update_order_status_request import (
            UpdateOrderStatusRequest,
        )
        from statuspro_public_api_client.utils import is_success

        body = UpdateOrderStatusRequest(
            status_code=status_code,
            comment=comment,
            public=public,
            email_customer=email_customer,
            email_additional=email_additional,
        )
        response = await update_order_status_api.asyncio_detailed(
            client=services.client, order=order_id, body=body
        )
        return {
            "confirmed": True,
            "success": is_success(response),
            "status_code": response.status_code,
        }

    @mcp.tool(
        name="add_order_comment",
        description="Add a history comment to an order (5/min rate limit). Two-step confirm.",
    )
    async def add_order_comment(
        context: Context,
        order_id: int,
        comment: Annotated[str, Field(description="Comment body")],
        public: Annotated[bool, Field(description="Visible to the customer")] = False,
        confirm: bool = False,
    ) -> dict[str, Any]:
        services = get_services(context)

        preview = {
            "action": "add_order_comment",
            "order_id": order_id,
            "comment": comment,
            "public": public,
        }
        if not confirm:
            return {"preview": preview, "confirmed": False}

        result = await require_confirmation(
            context, f"Add comment to order {order_id}?"
        )
        if result is not ConfirmationResult.CONFIRMED:
            return {"preview": preview, "confirmed": False, "result": result.value}

        from statuspro_public_api_client.api.orders import (
            add_order_comment as add_order_comment_api,
        )
        from statuspro_public_api_client.models.add_order_comment_request import (
            AddOrderCommentRequest,
        )
        from statuspro_public_api_client.utils import is_success

        body = AddOrderCommentRequest(comment=comment, public=public)
        response = await add_order_comment_api.asyncio_detailed(
            client=services.client, order=order_id, body=body
        )
        return {
            "confirmed": True,
            "success": is_success(response),
            "status_code": response.status_code,
        }

    @mcp.tool(
        name="update_order_due_date",
        description="Update an order's due date. Two-step confirm.",
    )
    async def update_order_due_date(
        context: Context,
        order_id: int,
        due_date: Annotated[str, Field(description="ISO 8601 date, e.g. '2026-03-15'")],
        due_date_to: Annotated[
            str | None, Field(description="Optional end of the range")
        ] = None,
        confirm: bool = False,
    ) -> dict[str, Any]:
        services = get_services(context)

        preview = {
            "action": "update_order_due_date",
            "order_id": order_id,
            "due_date": due_date,
            "due_date_to": due_date_to,
        }
        if not confirm:
            return {"preview": preview, "confirmed": False}

        result = await require_confirmation(
            context, f"Set due_date={due_date} for order {order_id}?"
        )
        if result is not ConfirmationResult.CONFIRMED:
            return {"preview": preview, "confirmed": False, "result": result.value}

        from statuspro_public_api_client.api.orders import (
            set_order_due_date,
        )
        from statuspro_public_api_client.models.set_due_date_request import (
            SetDueDateRequest,
        )
        from statuspro_public_api_client.utils import is_success

        body_kwargs: dict[str, Any] = {"due_date": due_date}
        if due_date_to is not None:
            body_kwargs["due_date_to"] = due_date_to
        body = SetDueDateRequest(**body_kwargs)
        response = await set_order_due_date.asyncio_detailed(
            client=services.client, order=order_id, body=body
        )
        return {
            "confirmed": True,
            "success": is_success(response),
            "status_code": response.status_code,
        }

    @mcp.tool(
        name="bulk_update_order_status",
        description=(
            "Update status for up to 50 orders in one call (5/min rate limit). "
            "Returns 202 Accepted; updates are queued asynchronously."
        ),
    )
    async def bulk_update_order_status(
        context: Context,
        order_ids: Annotated[
            list[int],
            Field(description="Order ids (1-50 items)", min_length=1, max_length=50),
        ],
        status_code: str,
        comment: str | None = None,
        public: bool = False,
        email_customer: bool = True,
        email_additional: bool = True,
        confirm: bool = False,
    ) -> dict[str, Any]:
        services = get_services(context)

        preview = {
            "action": "bulk_update_order_status",
            "order_ids": order_ids,
            "order_count": len(order_ids),
            "status_code": status_code,
            "comment": comment,
            "public": public,
            "email_customer": email_customer,
            "email_additional": email_additional,
        }
        if not confirm:
            return {"preview": preview, "confirmed": False}

        result = await require_confirmation(
            context,
            f"Bulk-update {len(order_ids)} orders to status {status_code}?",
        )
        if result is not ConfirmationResult.CONFIRMED:
            return {"preview": preview, "confirmed": False, "result": result.value}

        from statuspro_public_api_client.api.orders import (
            bulk_update_order_status as bulk_update_status,
        )
        from statuspro_public_api_client.models.bulk_status_update_request import (
            BulkStatusUpdateRequest,
        )
        from statuspro_public_api_client.utils import is_success

        body = BulkStatusUpdateRequest(
            order_ids=order_ids,
            status_code=status_code,
            comment=comment,
            public=public,
            email_customer=email_customer,
            email_additional=email_additional,
        )
        response = await bulk_update_status.asyncio_detailed(
            client=services.client, body=body
        )
        return {
            "confirmed": True,
            "success": is_success(response),
            "status_code": response.status_code,
            "note": "Bulk updates are queued and processed asynchronously.",
        }
