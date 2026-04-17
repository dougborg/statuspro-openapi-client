"""MCP prompts for the StatusPro API.

Prompts are optional guided multi-step templates. None are currently registered;
this module exists as an extension point.
"""

from fastmcp import FastMCP


def register_all_prompts(mcp: FastMCP) -> None:
    """Register all prompts with the FastMCP server (no-op placeholder)."""
    return None


__all__ = ["register_all_prompts"]
