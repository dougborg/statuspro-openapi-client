"""Prefab UI builders for the StatusPro MCP tool responses.

Each ``build_*_ui(...)`` returns a ``PrefabApp`` suitable for passing as the
``ui=`` kwarg of ``make_tool_result``. That in turn sets ``structured_content``
to the PrefabApp instance; FastMCP's ``ToolResult.__init__`` detects it via
isinstance and converts to the wire envelope via ``_prefab_to_json``. Combined
with ``meta={"ui": True}`` on the tool registration, this causes MCP-Apps
capable clients (Claude Desktop) to render the Prefab UI. Non-Prefab clients
fall back to the markdown content.

The shape of the four UIs matches the "find → view → decide → mutate" loop:

- ``build_orders_table_ui`` — sortable table; row click drills into ``get_order``
- ``build_order_detail_ui`` — detail Card with history timeline; footer button
  fires ``get_viable_statuses``
- ``build_viable_statuses_ui`` — color-coded status buttons; click sends a
  follow-up message asking Claude to ``update_order_status``
- ``build_status_change_preview_ui`` — preview Card for the mutation with a
  Confirm button that sends the ``confirm=true`` follow-up
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from prefab_ui.actions.mcp import CallTool, SendMessage
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    H3,
    Badge,
    Button,
    Card,
    CardContent,
    CardFooter,
    CardHeader,
    CardTitle,
    Column,
    DataTable,
    DataTableColumn,
    Metric,
    Muted,
    Row,
    Separator,
    Text,
)
from prefab_ui.components.control_flow import ForEach

from statuspro_mcp.tools.schemas import StatusChangePreview

BadgeVariant = Literal[
    "default",
    "secondary",
    "destructive",
    "outline",
    "ghost",
    "success",
    "warning",
    "info",
]


# Tailwind-style color names → nearest Prefab Badge variant. StatusPro's
# ``Status.color`` field is free-form (can be a named color like "green" or a
# hex code like "#F59E0B"), but Prefab's Badge only accepts a fixed set of
# semantic variants. Mapping is lossy but captures intent (status color is
# usually a nice-to-have; the status name is what matters).
_COLOR_TO_VARIANT: dict[str, BadgeVariant] = {
    "green": "success",
    "emerald": "success",
    "lime": "success",
    "red": "destructive",
    "rose": "destructive",
    "orange": "warning",
    "amber": "warning",
    "yellow": "warning",
    "blue": "info",
    "sky": "info",
    "cyan": "info",
    "gray": "secondary",
    "slate": "secondary",
    "zinc": "secondary",
    "neutral": "secondary",
    "stone": "secondary",
}


def _color_to_variant(color: str | None) -> BadgeVariant:
    """Map a StatusPro ``color`` value to the closest Prefab Badge variant.

    Accepts named colors (``"green"``, ``"pink"``) or hex codes
    (``"#F59E0B"``). Unknown values fall back to ``outline``.
    """
    if not color:
        return "outline"
    lowered = color.lower().lstrip("#")
    if lowered in _COLOR_TO_VARIANT:
        return _COLOR_TO_VARIANT[lowered]
    return "outline"


def _status_chip(code: str | None, name: str | None, color: str | None) -> None:
    """Render a Badge for a status inside the current Prefab context.

    Uses the name if present (falls back to code). Must be called inside a
    Prefab context manager (e.g. inside a ``Row``) — returns ``None`` because
    Prefab components register themselves via context.
    """
    label = name or code or "unknown"
    Badge(label=label, variant=_color_to_variant(color))


def _is_overdue(due_date: str | None) -> bool:
    """Return True if ``due_date`` (ISO 8601) is before now.

    Silently returns False if the date is missing or unparseable — the UI
    should show whatever raw value is there rather than error out.
    """
    if not due_date:
        return False
    try:
        dt = datetime.fromisoformat(due_date)
    except (TypeError, ValueError):
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt < datetime.now(UTC)


def build_orders_table_ui(
    orders: list[dict[str, Any]],
    total: int,
    filters_line: str | None = None,
) -> PrefabApp:
    """Build an interactive table of orders.

    Columns: order number, customer, status, due date. Row click fires
    ``CallTool("get_order", order_id=...)`` so Claude Desktop can navigate
    from the list into a detail view without a round-trip through the model.
    """
    with (
        PrefabApp(state={"orders": orders, "total": total}, css_class="p-4") as app,
        Column(gap=4),
    ):
        with Row(gap=2):
            H3(content="Orders")
            Badge(label=f"{total} results", variant="secondary")
            if filters_line:
                Badge(label=filters_line, variant="outline")

        DataTable(
            columns=[
                DataTableColumn(key="order_number", header="Order #", sortable=True),
                DataTableColumn(key="customer_name", header="Customer", sortable=True),
                DataTableColumn(key="status_name", header="Status", sortable=True),
                DataTableColumn(key="due_date", header="Due", sortable=True),
            ],
            rows="orders",
            search=True,
            paginated=True,
            pageSize=25,
            onRowClick=CallTool(
                "get_order",
                arguments={"order_id": "{{ id }}"},
            ),
        )
    return app


def build_order_detail_ui(
    order: dict[str, Any],
    *,
    status_color: str | None = None,
) -> PrefabApp:
    """Build a detail Card for a single order with history timeline.

    Footer button "Change status" fires ``get_viable_statuses`` for the order
    so the user can pick a valid next transition.
    """
    order_id = order.get("id")
    order_name = order.get("name") or order.get("order_number") or f"Order {order_id}"
    customer_display = order.get("customer_name") or "—"
    due_date = order.get("due_date") or "—"
    overdue = _is_overdue(order.get("due_date"))

    with PrefabApp(state={"order": order}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=order_name)
            if order.get("order_number"):
                Badge(label=f"#{order['order_number']}", variant="outline")
            _status_chip(
                order.get("status_code"), order.get("status_name"), status_color
            )
            if overdue:
                Badge(label="Overdue", variant="destructive")

        with CardContent(), Column(gap=3):
            with Row(gap=4):
                Metric(label="Customer", value=customer_display)
                Metric(label="Due date", value=str(due_date))
                Metric(label="History", value=str(len(order.get("history") or [])))

            if order.get("customer_email"):
                Text(content=f"Email: {order['customer_email']}")

            history = order.get("history") or []
            if history:
                Separator()
                Muted(content="History")
                with ForEach("order.history"), Row(gap=2):
                    Text(content="{{ created_at }}")
                    Text(content="{{ event }}")
                    Text(content="{{ status_name }}")
                    Text(content="{{ comment }}")
            else:
                Separator()
                Muted(content="No history entries.")

        with CardFooter(), Row(gap=2):
            Button(
                label="Change status",
                variant="default",
                on_click=CallTool(
                    "get_viable_statuses",
                    arguments={"order_id": order_id},
                ),
            )
            Button(
                label="Add comment",
                variant="outline",
                on_click=SendMessage(f"Add a comment to order {order_id}"),
            )
    return app


def build_viable_statuses_ui(
    order_id: int,
    statuses: list[dict[str, Any]],
) -> PrefabApp:
    """Build a Row of color-coded status buttons.

    Click sends a chat message asking Claude to invoke
    ``update_order_status(order_id, status_code, confirm=false)`` — which
    will then render the status-change preview UI.
    """
    with (
        PrefabApp(
            state={"order_id": order_id, "statuses": statuses}, css_class="p-4"
        ) as app,
        Card(),
    ):
        with CardHeader():
            CardTitle(content=f"Choose a new status for order {order_id}")
            Muted(content="Shown in order of valid transitions")

        with CardContent(), Row(gap=2):
            if not statuses:
                Muted(content="No valid transitions from the current status.")
            for status in statuses:
                code = status.get("code") or ""
                name = status.get("name") or code
                Button(
                    label=f"{name} ({code})",
                    variant=_color_to_variant(status.get("color")),
                    on_click=SendMessage(
                        f"Update order {order_id} to status {code} "
                        "(preview only, confirm=false)"
                    ),
                )
    return app


def build_status_change_preview_ui(
    preview: dict[str, Any],
    *,
    current_color: str | None = None,
    new_color: str | None = None,
) -> PrefabApp:
    """Build a preview Card for an impending status change.

    Shows current → new side by side, the optional comment (with visibility
    badge), and a Confirm button that sends the ``confirm=true`` follow-up.

    When ``preview["valid"]`` is ``False`` (the requested ``new_status_code``
    is not a viable transition from the current state), the Confirm button is
    replaced with a destructive warning surfacing the list of viable codes
    so the agent can self-correct.
    """
    order_id = preview.get("order_id")
    comment = preview.get("comment")
    public = bool(preview.get("public"))
    valid = bool(preview.get("valid", True))
    viable_codes = preview.get("viable_status_codes") or []
    # Re-hydrate as the schema so its ``recipients_text`` is the single source
    # of truth for both the UI and the markdown fallback rendered by orders.py.
    recipients_text = StatusChangePreview.model_validate(preview).recipients_text()

    with PrefabApp(state={"preview": preview}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"Preview: order {order_id} status change")
            Badge(
                label="INVALID TRANSITION" if not valid else "PREVIEW",
                variant="destructive" if not valid else "secondary",
            )

        with CardContent(), Column(gap=3):
            with Row(gap=3):
                _status_chip(
                    preview.get("current_status_code"),
                    preview.get("current_status_name"),
                    current_color,
                )
                Text(content="→")
                _status_chip(
                    preview.get("new_status_code"),
                    preview.get("new_status_name"),
                    new_color,
                )

            if not valid:
                Separator()
                Text(
                    content=(
                        f"⚠ Not a viable transition from "
                        f"`{preview.get('current_status_code') or '—'}`. "
                        f"Viable codes: "
                        + (
                            ", ".join(f"`{c}`" for c in viable_codes)
                            if viable_codes
                            else "_(none)_"
                        )
                    ),
                )

            if comment:
                Separator()
                with Row(gap=2):
                    Muted(content="Comment:")
                    Text(content=comment)
                    Badge(
                        label="public" if public else "private",
                        variant="info" if public else "outline",
                    )

            Separator()
            Metric(label="Emails to", value=recipients_text)

        with CardFooter(), Row(gap=2):
            if valid:
                Button(
                    label="Confirm change",
                    variant="default",
                    on_click=SendMessage(
                        f"Update order {order_id} to status "
                        f"{preview.get('new_status_code')} with confirm=true"
                    ),
                )
            else:
                Button(
                    label="See viable transitions",
                    variant="default",
                    on_click=CallTool(
                        "get_viable_statuses",
                        arguments={"order_id": order_id},
                    ),
                )
            Button(
                label="Cancel",
                variant="outline",
                on_click=SendMessage("Cancel the status change"),
            )
    return app


__all__ = [
    "build_order_detail_ui",
    "build_orders_table_ui",
    "build_status_change_preview_ui",
    "build_viable_statuses_ui",
]
