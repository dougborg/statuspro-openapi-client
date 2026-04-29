"""StatusPro MCP Server - FastMCP server with environment-based authentication.

This module implements the core MCP server for the StatusPro API, providing
tools and resources for looking up and updating order status.

Features:
- Environment-based authentication (STATUSPRO_API_KEY)
- Automatic client initialization with error handling
- Lifespan management for StatusProClient context
- Production-ready with transport-layer resilience
- Structured logging with observability
- Response caching for read-only tools (FastMCP 2.13+)
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from fastmcp.server.auth import AuthProvider  # pragma: no cover

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.middleware.caching import (
    CallToolSettings,
    ReadResourceSettings,
    ResponseCachingMiddleware,
)
from key_value.aio.stores.memory import MemoryStore

from statuspro_mcp import __version__
from statuspro_mcp._fastmcp_patches import apply_fastmcp_patches as _apply_patches
from statuspro_mcp.logging import get_logger, setup_logging
from statuspro_mcp.services import Services
from statuspro_public_api_client import StatusProClient

# Apply FastMCP patches for Pydantic 2.12+ compatibility BEFORE registering tools
_apply_patches()

# Initialize structured logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[Services]:
    """Manage server lifespan and StatusProClient lifecycle.

    This context manager:
    1. Loads environment variables from .env file
    2. Validates required configuration (STATUSPRO_API_KEY)
    3. Initializes StatusProClient with error handling
    4. Provides client to tools via ServerContext
    5. Ensures proper cleanup on shutdown

    Args:
        server: FastMCP server instance

    Yields:
        Services: Context object containing initialized StatusProClient

    Raises:
        ValueError: If STATUSPRO_API_KEY environment variable is not set
        Exception: If StatusProClient initialization fails
    """
    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    api_key = os.getenv("STATUSPRO_API_KEY")
    base_url = os.getenv("STATUSPRO_BASE_URL", "https://app.orderstatuspro.com/api/v1")

    # Validate required configuration
    if not api_key:
        logger.error(
            "authentication_failed",
            reason="STATUSPRO_API_KEY environment variable is required",
            message="Please set it in your .env file or environment.",
        )
        raise ValueError(
            "STATUSPRO_API_KEY environment variable is required for authentication"
        )

    logger.info("server_initializing", version=__version__, base_url=base_url)

    try:
        # Initialize StatusProClient with automatic resilience features
        async with StatusProClient(
            api_key=api_key,
            base_url=base_url,
            timeout=30.0,
            max_retries=5,
            max_pages=100,
        ) as client:
            logger.info(
                "client_initialized",
                timeout=30.0,
                max_retries=5,
                max_pages=100,
            )

            context = Services(client=client)
            logger.info("server_ready", version=__version__)
            yield context

    except ValueError as e:
        # Authentication or configuration errors
        logger.error("initialization_failed", error_type="ValueError", error=str(e))
        raise
    except Exception as e:
        # Unexpected errors during initialization
        # Note: exc_info intentionally omitted to avoid leaking file paths and
        # module internals in production logs. The exception is re-raised for
        # the caller to handle debugging.
        logger.error(
            "initialization_failed",
            error_type=type(e).__name__,
            error=str(e),
        )
        raise
    finally:
        logger.info("server_shutting_down")


def _build_auth() -> "AuthProvider | None":
    """Build auth provider from environment configuration.

    Supports two modes, selected by environment variables:
    - MCP_AUTH_TOKEN: Simple bearer token auth (dev/personal use)
    - MCP_GITHUB_CLIENT_ID + MCP_GITHUB_CLIENT_SECRET + MCP_BASE_URL: GitHub OAuth

    Returns None when no auth env vars are set (unauthenticated).
    """
    github_id = os.getenv("MCP_GITHUB_CLIENT_ID")
    github_secret = os.getenv("MCP_GITHUB_CLIENT_SECRET")
    base_url = os.getenv("MCP_BASE_URL")

    github_vars = {
        "MCP_GITHUB_CLIENT_ID": github_id,
        "MCP_GITHUB_CLIENT_SECRET": github_secret,
        "MCP_BASE_URL": base_url,
    }
    if all(github_vars.values()):
        from fastmcp.server.auth.providers.github import GitHubProvider

        return GitHubProvider(
            client_id=github_id,  # type: ignore[arg-type]
            client_secret=github_secret,  # type: ignore[arg-type]
            base_url=base_url,  # type: ignore[arg-type]
        )
    if any(github_vars.values()):
        missing = [k for k, v in github_vars.items() if not v]
        logger.warning(
            "incomplete_github_oauth_config",
            missing=missing,
            msg="Set all three vars for GitHub OAuth, or remove them for bearer token",
        )

    token = os.getenv("MCP_AUTH_TOKEN")
    if token:
        from fastmcp.server.auth import StaticTokenVerifier

        return StaticTokenVerifier(
            tokens={token: {"client_id": "statuspro-mcp", "scopes": ["all"]}},
        )

    return None


_auth = _build_auth()

# Initialize FastMCP server with lifespan management
mcp = FastMCP(
    name="statuspro-erp",
    version=__version__,
    lifespan=lifespan,
    auth=_auth,
    instructions="""\
