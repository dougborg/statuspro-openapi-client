"""Domain model for StatusPro status definitions.

Matches the OpenAPI ``StatusDefinition`` schema (returned by ``/statuses``)
and is structurally identical to ``ViableStatus`` (returned by
``/orders/{id}/viable-statuses``).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Status(BaseModel):
    """A top-level status definition from the account's status catalog."""

    code: str = Field(..., description="8-char code, e.g. 'st000002'")
    name: str | None = None
    description: str | None = None
    color: str | None = Field(
        None, description="Display color, either a name (e.g. 'pink') or hex"
    )

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        extra="ignore",
    )


__all__ = ["Status"]
