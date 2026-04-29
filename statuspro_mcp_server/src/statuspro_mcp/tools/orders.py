"""MCP tools for StatusPro orders.

6 tools mapping to the ``/orders*`` endpoints. Mutations use a two-step confirm
pattern: call with ``confirm=False`` to see a preview, then ``confirm=True`` to
execute (the client host elicits explicit user approval via ``ctx.elicit``).

Three tools — ``list_orders``, ``get_order``, ``update_order_status`` — return
a Prefab UI for MCP-Apps clients (Claude Desktop) via ``make_tool_result`` and
``meta=UI_META``. Others return plain Pydantic/dict responses.

The ``GET /orders/lookup`` endpoint is intentionally not exposed: it is the
public, customer-verification path (requires ``number`` + ``email``) and adds
nothing for an authenticated MCP caller, who can already use ``list_orders``
(``search`` matches order number) or ``get_order`` (by id).
"""

from __future__ import annotations

import asyncio
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import Field

from statuspro_mcp.services import get_services
from statuspro_mcp.tools.prefab_ui import (
    build_order_detail_ui,
    build_orders_table_ui,
    build_status_change_preview_ui,
)
from statuspro_mcp.tools.schemas import (
    ConfirmationResult,
    HistoryEntry,
    OrderDetail,
    OrderList,
    OrderSummary,
    StatusChangePreview,
    StatusChangeResult,
    require_confirmation,
)
from statuspro_mcp.tools.tool_result_utils import (
    UI_META,
    format_md_table,
    iso_or_none,
    make_tool_result,
)
from statuspro_public_api_client.api.orders import (
    add_order_comment as add_order_comment_api,
    bulk_update_order_status as bulk_update_status,
    set_order_due_date,
    update_order_status as update_order_status_api,
)
from statuspro_public_api_client.models.add_order_comment_request import (
    AddOrderCommentRequest,
)
from statuspro_public_api_client.models.bulk_status_update_request import (
    BulkStatusUpdateRequest,
)
from statuspro_public_api_client.models.set_due_date_request import SetDueDateRequest
from statuspro_public_api_client.models.update_order_status_request import (
    UpdateOrderStatusRequest,
)
from statuspro_public_api_client.utils import is_success


def _to_summary(order: Any) -> OrderSummary:
    """Convert a domain Order or attrs model to an OrderSummary."""
    customer = getattr(order, "customer", None)
    status = getattr(order, "status", None)
    return OrderSummary(
        id=order.id,
        name=getattr(order, "name", None),
        order_number=getattr(order, "order_number", None),
        customer_name=getattr(customer, "name", None) if customer else None,
        customer_email=getattr(customer, "email", None) if customer else None,
        status_code=getattr(status, "code", None) if status else None,
        status_name=getattr(status, "name", None) if status else None,
        due_date=iso_or_none(getattr(order, "due_date", None)),
    )


def _history_entry(item: Any) -> HistoryEntry:
    """Convert an attrs ``HistoryItem`` into a UI-friendly ``HistoryEntry``."""
    status = getattr(item, "status", None)
    return HistoryEntry(
        event=getattr(item, "event", None) or None,
        status_code=getattr(status, "code", None) if status else None,
        status_name=getattr(status, "name", None) if status else None,
        comment=getattr(item, "comment", None) or None,
        comment_is_public=getattr(item, "comment_is_public", None),
        created_at=iso_or_none(getattr(item, "created_at", None)),
    )


def _to_detail(order: Any) -> OrderDetail:
    """Convert a domain Order into a full ``OrderDetail`` including history."""
    summary = _to_summary(order)
    history_items = getattr(order, "history", None) or []
    return OrderDetail(
        **summary.model_dump(),
        due_date_to=iso_or_none(getattr(order, "due_date_to", None)),
        history=[_history_entry(h) for h in history_items],
    )


async def _status_color_catalog(services: Any) -> dict[str, str | None]:
    """Fetch the status catalog once and return a ``{code: color}`` map.

    The ``Status`` model on an order has no color field — only
    ``StatusDefinition`` (returned by ``statuses.list()``) does. Callers that
    want to color-chip an order's status must look up by code against this
    catalog. The call adds one HTTP round-trip per tool invocation; the
    StatusPro catalog is small (O(20)) so the response is cheap.
    """
    statuses = await services.client.statuses.list()
    catalog: dict[str, str | None] = {}
    for s in statuses:
        code = getattr(s, "code", None)
        if code:
            catalog[code] = getattr(s, "color", None)
    return catalog


