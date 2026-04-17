"""MCP resources for the StatusPro API.

Resources expose stable, read-only reference data so AI agents can orient
themselves without calling mutating tools.

Available resources:
- statuspro://statuses — the full status catalog
- statuspro://help — tool reference
"""

from __future__ import annotations

from fastmcp import FastMCP


def register_all_resources(mcp: FastMCP) -> None:
    """Register all resources with the FastMCP server."""
    from .help import register_resources as register_help_resources
    from .statuses import register_resources as register_statuses_resources

    register_statuses_resources(mcp)
    register_help_resources(mcp)


__all__ = ["register_all_resources"]
