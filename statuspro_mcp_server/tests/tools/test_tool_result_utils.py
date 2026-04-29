"""Tests for tool_result_utils — specifically the make_tool_result contract
around Prefab UI delivery.

make_tool_result is load-bearing for every tool that emits a Prefab UI:
- ``content`` is always ``response.model_dump_json(indent=2)`` — the LLM's
  view of the structured response.
- when ``ui`` is None, structured_content must be the Pydantic model dump
  so programmatic callers can read fields directly.
- when ``ui`` is a PrefabApp, structured_content must end up as a dict that
  represents the Prefab wire envelope (FastMCP's ToolResult.__init__ handles
  the conversion via _prefab_to_json on isinstance check).

A regression in either shape would silently break MCP-Apps rendering in
Claude Desktop. Mirrors the post-#422 / SEP-1865 contract from
``katana-openapi-client@ca986527``.
"""

from __future__ import annotations

import json

from prefab_ui.app import PrefabApp
from prefab_ui.components import Text
from pydantic import BaseModel
from statuspro_mcp.tools.tool_result_utils import UI_META, make_tool_result


class _StubResponse(BaseModel):
    id: int
    label: str


def _make_response() -> _StubResponse:
    return _StubResponse(id=42, label="hello")


def test_make_tool_result_emits_json_content():
    """``content`` should be the Pydantic JSON dump — that's the model context."""
    response = _make_response()
    result = make_tool_result(response)
    assert isinstance(result.content, list)
    assert len(result.content) == 1
    text_block = result.content[0]
    parsed = json.loads(text_block.text)
    assert parsed == {"id": 42, "label": "hello"}


def test_make_tool_result_without_ui_sets_pydantic_dump_as_structured_content():
    response = _make_response()
    result = make_tool_result(response)
    assert result.structured_content == {"id": 42, "label": "hello"}


def test_make_tool_result_with_ui_converts_prefab_to_envelope_dict():
    response = _make_response()
    with PrefabApp(state={"label": response.label}) as app:
        Text(content="{{ label }}")

    result = make_tool_result(response, ui=app)

    # FastMCP's ToolResult.__init__ detects the PrefabApp and converts it to
    # the wire-format envelope (dict). The resulting shape is not the Pydantic
    # dump — it's the Prefab app's JSON representation.
    assert isinstance(result.structured_content, dict)
    assert result.structured_content != {"id": 42, "label": "hello"}
    # The envelope carries the view definition; check one known Prefab key.
    assert "view" in result.structured_content


def test_ui_meta_is_the_opt_in_marker_for_prefab_rendering():
    # Keep UI_META's shape stable — tools pass it by reference to mcp.tool(meta=...)
    # and FastMCP's _maybe_apply_prefab_ui looks up meta.get("ui") == True.
    assert UI_META == {"ui": True}
