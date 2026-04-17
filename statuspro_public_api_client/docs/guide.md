# StatusProClient Guide

The **StatusProClient** is the modern, pythonic client for the StatusPro Manufacturing ERP
API. It provides automatic resilience (retries, rate limiting, error handling) using
httpx's native transport layer - no decorators or wrapper methods needed.

## 🎯 Key Features

- **🛡️ Automatic Resilience**: Transport-layer retries and rate limiting
- **🚀 Zero Configuration**: Works out of the box with environment variables
- **📦 Complete Type Safety**: Full type hints and IDE support
- **🔄 Smart Pagination**: Built-in pagination with safety limits
- **🔍 Rich Observability**: Structured logging and metrics
- **⚡ Pythonic Design**: Uses httpx's native extension points

## 🚀 Quick Start

### Installation & Setup

```bash
# Install the client
pip install -e .

# Create .env file with credentials
echo "STATUSPRO_API_KEY=your-api-key-here" > .env
echo "STATUSPRO_BASE_URL=https://app.orderstatuspro.com/api/v1" >> .env
```

### Basic Usage

```python
import asyncio

from statuspro_public_api_client import StatusProClient
from statuspro_public_api_client.api.product import get_all_products

async def main():
    # Automatic configuration from .env file
    async with StatusProClient() as client:
        # Direct API usage - automatic resilience built-in
        response = await get_all_products.asyncio_detailed(
            client=client,
            limit=50
        )

        if response.status_code == 200:
            products = response.parsed.data
            print(f"Retrieved {len(products)} products")

asyncio.run(main())
```

## 🛡️ Automatic Resilience

Every API call through `StatusProClient` automatically includes:

### Smart Retries

- **Network Errors**: Automatic retry with exponential backoff (1s, 2s, 4s, 8s, 16s)
- **Rate Limits (429)**: ALL methods (including POST/PATCH) retry with `Retry-After`
  header support
- **Server Errors (502/503/504)**: Only idempotent methods (GET, PUT, DELETE, etc.) are
  retried
- **Client Errors (4xx except 429)**: No retries

```python
async with StatusProClient(max_retries=5) as client:
    # This call will automatically retry on failures
    # POST/PATCH requests will retry on 429 but not on 5xx errors
    # GET/PUT/DELETE requests will retry on both 429 and 5xx errors
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=100
    )
    # No decorators or wrapper methods needed!
```

### Rate Limit Handling

```python
# Automatic rate limit handling with Retry-After header support
async with StatusProClient() as client:
    # These calls will automatically be rate limited
    for i in range(100):
        response = await get_all_products.asyncio_detailed(
            client=client,
            page=i,
            limit=50
        )
        # Client automatically waits when rate limited
```

### Error Recovery

```python
import logging

# Configure logging to see resilience in action
logging.basicConfig(level=logging.INFO)

async with StatusProClient() as client:
    # Automatic error recovery with detailed logging
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=100
    )
    # Logs will show retry attempts and recovery
```

## 🔄 Smart Pagination

Auto-pagination is **ON by default** for all GET requests. All pages are automatically
collected into a single response.

### Automatic Pagination (Default)

```python
async with StatusProClient() as client:
    # Get ALL products across all pages automatically
    all_products = await get_all_products.asyncio_detailed(
        client=client,
        is_sellable=True,  # API filter parameters
        limit=250  # Page size (all pages still collected)
    )
    print(f"Total products: {len(all_products.parsed.data)}")
```

### Single Page Request (Explicit Page)

To get a specific page instead of all pages, add an explicit `page` parameter. **Note:**
ANY explicit page value (including `page=1`) disables auto-pagination:

```python
async with StatusProClient() as client:
    # Get ONLY page 2 (auto-pagination disabled when page is explicit)
    page2_products = await get_all_products.asyncio_detailed(
        client=client,
        page=2,       # Explicit page disables auto-pagination
        limit=50
    )
    # Returns just the 50 items on page 2

    # page=1 ALSO disables auto-pagination (returns only first page)
    first_page = await get_all_products.asyncio_detailed(
        client=client,
        page=1,       # Get ONLY page 1, not all pages
        limit=50
    )
```

### Limiting Total Items

To limit the total number of items collected (not just page size), use the `max_items`
extension via the httpx client:

