"""Tests for MCP Apps (SEP-1865) UI integration.

When tools are registered with ``meta=UI_META`` (i.e. ``{"ui": True}``),
fastmcp's ``_maybe_apply_prefab_ui`` hook does two things:

1. Registers a per-tool Prefab renderer resource at
   ``ui://prefab/tool/<hash>/renderer.html`` with
   ``mimeType: text/html;profile=mcp-app`` (each UI-marked tool gets its
   own resource — fastmcp 3.x assigns a stable per-tool hash).
2. Expands the marker into the spec-compliant
   ``_meta.ui = {"resourceUri": "ui://prefab/tool/<hash>/renderer.html"}``
   shape on the tool definition.

These tests guard the contract: every UI-marked tool should surface a
renderer in resources/list AND have its ``_meta.ui.resourceUri`` pointing
at the matching renderer. Hosts advertising the
``io.modelcontextprotocol/ui`` capability use these signals to load the
renderer iframe and route ``ui/notifications/tool-result`` to it.

Mirrors the post-#422 contract from ``katana-openapi-client@ca986527``,
adapted for the per-tool renderer registration in our fastmcp/prefab-ui
versions.
"""

from __future__ import annotations

import re

import pytest

# Tools registered with meta=UI_META in tools/*.py. Hard-coded rather than
# discovered so a regression that drops UI_META from a tool surfaces as a
# missing test, not a silently-passing zero.
UI_TOOL_NAMES = {
    "list_orders",
    "list_orders_in_workflow",
    "get_order",
    "update_order_status",
    "add_order_comment",
    "update_order_due_date",
    "bulk_update_order_status",
    "get_viable_statuses",
}

# Match any ``ui://prefab/.../renderer.html`` shape. The path between
# ``prefab/`` and ``/renderer.html`` is an internal fastmcp/prefab-ui detail
# (currently ``tool/<hex-hash>``) that could legitimately change across
# versions without breaking the contract; the contract we actually care about
# is the ``ui://`` scheme + ``renderer.html`` suffix + the URI being present
# in ``resources/list`` so the host can fetch it.
PREFAB_RENDERER_URI_PATTERN = re.compile(r"^ui://prefab/.+/renderer\.html$")
MCP_APP_MIME_TYPE = "text/html;profile=mcp-app"


@pytest.fixture(scope="module")
def server_tools():
    """Resolve the registered tools from the configured mcp instance."""
    import asyncio

    from statuspro_mcp.server import mcp

    return asyncio.run(_collect_tools(mcp))


@pytest.fixture(scope="module")
def server_resources():
    """Resolve the registered resources from the configured mcp instance.

    Returned as a list (not a dict) so duplicate registrations of the same
    URI surface as duplicate entries.
    """
    import asyncio

    from statuspro_mcp.server import mcp

    return asyncio.run(_collect_resources(mcp))


async def _collect_tools(mcp):
    return {t.name: t for t in await mcp.list_tools()}


async def _collect_resources(mcp):
    return list(await mcp.list_resources())


def test_one_renderer_resource_per_ui_marked_tool(server_resources):
    """The bundled Prefab renderer is registered once per UI-marked tool.
    Asserts the count matches the UI tool list — a missing renderer means a
    UI tool's iframe couldn't load; an extra one means duplicate registration."""
    renderers = [
        r for r in server_resources if PREFAB_RENDERER_URI_PATTERN.match(str(r.uri))
    ]
    assert len(renderers) == len(UI_TOOL_NAMES), (
        f"Expected {len(UI_TOOL_NAMES)} prefab renderer resources (one per "
        f"UI-marked tool), found {len(renderers)}. Renderers: "
        f"{[str(r.uri) for r in renderers]}"
    )


def test_each_renderer_resource_has_correct_mime_type(server_resources):
    """Hosts route on ``mimeType == text/html;profile=mcp-app`` to identify
    MCP Apps content. A bare ``text/html`` would render outside the
    sandboxed iframe path."""
    renderers = [
        r for r in server_resources if PREFAB_RENDERER_URI_PATTERN.match(str(r.uri))
    ]
    for r in renderers:
        assert r.mime_type == MCP_APP_MIME_TYPE, (
            f"{r.uri}: mime_type={r.mime_type!r}; expected {MCP_APP_MIME_TYPE!r}"
        )


@pytest.mark.parametrize("tool_name", sorted(UI_TOOL_NAMES))
def test_ui_marked_tools_expose_resource_uri(server_tools, server_resources, tool_name):
    """fastmcp expands ``meta={'ui': True}`` to the full ``_meta.ui`` shape
    the spec defines. Hosts read ``_meta.ui.resourceUri`` to decide which
    UI resource to load for this tool. Asserts the URI also exists in
    resources/list — a meta pointing at a non-registered URI would 404 on
    fetch and break the renderer."""
    assert tool_name in server_tools, (
        f"Tool {tool_name!r} not registered. The UI_TOOL_NAMES list in this "
        "test file should be kept in sync with tools/*.py registrations."
    )
    tool = server_tools[tool_name]
    assert tool.meta is not None, (
        f"{tool_name} has no meta. Register with meta=UI_META in tools/*.py."
    )

    ui_meta = tool.meta.get("ui")
    assert isinstance(ui_meta, dict), (
        f"{tool_name}: meta['ui'] = {ui_meta!r}; expected fastmcp to expand "
        "True → {'resourceUri': ...}. Check fastmcp version is >=3.0 (the "
        "auto-expansion lives there)."
    )

    resource_uri = ui_meta.get("resourceUri")
    assert PREFAB_RENDERER_URI_PATTERN.match(str(resource_uri)), (
        f"{tool_name}: resourceUri={resource_uri!r} doesn't match expected "
        f"prefab renderer pattern {PREFAB_RENDERER_URI_PATTERN.pattern!r}"
    )

    # The URI in meta must actually exist in resources/list. Otherwise the
    # host fetches it and gets a 404, the iframe renders broken.
    registered_uris = {str(r.uri) for r in server_resources}
    assert str(resource_uri) in registered_uris, (
        f"{tool_name}: resourceUri={resource_uri} not registered in "
        "resources/list. fastmcp's _ensure_prefab_renderer should have "
        "registered it when the tool was applied."
    )
