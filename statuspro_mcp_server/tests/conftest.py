"""Shared pytest fixtures for MCP server tests."""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def statuspro_context():
    """Context fixture backed by a real StatusProClient for integration tests.

    Skipped when STATUSPRO_API_KEY is not set.
    """
    api_key = os.getenv("STATUSPRO_API_KEY")
    if not api_key:
        pytest.skip("STATUSPRO_API_KEY not set - skipping integration test")

    try:
        from statuspro_public_api_client import StatusProClient
    except ImportError:
        pytest.skip("statuspro_public_api_client not installed")

    context = MagicMock()
    mock_request_context = MagicMock()
    mock_lifespan_context = MagicMock()

    base_url = os.getenv("STATUSPRO_BASE_URL", "https://app.orderstatuspro.com/api/v1")
    client = StatusProClient(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,
        max_retries=3,
        max_pages=10,
    )

    mock_lifespan_context.client = client
    mock_request_context.lifespan_context = mock_lifespan_context
    context.request_context = mock_request_context

    yield context


def create_mock_context(elicit_confirm: bool = True):
    """Build a mock FastMCP context for unit tests.

    Args:
        elicit_confirm: If True, elicit() returns an accepted confirm=True result.
                       If False, elicit() returns a declined result.

    Returns:
        Tuple of (context, lifespan_context).
    """
    context = MagicMock()
    mock_request_context = MagicMock()
    mock_lifespan_context = MagicMock()
    context.request_context = mock_request_context
    mock_request_context.lifespan_context = mock_lifespan_context

    mock_elicit_result = MagicMock()
    if elicit_confirm:
        mock_elicit_result.action = "accept"
        mock_elicit_result.data = MagicMock()
        mock_elicit_result.data.confirm = True
    else:
        mock_elicit_result.action = "decline"
        mock_elicit_result.data = None

    context.elicit = AsyncMock(return_value=mock_elicit_result)

    return context, mock_lifespan_context


@pytest.fixture
def mock_context():
    """Mock FastMCP context fixture."""
    return create_mock_context()
