"""Utility functions for working with StatusPro API responses.

Helpers for unwrapping generated responses, extracting data, and raising typed
errors on API failures.
"""

from __future__ import annotations

from collections.abc import Callable
from http import HTTPStatus
from typing import Any, overload

from .client_types import Response, Unset
from .domain.converters import unwrap_unset
from .models.error_response import ErrorResponse
from .models.validation_error_response import ValidationErrorResponse


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int,
        error_response: ErrorResponse | ValidationErrorResponse | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error_response = error_response


class AuthenticationError(APIError):
    """Raised when authentication fails (401)."""


class ValidationError(APIError):
    """Raised when request validation fails (422).

    The ``validation_errors`` attribute is a ``dict[str, list[str]]`` mapping
    field name to the list of human-readable error messages that StatusPro
    returned for that field.
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        error_response: ValidationErrorResponse | None = None,
    ):
        super().__init__(message, status_code, error_response)
        errors = getattr(error_response, "errors", None)
        self.validation_errors: dict[str, list[str]] = unwrap_unset(errors, {}) or {}

    def __str__(self) -> str:
        msg = super().__str__()
        if self.validation_errors:
            lines = [
                f"  {field}: {'; '.join(errs)}"
                for field, errs in self.validation_errors.items()
            ]
            msg += "\n" + "\n".join(lines)
        return msg


class RateLimitError(APIError):
    """Raised when rate limit is exceeded (429)."""


class ServerError(APIError):
    """Raised when a server error occurs (5xx)."""


@overload
def unwrap[T](response: Response[T], *, raise_on_error: bool = True) -> T: ...


@overload
def unwrap[T](response: Response[T], *, raise_on_error: bool = False) -> T | None: ...


def unwrap[T](response: Response[T], *, raise_on_error: bool = True) -> T | None:
    """Unwrap a Response and return parsed data, raising typed errors on failure.

    Args:
        response: Response object from a generated API call.
        raise_on_error: If True (default), raise an APIError subclass for non-2xx
            responses; if False, return None.

    Returns:
        The parsed response body.

    Raises:
        AuthenticationError: 401
        ValidationError: 422
        RateLimitError: 429
        ServerError: 5xx
        APIError: other non-2xx statuses
    """
    if response.parsed is None:
        if raise_on_error:
            raise APIError(
                f"No parsed response data for status {response.status_code}",
                response.status_code,
            )
        return None

    parsed = response.parsed
    if isinstance(parsed, ErrorResponse | ValidationErrorResponse):
        if not raise_on_error:
            return None

        message_raw = getattr(parsed, "message", None)
        error_message = (
            message_raw
            if isinstance(message_raw, str) and message_raw
            else "No error message provided"
        )

        status = response.status_code
        if status == HTTPStatus.UNAUTHORIZED:
            raise AuthenticationError(error_message, status, parsed)
        if status == HTTPStatus.UNPROCESSABLE_ENTITY:
            detailed = parsed if isinstance(parsed, ValidationErrorResponse) else None
            raise ValidationError(error_message, status, detailed)
        if status == HTTPStatus.TOO_MANY_REQUESTS:
            raise RateLimitError(error_message, status, parsed)
        if 500 <= status < 600:
            raise ServerError(error_message, status, parsed)
        raise APIError(error_message, status, parsed)

    return response.parsed


@overload
def unwrap_data[T](
    response: Response[T], *, raise_on_error: bool = True, default: None = None
) -> Any: ...


@overload
def unwrap_data[T](
    response: Response[T], *, raise_on_error: bool = False, default: None = None
) -> Any | None: ...


@overload
def unwrap_data[T, DataT](
    response: Response[T],
    *,
    raise_on_error: bool = False,
    default: list[DataT],
) -> Any: ...


def unwrap_data[T, DataT](
    response: Response[T],
    *,
    raise_on_error: bool = True,
    default: list[DataT] | None = None,
) -> Any | None:
    """Unwrap a list response and extract the ``data`` array.

    For StatusPro's wrapped list endpoints like ``GET /orders`` which return
    ``{"data": [...], "meta": {...}}``. For raw-array endpoints like
    ``GET /statuses``, use ``unwrap()`` directly — the parsed response is the
    list itself.
    """
    try:
        parsed = unwrap(response, raise_on_error=raise_on_error)
    except APIError:
        if raise_on_error:
            raise
        return default

    if parsed is None:
        return default

    # If the parsed result is already a list, return it directly
    if isinstance(parsed, list):
        return parsed

    data = getattr(parsed, "data", None)
    if isinstance(data, Unset):
        return default if default is not None else []
    if data is not None:
        return data

    if default is not None:
        return default
    return [parsed]


def is_success(response: Response[Any]) -> bool:
    """True if the response has a 2xx status code."""
    return 200 <= response.status_code < 300


def is_error(response: Response[Any]) -> bool:
    """True if the response has a 4xx or 5xx status code."""
    return response.status_code >= 400


@overload
def unwrap_as[T, ExpectedT](
    response: Response[T],
    expected_type: type[ExpectedT],
    *,
    raise_on_error: bool = True,
) -> ExpectedT: ...


@overload
def unwrap_as[T, ExpectedT](
    response: Response[T],
    expected_type: type[ExpectedT],
    *,
    raise_on_error: bool = False,
) -> ExpectedT | None: ...


def unwrap_as[T, ExpectedT](
    response: Response[T],
    expected_type: type[ExpectedT],
    *,
    raise_on_error: bool = True,
) -> ExpectedT | None:
    """Unwrap and assert the parsed body is of the expected type."""
    result = unwrap(response, raise_on_error=raise_on_error)
    if result is None:
        if raise_on_error:
            raise TypeError(
                f"Expected {expected_type.__name__}, got None from response"
            )
        return None
    if not isinstance(result, expected_type):
        raise TypeError(
            f"Expected {expected_type.__name__}, got {type(result).__name__}"
        )
    return result


def get_error_message[T](response: Response[T]) -> str | None:
    """Extract ``message`` from an error response, if present."""
    if response.parsed is None:
        return None

    parsed = response.parsed
    if not isinstance(parsed, ErrorResponse | ValidationErrorResponse):
        return None

    message_raw = getattr(parsed, "message", None)
    return message_raw if isinstance(message_raw, str) and message_raw else None


def handle_response[T](
    response: Response[T],
    *,
    on_success: Callable[[T], Any] | None = None,
    on_error: Callable[[APIError], Any] | None = None,
    raise_on_error: bool = False,
) -> Any:
    """Call on_success with parsed data for 2xx, on_error with an APIError otherwise."""
    try:
        data = unwrap(response, raise_on_error=True)
        if on_success:
            return on_success(data)
        return data
    except APIError as e:
        if raise_on_error:
            raise
        if on_error:
            return on_error(e)
        return None


__all__ = [
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "ServerError",
    "ValidationError",
    "get_error_message",
    "handle_response",
    "is_error",
    "is_success",
    "unwrap",
    "unwrap_as",
    "unwrap_data",
]