StatusPro MCP Server — Read and update order status via the StatusPro API.

## Domain Model

- **Orders** are identified by a large integer `id` (e.g. 6110375248088) and have a human-readable `name` (e.g. "#1188") and an `order_number`.
- Each order has one **status** (a `Status` code + display name) plus `due_date` and `due_date_to` timestamps.
- **Statuses** are defined per-tenant with a unique 8-char `code` (e.g. "st000002"), a color, and optional public name/description.
- Not every status is a valid transition from the current order state — call `get_viable_statuses` before calling `update_order_status`.

## Tool Selection Guide

**Finding orders:**
  list_orders (filter by status, date range, tags; `search` matches order number, name, or customer fields) | get_order (by id)

**Changing status:**
  get_viable_statuses → update_order_status
  bulk_update_order_status (up to 50 orders at once)

**Other updates:**
  add_order_comment | update_order_due_date

## Safety Pattern

All mutation tools use a confirm=false/true pattern:
1. Call with confirm=false — returns a preview (no changes made)
2. Call with confirm=true — executes the operation

Per the MCP Tools spec (Security Considerations, 2025-11-25), the host —
not the server — drives user confirmation. Every mutation tool sets the
`destructiveHint` annotation, which is the canonical signal for hosts to
prompt the user. The Prefab Confirm button on each preview UI directly
re-invokes the tool with confirm=true via the MCP Apps `tools/call`
channel.

## Rate Limits

StatusPro documents rate limits per-endpoint in its API reference:
- Most endpoints: 60 requests/minute
- `add_order_comment` and `bulk_update_order_status`: 5 requests/minute

The client automatically retries with exponential backoff on 429 responses.

## Resources

- statuspro://statuses — full status catalog with codes and colors
- statuspro://help — tool reference
""",
)

# Add response caching middleware with TTLs for read-only tools
_READ_ONLY_TOOLS = [
    "list_orders",
    "list_orders_in_workflow",
    "get_order",
    "get_order_history",
    "get_orders_batch",
    "lookup_orders_batch",
    "summarize_active_orders",
    "list_statuses",
    "get_viable_statuses",
]

mcp.add_middleware(
    ResponseCachingMiddleware(
        cache_storage=MemoryStore(),
        call_tool_settings=CallToolSettings(
            ttl=30,
            included_tools=_READ_ONLY_TOOLS,
        ),
        read_resource_settings=ReadResourceSettings(ttl=60),
    )
)
logger.info(
    "middleware_added",
    middleware="ResponseCachingMiddleware",
    storage="MemoryStore",
    cached_tools=_READ_ONLY_TOOLS,
    tool_ttl=30,
    resource_ttl=60,
)

# Register all tools, resources, and prompts with the mcp instance
# This must come after mcp initialization
from statuspro_mcp.prompts import register_all_prompts  # noqa: E402
from statuspro_mcp.resources import register_all_resources  # noqa: E402
from statuspro_mcp.tools import register_all_tools  # noqa: E402

register_all_tools(mcp)
register_all_resources(mcp)
register_all_prompts(mcp)


def main(
    transport: Literal["stdio", "http", "sse", "streamable-http"] = "stdio",
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    """Main entry point for the StatusPro MCP Server.

    This function is called when running the server via:
    - uvx statuspro-mcp-server
    - python -m statuspro_mcp
    - statuspro-mcp-server (console script)

    Args:
        transport: Transport protocol ("stdio", "sse", or "http"). Default: "stdio"
        host: Host to bind to for HTTP/SSE transports. Default: "127.0.0.1"
        port: Port to bind to for HTTP/SSE transports. Default: 8765
    """
    logger.info(
        "server_starting",
        version=__version__,
        transport=transport,
        host=host,
        port=port,
    )
    if _auth is not None:
        provider = type(_auth).__name__
        logger.info("auth_configured", provider=provider)
    elif transport != "stdio":
        logger.warning(
            "no_auth_configured",
            transport=transport,
            msg="MCP endpoint is unauthenticated — set MCP_AUTH_TOKEN or "
            "MCP_GITHUB_CLIENT_ID + MCP_GITHUB_CLIENT_SECRET",
        )
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=transport, host=host, port=port)


if __name__ == "__main__":
    main()
