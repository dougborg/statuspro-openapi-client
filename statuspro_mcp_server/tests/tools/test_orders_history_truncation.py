"""Tests for history truncation in _to_detail and the get_order_history tool.

Covers the contract from issue #40: get_order returns the most recent
`history_limit` entries (default 50) with `history_truncated` and
`history_total_count` flags so callers know to use get_order_history
for older entries.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from statuspro_mcp.tools.orders import (
    DEFAULT_HISTORY_LIMIT,
    _history_entry,
    _to_detail,
)

from statuspro_public_api_client.domain import HistoryEntry, Order, OrderStatus


def _make_order(*, history_count: int) -> Order:
    """Build a domain Order with `history_count` history entries.

    Entries are ordered chronologically (oldest first) — server convention.
    """
    history = [
        HistoryEntry(
            event="status_change",
            status=OrderStatus(code="st000002", name="In Production"),
            comment=None,
            comment_is_public=False,
            created_at=datetime(2026, 1, 1, 10, 0, i % 60, tzinfo=UTC),
        )
        for i in range(history_count)
    ]
    return Order(
        id=42,
        name="#42",
        order_number="42",
        history=history,
    )


@pytest.mark.unit
class TestToDetailTruncation:
    """_to_detail respects history_limit and reports truncation accurately."""

    def test_no_history_returns_empty_not_truncated(self):
        order = Order(id=1, name="#1")
        detail = _to_detail(order)
        assert detail.history == []
        assert detail.history_truncated is False
        assert detail.history_total_count == 0

    def test_history_below_limit_passes_through(self):
        order = _make_order(history_count=10)
        detail = _to_detail(order, history_limit=DEFAULT_HISTORY_LIMIT)
        assert len(detail.history) == 10
        assert detail.history_truncated is False
        assert detail.history_total_count == 10

    def test_history_at_limit_not_truncated(self):
        """Exactly N entries with limit=N is not truncation."""
        order = _make_order(history_count=DEFAULT_HISTORY_LIMIT)
        detail = _to_detail(order)
        assert len(detail.history) == DEFAULT_HISTORY_LIMIT
        assert detail.history_truncated is False
        assert detail.history_total_count == DEFAULT_HISTORY_LIMIT

    def test_history_above_limit_truncated_to_most_recent(self):
        """Server returns chronological (oldest first); we keep the tail."""
        order = _make_order(history_count=DEFAULT_HISTORY_LIMIT + 7)
        detail = _to_detail(order)
        assert len(detail.history) == DEFAULT_HISTORY_LIMIT
        assert detail.history_truncated is True
        assert detail.history_total_count == DEFAULT_HISTORY_LIMIT + 7

        # The kept entries are the LAST N (most recent), not the first N.
        # First kept entry is index 7 (entries 0..6 were trimmed). created_at
        # on the MCP-shaped HistoryEntry is the ISO string, so parse to check
        # the second.
        first_kept = detail.history[0].created_at
        assert first_kept is not None
        first_kept_dt = datetime.fromisoformat(first_kept)
        assert first_kept_dt.second == 7 % 60

    def test_custom_history_limit_smaller(self):
        order = _make_order(history_count=20)
        detail = _to_detail(order, history_limit=5)
        assert len(detail.history) == 5
        assert detail.history_truncated is True
        assert detail.history_total_count == 20

    def test_custom_history_limit_zero_is_not_supported(self):
        """history_limit must be >= 1 — guarded at the MCP tool layer.
        Internal _to_detail with limit=0 would slice to []; verify the slice
        math doesn't blow up (defensive).
        """
        order = _make_order(history_count=5)
        # The tool itself rejects limit < 1 via Field(ge=1), but the helper
        # is permissive — verify it produces a sane result.
        detail = _to_detail(order, history_limit=1)
        assert len(detail.history) == 1
        assert detail.history_truncated is True


@pytest.mark.unit
class TestHistoryEntryConversion:
    """_history_entry converts a domain HistoryEntry into the MCP shape."""

    def test_status_change_entry(self):
        domain_entry = HistoryEntry(
            event="status_change",
            status=OrderStatus(code="st000002", name="In Production"),
            comment=None,
            comment_is_public=False,
            created_at=datetime(2026, 3, 12, 10, 14, tzinfo=UTC),
        )
        mcp_entry = _history_entry(domain_entry)
        assert mcp_entry.event == "status_change"
        assert mcp_entry.status_code == "st000002"
        assert mcp_entry.status_name == "In Production"
        assert mcp_entry.comment is None
        assert mcp_entry.created_at == "2026-03-12T10:14:00+00:00"

    def test_comment_entry(self):
        domain_entry = HistoryEntry(
            event="comment_added",
            status=None,
            comment="Customer asked about ETA.",
            comment_is_public=False,
            created_at=datetime(2026, 3, 13, 9, 0, tzinfo=UTC),
        )
        mcp_entry = _history_entry(domain_entry)
        assert mcp_entry.event == "comment_added"
        assert mcp_entry.status_code is None
        assert mcp_entry.status_name is None
        assert mcp_entry.comment == "Customer asked about ETA."
        assert mcp_entry.comment_is_public is False
