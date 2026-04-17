# StatusPro MCP Server

Model Context Protocol (MCP) server for StatusPro Manufacturing ERP.

## Features

- **Inventory Management**: Check stock, find low stock items, search items, get variant
  details
- **Catalog Management**: Create products and materials
- **Order Management**: Create and manage purchase orders, sales orders, and
  manufacturing orders
- **Document Verification**: Verify supplier documents against purchase orders
- **Two-Step Confirmation**: Preview operations before executing (elicitation pattern)
- **Environment-based Authentication**: Secure API key management
- **Built-in Resilience**: Automatic retries, rate limiting, and pagination via Python
  client
- **Type Safety**: Pydantic models for all requests and responses

## Installation

```bash
pip install statuspro-mcp-server
```

## Quick Start

### 1. Get Your StatusPro API Key

Obtain your API key from your StatusPro account settings.

### 2. Configure Environment

Create a `.env` file or set environment variable:

```bash
export STATUSPRO_API_KEY=your-api-key-here
```

Or create `.env` file:

```
STATUSPRO_API_KEY=your-api-key-here
STATUSPRO_BASE_URL=https://app.orderstatuspro.com/api/v1  # Optional, uses default if not set
```

### 3. Choose Your Transport

The MCP server supports multiple transport protocols for different environments:

| Transport         | Use Case                          | Command                                         |
| ----------------- | --------------------------------- | ----------------------------------------------- |
| `stdio` (default) | Claude Desktop, Claude Code       | `statuspro-mcp-server`                             |
| `streamable-http` | Claude.ai co-work, remote clients | `statuspro-mcp-server --transport streamable-http` |
| `sse`             | Cursor IDE                        | `statuspro-mcp-server --transport sse`             |
| `http`            | Generic HTTP clients              | `statuspro-mcp-server --transport http`            |

### 4. Use with Claude Desktop (stdio)

