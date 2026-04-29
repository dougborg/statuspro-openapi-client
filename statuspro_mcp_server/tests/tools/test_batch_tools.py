"""Tests for the batch read tools' schemas and disambiguation logic.

The batch tools themselves (`get_orders_batch`, `lookup_orders_batch`,
`summarize_active_orders`) are FastMCP-decorated and need a Context to
invoke directly, so these tests focus on the schema contracts and on the
exact-match disambiguation logic in `lookup_orders_batch` (which is the
non-trivial piece — `search` is fuzzy, multiple matches need to be
flagged as ambiguous rather than silently picking the first).
"""

from __future__ import annotations

import pytest
from statuspro_mcp.tools.schemas import (
    ActiveOrdersSummary,
    BatchOrderResponse,
    BatchOrderResult,
    OrderSummary,
    StatusCount,
)


@pytest.mark.unit
class TestBatchOrderResultShape:
    """BatchOrderResult correctly partitions success vs. failure."""

    def test_success_case(self):
        order = OrderSummary(id=42, name="#42", order_number="42")
        result = BatchOrderResult(order_id=42, requested="42", order=order, error=None)
        assert result.order is not None
        assert result.error is None

    def test_not_found_case(self):
        result = BatchOrderResult(
            order_id=42, requested="42", order=None, error="not_found: ..."
        )
        assert result.order is None
        assert result.error is not None

    def test_lookup_by_number_no_id_resolved(self):
        """When lookup_orders_batch fails to resolve a number, order_id is None."""
        result = BatchOrderResult(
            order_id=None, requested="20486", order=None, error="not_found: ..."
        )
        assert result.order_id is None

    def test_requested_field_echoes_input(self):
        """requested is the verbatim input — callers join on it to map results
        back to their original list (which may have leading '#' etc.)."""
        result = BatchOrderResult(
            requested="#20486", order=None, error="ambiguous: ..."
        )
        assert result.requested == "#20486"


@pytest.mark.unit
class TestBatchOrderResponseAggregates:
    """BatchOrderResponse exposes accurate found/not_found/error counts.

    The split matters: callers reconciling against an external system use
    ``not_found_count`` to know how many of their inputs are genuinely
    unknown to StatusPro vs. ``error_count`` for transient transport
    failures (which the caller should retry, not flag as missing).
    """

    def test_all_found(self):
        order = OrderSummary(id=1)
        results = [
            BatchOrderResult(order_id=i, requested=str(i), order=order)
            for i in (1, 2, 3)
        ]
        resp = BatchOrderResponse(
            requested_count=3,
            found_count=3,
            not_found_count=0,
            error_count=0,
            results=results,
        )
        assert resp.found_count == 3
        assert resp.not_found_count == 0
        assert resp.error_count == 0

    def test_partial_found_split_into_not_found_vs_error(self):
        order = OrderSummary(id=1)
        results = [
            BatchOrderResult(order_id=1, requested="1", order=order),
            BatchOrderResult(order_id=2, requested="2", error="not_found: order id 2"),
            BatchOrderResult(order_id=3, requested="3", error="ambiguous: 2 matches"),
            BatchOrderResult(
                order_id=4, requested="4", error="rate_limit: backoff exhausted"
            ),
        ]
        # 1 found, 1 not_found (404), 2 error (ambiguous + rate_limit)
        resp = BatchOrderResponse(
            requested_count=4,
            found_count=1,
            not_found_count=1,
            error_count=2,
            results=results,
        )
        assert resp.found_count == 1
        assert resp.not_found_count == 1
        assert resp.error_count == 2
        # Sum invariant: found + not_found + error == requested
        assert (
            resp.found_count + resp.not_found_count + resp.error_count
            == resp.requested_count
        )