```python
async with StatusProClient() as client:
    httpx_client = client.get_async_httpx_client()
    response = await httpx_client.get(
        "/products",
        params={"limit": 50},           # 50 items per page
        extensions={"max_items": 200}   # Stop after 200 items total
    )
```

The transport intelligently adjusts the `limit` on the final request to fetch only
what's needed, avoiding over-fetching.

### Pagination Behavior Summary

| Parameter       | Scope     | Effect                                            |
| --------------- | --------- | ------------------------------------------------- |
| `limit=50`      | URL param | Page size (50 items per request)                  |
| `page=2`        | URL param | Get specific page only (disables auto-pagination) |
| `max_pages=5`   | Client    | Max pages to fetch                                |
| `max_items=200` | Extension | Max total items to collect                        |

## ⚙️ Configuration

### Authentication Methods

The client supports multiple authentication methods (in priority order):

1. **Direct parameter**: Pass `api_key` to `StatusProClient()`
1. **Environment variable**: Set `STATUSPRO_API_KEY`
1. **`.env` file**: Create a `.env` file with your credentials
1. **`~/.netrc` file**: Use standard Unix credential file

#### Using .env file (Recommended)

```bash
# Create .env file
STATUSPRO_API_KEY=your-api-key-here
STATUSPRO_BASE_URL=https://app.orderstatuspro.com/api/v1  # Optional
```

```python
# Automatically loads from .env
async with StatusProClient() as client:
    # Uses credentials from .env
    pass
```

#### Using ~/.netrc file

For centralized credential management across multiple tools:

```bash
# Add to ~/.netrc
machine app.orderstatuspro.com/api/v1
password your-api-key-here

# Set proper permissions (required)
chmod 600 ~/.netrc
```

```python
# Automatically loads from ~/.netrc
async with StatusProClient() as client:
    # Uses credentials from ~/.netrc
    pass
```

**Note**: The `password` field in netrc stores your API key (bearer token), not an
actual password. The `login` field is optional and ignored.

#### Using environment variable

```bash
export STATUSPRO_API_KEY=your-api-key-here
```

#### Using direct parameter

```python
async with StatusProClient(api_key="your-api-key-here") as client:
    # Explicit API key
    pass
```

### Custom Configuration

```python
import logging

# Custom configuration with stdlib logger
async with StatusProClient(
    api_key="custom-key",
    base_url="https://custom.statuspro.com/v1",
    timeout=60.0,           # Request timeout
    max_retries=5,          # Maximum retry attempts
    logger=logging.getLogger("custom")  # stdlib logger
) as client:
    # Your API calls here
    pass
```

The `logger` parameter accepts any object whose `debug`, `info`, `warning`, and `error`
methods accept `(msg, *args, **kwargs)` — the standard `logging.Logger` call convention.
Both `logging.Logger` and structlog's `BoundLogger` satisfy this without adapters:

```python
import structlog

# Use structlog directly — no adapter needed
logger = structlog.get_logger("statuspro")
async with StatusProClient(logger=logger) as client:
    pass
```

### Advanced httpx Configuration

```python
import httpx

# Pass through httpx configuration
async with StatusProClient(
    # Standard StatusProClient options
    api_key="your-key",
    max_retries=3,

    # httpx client options
    verify=False,           # SSL verification
    proxies="http://proxy:8080",
    headers={"Custom": "Header"},
    event_hooks={
        "request": [custom_request_hook],
        "response": [custom_response_hook]
    }
) as client:
    # Client has both resilience AND custom httpx config
    pass
```

## 🔍 Observability

### Logging

```python
import logging

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async with StatusProClient() as client:
    # All resilience actions are logged
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=100
    )
```

Example log output:

```text
2025-01-15 10:30:15 - statuspro_client - WARNING - Rate limited on attempt 1, waiting 60.0s
2025-01-15 10:31:16 - statuspro_client - INFO - Request succeeded after 2 attempts
2025-01-15 10:31:16 - statuspro_client - DEBUG - Response: 200 GET https://app.orderstatuspro.com/api/v1/products (1.24s)
```

### Custom Event Hooks

