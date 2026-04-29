"""Tests for history truncation in _to_detail and the get_order_history tool.

Covers the contract from issue #40: get_order returns the most recent
`history_limit` entries (default 50) with `history_truncated` and
`history_total_count` flags so callers know to use get_order_history
for older entries. The pagination contract for get_order_history itself
is exercised via the extracted `_paginate_history` helper.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from statuspro_mcp.tools.orders import (
    DEFAULT_HISTORY_LIMIT,
    _history_entry,
    _paginate_history,
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

    def test_custom_history_limit_one_returns_most_recent_entry(self):
        """The MCP tool enforces history_limit >= 1; this verifies the
        smallest valid limit returns exactly the most recent entry.
        """
        order = _make_order(history_count=5)
        detail = _to_detail(order, history_limit=1)
        assert len(detail.history) == 1
        assert detail.history_truncated is True
        assert detail.history_total_count == 5

    def test_history_limit_zero_raises(self):
        """The helper rejects history_limit < 1 explicitly. Without the
        guard, ``items[-0:]`` returns the FULL list (since ``-0 == 0``),
        which would silently contradict ``history_truncated=True``.
        """
        order = _make_order(history_count=5)
        with pytest.raises(ValueError, match="history_limit must be >= 1"):
            _to_detail(order, history_limit=0)

    def test_history_limit_negative_raises(self):
        order = _make_order(history_count=5)
        with pytest.raises(ValueError, match="history_limit must be >= 1"):
            _to_detail(order, history_limit=-1)


@pytest.mark.unit
class TestPaginateHistory:
    """_paginate_history slices an in-memory list into page+total+total_pages."""

    def test_empty_list_first_page(self):
        items, total, total_pages = _paginate_history([], page=1, per_page=10)
        assert items == []
        assert total == 0
        # Empty list still reports total_pages=1 so callers can iterate
        # ``for p in range(1, total_pages+1)`` without an off-by-one.
        assert total_pages == 1

    def test_single_full_page(self):
        items, total, total_pages = _paginate_history(
            list(range(5)), page=1, per_page=10
        )
        assert items == [0, 1, 2, 3, 4]
        assert total == 5
        assert total_pages == 1

    def test_multiple_pages_first(self):
        items, total, total_pages = _paginate_history(
            list(range(25)), page=1, per_page=10
        )
        assert items == list(range(10))
        assert total == 25
        assert total_pages == 3

    def test_multiple_pages_middle(self):
        items, _, _ = _paginate_history(list(range(25)), page=2, per_page=10)
        assert items == list(range(10, 20))

    def test_multiple_pages_last_partial(self):
        """Final page may be shorter than per_page when total is not divisible."""
        items, total, total_pages = _paginate_history(
            list(range(25)), page=3, per_page=10
        )
        assert items == [20, 21, 22, 23, 24]
        assert total == 25
        assert total_pages == 3

    def test_page_past_end_returns_empty(self):
        items, total, total_pages = _paginate_history(
            list(range(5)), page=99, per_page=10
        )
        assert items == []
        assert total == 5
        assert total_pages == 1

    def test_per_page_larger_than_total(self):
        items, total, total_pages = _paginate_history(
            list(range(3)), page=1, per_page=100
        )
        assert items == [0, 1, 2]
        assert total == 3
        assert total_pages == 1

    def test_invalid_page_raises(self):
        with pytest.raises(ValueError, match="page must be >= 1"):
            _paginate_history([1, 2, 3], page=0, per_page=10)

    def test_invalid_per_page_raises(self):
        with pytest.raises(ValueError, match="per_page must be >= 1"):
            _paginate_history([1, 2, 3], page=1, per_page=0)


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