@pytest.mark.unit
class TestExactMatchDisambiguation:
    """The matching predicate used by `lookup_orders_batch.resolve_one`.

    Search is fuzzy across order_number, name, customer name, and email,
    so a result set may include false positives (e.g., search='42' may
    match orders #42, #420, and a customer whose phone contains 42).
    The disambiguation must require an EXACT match on order_number or name.
    """

    @staticmethod
    def _matches(orders: list[OrderSummary], number: str) -> list[OrderSummary]:
        # Replicate the predicate from `lookup_orders_batch.resolve_one`.
        return [
            o
            for o in orders
            if o.order_number == number or o.name in {number, f"#{number}"}
        ]

    def test_exact_order_number_match(self):
        orders = [
            OrderSummary(id=1, order_number="42", name="#42"),
            OrderSummary(id=2, order_number="420", name="#420"),
        ]
        assert len(self._matches(orders, "42")) == 1
        assert self._matches(orders, "42")[0].id == 1

    def test_name_with_hash_prefix_matches(self):
        """Some orders have name='#42' but order_number set differently —
        accept both forms."""
        orders = [
            OrderSummary(id=1, order_number="20486", name="#WEB20486"),
        ]
        assert len(self._matches(orders, "WEB20486")) == 1

    def test_no_partial_match(self):
        """A request for '42' must NOT match '420' or '142'."""
        orders = [
            OrderSummary(id=1, order_number="420"),
            OrderSummary(id=2, order_number="142"),
        ]
        assert self._matches(orders, "42") == []

    def test_ambiguous_returns_multiple(self):
        """If two orders share the same order_number (rare but possible
        across customers in some systems), both are returned — caller flags
        as ambiguous."""
        orders = [
            OrderSummary(id=1, order_number="42"),
            OrderSummary(id=2, order_number="42"),
        ]
        assert len(self._matches(orders, "42")) == 2


@pytest.mark.unit
class TestErrorClassification:
    """`_classify_error` produces canonical prefixes that the aggregate
    counters depend on. The contract: anything starting with `not_found:`
    counts as not-found; everything else counts as error."""

    def test_404_is_not_found(self):
        from statuspro_mcp.tools.orders import _classify_error

        from statuspro_public_api_client.utils import APIError

        err = APIError("Order not found.", 404)
        result = _classify_error(err, what="order id 42")
        assert result.startswith("not_found:")
        assert "order id 42" in result

    def test_rate_limit_classified(self):
        from statuspro_mcp.tools.orders import _classify_error

        from statuspro_public_api_client.utils import RateLimitError

        err = RateLimitError("Too many requests", 429)
        result = _classify_error(err, what="order id 1")
        assert result.startswith("rate_limit:")

    def test_auth_classified(self):
        from statuspro_mcp.tools.orders import _classify_error

        from statuspro_public_api_client.utils import AuthenticationError

        err = AuthenticationError("Invalid token", 401)
        result = _classify_error(err, what="order id 1")
        assert result.startswith("auth:")

    def test_server_error_classified(self):
        from statuspro_mcp.tools.orders import _classify_error

        from statuspro_public_api_client.utils import ServerError

        err = ServerError("Internal Server Error", 500)
        result = _classify_error(err, what="order id 1")
        assert result.startswith("server:")

    def test_generic_exception_falls_through(self):
        from statuspro_mcp.tools.orders import _classify_error

        err = ConnectionError("network unreachable")
        result = _classify_error(err, what="order id 1")
        assert result.startswith("ConnectionError:")
        # The fallback path doesn't start with not_found: so aggregate counts
        # the row as error_count, not not_found_count.
        assert not result.startswith("not_found")


@pytest.mark.unit
class TestBuildBatchResponseAggregation:
    """`_build_batch_response` partitions errors into not_found vs other."""

    def test_pure_success(self):
        from statuspro_mcp.tools.orders import _build_batch_response

        order = OrderSummary(id=1)
        results = [
            BatchOrderResult(order_id=1, requested="1", order=order),
            BatchOrderResult(order_id=2, requested="2", order=order),
        ]
        resp = _build_batch_response(2, results)
        assert resp.found_count == 2
        assert resp.not_found_count == 0
        assert resp.error_count == 0

    def test_mixed_outcomes(self):
        from statuspro_mcp.tools.orders import _build_batch_response

        order = OrderSummary(id=1)
        results = [
            BatchOrderResult(order_id=1, requested="1", order=order),
            BatchOrderResult(order_id=2, requested="2", error="not_found: order id 2"),
            BatchOrderResult(order_id=3, requested="3", error="ambiguous: 2 matches"),
            BatchOrderResult(
                order_id=4, requested="4", error="ConnectionError: timeout"
            ),
        ]
        resp = _build_batch_response(4, results)
        assert resp.found_count == 1
        assert resp.not_found_count == 1  # only the "not_found:" prefix
        assert resp.error_count == 2  # ambiguous + ConnectionError