```python
async def custom_response_hook(response):
    """Custom hook to track API usage."""
    print(f"API call: {response.request.method} {response.request.url}")
    print(f"Status: {response.status_code}")

async with StatusProClient(
    event_hooks={
        "response": [custom_response_hook]
    }
) as client:
    # Your custom hooks are called alongside built-in ones
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=10
    )
```

## 🧪 Testing

### Mocking for Tests

```python
import pytest
from unittest.mock import AsyncMock, patch
from statuspro_public_api_client import StatusProClient

@pytest.mark.asyncio
async def test_api_integration():
    """Test API integration with mocked responses."""
    with patch.dict('os.environ', {'STATUSPRO_API_KEY': 'test-key'}):
        async with StatusProClient() as client:
            # Mock the underlying httpx client
            with patch.object(client, 'get_async_httpx_client') as mock_httpx:
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"data": [{"id": 1}]}

                mock_httpx.return_value.request = AsyncMock(return_value=mock_response)

                # Test your API logic here
                from statuspro_public_api_client.api.product import get_all_products
                response = await get_all_products.asyncio_detailed(
                    client=client,
                    limit=10
                )

                assert response.status_code == 200
```

### Integration Tests

```python
import os

import pytest

from statuspro_public_api_client import StatusProClient
from statuspro_public_api_client.api.product import get_all_products

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api():
    """Test against real StatusPro API (requires STATUSPRO_API_KEY)."""
    api_key = os.getenv('STATUSPRO_API_KEY')
    if not api_key:
        pytest.skip("STATUSPRO_API_KEY not set")

    async with StatusProClient() as client:
        response = await get_all_products.asyncio_detailed(
            client=client,
            limit=1
        )

        assert response.status_code == 200
        assert hasattr(response.parsed, 'data')
```

## 🔧 Advanced Patterns

### Custom Transport

```python
from statuspro_public_api_client.statuspro_client import ResilientAsyncTransport

# Create custom transport with different settings
custom_transport = ResilientAsyncTransport(
    max_retries=10,
    max_pages=50,  # Limit automatic pagination
    logger=custom_logger
)

async with StatusProClient(
    transport=custom_transport
) as client:
    # Uses your custom retry logic
    pass
```

### Batch Operations

```python
import asyncio
from statuspro_public_api_client.api.product import get_product

async def process_products_in_batches(product_ids, batch_size=10):
    """Process products in batches with automatic resilience."""
    async with StatusProClient() as client:
        results = []
        for i in range(0, len(product_ids), batch_size):
            batch = product_ids[i:i + batch_size]

            # Each call automatically has resilience
            batch_results = await asyncio.gather(*[
                get_product.asyncio_detailed(client=client, id=product_id)
                for product_id in batch
            ])

            results.extend(batch_results)

            # Be nice to the API
            await asyncio.sleep(0.1)

        return results
```

### Error Handling

```python
import httpx
from statuspro_public_api_client.errors import UnexpectedStatus

async with StatusProClient() as client:
    try:
        response = await get_all_products.asyncio_detailed(
            client=client,
            limit=50
        )

        if response.status_code == 200:
            products = response.parsed.data
            print(f"Success: {len(products)} products")
        else:
            print(f"API returned: {response.status_code}")

    except httpx.TimeoutException:
        print("Request timed out after retries")
    except httpx.ConnectError:
        print("Connection failed after retries")
    except UnexpectedStatus as e:
        print(f"Unexpected API response: {e.status_code}")
```

## 📚 Best Practices

### 1. Use Context Managers

```python
# ✅ Good: Properly manages connections
async with StatusProClient() as client:
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=50
    )

# ❌ Bad: Doesn't close connections
client = StatusProClient()
response = await get_all_products.asyncio_detailed(
    client=client,
    limit=50
)
```

### 2. Configure Appropriate Timeouts

```python
# ✅ Good: Reasonable timeout for your use case
async with StatusProClient(timeout=30.0) as client:
    # Timeout is appropriate for expected response time
    pass

# ❌ Bad: Too short timeout causes unnecessary retries
async with StatusProClient(timeout=1.0) as client:
    # Will likely timeout and retry frequently
    pass
```

### 3. Let Auto-Pagination Handle Large Datasets

