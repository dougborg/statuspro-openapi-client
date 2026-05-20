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

from prefab_ui.actions import Action, SetState, ShowToast
from prefab_ui.actions.mcp import CallTool, SendMessage, UpdateContext
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    H3,
    Alert,
    AlertDescription,
    AlertTitle,
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
from prefab_ui.components.control_flow import Elif, Else, ForEach, If
from prefab_ui.rx import ERROR, RESULT, Rx

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


# Initial state seeded into every preview card. The Confirm/Cancel action
# chains flip these via SetState; the footer's If/Elif blocks bind to them to
# morph the button row through Preview → Pending… → Applied / Failed /
# Cancelled. Seeding them up-front gives the iframe something to bind to
# before the first click — otherwise the first `Rx("pending")` read would
# resolve to undefined and the disable guard wouldn't fire.
_PREVIEW_STATE_INIT: dict[str, Any] = {
    "pending": False,
    "cancelled": False,
    "applied": False,
    "error": None,
}


def _build_confirm_action(
    tool: str,
    arguments: dict[str, Any],
) -> list[Action]:
    """Build the Confirm-button click chain for a preview card.

    The chain is ``[SetState(pending, True), CallTool(...)]``. Setting
    ``pending=True`` synchronously before the call fires is the double-click
    guard: the button also binds ``disabled=Rx("pending") | Rx("cancelled")``
    as belt-and-suspenders, but the SetState happens *before* the network
    call so a second click can never sneak through while the iframe's
    re-render is in flight.

    ``on_success`` clears ``pending`` and flips ``applied=True`` so the
    button row morphs in-place to a terminal "Applied" pill — the user gets
    visible confirmation that their click landed. ``UpdateContext`` pushes
    the structured response into the agent's model context so the next turn
    sees the apply result without an extra round-trip.

    ``on_error`` clears ``pending`` and flips ``error`` to the failure
    reason so the footer can swap to a Retry button + inline error text.

    ``error`` is also cleared synchronously at the start of the chain so a
    Retry click hides the prior failure Alert immediately — without this,
    a successful retry would leave the stale Alert visible alongside the
    Applied pill.
    """
    return [
        SetState("pending", True),
        SetState("error", None),
        CallTool(
            tool=tool,
            arguments=arguments,
            on_success=[
                SetState("pending", False),
                SetState("applied", True),
                UpdateContext(content=RESULT),
            ],
            on_error=[
                SetState("pending", False),
                SetState("error", ERROR),
                # ShowToast.__init__ types ``message: str`` despite the field
                # being ``RxStr``; coerce so pyright accepts the Rx reference.
                ShowToast(message=str(ERROR), variant="error"),
                UpdateContext(content=f"Apply failed: {ERROR}"),
            ],
        ),
    ]


def _build_cancel_action(toast_message: str) -> list[Action]:
    """Build the Cancel-button click chain.

    Flips ``cancelled=True`` so the footer's Else block morphs to a
    "Cancelled" pill + disabled Cancel button, and surfaces a toast for
    immediate visual feedback. The Confirm button binds
    ``disabled=Rx("pending") | Rx("cancelled")`` so cancelling locks out
    a subsequent confirm as well.
    """
    return [
        SetState("cancelled", True),
        ShowToast(message=toast_message, variant="info"),
    ]


def _render_error_block() -> None:
    """Render the inline apply-failed Alert, bound to iframe ``error`` state.

    Sits inside ``CardContent`` and stays hidden until ``on_error`` flips
    ``error`` to a truthy string; matches katana's shadcn ``Alert`` primitive
    so the error surface is visually consistent across sibling MCP servers.
    """
    with If("error"):
        Separator()
        with Alert(variant="destructive", icon="circle-alert"):
            AlertTitle(content="Apply failed")
            AlertDescription(content="{{ error }}")


