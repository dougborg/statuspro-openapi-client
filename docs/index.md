# StatusPro OpenAPI Client Documentation

Welcome to the **StatusPro OpenAPI Client** documentation. This is a modern, pythonic
client for the StatusPro Manufacturing ERP API with automatic resilience features.

## Features

- **Transport-layer resilience**: Automatic retries, rate limiting, and smart pagination
  at the HTTP transport level
- **Type-safe**: Full type hints and ty/mypy compatibility
- **Async/await support**: Built on httpx for modern Python async patterns
- **Production-ready**: Comprehensive error handling and logging
- **Zero-wrapper philosophy**: All resilience features work transparently with the
  generated API client

## Quick Start

```python
from statuspro_public_api_client import StatusProClient
from statuspro_public_api_client.api.product import get_all_products

async def main():
    async with StatusProClient() as client:
        # This call automatically gets retries, rate limiting, and pagination
        response = await get_all_products.asyncio_detailed(
            client=client,
            limit=50  # Will auto-paginate if needed
        )

        if response.status_code == 200:
            products = response.parsed
            print(f"Found {len(products)} products")
```

## Architecture

The client uses a **transport-layer resilience** approach where all resilience features
(retries, rate limiting, pagination) are implemented at the HTTP transport level rather
than as decorators or wrapper methods. This means:

- All 150+ generated API methods automatically get resilience features
- No code changes needed when the OpenAPI spec is updated
- Type safety is preserved throughout the entire client
- Performance is optimized by handling resilience at the lowest level

## Documentation Structure

```{toctree}
:maxdepth: 2
:caption: User Guides

client/guide
client/cookbook
client/testing
CONTRIBUTING
```

```{toctree}
:maxdepth: 2
:caption: MCP Server

mcp-server/README
mcp-server/architecture
mcp-server/development
mcp-server/deployment
```

```{toctree}
:maxdepth: 2
:caption: API Reference

autoapi/statuspro_public_api_client/index
```

```{toctree}
:maxdepth: 2
:caption: Development

RELEASE
MONOREPO_SEMANTIC_RELEASE
UV_USAGE
PYPI_SETUP
```

```{toctree}
:maxdepth: 2
:caption: Project Information

client/CHANGELOG
CODE_OF_CONDUCT
```

## API Reference

The API reference documentation is automatically generated from the source code
docstrings and includes:

- **Main Client Classes**: `StatusProClient`, `ResilientAsyncTransport`
- **Logging Utilities**: `setup_logging`, `get_logger`
- **Generated API Methods**: 150+ endpoint methods with full type annotations
- **Data Models**: All request/response models with validation

## Installation

```bash
pip install statuspro-openapi-client
```

## Configuration

The client can be configured through environment variables or direct initialization:

```python
# Via environment variables (.env file)
STATUSPRO_API_KEY=your_api_key_here
STATUSPRO_BASE_URL=https://app.orderstatuspro.com/api/v1  # Optional, defaults to production

# Via direct initialization
from statuspro_public_api_client import StatusProClient

async with StatusProClient(
    api_key="your_api_key_here",
    base_url="https://app.orderstatuspro.com/api/v1",
    max_retries=5,
    max_pages=100
) as client:
    # Use the client
    pass
```

## Support

- **Documentation**:
  [GitHub Pages](https://dougborg.github.io/statuspro-openapi-client/)
- **Issues**:
  [GitHub Issues](https://github.com/dougborg/statuspro-openapi-client/issues)
- **Source**: [GitHub Repository](https://github.com/dougborg/statuspro-openapi-client)

## License

MIT License - see
[LICENSE](https://github.com/dougborg/statuspro-openapi-client/blob/main/LICENSE) for
details.
