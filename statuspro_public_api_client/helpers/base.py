"""Base class for domain classes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from statuspro_public_api_client.statuspro_client import StatusProClient


class Base:
    """Base class for all domain classes.

    Provides common functionality and access to the StatusProClient instance.

    Args:
        client: The StatusProClient instance to use for API calls.
    """

    def __init__(self, client: StatusProClient) -> None:
        """Initialize with a client instance.

        Args:
            client: The StatusProClient instance to use for API calls.
        """
        self._client = client
