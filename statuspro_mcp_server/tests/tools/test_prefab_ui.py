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
from collections.abc import Iterator
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


def _walk_nodes(envelope: Any) -> Iterator[dict[str, Any]]:
    """Yield every dict node in ``envelope`` in document order.

    The Prefab wire envelope nests dicts and lists; this generator visits
    them depth-first so callers can scan for action payloads, component
    types, or other structural matches without re-implementing the walk.
    """
    if isinstance(envelope, dict):
        yield envelope
        for v in envelope.values():
            yield from _walk_nodes(v)
    elif isinstance(envelope, list):
        for item in envelope:
            yield from _walk_nodes(item)


def _find_confirm_button(envelope: dict[str, Any]) -> dict[str, Any] | None:
    """Return the first Button with ``"Confirm"`` in its label.

    Targets the *initial* Confirm button (the footer Condition's ``else``
    branch) so its ``onClick`` chain can be asserted on directly without
    hardcoding the path through Condition.else.
    """
    return next(
        (
            n
            for n in _walk_nodes(envelope)
            if n.get("type") == "Button" and "Confirm" in str(n.get("label", ""))
        ),
        None,
    )


def _find_tool_calls(envelope: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect every ``toolCall`` action payload in ``envelope``.

    Used to assert against the actual button-click wiring, which would be
    invisible to a substring scan because the preview model's ``action``
    field lives in iframe ``state`` and would satisfy the substring check
    even when the Confirm button is mis-wired.
    """
    return [
        n
        for n in _walk_nodes(envelope)
        if n.get("action") == "toolCall" and "tool" in n
    ]


# Smallest-viable preview fixtures for the four mutation cards. Used by tests
# that pin contracts across every preview card (state-machine guards,
# Cancel-no-SendMessage). Kept module-level so a new "every card must…"
# assertion can iterate over them without copying ~45 lines per test.
_PREVIEW_BUILDER_FIXTURES: list[tuple[Any, dict[str, Any]]] = [
    (
        build_status_change_preview_ui,
        {
            "order_id": 1,
            "current_status_code": "st000002",
            "new_status_code": "st000003",
            "comment": None,
            "public": False,
            "email_customer": True,
            "email_additional": False,
            "valid": True,
            "viable_status_codes": ["st000003"],
        },
    ),
    (
        build_comment_preview_ui,
        {
            "order_id": 1,
            "order_summary": {"id": 1},
            "comment": "hi",
            "public": False,
        },
    ),
    (
        build_due_date_change_preview_ui,
        {
            "order_id": 1,
            "order_summary": {"id": 1},
            "current_due_date": "2026-01-01",
            "new_due_date": "2026-02-01",
        },
    ),
    (
        build_bulk_status_change_preview_ui,
        {
            "order_ids": [1, 2],
            "order_count": 2,
            "target_status_code": "st000003",
            "target_status_name": "Shipped",
            "comment": None,
            "public": False,
            "email_customer": True,
            "email_additional": False,
        },
    ),
]


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
    # Assert on the toolCall payload (not a substring) — the preview model's
    # ``action`` field is also "update_order_status" and lives in iframe state,
    # so a substring match would pass even with a mis-wired button.
    tool_calls = _find_tool_calls(_envelope(app))
    update_calls = [tc for tc in tool_calls if tc["tool"] == "update_order_status"]
    assert update_calls, (
        f"expected an update_order_status CallTool action; got {tool_calls}"
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
    assert confirm_calls, "expected an add_order_comment toolCall action"
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
    assert confirm_calls, "expected an update_order_due_date toolCall action"
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
    assert confirm_calls, "expected a bulk_update_order_status toolCall action"
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


def test_preview_cards_wire_double_click_guard():
    """Every preview card must seed the pending/cancelled state slots and bind
    its Confirm button to a chain that flips ``pending=True`` *before* firing
    the apply CallTool.

    Without these, a rapid double-click on the Confirm button fires two
    identical mutation calls — e.g. two bulk status updates that double-send
    notification emails to the customer. The SetState in the on_click chain
    is the spam guard; the explicit ``disabled={{ pending || cancelled }}``
    binding on the button is belt-and-suspenders.
    """
    for builder, preview in _PREVIEW_BUILDER_FIXTURES:
        envelope = _envelope(builder(preview))
        state = envelope.get("state") or {}
        # The four state slots the footer's If/Elif blocks bind to.
        assert state.get("pending") is False, (
            f"{builder.__name__} must seed pending=False"
        )
        assert state.get("cancelled") is False, (
            f"{builder.__name__} must seed cancelled=False"
        )
        assert state.get("applied") is False, (
            f"{builder.__name__} must seed applied=False"
        )
        # Locate the Confirm button (lives in the footer Condition's ``else``
        # branch — the initial Preview state) and verify its on_click chain
        # leads with ``SetState("pending", True)``. A substring match on the
        # whole envelope wouldn't catch a regression that moved the guard
        # SetState into ``on_success``/``on_error`` (where ``pending`` is
        # also referenced, but for clearing rather than guarding).
        confirm = _find_confirm_button(envelope)
        assert confirm is not None, (
            f"{builder.__name__}: could not locate Confirm button in footer"
        )
        on_click = confirm.get("onClick") or []
        assert on_click and isinstance(on_click, list), (
            f"{builder.__name__}: Confirm button has no on_click chain"
        )
        assert (
            on_click[0].get("action") == "setState"
            and on_click[0].get("key") == "pending"
            and on_click[0].get("value") is True
        ), (
            f"{builder.__name__}: on_click[0] must be SetState(pending, True); "
            f"got {on_click[0]}"
        )
        # The disabled binding gates rapid clicks even if the SetState above
        # is somehow delayed (belt-and-suspenders). It must reference both
        # ``pending`` and ``cancelled``.
        disabled = str(confirm.get("disabled") or "")
        assert "pending" in disabled and "cancelled" in disabled, (
            f"{builder.__name__}: Confirm button disabled binding must include "
            f"both pending and cancelled; got {disabled!r}"
        )


def test_confirm_footer_state_precedence():
    """The footer state machine must check ``cancelled`` before ``error`` so a
    Cancel click after an apply failure locks the footer down. Otherwise
    ``cancelled=True`` would be set but the Retry button would keep showing
    because ``error`` is still truthy from the prior failure.

    Pinning the case order here so a future shuffle of the If/Elif chain
    can't silently regress the user-cancel-after-error flow.
    """
    app = build_comment_preview_ui(
        {
            "order_id": 1,
            "order_summary": {"id": 1},
            "comment": "hi",
            "public": False,
        },
    )
    envelope = _envelope(app)
    # Find the footer Condition (the one with multiple cases — the error-block
    # uses an If too but only has a single ``{{ error }}`` case).
    footer_condition = next(
        (
            n
            for n in _walk_nodes(envelope)
            if n.get("type") == "Condition" and len(n.get("cases") or []) > 1
        ),
        None,
    )
    assert footer_condition is not None, "footer Condition not found in envelope"
    whens = [c.get("when") for c in footer_condition["cases"]]
    cancelled_idx = next(
        (i for i, w in enumerate(whens) if w and "cancelled" in str(w)), -1
    )
    error_idx = next((i for i, w in enumerate(whens) if w and "error" in str(w)), -1)
    assert cancelled_idx >= 0 and error_idx >= 0, (
        f"footer must have both cancelled and error cases; got whens={whens}"
    )
    assert cancelled_idx < error_idx, (
        f"cancelled case must precede error case in the footer state machine; "
        f"got cancelled@{cancelled_idx}, error@{error_idx} in {whens}"
    )


def test_retry_button_has_double_click_guard():
    """The Retry button (rendered in the error state) must share the initial
    Confirm button's ``disabled=Rx(pending) | Rx(cancelled)`` belt-and-
    suspenders binding. Without it, a rapid double-click on Retry during an
    in-flight retry can fire a second apply call before the iframe re-renders.
    """
    app = build_comment_preview_ui(
        {
            "order_id": 1,
            "order_summary": {"id": 1},
            "comment": "hi",
            "public": False,
        },
    )
    envelope = _envelope(app)
    retry = next(
        (
            n
            for n in _walk_nodes(envelope)
            if n.get("type") == "Button" and n.get("label") == "Retry"
        ),
        None,
    )
    assert retry is not None, "Retry button missing from footer state machine"
    disabled = str(retry.get("disabled") or "")
    assert "pending" in disabled and "cancelled" in disabled, (
        f"Retry button disabled binding must include both pending and "
        f"cancelled; got {disabled!r}"
    )


def test_cancel_buttons_do_not_send_chat_messages():
    """Cancel on every preview card must dismiss client-side (SetState +
    optional toast) — never fire ``SendMessage``.

    SendMessage round-trips through the LLM and shows up as a fake user
    message in the chat, which is noisy and unnecessary now that Confirm
    fires the apply directly via CallTool (no agent middleman). Pinning
    this so a future regression that re-introduces SendMessage on Cancel
    surfaces here instead of as chat-noise in production.
    """
    for builder, preview in _PREVIEW_BUILDER_FIXTURES:
        envelope = _envelope(builder(preview))
        cancel_buttons = [
            n
            for n in _walk_nodes(envelope)
            if n.get("type") == "Button" and n.get("label") == "Cancel"
        ]
        assert cancel_buttons, f"{builder.__name__}: no Cancel button found in envelope"
        for cancel in cancel_buttons:
            # ``_build_cancel_action`` returns ``list[Action]``, so the
            # serialized on_click is always a list — no defensive coercion
            # needed.
            on_click = cancel.get("onClick") or []
            assert isinstance(on_click, list), (
                f"{builder.__name__}: Cancel on_click must be a list; got {on_click!r}"
            )
            send_messages = [
                a
                for a in on_click
                if isinstance(a, dict) and a.get("action") == "sendMessage"
            ]
            assert not send_messages, (
                f"{builder.__name__}: Cancel button must not fire SendMessage; "
                f"got {send_messages}"
            )


def test_status_change_preview_invalid_does_not_seed_apply_state():
    """When ``valid=False`` the Confirm button is replaced with a "See viable
    transitions" button — the apply rail isn't live, so the pending/applied
    state slots shouldn't appear in the envelope (no apply to guard).
    """
    app = build_status_change_preview_ui(
        {
            "order_id": 1,
            "current_status_code": "st000002",
            "new_status_code": "st000099",
            "comment": None,
            "public": False,
            "email_customer": True,
            "email_additional": True,
            "valid": False,
            "viable_status_codes": ["st000003"],
        },
    )
    envelope = _envelope(app)
    state = envelope.get("state") or {}
    assert "pending" not in state
    assert "applied" not in state
