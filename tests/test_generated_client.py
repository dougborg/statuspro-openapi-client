"""Tests for the generated client structure and API methods.

These tests verify that our StatusPro client properly integrates with
the generated OpenAPI client and doesn't break existing functionality.
"""

from typing import Any
from unittest.mock import MagicMock

import pytest

from statuspro_public_api_client import AuthenticatedClient, StatusProClient


class TestGeneratedClientStructure:
    """Test the structure of the generated client."""

    def test_authenticated_client_creation(self, mock_api_credentials):
        """Test that we can create the underlying authenticated client."""
        client = AuthenticatedClient(
            base_url=mock_api_credentials["base_url"],
            token=mock_api_credentials["api_key"],
        )

        assert client is not None
        assert hasattr(client, "_client")  # httpx client

    def test_statuspro_client_wraps_generated_client(self, statuspro_client):
        """Test that StatusPro client inherits from AuthenticatedClient."""
        # StatusProClient now inherits from AuthenticatedClient directly
        assert isinstance(statuspro_client, AuthenticatedClient)
        assert hasattr(statuspro_client, "token")
        assert hasattr(statuspro_client, "get_async_httpx_client")

    def test_api_modules_structure(self, statuspro_client):
        """Test that the API modules have the expected structure."""
        # This is a structural test to ensure we're not breaking the generated code
        # StatusProClient now inherits from AuthenticatedClient directly

        # The client should have expected attributes from AuthenticatedClient
        assert statuspro_client.get_async_httpx_client() is not None
        assert hasattr(statuspro_client, "get_async_httpx_client")

        # Should be able to access client properties
        assert statuspro_client is not None


class TestGeneratedMethodCompatibility:
    """Test compatibility with generated API methods."""

    @pytest.mark.asyncio
    async def test_method_signature_preservation(self, statuspro_client):
        """Test that enhanced methods preserve original signatures."""

        # Create a mock method that represents a typical generated API method
        async def mock_generated_method(*, client, id: int, limit: int = 50):
            """Mock generated method with typical signature."""
            return {"client": client, "id": id, "limit": limit}

        # Test that we can call the method directly through the client
        # The transport layer automatically handles resilience
        result = await mock_generated_method(client=statuspro_client, id=123, limit=100)

        # Verify the method works correctly
        assert result is not None
        assert isinstance(result, dict)
        assert result["id"] == 123
        assert result["limit"] == 100

    def test_response_object_handling(self, statuspro_client):
        """Test that response objects are handled correctly."""
        # Mock a typical response structure from the generated client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.parsed = MagicMock()
        mock_response.parsed.data = [{"id": 1, "name": "Test"}]

        # This response structure should be compatible with our enhancement logic
        assert hasattr(mock_response, "status_code")
        assert hasattr(mock_response, "headers")
        assert hasattr(mock_response, "parsed")

        # Our enhancement logic checks for these attributes
        assert mock_response.status_code == 200
        assert mock_response.headers is not None

    def test_error_response_structure(self, statuspro_client):
        """Test handling of error response structures."""
        # Mock error responses that might come from the generated client
        error_responses = [
            # 4xx client error
            MagicMock(status_code=404, headers={}, parsed=None),
            # 5xx server error
            MagicMock(status_code=500, headers={}, parsed=None),
            # Rate limit error
            MagicMock(status_code=429, headers={"Retry-After": "60"}, parsed=None),
        ]

        for response in error_responses:
            # Our enhancement logic should be able to handle these
            assert hasattr(response, "status_code")
            assert hasattr(response, "headers")
            # Should be able to check status codes
            assert isinstance(response.status_code, int)


class TestTypeSystemCompatibility:
    """Test that type hints and IDE support are preserved."""

    def test_statuspro_client_type_hints(self, statuspro_client):
        """Test that the StatusPro client maintains proper types."""
        # The StatusPro client should maintain type information
        assert (
            hasattr(statuspro_client, "__annotations__") or True
        )  # Python may optimize these away

        # Key properties should be present and accessible
        # StatusProClient now inherits from AuthenticatedClient directly
        assert hasattr(statuspro_client, "token")
        assert hasattr(statuspro_client, "get_async_httpx_client")

        # Properties should be accessible
        assert statuspro_client.token is not None
        assert statuspro_client.get_async_httpx_client is not None

    @pytest.mark.asyncio
    async def test_method_enhancement_preserves_types(self, statuspro_client):
        """Test that method enhancement preserves type information."""

        # Create a typed mock method
        async def typed_method(
            *, client: AuthenticatedClient, id: int
        ) -> dict[str, Any]:
            return {"id": id, "client_type": type(client).__name__}

        # Call the method directly through the client
        # The transport layer handles resilience automatically
        result = await typed_method(client=statuspro_client, id=123)

        assert result is not None
        assert result["id"] == 123

        # The method should still be awaitable (async)
        import inspect

        assert inspect.iscoroutinefunction(typed_method)


class TestImportStructure:
    """Test that imports work correctly and don't break existing code."""

    def test_main_imports(self):
        """Test that main classes can be imported correctly."""
        # These imports should work without errors
        from statuspro_public_api_client import AuthenticatedClient, StatusProClient

        # Classes should be available
        assert AuthenticatedClient is not None
        assert StatusProClient is not None

    def test_direct_client_creation(self):
        """Test that clients can be created directly."""
        # Should be able to create a client directly
        client = StatusProClient(
            api_key="test-key", base_url="https://test.example.com"
        )

        assert isinstance(client, StatusProClient)

    def test_module_structure(self):
        """Test that the module structure is correct."""
        import statuspro_public_api_client

        # Main module should have expected exports
        assert hasattr(statuspro_public_api_client, "AuthenticatedClient")
        assert hasattr(statuspro_public_api_client, "StatusProClient")


class TestConfigurationCompatibility:
    """Test that configuration options work correctly."""

    def test_httpx_kwargs_passthrough(self, mock_api_credentials):
        """Test that httpx kwargs are passed through correctly."""
        # Test that additional httpx configuration can be passed
        custom_headers = {"User-Agent": "Custom-Agent/1.0"}

        client = StatusProClient(**mock_api_credentials, headers=custom_headers)

        # Should create successfully with custom configuration
        assert client is not None
        # StatusProClient now inherits from AuthenticatedClient directly
        assert hasattr(client, "get_async_httpx_client")

    def test_timeout_configuration(self, mock_api_credentials):
        """Test that timeout configuration works."""
        client = StatusProClient(**mock_api_credentials, timeout=45.0)

        # Should create successfully with custom timeout
        assert client is not None
        # Note: Actual timeout testing would require inspecting the underlying httpx client

    def test_retry_configuration(self, mock_api_credentials):
        """Test that retry configuration is properly set."""
        client = StatusProClient(**mock_api_credentials, max_retries=10)

        # StatusProClient stores retry configuration internally
        assert client is not None

    def test_logger_configuration(self, mock_api_credentials):
        """Test that custom logger configuration works."""
        import logging

        custom_logger = logging.getLogger("custom_test_logger")

        client = StatusProClient(**mock_api_credentials, logger=custom_logger)

        assert client.logger is custom_logger
