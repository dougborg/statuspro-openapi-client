"""Smoke tests for the Prefab UI builders.

Each builder must return a ``PrefabApp`` whose ``.to_json()`` produces a dict
with a ``"view"`` key — that's the contract FastMCP's ``_prefab_to_json``
relies on to turn the app into the MCP-Apps wire envelope. Pin it so a future
Prefab version can't silently change the shape under us.
"""

from __future__ import annotations

from prefab_ui.app import PrefabApp
from statuspro_mcp.tools.prefab_ui import (
    build_order_detail_ui,
    build_orders_table_ui,
    build_status_change_preview_ui,
    build_viable_statuses_ui,
)


def _assert_renders(app: PrefabApp) -> None:
    envelope = app.to_json()
    assert isinstance(envelope, dict)
    assert "view" in envelope


def test_build_orders_table_ui_renders():
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
    _assert_renders(app)


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


def test_build_status_change_preview_ui_renders():
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
        },
        current_color="pink",
        new_color="green",
    )
    _assert_renders(app)
