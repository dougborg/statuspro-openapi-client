"""Tests for HistoryEntry parsing on the domain Order pydantic model.

The domain Order is validated from `OrderResponse.to_dict()`, which is the
shape the server returns for `GET /orders/{id}`. The pydantic model uses
`extra="ignore"`, so any field that isn't explicitly declared on the model
is silently dropped. These tests pin down that `history` IS declared and
populates correctly — without them, the MCP `get_order` tool's history
field silently regresses to empty (the bug fixed in #40).
"""

from __future__ import annotations

import pytest

from statuspro_public_api_client.domain import HistoryEntry, Order


@pytest.mark.unit
class TestOrderHistoryParsing:
    """Order.model_validate() correctly populates history entries."""

    def test_order_with_no_history_field(self):
        """A response with no `history` key parses to history=None."""
        order = Order.model_validate(
            {
                "id": 123,
                "name": "#1188",
                "order_number": "1188",
            }
        )
        assert order.history is None

    def test_order_with_empty_history_array(self):
        """A response with `history: []` parses to history=[] (distinct from None)."""
        order = Order.model_validate(
            {
                "id": 123,
                "name": "#1188",
                "order_number": "1188",
                "history": [],
            }
        )
        assert order.history == []

    def test_order_with_history_entries(self):
        """All fields on each history entry round-trip from server-shaped dict."""
        order = Order.model_validate(
            {
                "id": 123,
                "name": "#1188",
                "order_number": "1188",
                "history": [
                    {
                        "event": "status_change",
                        "status": {
                            "is_set": True,
                            "code": "st000002",
                            "name": "In Production",
                            "public": True,
                        },
                        "comment": None,
                        "comment_is_public": False,
                        "created_at": "2026-03-12T10:14:00+00:00",
                    },
                    {
                        "event": "comment_added",
                        "status": None,
                        "comment": "Customer asked about ETA.",
                        "comment_is_public": False,
                        "created_at": "2026-03-13T09:00:00+00:00",
                    },
                ],
            }
        )
        assert order.history is not None
        assert len(order.history) == 2

        first, second = order.history
        assert isinstance(first, HistoryEntry)
        assert first.event == "status_change"
        assert first.status is not None
        assert first.status.code == "st000002"
        assert first.status.name == "In Production"
        assert first.comment is None
        assert first.created_at is not None
        assert first.created_at.isoformat() == "2026-03-12T10:14:00+00:00"

        assert second.event == "comment_added"
        assert second.status is None
        assert second.comment == "Customer asked about ETA."

    def test_order_drops_mail_log_field(self):
        """The audit `mail_log` field on server HistoryItem is intentionally
        not exposed on the domain HistoryEntry. Should not cause a parse error
        — `extra="ignore"` drops it silently.
        """
        order = Order.model_validate(
            {
                "id": 123,
                "history": [
                    {
                        "event": "status_change",
                        "status": None,
                        "created_at": "2026-03-12T10:14:00+00:00",
                        "mail_log": {"sent_at": "2026-03-12T10:15:00+00:00"},
                    }
                ],
            }
        )
        assert order.history is not None
        assert len(order.history) == 1
        # mail_log isn't on the model — verifying via attribute access raises
        assert not hasattr(order.history[0], "mail_log")