Add to your Claude Desktop configuration
(`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "statuspro": {
      "command": "uvx",
      "args": ["statuspro-mcp-server"],
      "env": {
        "STATUSPRO_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Desktop, and you'll see StatusPro inventory tools available!

### 5. Use with Claude.ai Co-work (streamable-http)

Claude.ai requires **HTTPS** and a **publicly reachable URL**. For local development,
use a tunnel like [ngrok](https://ngrok.com):

```bash
# Terminal 1: Start the MCP server with hot-reload
uv run poe dev

# Terminal 2: Create an HTTPS tunnel
ngrok http 8765
# → Gives you https://abc123.ngrok-free.app
```

Then in Claude.ai:

1. Go to **Customize > Connectors**
1. Select **"Add custom connector"**
1. Paste your ngrok HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

For production, deploy the Docker image behind a reverse proxy with TLS:

```bash
docker run -p 8765:8765 -e STATUSPRO_API_KEY=your-key ghcr.io/dougborg/statuspro-mcp-server:latest
```

### 6. Run Standalone (Optional)

For testing or development:

```bash
export STATUSPRO_API_KEY=your-api-key
statuspro-mcp-server
```

## Available Tools

### check_inventory

Check stock levels for a specific product SKU.

**Parameters**:

- `sku` (string, required): Product SKU to check

**Example Request**:

```json
{
  "sku": "WIDGET-001"
}
```

**Example Response**:

```json
{
  "sku": "WIDGET-001",
  "product_name": "Premium Widget",
  "available_stock": 150,
  "in_production": 50,
  "committed": 75
}
```

**Use Cases**:

- "What's the current stock level for SKU WIDGET-001?"
- "Check inventory for my best-selling product"
- "How much stock do we have available for order fulfillment?"

______________________________________________________________________

### list_low_stock_items

Find products below a specified stock threshold.

**Parameters**:

- `threshold` (integer, optional, default: 10): Stock level threshold
- `limit` (integer, optional, default: 50): Maximum items to return

**Example Request**:

```json
{
  "threshold": 5,
  "limit": 20
}
```

**Example Response**:

```json
{
  "items": [
    {
      "sku": "PART-123",
      "product_name": "Component A",
      "current_stock": 3,
      "threshold": 5
    },
    {
      "sku": "PART-456",
      "product_name": "Component B",
      "current_stock": 2,
      "threshold": 5
    }
  ],
  "total_count": 15
}
```

**Use Cases**:

- "Show me products with less than 10 units in stock"
- "What items need reordering?"
- "Find critical low stock items (below 5 units)"

______________________________________________________________________

### search_items

Search for items (products, materials, services) by name or SKU.

**Parameters**:

- `query` (string, required): Search term (matches name or SKU)
- `limit` (integer, optional, default: 20): Maximum results to return

**Example Request**:

```json
{
  "query": "widget",
  "limit": 10
}
```

**Example Response**:

```json
{
  "items": [
    {
      "id": 12345,
      "sku": "WIDGET-001",
      "name": "Premium Widget",
      "is_sellable": true,
      "stock_level": null
    },
    {
      "id": 12346,
      "sku": "WIDGET-002",
      "name": "Economy Widget",
      "is_sellable": true,
      "stock_level": null
    }
  ],
  "total_count": 2
}
```

**Note**: `stock_level` is always `null` for search results in the current
implementation.

**Use Cases**:

- "Find all products containing 'widget'"
- "Search for SKU PART-123"
- "What items do we have for order creation?"
- "Show me all sellable products vs internal materials"

## Configuration

### Environment Variables

- `STATUSPRO_API_KEY` (required): Your StatusPro API key
- `STATUSPRO_BASE_URL` (optional): API base URL (default: https://app.orderstatuspro.com/api/v1)
- `STATUSPRO_MCP_LOG_LEVEL` (optional): Log level - DEBUG, INFO, WARNING, ERROR (default:
  INFO)
- `STATUSPRO_MCP_LOG_FORMAT` (optional): Log format - json, text (default: json)

### Endpoint Authentication (HTTP transport)

When using HTTP transport, the MCP endpoint is **unauthenticated by default**. Set one
of the following to secure it:

**Bearer token** (simple, for dev/personal use):

```bash
export MCP_AUTH_TOKEN=your-secret-token
```

Clients must send `Authorization: Bearer your-secret-token` with each request. In
Claude.ai, enter the token in the connector's Advanced Settings.

**GitHub OAuth** (production):

```bash
export MCP_GITHUB_CLIENT_ID=your-github-client-id
export MCP_GITHUB_CLIENT_SECRET=your-github-client-secret
export MCP_BASE_URL=https://your-public-url.ngrok-free.app
```

Create a GitHub OAuth App at https://github.com/settings/developers with the callback
URL set to `<MCP_BASE_URL>/auth/callback`.

Auth is **not required** for stdio transport (local only).

### Logging Configuration

The server uses structured logging with configurable output format and verbosity:

**Development (verbose text logs):**

```bash
export STATUSPRO_MCP_LOG_LEVEL=DEBUG
export STATUSPRO_MCP_LOG_FORMAT=text
statuspro-mcp-server
```

**Production (structured JSON logs):**

```bash
export STATUSPRO_MCP_LOG_LEVEL=INFO
export STATUSPRO_MCP_LOG_FORMAT=json
statuspro-mcp-server
```

See [docs/LOGGING.md](docs/LOGGING.md) for complete logging documentation.

### Advanced Configuration

The server uses the
[statuspro-openapi-client](https://pypi.org/project/statuspro-openapi-client/) library with:

- Automatic retries on rate limits (429) and server errors (5xx)
- Exponential backoff with jitter
- Transparent pagination for large result sets
- 30-second default timeout

## Troubleshooting

### "STATUSPRO_API_KEY environment variable is required"

**Cause**: API key not set in environment.

**Solution**: Set the environment variable or add to `.env` file:

```bash
export STATUSPRO_API_KEY=your-api-key-here
```

### "Authentication error: 401 Unauthorized"

**Cause**: Invalid or expired API key.

**Solution**: Verify your API key in StatusPro account settings and update the environment
variable.

### Tools not showing up in Claude Desktop

**Cause**: Configuration error or server not starting.

**Solutions**:

1. Check Claude Desktop logs: `~/Library/Logs/Claude/mcp*.log`
1. Verify configuration file syntax (valid JSON)
1. Test server standalone: `statuspro-mcp-server` (should start without errors)
1. Restart Claude Desktop after configuration changes

### Rate limiting (429 errors)

**Cause**: Too many requests to StatusPro API.

**Solution**: The server automatically retries with exponential backoff. If you see
persistent rate limiting, reduce request frequency.

## Development

### Prerequisites

- **uv** package manager -
  [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- **Python 3.12+** (for hot-reload mode)

### Development Mode with Hot Reload ⚡

For **rapid iteration** during development, use hot-reload mode to see changes instantly
without rebuilding or restarting:

```bash
# 1. Install dependencies
cd statuspro_mcp_server
uv sync

# 2. Install mcp-hmr (requires Python 3.12+)
uv pip install mcp-hmr

# 3. Run with hot reload
uv run mcp-hmr src/statuspro_mcp/server.py:mcp
```

**Benefits**:

- Edit code → Save → Changes apply instantly
- No rebuild, no reinstall, no restart needed
- Keep your Claude Desktop conversation context
- Iteration time: ~5 seconds instead of 5-10 minutes

**Claude Desktop Configuration for Development**:

```json
{
  "mcpServers": {
    "statuspro-erp-dev": {
      "comment": "Use full path to uv - find with: which uv",
      "command": "/Users/YOUR_USERNAME/.local/bin/uv",
      "args": ["run", "mcp-hmr", "src/statuspro_mcp/server.py:mcp"],
      "cwd": "/absolute/path/to/statuspro-openapi-client/statuspro_mcp_server",
      "env": {
        "STATUSPRO_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Important**:

- Replace `YOUR_USERNAME` with your actual username
- Run `which uv` to find the correct uv path (usually `~/.local/bin/uv`)
- Replace `/absolute/path/to/` with your repository path
- Hot reload requires Python >=3.12. For Python 3.11 users, use the production install
  method.

See [DEVELOPMENT.md](../docs/mcp-server/DEVELOPMENT.md) for the complete development
guide.

### Install from Source

```bash
git clone https://github.com/dougborg/statuspro-openapi-client.git
cd statuspro-openapi-client/statuspro_mcp_server
uv sync
```

### Run Tests

```bash
# Unit tests only (no API key needed)
uv run pytest tests/ -m "not integration"

# All tests (requires STATUSPRO_API_KEY)
export STATUSPRO_API_KEY=your-key
uv run pytest tests/
```

### Build and Install Locally

```bash
# Build the package
uv build

# Install with pipx
pipx install --force dist/statuspro_mcp_server-*.whl
```

## Version

Current version: **0.33.0**

### Available Tools

**Inventory Tools:**

- `check_inventory` - Check stock levels for a specific SKU
- `list_low_stock_items` - Find products below stock threshold
- `search_items` - Search for items by name or SKU
- `get_variant_details` - Get detailed variant information

**Catalog Tools:**

- `create_product` - Create a new product
- `create_material` - Create a new material

**Order Tools:**

- `create_purchase_order` - Create purchase orders with two-step confirmation
- `receive_purchase_order` - Receive items from purchase orders
- `verify_order_document` - Verify documents against purchase orders
- `create_manufacturing_order` - Create manufacturing orders
- `create_sales_order` - Create sales orders with two-step confirmation
- `fulfill_order` - Fulfill manufacturing or sales orders

### Available Resources

Resources expose cached reference data (small, stable datasets). For transactional data
(orders, stock movements), use the corresponding tools.

- `statuspro://inventory/items` - Complete catalog of products, materials, services
- `statuspro://suppliers` - Supplier directory with contact info
- `statuspro://locations` - Warehouses and facilities
- `statuspro://tax-rates` - Configured tax rates
- `statuspro://operators` - Manufacturing operators
- `statuspro://help` - Workflow guides and tool reference

## Links

- **Documentation**: https://github.com/dougborg/statuspro-openapi-client
- **Issue Tracker**: https://github.com/dougborg/statuspro-openapi-client/issues
- **PyPI**: https://pypi.org/project/statuspro-mcp-server/
- **StatusPro API**: https://help.orderstatuspro.com/api/overview

## License

MIT License - see LICENSE file for details
