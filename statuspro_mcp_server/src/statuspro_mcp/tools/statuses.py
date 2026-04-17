"""MCP tools for StatusPro status definitions.

2 tools: ``list_statuses`` (account-level catalog) and ``get_viable_statuses``
(transitions valid for a specific order's current state).
"""

from __future__ import annotations

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from statuspro_mcp.services import get_services


class StatusEntry(BaseModel):
    """Human-readable status record for tool responses."""

    code: str = Field(..., description="8-char status code, e.g. 'st000002'")
    name: str | None = None
    description: str | None = None
    color: str | None = None


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
    )
    async def get_viable_statuses(context: Context, order_id: int) -> list[StatusEntry]:
        services = get_services(context)
        statuses = await services.client.statuses.viable_for(order_id)
        return [_to_entry(s) for s in statuses]