def _render_confirm_footer(
    *,
    confirm_label: str,
    confirm_action: list[Action],
    cancel_action: list[Action],
    applied_label: str = "Applied",
) -> None:
    """Render the preview-card footer button row with a state machine.

    Five visible states driven by ``pending`` / ``cancelled`` / ``applied`` /
    ``error`` in iframe state. The If/Elif chain checks them in that order:

    - **Pending…** (highest): action in flight — loader icon, disabled.
    - **Cancelled**: user opted out — outline pill, disabled. Wins over
      ``error`` so a Cancel click after an apply failure reliably locks the
      footer down (otherwise the Retry button would keep showing because
      ``error`` is still set).
    - **Applied**: terminal success — success pill, disabled. The agent
      has the structured result via ``UpdateContext``.
    - **Error**: apply failed — warning Retry pill. Cancel remains usable
      and (per its own ``disabled`` binding) ends the flow.
    - **Preview** (initial, ``Else()``): Confirm + Cancel both enabled.

    Must be called inside a ``CardFooter`` context.
    """
    with Row(gap=2):
        with If("pending"):
            Button(
                label="Applying…",
                variant="default",
                icon="loader",
                disabled=True,
            )
        with Elif("cancelled"):
            Button(label="Cancelled", variant="outline", disabled=True)
        with Elif("applied"):
            Button(
                label=applied_label,
                variant="success",
                icon="check",
                disabled=True,
            )
        with Elif("error"):
            Button(
                label="Retry",
                variant="warning",
                icon="rotate-cw",
                on_click=confirm_action,
                # Mirror the initial Confirm button's belt-and-suspenders
                # guard so a rapid double-click on Retry during an in-flight
                # call can't fire a second apply. ``SetState("pending", True)``
                # in ``confirm_action`` flips state before re-render, but
                # the explicit ``disabled`` binding closes any iframe
                # propagation gap.
                disabled=Rx("pending") | Rx("cancelled"),
            )
        with Else():
            Button(
                label=confirm_label,
                variant="default",
                on_click=confirm_action,
                disabled=Rx("pending") | Rx("cancelled"),
            )

        Button(
            label="Cancel",
            variant="outline",
            on_click=cancel_action,
            disabled=Rx("pending") | Rx("applied") | Rx("cancelled"),
        )


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
                # Inside ForEach, bare ``{{ field }}`` resolves against
                # parent state, not the row. Capture the LoopItem so each
                # cell binds to ``$item.field``.
                with ForEach("order.history") as entry, Row(gap=2):
                    Text(content=entry.created_at)
                    Text(content=entry.event)
                    Text(content=entry.status_name)
                    Text(content=entry.comment)
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
    badge), and a Confirm button that re-invokes ``update_order_status``
    directly via ``CallTool`` with ``confirm=true``. The button click is the
    user-consent surface per the MCP Apps spec — no LLM round-trip.

    When ``preview["valid"]`` is ``False`` (the requested ``new_status_code``
    is not a viable transition from the current state), the Confirm button is
    replaced with a destructive warning surfacing the list of viable codes
    so the agent can self-correct.
    """
    order_id = preview.get("order_id")
    comment = preview.get("comment")
    public = bool(preview.get("public"))
    if not bool(preview.get("valid", True)):
        return _build_invalid_status_change_ui(
            preview, current_color=current_color, new_color=new_color
        )
    # Re-hydrate as the schema so its ``recipients_text`` is the single source
    # of truth for both the UI and the markdown fallback rendered by orders.py.
    recipients_text = StatusChangePreview.model_validate(preview).recipients_text()

    state: dict[str, Any] = {"preview": preview, **_PREVIEW_STATE_INIT}
    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"Preview: order {order_id} status change")
            Badge(label="PREVIEW", variant="secondary")

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
            _render_error_block()

        with CardFooter():
            _render_confirm_footer(
                confirm_label="Confirm change",
                confirm_action=_build_confirm_action(
                    "update_order_status",
                    {
                        "order_id": "{{ preview.order_id }}",
                        "status_code": "{{ preview.new_status_code }}",
                        "comment": "{{ preview.comment }}",
                        "public": "{{ preview.public }}",
                        "email_customer": "{{ preview.email_customer }}",
                        "email_additional": "{{ preview.email_additional }}",
                        "confirm": True,
                    },
                ),
                cancel_action=_build_cancel_action("Status change cancelled"),
                applied_label="Status updated",
            )
    return app


def _build_invalid_status_change_ui(
    preview: dict[str, Any],
    *,
    current_color: str | None,
    new_color: str | None,
) -> PrefabApp:
    """Render the destructive-warning card for an invalid status transition.

    The confirm rail is intentionally absent — agents that picked an
    unreachable ``new_status_code`` see the viable codes and a button that
    refetches them, but cannot fire the apply.
    """
    order_id = preview.get("order_id")
    viable_codes = preview.get("viable_status_codes") or []

    with PrefabApp(state={"preview": preview}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"Preview: order {order_id} status change")
            Badge(label="INVALID TRANSITION", variant="destructive")

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

        with CardFooter(), Row(gap=2):
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
                on_click=ShowToast(message="Status change cancelled", variant="info"),
            )
    return app


def _summary_chip(summary: dict[str, Any]) -> None:
    """Render a compact "order #N (status)" chip for mutation previews."""
    label = summary.get("name") or f"order #{summary.get('order_number') or '?'}"
    status_name = summary.get("status_name") or "—"
    Badge(label=f"{label} · {status_name}", variant="secondary")


def build_comment_preview_ui(preview: dict[str, Any]) -> PrefabApp:
    """Preview Card for ``add_order_comment``.

    Shows which order the comment lands on (id + current status), the comment
    body, and a public/private visibility badge — then the standard
    Confirm/Cancel pair. Mirrors ``build_status_change_preview_ui`` so all
    mutation previews share UX shape.
    """
    order_id = preview.get("order_id")
    summary = preview.get("order_summary") or {}
    comment = preview.get("comment") or ""
    public = bool(preview.get("public"))

    state = {"preview": preview, **_PREVIEW_STATE_INIT}
    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"Preview: comment on order {order_id}")
            Badge(label="PREVIEW", variant="secondary")

        with CardContent(), Column(gap=3):
            with Row(gap=2):
                _summary_chip(summary)
            Separator()
            with Row(gap=2):
                Muted(content="Comment:")
                Text(content=comment)
                Badge(
                    label="public" if public else "private",
                    variant="info" if public else "outline",
                )
            _render_error_block()

        with CardFooter():
            _render_confirm_footer(
                confirm_label="Confirm comment",
                confirm_action=_build_confirm_action(
                    "add_order_comment",
                    {
                        "order_id": "{{ preview.order_id }}",
                        "comment": "{{ preview.comment }}",
                        "public": "{{ preview.public }}",
                        "confirm": True,
                    },
                ),
                cancel_action=_build_cancel_action("Comment cancelled"),
                applied_label="Comment added",
            )
    return app


def build_due_date_change_preview_ui(preview: dict[str, Any]) -> PrefabApp:
    """Preview Card for ``update_order_due_date``.

    Shows current vs. proposed due_date (and due_date_to if set) side-by-side
    so the agent can see the delta before confirming.
    """
    order_id = preview.get("order_id")
    summary = preview.get("order_summary") or {}
    current = preview.get("current_due_date") or "—"
    current_to = preview.get("current_due_date_to")
    new_due = preview.get("new_due_date") or "—"
    new_to = preview.get("new_due_date_to")

    current_label = f"{current} → {current_to}" if current_to else current
    new_label = f"{new_due} → {new_to}" if new_to else new_due

    state = {"preview": preview, **_PREVIEW_STATE_INIT}
    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"Preview: due date for order {order_id}")
            Badge(label="PREVIEW", variant="secondary")

        with CardContent(), Column(gap=3):
            _summary_chip(summary)
            Separator()
            with Row(gap=3):
                with Column(gap=1):
                    Muted(content="Current")
                    Text(content=current_label)
                Text(content="→")
                with Column(gap=1):
                    Muted(content="Proposed")
                    Text(content=new_label)
            _render_error_block()

        with CardFooter():
            _render_confirm_footer(
                confirm_label="Confirm due date",
                confirm_action=_build_confirm_action(
                    "update_order_due_date",
                    {
                        "order_id": "{{ preview.order_id }}",
                        "due_date": "{{ preview.new_due_date }}",
                        "due_date_to": "{{ preview.new_due_date_to }}",
                        "confirm": True,
                    },
                ),
                cancel_action=_build_cancel_action("Due date change cancelled"),
                applied_label="Due date updated",
            )
    return app


def build_bulk_status_change_preview_ui(preview: dict[str, Any]) -> PrefabApp:
    """Preview Card for ``bulk_update_order_status``.

    Lists every order id about to be updated, the target status, and the
    notification flags. Per-order context (current status) is intentionally
    not fetched — that would be N round-trips today; once the ``id[]`` batch
    fetch lands (issue #32) the UI can render a richer per-order table.
    """
    target_code = preview.get("target_status_code") or "—"
    target_name = preview.get("target_status_name") or "—"
    order_ids = preview.get("order_ids") or []
    order_count = preview.get("order_count") or len(order_ids)
    comment = preview.get("comment")
    public = bool(preview.get("public"))
    # Re-hydrate as the schema so its ``recipients_text`` is the single source
    # of truth for both the UI and the markdown fallback rendered by orders.py.
    from statuspro_mcp.tools.schemas import BulkStatusChangePreview as _BSP

    recipients_text = _BSP.model_validate(preview).recipients_text()

    state = {"preview": preview, **_PREVIEW_STATE_INIT}
    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"Preview: bulk status change ({order_count} orders)")
            Badge(label="PREVIEW", variant="secondary")

        with CardContent(), Column(gap=3):
            with Row(gap=2):
                Muted(content="Target status:")
                Badge(label=f"{target_name} · {target_code}", variant="info")
            Separator()
            Metric(label="Orders affected", value=str(order_count))
            # Show the first ~10 ids inline; agents can ask for full list if needed.
            ids_preview = ", ".join(str(i) for i in order_ids[:10])
            if len(order_ids) > 10:
                ids_preview += f", … (+{len(order_ids) - 10} more)"
            Muted(content=f"IDs: {ids_preview}")

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
            _render_error_block()

        with CardFooter():
            _render_confirm_footer(
                confirm_label=f"Confirm bulk update ({order_count})",
                confirm_action=_build_confirm_action(
                    "bulk_update_order_status",
                    {
                        "order_ids": "{{ preview.order_ids }}",
                        "status_code": "{{ preview.target_status_code }}",
                        "comment": "{{ preview.comment }}",
                        "public": "{{ preview.public }}",
                        "email_customer": "{{ preview.email_customer }}",
                        "email_additional": "{{ preview.email_additional }}",
                        "confirm": True,
                    },
                ),
                cancel_action=_build_cancel_action("Bulk update cancelled"),
                applied_label=f"Updated {order_count} orders",
            )
    return app


__all__ = [
    "build_bulk_status_change_preview_ui",
    "build_comment_preview_ui",
    "build_due_date_change_preview_ui",
    "build_order_detail_ui",
    "build_orders_table_ui",
    "build_status_change_preview_ui",
    "build_viable_statuses_ui",
]