def register_tools(mcp: FastMCP) -> None:
    """Register order-related tools with the FastMCP server."""

    @mcp.tool(
        name="list_orders",
        description="List orders with optional filters. Auto-paginates when page is unset.",
        meta=UI_META,
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
    ) -> ToolResult:
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
        summaries = [_to_summary(o) for o in orders]
        summary_dicts = [s.model_dump() for s in summaries]
        filters: dict[str, Any] = {
            k: v
            for k, v in {
                "search": search,
                "status_code": status_code,
                "tags": tags,
                "tags_any": tags_any,
                "financial_status": financial_status,
                "fulfillment_status": fulfillment_status,
                "exclude_cancelled": exclude_cancelled,
                "due_date_from": due_date_from,
                "due_date_to": due_date_to,
            }.items()
            if v not in (None, [], "")
        }
        filters_line = (
            ", ".join(f"{k}={v}" for k, v in filters.items()) if filters else ""
        )

        response = OrderList(orders=summaries, total=len(summaries), filters=filters)
        app = build_orders_table_ui(
            summary_dicts,
            total=len(summaries),
            filters_line=filters_line or None,
        )
        orders_table = (
            format_md_table(
                headers=["Order #", "Customer", "Status", "Due"],
                rows=[
                    [
                        d.get("order_number") or "—",
                        d.get("customer_name") or "—",
                        d.get("status_name") or "—",
                        d.get("due_date") or "—",
                    ]
                    for d in summary_dicts
                ],
            )
            or "_(no orders)_"
        )

        return make_tool_result(
            response,
            template_name="orders_list",
            ui=app,
            total=len(summaries),
            filters_line=f"Filters: {filters_line}" if filters_line else "",
            orders_table=orders_table,
        )

    @mcp.tool(
        name="get_order",
        description="Fetch full details for one order by id (with history).",
        meta=UI_META,
    )
    async def get_order(
        context: Context,
        order_id: Annotated[int, Field(description="StatusPro order id")],
    ) -> ToolResult:
        services = get_services(context)
        order, catalog = await asyncio.gather(
            services.client.orders.get(order_id),
            _status_color_catalog(services),
        )

        detail = _to_detail(order)
        status_color = catalog.get(detail.status_code) if detail.status_code else None

        app = build_order_detail_ui(detail.model_dump(), status_color=status_color)

        history_table = (
            format_md_table(
                headers=["When", "Event", "Status", "Comment"],
                rows=[
                    [
                        h.created_at or "—",
                        h.event or "—",
                        h.status_name or "—",
                        h.comment or "—",
                    ]
                    for h in detail.history
                ],
            )
            or "_(no history)_"
        )
        due_date_range = f" — {detail.due_date_to}" if detail.due_date_to else ""

        return make_tool_result(
            detail,
            template_name="order_detail",
            ui=app,
            order_name=detail.name or detail.order_number or f"Order {detail.id}",
            order_number=detail.order_number or "—",
            customer_name=detail.customer_name or "—",
            customer_email=detail.customer_email or "—",
            status_name=detail.status_name or "—",
            status_code=detail.status_code or "—",
            due_date=detail.due_date or "—",
            due_date_range=due_date_range,
            history_table=history_table,
        )

    @mcp.tool(
        name="update_order_status",
        description=(
            "Change an order's status. Two-step confirm: call with confirm=false "
            "to preview; confirm=true runs the update."
        ),
        meta=UI_META,
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
    ) -> ToolResult:
        services = get_services(context)

        if not confirm:
            # Preview branch: fetch the order + catalog so the UI can show
            # the current status side-by-side with the proposed new one.
            # Single catalog fetch services both the color map and the
            # new-status-name lookup (``list_statuses`` is cached, but pulling
            # the local list avoids round-tripping the cache twice).
            order = await services.client.orders.get(order_id)
            statuses_list = await services.client.statuses.list()
            catalog: dict[str, str | None] = {}
            new_name: str | None = None
            for s in statuses_list:
                code = getattr(s, "code", None)
                if not code:
                    continue
                catalog[code] = getattr(s, "color", None)
                if code == status_code:
                    new_name = getattr(s, "name", None)

            current = getattr(order, "status", None)
            current_code = getattr(current, "code", None) if current else None
            current_name = getattr(current, "name", None) if current else None

            preview = StatusChangePreview(
                order_id=order_id,
                current_status_code=current_code,
                current_status_name=current_name,
                new_status_code=status_code,
                new_status_name=new_name,
                comment=comment,
                public=public,
                email_customer=email_customer,
                email_additional=email_additional,
            )
            app = build_status_change_preview_ui(
                preview.model_dump(),
                current_color=catalog.get(current_code) if current_code else None,
                new_color=catalog.get(status_code),
            )

            recipients_text = preview.recipients_text()
            comment_block = (
                f"**Comment** ({'public' if public else 'private'}): {comment}"
                if comment
                else "_No comment._"
            )

            return make_tool_result(
                preview,
                template_name="status_change_preview",
                ui=app,
                order_id=order_id,
                current_status_code=current_code or "—",
                current_status_name=current_name or "—",
                new_status_code=status_code,
                new_status_name=new_name or "—",
                comment_block=comment_block,
                recipients=recipients_text,
            )

        # Confirm branch: elicit approval, then execute. Renders the
        # (markdown-only) status_change_result template — this branch doesn't
        # emit a PrefabApp since the confirmation surface already lives in
        # the elicit prompt.
        result = await require_confirmation(
            context,
            f"Change order {order_id} status to {status_code}?",
        )
        if result is not ConfirmationResult.CONFIRMED:
            declined = StatusChangeResult(
                order_id=order_id,
                new_status_code=status_code,
                success=False,
                http_status=0,
                message=f"User {result.value}",
            )
            return make_tool_result(
                declined,
                template_name="status_change_result",
                order_id=order_id,
                new_status_code=status_code,
                outcome=result.value,
                http_status=0,
                message_line=f"\n- **Message:** User {result.value}",
            )

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
        outcome = StatusChangeResult(
            order_id=order_id,
            new_status_code=status_code,
            success=is_success(response),
            http_status=response.status_code,
        )
        return make_tool_result(
            outcome,
            template_name="status_change_result",
            order_id=order_id,
            new_status_code=status_code,
            outcome="applied" if outcome.success else "failed",
            http_status=response.status_code,
            message_line="",
        )

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
