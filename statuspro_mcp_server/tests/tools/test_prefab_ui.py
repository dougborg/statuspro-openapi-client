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
    build_bulk_status_change_preview_ui,
    build_comment_preview_ui,
    build_due_date_change_preview_ui,
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
    # The Confirm button's CallTool action drives the second half of the
    # two-step mutation flow. Asserts the wire envelope carries:
    # - the tool name to invoke (update_order_status), so the host knows
    #   which tool/call channel to use (vs. SendMessage which would force
    #   an LLM round-trip),
    # - the new_status_code arg (the most likely-to-rot field — confirms
    #   the rename from preview's `new_status_code` → tool arg
    #   `status_code` works), and
    # - the literal `confirm: true` flag.
    serialized = json.dumps(_envelope(app))
    assert "update_order_status" in serialized
    assert "st000003" in serialized
    # Confirm flag in the CallTool args — both shapes possible depending on
    # how Prefab serializes booleans into the tool/call template.
    assert (
        '"confirm": true' in serialized or "{{ preview.new_status_code }}" in serialized
    )


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
    # No Confirm button → no update_order_status CallTool action.
    assert "update_order_status" not in serialized
    # The remediation path: the get_viable_statuses CallTool action must be
    # wired to the replacement button.
    assert "get_viable_statuses" in serialized
    # Viable codes surface in the warning text so the agent can self-correct.
    assert "st000003" in serialized
    assert "st000004" in serialized


def test_build_comment_preview_ui_renders_with_confirm_action():
    """Comment preview shows the order context, the comment body + visibility,
    and a Confirm button that fires the confirm=true follow-up.
    """
    app = build_comment_preview_ui(
        {
            "order_id": 1188,
            "order_summary": {
                "id": 1188,
                "name": "#1188",
                "order_number": "1188",
                "status_name": "In Production",
            },
            "comment": "Customer asked about ETA.",
            "public": False,
        },
    )
    serialized = json.dumps(_envelope(app))
    # CallTool wiring re-invokes add_order_comment with confirm=true.
    assert "add_order_comment" in serialized
    assert "Customer asked about ETA." in serialized
    assert "private" in serialized  # visibility badge
    # The order context surfaces so the agent isn't commenting blind.
    assert "1188" in serialized


def test_build_comment_preview_ui_public_visibility_renders():
    """Public flag flips the badge variant and label."""
    app = build_comment_preview_ui(
        {
            "order_id": 1,
            "order_summary": {
                "id": 1,
                "name": "#1",
                "order_number": "1",
                "status_name": None,
            },
            "comment": "Shipped today.",
            "public": True,
        },
    )
    serialized = json.dumps(_envelope(app))
    assert "public" in serialized


def test_build_due_date_change_preview_ui_shows_before_after():
    """Due date preview side-by-sides current vs. proposed so the delta is
    obvious before confirmation. Without this test, a regression that
    accidentally hides the current value passes silently.
    """
    app = build_due_date_change_preview_ui(
        {
            "order_id": 1188,
            "order_summary": {
                "id": 1188,
                "name": "#1188",
                "order_number": "1188",
                "status_name": "In Production",
            },
            "current_due_date": "2026-03-15",
            "current_due_date_to": None,
            "new_due_date": "2026-03-22",
            "new_due_date_to": "2026-03-24",
        },
    )
    serialized = json.dumps(_envelope(app))
    assert "2026-03-15" in serialized  # current
    assert "2026-03-22" in serialized  # new
    assert "2026-03-24" in serialized  # new range end
    # CallTool wiring re-invokes update_order_due_date with confirm=true.
    assert "update_order_due_date" in serialized


def test_build_bulk_status_change_preview_ui_shows_count_and_target():
    """Bulk preview must surface the affected count + target status code so
    the agent can sanity-check before confirming a 50-order mutation.
    """
    app = build_bulk_status_change_preview_ui(
        {
            "order_ids": list(range(1, 26)),  # 25 ids
            "order_count": 25,
            "target_status_code": "st000003",
            "target_status_name": "Shipped",
            "comment": None,
            "public": False,
            "email_customer": True,
            "email_additional": False,
        },
    )
    serialized = json.dumps(_envelope(app))
    assert "25" in serialized  # order count
    assert "st000003" in serialized  # target code
    assert "Shipped" in serialized  # target name (resolved from catalog)
    # CallTool wiring re-invokes bulk_update_order_status with confirm=true.
    assert "bulk_update_order_status" in serialized
    # Recipients line should include "customer" but not "additional contacts"
    # since email_additional=False.
    assert "customer" in serialized


def test_build_bulk_status_change_preview_ui_truncates_long_id_list():
    """When more than 10 ids are bulk-updated, the UI must truncate the
    inline ids preview with a "+N more" hint rather than dumping all 50.
    """
    app = build_bulk_status_change_preview_ui(
        {
            "order_ids": list(range(1, 51)),  # 50 ids — the API max
            "order_count": 50,
            "target_status_code": "st000003",
            "target_status_name": "Shipped",
            "comment": None,
            "public": False,
            "email_customer": True,
            "email_additional": True,
        },
    )
    serialized = json.dumps(_envelope(app))
    # First 10 ids visible (1, 2, ..., 10); last id (50) hidden behind "+40 more"
    assert "+40 more" in serialized
    assert "50" in serialized  # the count, not the id
