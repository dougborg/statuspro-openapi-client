"""MCP tools for the StatusPro API.

Each tool module exports a ``register_tools(mcp)`` function that registers its
tools on the FastMCP instance. ``register_all_tools`` is the single entry point
called by ``server.py``.
"""

from fastmcp import FastMCP


def register_all_tools(mcp: FastMCP) -> None:
    """Register every tool module with the FastMCP instance."""
    from .orders import register_tools as register_orders_tools
    from .statuses import register_tools as register_statuses_tools

    register_orders_tools(mcp)
    register_statuses_tools(mcp)


__all__ = ["register_all_tools"]
