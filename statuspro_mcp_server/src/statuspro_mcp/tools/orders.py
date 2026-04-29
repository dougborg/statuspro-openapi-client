"""MCP tools for StatusPro orders.

11 tools covering the ``/orders*`` endpoints plus a set of batch / aggregation
read tools (``get_orders_batch``, ``lookup_orders_batch``,
``list_orders_in_workflow``, ``summarize_active_orders``) that fan out
parallel calls under the hood when the StatusPro server has no native batch
endpoint. Mutations use a two-step confirm pattern: call with
``confirm=False`` to see a preview, then ``confirm=True`` to execute (the
client host elicits explicit user approval via ``ctx.elicit``).

Tools that benefit from interactive rendering register with ``meta=UI_META``
— ``list_orders``, ``list_orders_in_workflow``, ``get_order``,
``update_order_status``, ``add_order_comment``, ``update_order_due_date``,
``bulk_update_order_status``, ``get_viable_statuses``. FastMCP 3.x's
``_maybe_apply_prefab_ui`` expands the marker into the spec-required
``_meta.ui.resourceUri`` and auto-registers a per-tool ``ui://`` renderer
resource. Non-UI clients get the structured JSON content. See SEP-1865.

The ``GET /orders/lookup`` endpoint is intentionally not exposed: it is the
public, customer-verification path (requires ``number`` + ``email``) and adds
nothing for an authenticated MCP caller, who can already use ``list_orders``
(``search`` partially matches order name, order number, customer name, or
customer email) or ``get_order`` (by id).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import Field

from statuspro_mcp.services import get_services
from statuspro_mcp.tools.prefab_ui import (
    build_bulk_status_change_preview_ui,
    build_comment_preview_ui,
    build_due_date_change_preview_ui,
    build_order_detail_ui,
    build_orders_table_ui,
    build_status_change_preview_ui,
)
from statuspro_mcp.tools.schemas import (
    ActiveOrdersSummary,
    BatchOrderResponse,
    BatchOrderResult,
    BulkStatusChangePreview,
    BulkStatusChangeResult,
    CommentPreview,
    CommentResult,
    ConfirmationResult,
    DueDateChangePreview,
    DueDateChangeResult,
    HistoryEntry,
    OrderDetail,
    OrderHistoryPage,
    OrderList,
    OrderSummary,
    StatusChangePreview,
    StatusChangeResult,
    StatusCount,
    require_confirmation,
)
from statuspro_mcp.tools.tool_result_utils import (
    UI_META,
    iso_or_none,
    make_tool_result,
)
from statuspro_public_api_client.api.orders import (
    add_order_comment as add_order_comment_api,
    bulk_update_order_status as bulk_update_status,
    list_orders as list_orders_api,
    set_order_due_date,
    update_order_status as update_order_status_api,
)
from statuspro_public_api_client.models.add_order_comment_request import (
    AddOrderCommentRequest,
)
from statuspro_public_api_client.models.bulk_status_update_request import (
    BulkStatusUpdateRequest,
)
from statuspro_public_api_client.models.list_orders_financial_status_item import (
    ListOrdersFinancialStatusItem,
)
from statuspro_public_api_client.models.list_orders_fulfillment_status_item import (
    ListOrdersFulfillmentStatusItem,
)
from statuspro_public_api_client.models.set_due_date_request import SetDueDateRequest
from statuspro_public_api_client.models.update_order_status_request import (
    UpdateOrderStatusRequest,
)
from statuspro_public_api_client.utils import is_success, unwrap

logger = logging.getLogger(__name__)


def _to_summary(order: Any) -> OrderSummary:
    """Convert a domain Order or attrs model to an OrderSummary."""
    customer = getattr(order, "customer", None)
    status = getattr(order, "status", None)
    return OrderSummary(
        id=order.id,
        name=getattr(order, "name", None),
        order_number=getattr(order, "order_number", None),
        customer_name=getattr(customer, "name", None) if customer else None,
        customer_email=getattr(customer, "email", None) if customer else None,
        status_code=getattr(status, "code", None) if status else None,
        status_name=getattr(status, "name", None) if status else None,
        due_date=iso_or_none(getattr(order, "due_date", None)),
    )


def _history_entry(item: Any) -> HistoryEntry:
    """Convert an attrs ``HistoryItem`` into a UI-friendly ``HistoryEntry``."""
    status = getattr(item, "status", None)
    return HistoryEntry(
        event=getattr(item, "event", None) or None,
        status_code=getattr(status, "code", None) if status else None,
        status_name=getattr(status, "name", None) if status else None,
        comment=getattr(item, "comment", None) or None,
        comment_is_public=getattr(item, "comment_is_public", None),
        created_at=iso_or_none(getattr(item, "created_at", None)),
    )


DEFAULT_HISTORY_LIMIT = 50

# Cap concurrent calls in batch tools. The transport layer retries 429s but
# does not proactively throttle; firing 50 simultaneous requests turns one
# rate-limit hit into 50 concurrent backoff waits. 10 keeps the batch fast
# (well under the 60/min ceiling for read endpoints) and avoids the
# thundering-herd pattern. Applies to all three batch read tools.
_BATCH_CONCURRENCY_LIMIT = 10


async def _bounded_gather[T](
    coros: list[Any], *, limit: int = _BATCH_CONCURRENCY_LIMIT
) -> list[T | Exception]:
    """Run ``coros`` with bounded concurrency; mirrors ``asyncio.gather`` shape.

    Like ``asyncio.gather(..., return_exceptions=True)`` but caps how many
    coroutines run at once via a semaphore. Cancellation propagates: if the
    enclosing task is cancelled, the inner tasks are cancelled too — we
    only catch ``Exception``, not ``BaseException``, so ``CancelledError``
    is not swallowed and reported as a row-level error.
    """
    sem = asyncio.Semaphore(limit)

    async def _run(coro: Any) -> Any:
        async with sem:
            try:
                return await coro
            except Exception as e:
                return e

    return await asyncio.gather(*(_run(c) for c in coros))


def _classify_error(exc: Exception, *, what: str) -> str:
    """Format a per-row error string for batch results.

    Maps known StatusPro API errors to canonical prefixes that callers can
    parse: ``not_found``, ``ambiguous``, ``rate_limit``, ``auth``, ``server``,
    ``api``, or the exception class name as a generic fallback. The
    ``not_found_count`` / ``error_count`` aggregates rely on this prefix.
    """
    from statuspro_public_api_client.utils import (
        APIError,
        AuthenticationError,
        RateLimitError,
        ServerError,
    )

    detail = str(exc)[:120]
    if isinstance(exc, APIError):
        status = getattr(exc, "status_code", None)
        if status == 404:
            return f"not_found: {what}"
        if isinstance(exc, RateLimitError):
            return f"rate_limit: {detail}"
        if isinstance(exc, AuthenticationError):
            return f"auth: {detail}"
        if isinstance(exc, ServerError):
            return f"server: {detail}"
        return f"api: HTTP {status} {detail}"
    return f"{type(exc).__name__}: {detail}"


async def _count_financial(
    client: Any, value: ListOrdersFinancialStatusItem
) -> tuple[str, int]:
    """Return (financial_status name, active-order count) for one enum value."""
    resp = await list_orders_api.asyncio_detailed(
        client=client,
        exclude_cancelled=True,
        financial_status=[value],
        per_page=1,
        page=1,
    )
    parsed = unwrap(resp)
    return value.value, int(getattr(getattr(parsed, "meta", None), "total", None) or 0)


async def _count_fulfillment(
    client: Any, value: ListOrdersFulfillmentStatusItem
) -> tuple[str, int]:
    """Return (fulfillment_status name, active-order count) for one enum value."""
    resp = await list_orders_api.asyncio_detailed(
        client=client,
        exclude_cancelled=True,
        fulfillment_status=[value],
        per_page=1,
        page=1,
    )
    parsed = unwrap(resp)
    return value.value, int(getattr(getattr(parsed, "meta", None), "total", None) or 0)


def _merge_unique_by_id[T](batches: list[list[T]]) -> list[T]:
    """Flatten ``batches`` preserving first-seen order, deduplicated by ``.id``.

    Used by ``list_orders_in_workflow`` to merge per-status_code results.
    Output is deterministic: orders within a batch keep API order, and
    earlier batches take precedence over later ones for the same id.

    Each item in each batch must have an ``.id`` attribute.
    """
    seen_ids: set[Any] = set()
    out: list[T] = []
    for batch in batches:
        for item in batch:
            item_id = getattr(item, "id", None)
            if item_id is None or item_id in seen_ids:
                continue
            seen_ids.add(item_id)
            out.append(item)
    return out


def _build_batch_response(
    requested_count: int, results: list[BatchOrderResult]
) -> BatchOrderResponse:
    """Compute aggregate counts and assemble the typed response.

    Splits failures into ``not_found_count`` (rows whose error starts with
    ``not_found``) and ``error_count`` (everything else, including ambiguous
    and transport errors), matching the field-level docstring contract.
    """
    found = sum(1 for r in results if r.order is not None)
    not_found = sum(
        1
        for r in results
        if r.order is None and (r.error or "").startswith("not_found")
    )
    errors = sum(
        1
        for r in results
        if r.order is None and not (r.error or "").startswith("not_found")
    )
    return BatchOrderResponse(
        requested_count=requested_count,
        found_count=found,
        not_found_count=not_found,
        error_count=errors,
        results=results,
    )


def _to_detail(
    order: Any, *, history_limit: int = DEFAULT_HISTORY_LIMIT
) -> OrderDetail:
    """Convert a domain Order into a full ``OrderDetail``.

    History is truncated to the most recent ``history_limit`` entries
    (server returns chronological order, so we slice from the tail).
    Callers receive ``history_truncated`` + ``history_total_count`` to
    detect truncation and page through older entries via
    ``get_order_history``.

    ``history_limit`` must be >= 1. The MCP tool layer enforces this via
    ``Field(ge=1)``, but the helper guards explicitly: Python's
    ``items[-0:]`` returns the full list (since ``-0 == 0``), which would
    silently contradict ``history_truncated=True`` when called with 0.
    """
    if history_limit < 1:
        msg = f"history_limit must be >= 1, got {history_limit}"
        raise ValueError(msg)
    summary = _to_summary(order)
    history_items = getattr(order, "history", None) or []
    total = len(history_items)
    truncated = total > history_limit
    visible = history_items[-history_limit:] if truncated else history_items
    return OrderDetail(
        **summary.model_dump(),
        due_date_to=iso_or_none(getattr(order, "due_date_to", None)),
        history=[_history_entry(h) for h in visible],
        history_truncated=truncated,
        history_total_count=total,
    )


def _paginate_history(
    items: list[Any], *, page: int, per_page: int
) -> tuple[list[Any], int, int]:
    """Slice the in-memory history array into one page.

    Returns ``(page_items, total, total_pages)``. Extracted so the
    pagination contract is testable without spinning up FastMCP to
    invoke the registered ``get_order_history`` tool.

    ``page`` and ``per_page`` are assumed >= 1 (enforced at the tool
    layer via ``Field(ge=1)``); guard explicitly so a misuse raises
    rather than producing nonsensical slices.
    """
    if page < 1:
        msg = f"page must be >= 1, got {page}"
        raise ValueError(msg)
    if per_page < 1:
        msg = f"per_page must be >= 1, got {per_page}"
        raise ValueError(msg)
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], total, total_pages


async def _status_color_catalog(services: Any) -> dict[str, str | None]:
    """Fetch the status catalog once and return a ``{code: color}`` map.

    The ``Status`` model on an order has no color field — only
    ``StatusDefinition`` (returned by ``statuses.list()``) does. Callers that
    want to color-chip an order's status must look up by code against this
    catalog. The call adds one HTTP round-trip per tool invocation; the
    StatusPro catalog is small (O(20)) so the response is cheap.
    """
    statuses = await services.client.statuses.list()
    catalog: dict[str, str | None] = {}
    for s in statuses:
        code = getattr(s, "code", None)
        if code:
            catalog[code] = getattr(s, "color", None)
    return catalog


def register_tools(mcp: FastMCP) -> None:
    """Register order-related tools with the FastMCP server."""

    @mcp.tool(
        name="list_orders",
        description=(
            "List orders with optional filters. Auto-paginates when page is "
            "unset.\n\n"
            "Two gotchas worth knowing about:\n"
            "1. Many orders may have NO `status` set at all (newly created, "
            "not yet moved into the workflow). If you only want orders "
            "StatusPro is actively tracking through workflow stages, use "
            "`list_orders_in_workflow` — it iterates per known status_code "
            "and returns only orders with a status assigned.\n"
            "2. The `financial_status`, `fulfillment_status`, and `tags` "
            "filters work server-side but those fields are NOT echoed back "
            "on results. Filter for what you need; don't list-then-inspect."
        ),
        meta=UI_META,
    )
    async def list_orders(
        context: Context,
        search: Annotated[str | None, Field(description="Full-text search")] = None,
        status_code: Annotated[
            str | None, Field(description="Filter to one status code")
        ] = None,
        tags: Annotated[
            list[str] | None, Field(description="Must match all tags")
        ] = None,
        tags_any: Annotated[
            list[str] | None, Field(description="Match any of these tags")
        ] = None,
        financial_status: list[str] | None = None,
        fulfillment_status: list[str] | None = None,
        exclude_cancelled: Annotated[
            bool | None, Field(description="Exclude cancelled orders")
        ] = None,
        due_date_from: Annotated[
            str | None, Field(description="ISO 8601 lower bound on due_date")
        ] = None,
        due_date_to: Annotated[
            str | None, Field(description="ISO 8601 upper bound on due_date")
        ] = None,
        page: Annotated[
            int | None, Field(description="Specific page; disables auto-pagination")
        ] = None,
        per_page: Annotated[
            int | None, Field(description="Items per page (max 100)")
        ] = None,
    ) -> ToolResult:
        services = get_services(context)
        orders = await services.client.orders.list(
            search=search,
            status_code=status_code,
            tags=tags,
            tags_any=tags_any,
            financial_status=financial_status,
            fulfillment_status=fulfillment_status,
            exclude_cancelled=exclude_cancelled,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            page=page,
            per_page=per_page,
        )
        summaries = [_to_summary(o) for o in orders]
        summary_dicts = [s.model_dump() for s in summaries]
        filters: dict[str, Any] = {
            k: v
            for k, v in {
                "search": search,
                "status_code": status_code,
                "tags": tags,
                "tags_any": tags_any,
                "financial_status": financial_status,
                "fulfillment_status": fulfillment_status,
                "exclude_cancelled": exclude_cancelled,
                "due_date_from": due_date_from,
                "due_date_to": due_date_to,
            }.items()
            if v not in (None, [], "")
        }
        filters_line = (
            ", ".join(f"{k}={v}" for k, v in filters.items()) if filters else ""
        )

        response = OrderList(orders=summaries, total=len(summaries), filters=filters)
        app = build_orders_table_ui(
            summary_dicts,
            total=len(summaries),
            filters_line=filters_line or None,
        )
        return make_tool_result(response, ui=app)

    @mcp.tool(
        name="list_orders_in_workflow",
        description=(
            "Return only orders that StatusPro is actively tracking through "
            "a workflow stage — i.e. orders with a `status` set to one of "
            "the tenant's defined status codes. Excludes cancelled orders "
            "and orders with no status assigned (which can be a large "
            "fraction of the total — see `list_orders` description for "
            "context). Internally fans out one `list_orders(status_code=…)` "
            "call per defined status (concurrency capped at 10) and merges "
            "the results."
        ),
        meta=UI_META,
    )
    async def list_orders_in_workflow(
        context: Context,
        search: Annotated[
            str | None,
            Field(
                description=(
                    "Optional full-text search applied within each "
                    "status_code call (matches order number, name, or "
                    "customer fields)."
                ),
            ),
        ] = None,
    ) -> ToolResult:
        services = get_services(context)

        # Fetch the status catalog first, then fetch the per-status order
        # lists concurrently via _bounded_gather (capped at 10 in-flight,
        # captures per-row exceptions). Each per-status call auto-paginates
        # (no `page` set), so we get the full set per status code without
        # ceiling at per_page=100.
        statuses_list = await services.client.statuses.list()
        active_codes: list[str] = []
        for s in statuses_list:
            code = getattr(s, "code", None)
            if isinstance(code, str) and code:
                active_codes.append(code)

        async def fetch_for_code(code: str) -> list[Any]:
            kwargs: dict[str, Any] = {
                "exclude_cancelled": True,
                "status_code": code,
                "per_page": 100,
            }
            if search:
                kwargs["search"] = search
            return await services.client.orders.list(**kwargs)

        # _bounded_gather catches Exception (not BaseException) so individual
        # failures (rate limit, transport error, auth) don't kill the whole
        # call — we proceed with whatever buckets succeeded. CancelledError
        # propagates correctly.
        gathered = await _bounded_gather(
            [fetch_for_code(code) for code in active_codes]
        )
        successful_batches: list[list[Any]] = []
        failed_codes: list[str] = []
        for code, result in zip(active_codes, gathered, strict=True):
            if isinstance(result, Exception):
                failed_codes.append(code)
                logger.warning(
                    "list_orders_in_workflow: status_code=%s fetch failed: %s",
                    code,
                    _classify_error(result, what=f"status_code={code}"),
                )
            else:
                successful_batches.append(result)

        orders = _merge_unique_by_id(successful_batches)

        summaries = [_to_summary(o) for o in orders]
        summary_dicts = [s.model_dump() for s in summaries]
        filters_line = f"in workflow ({len(active_codes)} statuses)" + (
            f", search={search!r}" if search else ""
        )

        response = OrderList(
            orders=summaries,
            total=len(summaries),
            filters={
                "in_workflow": True,
                "status_codes": active_codes,
                "search": search,
            },
        )
        app = build_orders_table_ui(
            summary_dicts,
            total=len(summaries),
            filters_line=filters_line,
        )
        return make_tool_result(response, ui=app)

    @mcp.tool(
        name="get_order",
        description=(
            "Fetch full details for one order by id (with history). "
            "History is capped at history_limit entries (default 50, most recent); "
            "if history_truncated is true on the result, use get_order_history to "
            "page through older entries."
        ),
        meta=UI_META,
    )
    async def get_order(
        context: Context,
        order_id: Annotated[int, Field(description="StatusPro order id")],
        history_limit: Annotated[
            int,
            Field(
                description="Max history entries to include (most recent N).",
                ge=1,
                le=500,
            ),
        ] = DEFAULT_HISTORY_LIMIT,
    ) -> ToolResult:
        services = get_services(context)
        order, catalog = await asyncio.gather(
            services.client.orders.get(order_id),
            _status_color_catalog(services),
        )

        detail = _to_detail(order, history_limit=history_limit)
        status_color = catalog.get(detail.status_code) if detail.status_code else None
        app = build_order_detail_ui(detail.model_dump(), status_color=status_color)
        return make_tool_result(detail, ui=app)

    @mcp.tool(
        name="get_orders_batch",
        description=(
            "Fetch summary details for multiple orders by id in one call. "
            "Fans out to N parallel get_order requests under the hood; "
            "transport layer handles 60/min rate-limit backoff. Capped at "
            "50 ids per call. Returns a result per requested id with "
            "explicit not-found markers."
        ),
    )
    async def get_orders_batch(
        context: Context,
        order_ids: Annotated[
            list[int],
            Field(
                description="Order ids to fetch (1-50 items).",
                min_length=1,
                max_length=50,
            ),
        ],
    ) -> BatchOrderResponse:
        services = get_services(context)
        # Fan out with a concurrency cap; transport-layer retry handles 429s
        # if any individual call hits the rate limit. _bounded_gather only
        # catches Exception (not BaseException), so CancelledError propagates
        # cleanly if the caller cancels mid-batch.
        fetched = await _bounded_gather(
            [services.client.orders.get(oid) for oid in order_ids],
        )
        results: list[BatchOrderResult] = []
        for oid, outcome in zip(order_ids, fetched, strict=True):
            if isinstance(outcome, Exception):
                results.append(
                    BatchOrderResult(
                        order_id=oid,
                        requested=str(oid),
                        order=None,
                        error=_classify_error(outcome, what=f"order id {oid}"),
                    )
                )
            else:
                results.append(
                    BatchOrderResult(
                        order_id=oid,
                        requested=str(oid),
                        order=_to_summary(outcome),
                        error=None,
                    )
                )
        return _build_batch_response(len(order_ids), results)

    @mcp.tool(
        name="lookup_orders_batch",
        description=(
            "Resolve multiple order numbers to orders in one call. Uses "
            "list_orders(search=…) per number with exact-match disambiguation; "
            "useful when an external system (e.g. Katana) hands you order "
            "numbers but no ids. Capped at 50 numbers. Marks ambiguous "
            "matches (multiple orders matching the same number) as errors."
        ),
    )
    async def lookup_orders_batch(
        context: Context,
        order_numbers: Annotated[
            list[str],
            Field(
                description=(
                    "Order numbers to resolve (1-50 items). Both '20486' "
                    "and '#20486' formats accepted; the '#' prefix is stripped."
                ),
                min_length=1,
                max_length=50,
            ),
        ],
    ) -> BatchOrderResponse:
        services = get_services(context)
        sem = asyncio.Semaphore(_BATCH_CONCURRENCY_LIMIT)

        async def resolve_one(raw: str) -> BatchOrderResult:
            number = raw.lstrip("#").strip()
            async with sem:
                try:
                    # page=1 disables the transport's auto-pagination —
                    # for short numbers like "42" the fuzzy search can match
                    # many orders, and walking every page per row would
                    # explode the cost of a 50-item batch.
                    matches = await services.client.orders.list(
                        search=number, page=1, per_page=10
                    )
                except Exception as e:
                    return BatchOrderResult(
                        requested=raw,
                        order=None,
                        error=_classify_error(e, what=f"order number {raw!r}"),
                    )
            # Disambiguate to exact order_number / name match. search is
            # fuzzy across multiple fields, so blindly taking the first
            # match risks false positives.
            exact = [
                o
                for o in matches
                if o.order_number == number or o.name in {number, f"#{number}"}
            ]
            if len(exact) == 1:
                return BatchOrderResult(
                    order_id=exact[0].id,
                    requested=raw,
                    order=_to_summary(exact[0]),
                    error=None,
                )
            if len(exact) > 1:
                return BatchOrderResult(
                    requested=raw,
                    order=None,
                    error=f"ambiguous: {len(exact)} exact matches for {number!r}",
                )
            return BatchOrderResult(
                requested=raw,
                order=None,
                error=f"not_found: no exact match for {number!r}",
            )

        results = list(await asyncio.gather(*(resolve_one(n) for n in order_numbers)))
        return _build_batch_response(len(order_numbers), results)

    @mcp.tool(
        name="summarize_active_orders",
        description=(
            "One-shot summary of all non-cancelled orders. Returns counts "
            "by workflow status, financial_status, and fulfillment_status. "
            "Useful for reporting / dashboard views without paginating "
            "through hundreds of records. Internally issues a variable "
            "number of read requests: 1 totals + 1 status-catalog + N "
            "per workflow status code + 8 financial_status counts + 4 "
            "fulfillment_status counts. Cached at the response middleware "
            "(30s TTL). Concurrency capped at 10 in-flight to avoid "
            "rate-limit thundering herd. The no_status_count is computed "
            "as total_active minus the sum of per-status counts; this is "
            "best-effort (not snapshot-atomic) and assumes one status "
            "code per order, which is the StatusPro server's contract."
        ),
    )
    async def summarize_active_orders(
        context: Context,
    ) -> ActiveOrdersSummary:
        services = get_services(context)

        async def total(**kwargs: Any) -> int:
            kwargs.setdefault("exclude_cancelled", True)
            kwargs.setdefault("per_page", 1)
            kwargs.setdefault("page", 1)
            resp = await list_orders_api.asyncio_detailed(
                client=services.client, **kwargs
            )
            parsed = unwrap(resp)
            return int(getattr(getattr(parsed, "meta", None), "total", None) or 0)

        async def count_by_status(code: str | None, name: str | None) -> StatusCount:
            kwargs: dict[str, Any] = {}
            if code:
                kwargs["status_code"] = code
            return StatusCount(
                status_code=code,
                status_name=name,
                count=await total(**kwargs),
            )

        # Get total active + status catalog in parallel.
        statuses_list, total_active = await asyncio.gather(
            services.client.statuses.list(), total()
        )

        # Per-status / financial / fulfillment counts in parallel, but
        # bounded so we don't fire ~20 simultaneous requests at the same
        # endpoint and turn one rate-limit hit into 20 retries in lockstep.
        sem = asyncio.Semaphore(_BATCH_CONCURRENCY_LIMIT)

        async def bounded[T](coro: Any) -> T:
            async with sem:
                return await coro

        status_coros = [
            bounded(count_by_status(getattr(s, "code", None), getattr(s, "name", None)))
            for s in statuses_list
            if getattr(s, "code", None)
        ]
        financial_coros = [
            bounded(_count_financial(services.client, v))
            for v in ListOrdersFinancialStatusItem
        ]
        fulfillment_coros = [
            bounded(_count_fulfillment(services.client, v))
            for v in ListOrdersFulfillmentStatusItem
        ]

        status_counts, financial_results, fulfillment_results = await asyncio.gather(
            asyncio.gather(*status_coros),
            asyncio.gather(*financial_coros),
            asyncio.gather(*fulfillment_coros),
        )

        # Active orders not accounted for by any status code = "no status set".
        # Snapshot-best-effort: this back-computes from total_active minus the
        # sum of per-status counts, so it's accurate when the data is stable
        # but can be stale (or even briefly negative, hence the max(0, ...))
        # if orders move between statuses while we're counting. Documented
        # in the tool description above.
        accounted_for = sum(s.count for s in status_counts)
        no_status = max(0, total_active - accounted_for)

        return ActiveOrdersSummary(
            total_active=total_active,
            by_status=sorted(status_counts, key=lambda s: -s.count),
            by_financial_status={k: v for k, v in financial_results if v > 0},
            by_fulfillment_status={k: v for k, v in fulfillment_results if v > 0},
            no_status_count=no_status,
        )

    @mcp.tool(
        name="get_order_history",
        description=(
            "Page through an order's full history timeline. Useful when "
            "get_order returned history_truncated=true and you need older "
            "entries. Page is 1-based; per_page defaults to 50, max 100."
        ),
    )
    async def get_order_history(
        context: Context,
        order_id: Annotated[int, Field(description="StatusPro order id")],
        page: Annotated[
            int,
            Field(description="1-based page number.", ge=1),
        ] = 1,
        per_page: Annotated[
            int,
            Field(description="Entries per page (max 100).", ge=1, le=100),
        ] = 50,
    ) -> OrderHistoryPage:
        services = get_services(context)
        # No server-side history pagination today — fetch the full order and
        # slice client-side via _paginate_history. Cheap relative to LLM
        # context cost; the helper makes the slicing math testable.
        order = await services.client.orders.get(order_id)
        all_items = getattr(order, "history", None) or []
        page_items, total, total_pages = _paginate_history(
            all_items, page=page, per_page=per_page
        )
        return OrderHistoryPage(
            order_id=order_id,
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            entries=[_history_entry(h) for h in page_items],
        )

    @mcp.tool(
        name="update_order_status",
        description=(
            "Change an order's status. Two-step confirm: call with confirm=false "
            "to preview; confirm=true runs the update."
        ),
        meta=UI_META,
    )
    async def update_order_status(
        context: Context,
        order_id: int,
        status_code: Annotated[
            str, Field(description="8-char status code, e.g. 'st000002'")
        ],
        comment: Annotated[
            str | None, Field(description="Optional history comment")
        ] = None,
        public: Annotated[
            bool, Field(description="Make the comment visible to the customer")
        ] = False,
        email_customer: Annotated[
            bool, Field(description="Send the customer a status email")
        ] = True,
        email_additional: Annotated[
            bool, Field(description="Send additional notification emails")
        ] = True,
        confirm: Annotated[
            bool, Field(description="Must be true to apply the change")
        ] = False,
    ) -> ToolResult:
        services = get_services(context)

        if not confirm:
            # Preview branch: fetch order + status catalog + viable transitions
            # in parallel so the UI can show current vs. proposed AND so we
            # can pre-validate the transition before the user confirms (saves
            # the agent from getting a 422 surprise on the confirm step).
            order, statuses_list, viable = await asyncio.gather(
                services.client.orders.get(order_id),
                services.client.statuses.list(),
                services.client.statuses.viable_for(order_id),
            )

            # Single catalog fetch services both the color map and the
            # new-status-name lookup (``list_statuses`` is cached).
            catalog: dict[str, str | None] = {}
            new_name: str | None = None
            for s in statuses_list:
                code = getattr(s, "code", None)
                if not code:
                    continue
                catalog[code] = getattr(s, "color", None)
                if code == status_code:
                    new_name = getattr(s, "name", None)

            viable_codes: list[str] = []
            for s in viable:
                code = getattr(s, "code", None)
                if isinstance(code, str) and code:
                    viable_codes.append(code)
            valid_transition = status_code in viable_codes

            current = getattr(order, "status", None)
            current_code = getattr(current, "code", None) if current else None
            current_name = getattr(current, "name", None) if current else None

            preview = StatusChangePreview(
                order_id=order_id,
                current_status_code=current_code,
                current_status_name=current_name,
                new_status_code=status_code,
                new_status_name=new_name,
                comment=comment,
                public=public,
                email_customer=email_customer,
                email_additional=email_additional,
                valid=valid_transition,
                viable_status_codes=viable_codes,
            )
            app = build_status_change_preview_ui(
                preview.model_dump(),
                current_color=catalog.get(current_code) if current_code else None,
                new_color=catalog.get(status_code),
            )
            return make_tool_result(preview, ui=app)

        # Confirm branch: elicit approval, then execute. Result branch
        # doesn't emit a PrefabApp since the confirmation surface already
        # lives in the elicit prompt.
        result = await require_confirmation(
            context,
            f"Change order {order_id} status to {status_code}?",
        )
        if result is not ConfirmationResult.CONFIRMED:
            declined = StatusChangeResult(
                confirmed=False,
                order_id=order_id,
                new_status_code=status_code,
                success=False,
                http_status=0,
                message=f"User {result.value}",
            )
            return make_tool_result(declined)

        body = UpdateOrderStatusRequest(
            status_code=status_code,
            comment=comment,
            public=public,
            email_customer=email_customer,
            email_additional=email_additional,
        )
        response = await update_order_status_api.asyncio_detailed(
            client=services.client, order=order_id, body=body
        )
        outcome = StatusChangeResult(
            order_id=order_id,
            new_status_code=status_code,
            success=is_success(response),
            http_status=response.status_code,
        )
        return make_tool_result(outcome)

    @mcp.tool(
        name="add_order_comment",
        description="Add a history comment to an order (5/min rate limit). Two-step confirm.",
        meta=UI_META,
    )
    async def add_order_comment(
        context: Context,
        order_id: int,
        comment: Annotated[str, Field(description="Comment body")],
        public: Annotated[bool, Field(description="Visible to the customer")] = False,
        confirm: bool = False,
    ) -> ToolResult:
        services = get_services(context)

        if not confirm:
            order = await services.client.orders.get(order_id)
            order_summary = _to_summary(order)
            preview_model = CommentPreview(
                order_id=order_id,
                order_summary=order_summary,
                comment=comment,
                public=public,
            )
            app = build_comment_preview_ui(preview_model.model_dump())
            return make_tool_result(preview_model, ui=app)

        confirmation = await require_confirmation(
            context, f"Add comment to order {order_id}?"
        )
        if confirmation is not ConfirmationResult.CONFIRMED:
            declined = CommentResult(
                confirmed=False,
                order_id=order_id,
                success=False,
                http_status=0,
                message=f"User {confirmation.value}",
            )
            return make_tool_result(declined)

        body = AddOrderCommentRequest(comment=comment, public=public)
        response = await add_order_comment_api.asyncio_detailed(
            client=services.client, order=order_id, body=body
        )
        outcome = CommentResult(
            order_id=order_id,
            success=is_success(response),
            http_status=response.status_code,
        )
        return make_tool_result(outcome)

    @mcp.tool(
        name="update_order_due_date",
        description="Update an order's due date. Two-step confirm.",
        meta=UI_META,
    )
    async def update_order_due_date(
        context: Context,
        order_id: int,
        due_date: Annotated[str, Field(description="ISO 8601 date, e.g. '2026-03-15'")],
        due_date_to: Annotated[
            str | None, Field(description="Optional end of the range")
        ] = None,
        confirm: bool = False,
    ) -> ToolResult:
        services = get_services(context)

        if not confirm:
            order = await services.client.orders.get(order_id)
            order_summary = _to_summary(order)
            preview_model = DueDateChangePreview(
                order_id=order_id,
                order_summary=order_summary,
                current_due_date=iso_or_none(getattr(order, "due_date", None)),
                current_due_date_to=iso_or_none(getattr(order, "due_date_to", None)),
                new_due_date=due_date,
                new_due_date_to=due_date_to,
            )
            app = build_due_date_change_preview_ui(preview_model.model_dump())
            return make_tool_result(preview_model, ui=app)

        confirmation = await require_confirmation(
            context, f"Set due_date={due_date} for order {order_id}?"
        )
        if confirmation is not ConfirmationResult.CONFIRMED:
            declined = DueDateChangeResult(
                confirmed=False,
                order_id=order_id,
                new_due_date=due_date,
                new_due_date_to=due_date_to,
                success=False,
                http_status=0,
                message=f"User {confirmation.value}",
            )
            return make_tool_result(declined)

        body_kwargs: dict[str, Any] = {"due_date": due_date}
        if due_date_to is not None:
            body_kwargs["due_date_to"] = due_date_to
        body = SetDueDateRequest(**body_kwargs)
        response = await set_order_due_date.asyncio_detailed(
            client=services.client, order=order_id, body=body
        )
        outcome = DueDateChangeResult(
            order_id=order_id,
            new_due_date=due_date,
            new_due_date_to=due_date_to,
            success=is_success(response),
            http_status=response.status_code,
        )
        return make_tool_result(outcome)

    @mcp.tool(
        name="bulk_update_order_status",
        description=(
            "Update status for up to 50 orders in one call (5/min rate limit). "
            "Returns 202 Accepted; updates are queued asynchronously."
        ),
        meta=UI_META,
    )
    async def bulk_update_order_status(
        context: Context,
        order_ids: Annotated[
            list[int],
            Field(description="Order ids (1-50 items)", min_length=1, max_length=50),
        ],
        status_code: str,
        comment: str | None = None,
        public: bool = False,
        email_customer: bool = True,
        email_additional: bool = True,
        confirm: bool = False,
    ) -> ToolResult:
        services = get_services(context)

        if not confirm:
            # Resolve target status name from the catalog so the preview can
            # show "In Production" alongside the opaque code. statuses.list
            # is cached at the middleware layer.
            statuses_list = await services.client.statuses.list()
            target_name: str | None = None
            for s in statuses_list:
                if getattr(s, "code", None) == status_code:
                    target_name = getattr(s, "name", None)
                    break

            preview_model = BulkStatusChangePreview(
                order_ids=order_ids,
                order_count=len(order_ids),
                target_status_code=status_code,
                target_status_name=target_name,
                comment=comment,
                public=public,
                email_customer=email_customer,
                email_additional=email_additional,
            )
            app = build_bulk_status_change_preview_ui(preview_model.model_dump())
            return make_tool_result(preview_model, ui=app)

        confirmation = await require_confirmation(
            context,
            f"Bulk-update {len(order_ids)} orders to status {status_code}?",
        )
        if confirmation is not ConfirmationResult.CONFIRMED:
            declined = BulkStatusChangeResult(
                confirmed=False,
                order_count=len(order_ids),
                target_status_code=status_code,
                success=False,
                http_status=0,
                message=f"User {confirmation.value}",
            )
            return make_tool_result(declined)

        body = BulkStatusUpdateRequest(
            order_ids=order_ids,
            status_code=status_code,
            comment=comment,
            public=public,
            email_customer=email_customer,
            email_additional=email_additional,
        )
        response = await bulk_update_status.asyncio_detailed(
            client=services.client, body=body
        )
        outcome = BulkStatusChangeResult(
            order_count=len(order_ids),
            target_status_code=status_code,
            success=is_success(response),
            http_status=response.status_code,
            note="Bulk updates are queued and processed asynchronously.",
        )
        return make_tool_result(outcome)
