"""StatusPro Public API Client — Python client for the StatusPro API."""

from .client import AuthenticatedClient, Client
from .statuspro_client import StatusProClient
from .utils import (
    APIError,
    AuthenticationError,
    RateLimitError,
    ServerError,
    ValidationError,
    get_error_message,
    handle_response,
    is_error,
    is_success,
    unwrap,
    unwrap_as,
    unwrap_data,
)

__all__ = [
    "APIError",
    "AuthenticatedClient",
    "AuthenticationError",
    "Client",
    "RateLimitError",
    "ServerError",
    "StatusProClient",
    "ValidationError",
    "get_error_message",
    "handle_response",
    "is_error",
    "is_success",
    "unwrap",
    "unwrap_as",
    "unwrap_data",
]