@pytest.mark.unit
class TestMergeUniqueById:
    """`_merge_unique_by_id` is the dedupe helper used by `list_orders_in_workflow`.

    It must produce deterministic output (so callers can rely on stable
    ordering across calls), preserve API order within batches, and skip
    items missing an id.
    """

    def test_empty_input(self):
        from statuspro_mcp.tools.orders import _merge_unique_by_id

        assert _merge_unique_by_id([]) == []

    def test_single_batch_passthrough(self):
        from statuspro_mcp.tools.orders import _merge_unique_by_id

        a = OrderSummary(id=1)
        b = OrderSummary(id=2)
        result = _merge_unique_by_id([[a, b]])
        assert [o.id for o in result] == [1, 2]

    def test_dedupe_across_batches(self):
        """Order appearing in two status_code buckets is included exactly once."""
        from statuspro_mcp.tools.orders import _merge_unique_by_id

        a = OrderSummary(id=1)
        b = OrderSummary(id=2)
        result = _merge_unique_by_id([[a, b], [a]])
        assert [o.id for o in result] == [1, 2]

    def test_first_seen_wins(self):
        """When the same id appears in two batches, the first batch's item wins.

        Batches are passed in catalog order — so the order's "primary" status
        bucket (whichever comes first in the catalog) is what we surface.
        """
        from statuspro_mcp.tools.orders import _merge_unique_by_id

        a_v1 = OrderSummary(id=1, status_name="In Production")
        a_v2 = OrderSummary(id=1, status_name="Shipped")
        result = _merge_unique_by_id([[a_v1], [a_v2]])
        assert len(result) == 1
        assert result[0].status_name == "In Production"

    def test_preserves_api_order_within_batch(self):
        from statuspro_mcp.tools.orders import _merge_unique_by_id

        items = [OrderSummary(id=i) for i in (5, 2, 8, 1)]
        result = _merge_unique_by_id([items])
        assert [o.id for o in result] == [5, 2, 8, 1]

    def test_skips_items_with_no_id(self):
        """Defensive: if an item has no `.id`, skip it rather than crash."""
        from statuspro_mcp.tools.orders import _merge_unique_by_id

        # OrderSummary requires id, so use a stand-in that has no id attr.
        class Anonymous:
            pass

        a = OrderSummary(id=1)
        b = Anonymous()
        c = OrderSummary(id=3)
        result = _merge_unique_by_id([[a, b, c]])
        assert [getattr(o, "id", None) for o in result] == [1, 3]


@pytest.mark.unit
class TestExactMatchDisambiguationNoneSafety:
    """Edge case: rows with None order_number/name must not match."""

    def test_none_fields_dont_match_any_query(self):
        # If StatusPro ever returns an order with no order_number AND no name
        # (shouldn't happen but defend against it), the predicate must not
        # produce a false positive. None == "X" is always False, and None
        # in {"X", "#X"} is also always False, so this is correctly safe;
        # this test pins the behavior so a future refactor doesn't introduce
        # something like `(o.order_number or "") == number` that would match
        # an empty-string query.
        orders = [OrderSummary(id=1)]  # order_number=None, name=None by default
        for query in ("42", "WEB42", "#42", ""):
            matches = [
                o
                for o in orders
                if o.order_number == query or o.name in {query, f"#{query}"}
            ]
            # Even the empty-string query must not silently match a None field.
            assert matches == []


@pytest.mark.unit
class TestActiveOrdersSummaryShape:
    def test_shape(self):
        # Construct a well-formed response where by_status (32 = 17+15) +
        # no_status_count (443) sums exactly to total_active (475). The
        # invariant we want to pin down is that callers can rely on this
        # math: pre-fix, the test compared against a hard-coded literal,
        # which would have passed even if total_active drifted.
        summary = ActiveOrdersSummary(
            total_active=475,
            by_status=[
                StatusCount(
                    status_code="st0005B1", status_name="Order Confirmed", count=17
                ),
                StatusCount(
                    status_code="st0005B7", status_name="Bicycle Assembly", count=15
                ),
            ],
            by_financial_status={"paid": 458, "partially_refunded": 11},
            by_fulfillment_status={"fulfilled": 431, "partial": 1},
            no_status_count=443,
        )
        assert summary.total_active == 475
        assert summary.no_status_count == 443
        assert summary.by_financial_status["paid"] == 458
        # Invariant: sum of by_status counts + no_status_count == total_active
        # in a well-formed response. Pin against summary.total_active rather
        # than a hard-coded literal so the test catches drift on either side.
        assert (
            sum(s.count for s in summary.by_status) + summary.no_status_count
            == summary.total_active
        )
