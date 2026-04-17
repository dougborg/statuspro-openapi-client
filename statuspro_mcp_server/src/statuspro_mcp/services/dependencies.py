"""Dependency injection helpers for MCP tools."""

from dataclasses import dataclass

from fastmcp import Context

from statuspro_public_api_client import StatusProClient


@dataclass
class Services:
    """Container for services available to tools.

    Attributes:
        client: The StatusProClient instance for API operations
    """

    client: StatusProClient


def get_services(context: Context) -> Services:
    """Extract services from MCP context.

    Args:
        context: FastMCP context containing lifespan_context with Services

    Returns:
        Services: The lifespan context containing the StatusProClient
    """
    if context.request_context is None:
        raise RuntimeError(
            "get_services() called outside a request context — "
            "services are only available during tool/resource invocations"
        )
    return context.request_context.lifespan_context
