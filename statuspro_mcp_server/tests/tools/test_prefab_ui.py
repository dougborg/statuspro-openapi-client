"""Smoke tests for the Prefab UI builders.

Each builder must return a ``PrefabApp`` whose ``.to_json()`` produces a dict
with a ``"view"`` key — that's the contract FastMCP's ``_prefab_to_json``
relies on to turn the app into the MCP-Apps wire envelope. Pin it so a future
Prefab version can't silently change the shape under us.

Where a builder ships behavior the user actually sees — the Confirm button's
follow-up message, the get_order drill-down tool name — assert against the
serialized envelope so a regression in the action wiring surfaces here rather
than in Claude Desktop.
"""

from __future__ import annotations

import json

from prefab_ui.app import PrefabApp
from statuspro_mcp.tools.prefab_ui import (
    build_order_detail_ui,
    build_orders_table_ui,
    build_status_change_preview_ui,
    build_viable_statuses_ui,
)


def _envelope(app: PrefabApp) -> dict:
    envelope = app.to_json()
    assert isinstance(envelope, dict)
    assert "view" in envelope
    return envelope


def _assert_renders(app: PrefabApp) -> None:
    _envelope(app)


def test_build_orders_table_ui_renders_with_drill_down_action():
    app = build_orders_table_ui(
        [
            {
                "id": 1,
                "order_number": "1188",
                "customer_name": "Jane Doe",
                "status_name": "In Production",
                "due_date": "2026-03-15",
            }
        ],
        total=1,
        filters_line="status=In Production",
    )
    # Row click must wire CallTool("get_order"); without it, the drill-down
    # half of the find/view/decide/mutate loop silently breaks in Claude Desktop.
    serialized = json.dumps(_envelope(app))
    assert "get_order" in serialized


def test_build_order_detail_ui_renders_with_history():
    app = build_order_detail_ui(
        {
            "id": 1,
            "name": "#1188",
            "order_number": "1188",
            "customer_name": "Jane Doe",
            "customer_email": "j@d.com",
            "status_code": "st000002",
            "status_name": "In Production",
            "due_date": "2020-01-01",  # deliberately overdue
            "history": [
                {
                    "created_at": "2026-03-01T10:00:00+00:00",
                    "event": "status_change",
                    "status_name": "In Production",
                    "comment": None,
                },
            ],
        },
        status_color="pink",
    )
    _assert_renders(app)


def test_build_order_detail_ui_renders_without_history():
    app = build_order_detail_ui(
        {
            "id": 1,
            "name": "#1188",
            "status_code": "st000001",
            "status_name": "Received",
            "history": [],
        }
    )
    _assert_renders(app)


def test_build_viable_statuses_ui_renders():
    app = build_viable_statuses_ui(
        42,
        [
            {"code": "st000003", "name": "Shipped", "color": "green"},
            {"code": "st000004", "name": "Delivered", "color": "blue"},
        ],
    )
    _assert_renders(app)


def test_build_viable_statuses_ui_renders_empty():
    app = build_viable_statuses_ui(42, [])
    _assert_renders(app)


def test_build_status_change_preview_ui_renders_with_confirm_action():
    app = build_status_change_preview_ui(
        {
            "order_id": 1,
            "current_status_code": "st000002",
            "current_status_name": "In Production",
            "new_status_code": "st000003",
            "new_status_name": "Shipped",
            "comment": "On the way",
            "public": True,
            "email_customer": True,
            "email_additional": False,
            "valid": True,
            "viable_status_codes": ["st000003", "st000004"],
        },
        current_color="pink",
        new_color="green",
    )
    # The Confirm button's SendMessage payload drives the second half of the
    # two-step mutation flow; if the literal "confirm=true" disappears, the
    # user can preview but never apply, with no test catching the regression.
    serialized = json.dumps(_envelope(app))
    assert "confirm=true" in serialized
    assert "st000003" in serialized


def test_build_status_change_preview_ui_invalid_transition_hides_confirm():
    """When valid=False, the Confirm button is replaced with a 'See viable
    transitions' button that calls get_viable_statuses, and the destructive
    INVALID TRANSITION badge surfaces. Without these, an agent that tried an
    invalid status_code could still confirm into a guaranteed 422.
    """
    app = build_status_change_preview_ui(
        {
            "order_id": 1,
            "current_status_code": "st000002",
            "current_status_name": "In Production",
            "new_status_code": "st000099",
            "new_status_name": None,
            "comment": None,
            "public": False,
            "email_customer": True,
            "email_additional": True,
            "valid": False,
            "viable_status_codes": ["st000003", "st000004"],
        },
    )
    serialized = json.dumps(_envelope(app))
    # No Confirm button → no "confirm=true" SendMessage payload.
    assert "confirm=true" not in serialized
    # The remediation path: the get_viable_statuses CallTool action must be
    # wired to the replacement button.
    assert "get_viable_statuses" in serialized
    # Viable codes surface in the warning text so the agent can self-correct.
    assert "st000003" in serialized
    assert "st000004" in serialized
