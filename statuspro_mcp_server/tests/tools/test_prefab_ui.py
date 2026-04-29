"""Smoke tests for the Prefab UI builders.

Each builder must return a ``PrefabApp`` whose ``.to_json()`` produces a dict
with a ``"view"`` key — that's the contract FastMCP's ``_prefab_to_json``
relies on to turn the app into the MCP-Apps wire envelope. Pin it so a future
Prefab version can't silently change the shape under us.

Where a builder ships behavior the user actually sees — the Confirm button's
CallTool action, the get_order drill-down tool name — assert against the
``toolCall`` payload in the serialized envelope so a regression in the
action wiring surfaces here rather than in Claude Desktop.

Note on assertion strategy: the preview model's ``.action`` field
(e.g. ``action="update_order_status"``) ends up in iframe state, so a naive
``"update_order_status" in serialized`` assertion can pass even if the
Confirm button is mis-wired or hidden. The ``_find_tool_calls`` helper
extracts the actual ``toolCall`` action payloads, which only appear when a
button is wired with ``CallTool(...)``.
"""

from __future__ import annotations

import json
from typing import Any

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


def _find_tool_calls(envelope: dict[str, Any]) -> list[dict[str, Any]]:
    """Walk ``envelope`` and collect every ``toolCall`` action payload.

    Each entry has the shape produced by Prefab's ``CallTool`` action:
    ``{"action": "toolCall", "tool": "...", "arguments": {...}}``. Returns
    them in document order. Used by the assertion helpers below to check
    that a builder wires a CallTool with specific tool name + args (vs. a
    substring match on the serialized JSON, which can be satisfied by the
    preview model's ``action`` field that lives in iframe ``state``).
    """
    found: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("action") == "toolCall" and "tool" in node:
                found.append(node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(envelope)
    return found


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
    # two-step mutation flow. The assertion target is the toolCall action
    # payload itself (not a substring of the wire envelope), since the
    # preview model's `action` field is also "update_order_status" and
    # lives in iframe state — a substring assertion would pass even if
    # the Confirm button were mis-wired.
    tool_calls = _find_tool_calls(_envelope(app))
    update_calls = [tc for tc in tool_calls if tc["tool"] == "update_order_status"]
    assert len(update_calls) == 1, (
        f"expected exactly one update_order_status CallTool action; got {tool_calls}"
    )
    args = update_calls[0]["arguments"]
    assert args.get("confirm") is True
    # Pin the new_status_code → status_code rename — the most likely-to-rot
    # arg if the builder is refactored.
    assert args.get("status_code") == "{{ preview.new_status_code }}"


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
    envelope = _envelope(app)
    tool_calls = _find_tool_calls(envelope)
    # No update_order_status toolCall action — the Confirm-change button
    # was replaced. (The string itself appears in iframe state under
    # preview.action, but that's not a button wiring.)
    assert not [tc for tc in tool_calls if tc["tool"] == "update_order_status"]
    # The remediation: a get_viable_statuses toolCall is wired instead.
    viable_calls = [tc for tc in tool_calls if tc["tool"] == "get_viable_statuses"]
    assert len(viable_calls) == 1
    assert viable_calls[0]["arguments"].get("order_id") == 1
    # Viable codes surface in the warning text so the agent can self-correct.
    serialized = json.dumps(envelope)
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
    envelope = _envelope(app)
    serialized = json.dumps(envelope)
    # The Confirm button must be wired with a toolCall to add_order_comment
    # carrying confirm=true.
    tool_calls = _find_tool_calls(envelope)
    confirm_calls = [tc for tc in tool_calls if tc["tool"] == "add_order_comment"]
    assert len(confirm_calls) == 1, (
        "expected exactly one add_order_comment toolCall action"
    )
    args = confirm_calls[0]["arguments"]
    assert args.get("confirm") is True
    # The visible content stays as substring assertions — those legitimately
    # appear in the rendered text, not in state.
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
    envelope = _envelope(app)
    serialized = json.dumps(envelope)
    assert "2026-03-15" in serialized  # current
    assert "2026-03-22" in serialized  # new
    assert "2026-03-24" in serialized  # new range end
    # Confirm button: toolCall to update_order_due_date with confirm=true,
    # and pin the new_due_date → due_date arg rename.
    tool_calls = _find_tool_calls(envelope)
    confirm_calls = [tc for tc in tool_calls if tc["tool"] == "update_order_due_date"]
    assert len(confirm_calls) == 1
    args = confirm_calls[0]["arguments"]
    assert args.get("confirm") is True
    assert args.get("due_date") == "{{ preview.new_due_date }}"
    assert args.get("due_date_to") == "{{ preview.new_due_date_to }}"


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
    envelope = _envelope(app)
    serialized = json.dumps(envelope)
    assert "25" in serialized  # order count
    assert "st000003" in serialized  # target code
    assert "Shipped" in serialized  # target name (resolved from catalog)
    # Confirm button: toolCall to bulk_update_order_status with confirm=true,
    # plus the target_status_code → status_code arg rename.
    tool_calls = _find_tool_calls(envelope)
    confirm_calls = [
        tc for tc in tool_calls if tc["tool"] == "bulk_update_order_status"
    ]
    assert len(confirm_calls) == 1
    args = confirm_calls[0]["arguments"]
    assert args.get("confirm") is True
    assert args.get("status_code") == "{{ preview.target_status_code }}"
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