```python
# ✅ Good: Auto-pagination is ON by default with safety limits
all_products = await get_all_products.asyncio_detailed(
    client=client,
    limit=250  # Sets page size; all pages collected automatically
)

# ✅ Good: Use explicit page when you need just one page
page2 = await get_all_products.asyncio_detailed(
    client=client,
    page=2,    # Explicit page = single page only
    limit=100
)

# ❌ Bad: Manual pagination loop without safety limits
page = 1
while True:  # Could run forever!
    response = await get_all_products.asyncio_detailed(
        client=client,
        page=page,
        limit=100
    )
    # ... handle response
    page += 1
```

### 4. Handle Different Response Types

```python
async with StatusProClient() as client:
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=50
    )

    # ✅ Good: Check status before accessing data
    if response.status_code == 200:
        products = response.parsed.data
        print(f"Retrieved {len(products)} products")
    elif response.status_code == 401:
        print("Authentication failed")
    else:
        print(f"Unexpected status: {response.status_code}")
```

### 5. Use Direct API Calls

```python
from statuspro_public_api_client.api.product import get_all_products

# ✅ Good: Direct API calls with automatic resilience
async with StatusProClient() as client:
    response = await get_all_products.asyncio_detailed(
        client=client,
        is_sellable=True
    )
    if response.status_code == 200:
        products = response.parsed.data
```

## 🚀 Performance Tips

### 1. Reuse Client Instances

```python
from statuspro_public_api_client.api.product import get_all_products
from statuspro_public_api_client.api.sales_order import get_all_sales_orders
from statuspro_public_api_client.api.inventory import get_all_inventory_points

# ✅ Good: One client for multiple operations
async with StatusProClient() as client:
    products = await get_all_products.asyncio_detailed(client=client)
    orders = await get_all_sales_orders.asyncio_detailed(client=client)
    inventory = await get_all_inventory_points.asyncio_detailed(client=client)

# ❌ Bad: New client for each operation
for operation in [get_all_products, get_all_sales_orders]:
    async with StatusProClient() as client:
        await operation.asyncio_detailed(client=client)
```

### 2. Optimize Page Sizes

```python
# ✅ Good: Reasonable page size
products = await get_all_products.asyncio_detailed(
    client=client,
    limit=250  # Good balance of efficiency and memory - automatically paginated
)

# ❌ Bad: Too small (many requests)
products = await get_all_products.asyncio_detailed(
    client=client,
    limit=10   # Will make many small requests
)

# ❌ Bad: Too large (may hit API limits)
products = await get_all_products.asyncio_detailed(
    client=client,
    limit=10000  # May exceed API limits
)
```

### 3. Use Concurrent Requests Wisely

```python
import asyncio
from statuspro_public_api_client.api.product import get_product

# ✅ Good: Limited concurrency respects rate limits
async def get_multiple_products(product_ids):
    async with StatusProClient() as client:
        # Process in small batches
        results = []
        for i in range(0, len(product_ids), 5):  # 5 concurrent requests
            batch = product_ids[i:i+5]
            batch_results = await asyncio.gather(*[
                get_product.asyncio_detailed(client=client, id=pid)
                for pid in batch
            ])
            results.extend(batch_results)

            # Small delay between batches
            if i + 5 < len(product_ids):
                await asyncio.sleep(0.2)

        return results
```

## 📖 API Reference

### StatusProClient

```python
class StatusProClient(AuthenticatedClient):
    """The pythonic StatusPro API client with automatic resilience and pagination."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 5,
        max_pages: int = 100,
        logger: Optional[Logger] = None,
        **httpx_kwargs: Any,
    ): ...

    async def __aenter__(self) -> "StatusProClient": ...
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

### ResilientAsyncTransport

Factory function that creates a layered transport with automatic resilience:

```python
def ResilientAsyncTransport(
    max_retries: int = 5,
    max_pages: int = 100,
    logger: Optional[Logger] = None,
    **kwargs: Any
) -> RetryTransport:
    """
    Creates a chained transport with:
    1. AsyncHTTPTransport (base HTTP transport)
    2. ErrorLoggingTransport (logs detailed 4xx errors)
    3. PaginationTransport (auto-collects paginated responses)
    4. RetryTransport (handles retries with Retry-After header support)
    """
    ...
```

______________________________________________________________________

**Next Steps**: Check out the
[API Reference](reference/statuspro_public_api_client/index.md) for detailed endpoint
documentation, or see [Testing Guide](testing.md) for testing patterns.
