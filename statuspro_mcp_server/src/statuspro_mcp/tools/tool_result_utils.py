"""Utilities for creating ToolResult responses for MCP tools.

Tools emit two pieces of data per call:

- ``content`` — the LLM's model context, served as ``response.model_dump_json()``
  so the structured response is the model's view. Per the MCP spec,
  ``structuredContent`` is "not added to model context" so we can't rely on it
  to inform the LLM; the JSON dump in ``content`` is what Claude actually sees.
- ``structured_content`` — for UI binding only. When a tool returns a Prefab
  ``ui`` argument, this is the PrefabApp itself; FastMCP's ``ToolResult.__init__``
  converts it to the Prefab wire envelope via ``_prefab_to_json``. Without
  ``ui``, this is ``response.model_dump()`` for any programmatic caller that
  reads structured fields directly.

Tool registrations that want interactive UI rendering pass ``meta=UI_META``
on ``@mcp.tool(...)``. FastMCP 3.x's ``_maybe_apply_prefab_ui`` expands that
into the spec-required ``_meta.ui = {"resourceUri": ..., "csp": ...}`` and
auto-registers the Prefab renderer as a ``ui://`` resource. Claude Desktop
(and other MCP Apps hosts) then renders the UI in a sandboxed iframe via
``ui/notifications/tool-result``.

Reference: SEP-1865 / MCP Apps spec; mirrors the post-#422 pattern from
``katana-openapi-client@ca986527``. The previous Jinja-template-based
markdown rendering path was removed — every reference MCP server (e.g.
``modelcontextprotocol/ext-apps/examples/customer-segmentation``,
``system-monitor``) emits raw JSON content for the same reason.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from fastmcp.tools import ToolResult
from pydantic import BaseModel

if TYPE_CHECKING:
    from prefab_ui.app import PrefabApp


# Opt-in marker for Prefab UI rendering. Pass as ``meta=UI_META`` in
# ``@mcp.tool(...)``. FastMCP 3.x's ``_maybe_apply_prefab_ui`` expands this
# into the spec-required ``_meta.ui`` resource pointer; tools without the
# marker ship JSON content + structured_content but no interactive UI.
UI_META: dict[str, Any] = {"ui": True}


def enum_to_str(value: Any) -> str | None:
    """Extract the string value from an enum, or return as-is.

    Handles the common case where an attrs model field may be a StrEnum,
    a plain string, or None. Pattern: `enum_to_str(status)` instead of
    `status.value if hasattr(status, "value") else status`.
    """
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


def iso_or_none(dt: datetime | None) -> str | None:
    """Format a datetime as ISO 8601, or return None.

    Shorthand for `dt.isoformat() if dt else None`.
    """
    return dt.isoformat() if dt else None


def make_tool_result(
    response: BaseModel,
    *,
    ui: PrefabApp | None = None,
) -> ToolResult:
    """Create a ToolResult with JSON content and optional Prefab UI binding.

    Always emits ``response.model_dump_json(indent=2)`` as ``content`` — the
    LLM's view of the structured response. When ``ui`` is provided, the
    PrefabApp goes into ``structured_content`` for FastMCP's auto-detection
    to convert into the Prefab wire envelope; UI-capable hosts (Claude
    Desktop) render the iframe via the canonical MCP Apps resource path.
    Without ``ui``, structured_content is ``response.model_dump()`` so
    programmatic callers can read fields directly.

    Args:
        response: Pydantic model response from the tool.
        ui: Optional PrefabApp for MCP Apps rendering. Tool registration
            must include ``meta=UI_META`` for the host to know to render it.

    Returns:
        ToolResult with JSON content and (Prefab or dict) structured_content.
    """
    return ToolResult(
        content=response.model_dump_json(indent=2),
        structured_content=ui if ui is not None else response.model_dump(),
    )


def make_simple_result(
    message: str,
    structured_data: dict[str, Any] | None = None,
) -> ToolResult:
    """Create a simple ToolResult with a message.

    For simple responses where a Pydantic model isn't appropriate.

    Args:
        message: The message to display
        structured_data: Optional structured data dict

    Returns:
        ToolResult with message as content
    """
    return ToolResult(
        content=message,
        structured_content=structured_data or {},
    )
