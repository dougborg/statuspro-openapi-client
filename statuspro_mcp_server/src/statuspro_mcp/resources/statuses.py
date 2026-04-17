"""MCP resource exposing the StatusPro status catalog."""

from __future__ import annotations

from fastmcp import Context, FastMCP

from statuspro_mcp.services import get_services


def register_resources(mcp: FastMCP) -> None:
    """Register the ``statuspro://statuses`` resource."""

    @mcp.resource(
        uri="statuspro://statuses",
        name="Status catalog",
        description="Every status defined on this StatusPro account (code, name, color).",
        mime_type="application/json",
    )
    async def statuses_resource(context: Context) -> list[dict[str, str | None]]:
        services = get_services(context)
        statuses = await services.client.statuses.list()
        return [
            {
                "code": s.code,
                "name": s.name,
                "description": s.description,
                "color": s.color,
            }
            for s in statuses
        ]
