"""MCP tools for StatusPro status definitions.

2 tools: ``list_statuses`` (account-level catalog) and ``get_viable_statuses``
(transitions valid for a specific order's current state).

``get_viable_statuses`` returns a Prefab UI (color-coded status buttons) for
MCP-Apps clients; the click action sends a follow-up message asking Claude to
``update_order_status(..., confirm=false)`` — which then renders the
status-change preview UI.
"""

from __future__ import annotations

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult

from statuspro_mcp.services import get_services
from statuspro_mcp.tools.prefab_ui import build_viable_statuses_ui
from statuspro_mcp.tools.schemas import StatusEntry, ViableStatusesResponse
from statuspro_mcp.tools.tool_result_utils import UI_META, make_tool_result


def _to_entry(status: object) -> StatusEntry:
    return StatusEntry(
        code=getattr(status, "code", "") or "",
        name=getattr(status, "name", None),
        description=getattr(status, "description", None),
        color=getattr(status, "color", None),
    )


def register_tools(mcp: FastMCP) -> None:
    """Register status-related tools with the FastMCP server."""

    @mcp.tool(
        name="list_statuses",
        description="List every status defined for this StatusPro account.",
    )
    async def list_statuses(context: Context) -> list[StatusEntry]:
        services = get_services(context)
        statuses = await services.client.statuses.list()
        return [_to_entry(s) for s in statuses]

    @mcp.tool(
        name="get_viable_statuses",
        description=(
            "Return the set of statuses that are valid transitions from an "
            "order's current state. Call this before update_order_status so the "
            "chosen status is guaranteed to be accepted."
        ),
        meta=UI_META,
    )
    async def get_viable_statuses(context: Context, order_id: int) -> ToolResult:
        services = get_services(context)
        statuses = await services.client.statuses.viable_for(order_id)
        entries = [_to_entry(s) for s in statuses]

        response = ViableStatusesResponse(order_id=order_id, statuses=entries)
        app = build_viable_statuses_ui(order_id, [e.model_dump() for e in entries])

        if entries:
            status_list = "\n".join(f"- `{e.code}` — {e.name or '—'}" for e in entries)
        else:
            status_list = "_(no valid transitions)_"

        return make_tool_result(
            response,
            template_name="viable_statuses",
            ui=app,
            order_id=order_id,
            status_list=status_list,
        )
