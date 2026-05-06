"""Reusable ``Annotated[..., Field(...)]`` aliases for MCP tool parameters.

Tool registrations push ``Field(description=...)`` metadata into the JSON
schema FastMCP advertises to clients, which gives the LLM inline guidance
about each argument. When the same parameter (``order_id``, the
``confirm`` two-step flag) appears across many tools, repeating the full
``Annotated[...]`` literal at every call site drifts: descriptions go out
of sync between siblings, the convention is harder to enforce in review,
and bare ``int`` / ``bool`` slips back in (the documented anti-pattern).

Mirrors the pattern in ``list_coercion.py``: collapse the per-field
boilerplate into a single readable token at the call site.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

OrderIdParam = Annotated[int, Field(description="StatusPro order id")]
ConfirmFlag = Annotated[bool, Field(description="Set to true to apply the change")]
