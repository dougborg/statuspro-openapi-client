"""Generic conversion utilities for attrs API models.

These helpers bridge the attrs-based generated models (which use ``UNSET`` for
unprovided fields) and Pydantic domain models (which use ``None``).
"""

from __future__ import annotations

from typing import overload

from ..client_types import UNSET, Unset


def to_unset[T](value: T | None) -> T | Unset:
    """Convert None to UNSET sentinel value.

    Useful when building attrs API request models from optional Pydantic fields,
    where None means "not provided" and should be sent as UNSET to avoid
    overwriting existing values.

    Args:
        value: Value that might be None

    Returns:
        The value unchanged if not None, or UNSET if None

    Example:
        ```python
        from statuspro_public_api_client.domain.converters import to_unset

        to_unset(42)  # 42
        to_unset(None)  # UNSET
        to_unset("USD")  # "USD"
        ```
    """
    return UNSET if value is None else value


@overload
def unwrap_unset[T](value: T | Unset | None) -> T | None: ...


@overload
def unwrap_unset[T](value: T | Unset | None, default: T) -> T: ...


def unwrap_unset[T](value: T | Unset | None, default: T | None = None) -> T | None:
    """Unwrap an Unset or None sentinel value.

    Args:
        value: Value that might be Unset or None
        default: Default value to return if Unset or None

    Returns:
        The unwrapped value, or default if value is Unset or None. When a
        non-None default is provided, the return type is narrowed to ``T``
        (never None).

    Example:
        ```python
        from statuspro_public_api_client.client_types import UNSET

        unwrap_unset(42)  # 42
        unwrap_unset(UNSET)  # None
        unwrap_unset(UNSET, 0)  # 0
        unwrap_unset(None, 0)  # 0
        ```
    """
    if value is None or isinstance(value, Unset):
        return default
    return value
