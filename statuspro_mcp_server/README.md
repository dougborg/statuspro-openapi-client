# StatusPro MCP Server

Model Context Protocol (MCP) server for the
[StatusPro API](https://app.orderstatuspro.com/api/v1). Exposes the API as tools so AI
assistants (Claude Desktop, Claude.ai, Cursor, etc.) can read and update order status
through natural language.

The StatusPro API is intentionally small — seven endpoints for listing and looking up
orders and applying status/comment/due-date changes. This server maps them to nine tools
and adds a two-step confirm pattern on every mutation.

## Features

- **9 tools** across Orders and Statuses — see the table below.
- **Two-step confirmation**: mutations require `confirm=true` and elicit explicit user
  approval via `ctx.elicit`.
- **Built-in resilience**: automatic retries, 429 rate-limit handling with exponential
  backoff, and auto-pagination inherited from the `statuspro-openapi-client` transport
  layer.
- **Environment-based authentication**: bearer token via `STATUSPRO_API_KEY` (env var,
  `.env`, or `~/.netrc`).
- **Response caching** for read-only tools (30s TTL) via the FastMCP response caching
  middleware.
- **Structured logging** with sensitive-data redaction.

## Installation

```bash
pip install statuspro-mcp-server
```

## Quick Start

### 1. Get your StatusPro API Key

Obtain your API key from your StatusPro account settings.

### 2. Configure environment

```bash
export STATUSPRO_API_KEY=your-api-key-here
```

Or create a `.env`:

```
STATUSPRO_API_KEY=your-api-key-here
STATUSPRO_BASE_URL=https://app.orderstatuspro.com/api/v1  # optional override
```

### 3. Choose a transport

| Transport         | Use case                    | Command                                            |
| ----------------- | --------------------------- | -------------------------------------------------- |
| `stdio` (default) | Claude Desktop, Claude Code | `statuspro-mcp-server`                             |
| `streamable-http` | Claude.ai, remote clients   | `statuspro-mcp-server --transport streamable-http` |
| `sse`             | Cursor IDE                  | `statuspro-mcp-server --transport sse`             |
| `http`            | Generic HTTP clients        | `statuspro-mcp-server --transport http`            |

### 4. Use with Claude Desktop (stdio)

**Recommended: install the `.mcpb` bundle** — Claude Desktop has built-in support for
[MCP Bundles](https://github.com/anthropics/mcpb), which install local MCP servers in
one click and prompt for the API key via UI (no JSON editing).

1. Download `statuspro-mcp-server-<version>.mcpb` from the
   [latest GitHub release](https://github.com/dougborg/statuspro-openapi-client/releases?q=mcp-v).
1. Drag the `.mcpb` file into Claude Desktop, or open it from the Finder.
1. Confirm install in the dialog. Claude Desktop prompts for your StatusPro API key
   (stored securely; never written to a config file by hand).

The bundle ships the server source plus a manifest that declares the runtime
requirements; UV handles dep resolution on first launch.

**Manual `uvx` install (fallback)** — if you'd rather edit
`~/Library/Application Support/Claude/claude_desktop_config.json` directly:

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

Either path: restart Claude Desktop and the StatusPro tools will appear.

### 5. Use with Claude.ai (streamable-http)

Claude.ai requires **HTTPS** and a **publicly reachable URL**. For local development,
use a tunnel like [ngrok](https://ngrok.com):

```bash
# Terminal 1: Start the MCP server with hot-reload
uv run poe dev

# Terminal 2: Create an HTTPS tunnel
ngrok http 8765
# → gives you https://abc123.ngrok-free.app
```

Then in Claude.ai:

1. Go to **Customize > Connectors**
1. Select **"Add custom connector"**
1. Paste your ngrok HTTPS URL

For production, run the Docker image behind a reverse proxy with TLS:

```bash
docker run -p 8765:8765 \
  -e STATUSPRO_API_KEY=your-key \
  ghcr.io/dougborg/statuspro-mcp-server:latest
```

### 6. Run standalone (optional)

```bash
export STATUSPRO_API_KEY=your-api-key
statuspro-mcp-server
```

## Tools

Mutations use a two-step confirm pattern: call with `confirm=false` first to get a
preview, then `confirm=true` to execute.

| Tool                       | Mutation? | Endpoint                           | Purpose                                       |
| -------------------------- | --------- | ---------------------------------- | --------------------------------------------- |
| `list_orders`              | no        | `GET /orders`                      | Paginated list with filters                   |
| `get_order`                | no        | `GET /orders/{id}`                 | Full detail incl. history                     |
| `lookup_order`             | no        | `GET /orders/lookup`               | Lookup by order number + customer email       |
| `list_statuses`            | no        | `GET /statuses`                    | Full status catalog                           |
| `get_viable_statuses`      | no        | `GET /orders/{id}/viable-statuses` | Valid transitions for this order              |
| `update_order_status`      | yes       | `POST /orders/{id}/status`         | Change an order's status                      |
| `add_order_comment`        | yes       | `POST /orders/{id}/comment`        | Add a history comment (5/min limit)           |
| `update_order_due_date`    | yes       | `POST /orders/{id}/due-date`       | Set or change the due date                    |
| `bulk_update_order_status` | yes       | `POST /orders/bulk-status`         | Update up to 50 orders at once (5/min, async) |

### Example: look up an order and change its status

```
lookup_order(number="1188", email="customer@example.com")
  → Order 6110375248088, status "In Production"

get_viable_statuses(order_id=6110375248088)
  → [Shipped, Ready for Pickup, Cancelled]

update_order_status(order_id=6110375248088, status_code="st000003", confirm=False)
  → Preview: change status from "In Production" to "Shipped"
  → ...confirm=true to execute
```

## Resources

Resources expose stable, read-only reference data so AI agents can orient themselves
without mutating tools.

- `statuspro://statuses` — full status catalog (JSON).
- `statuspro://help` — tool reference and recommended workflows (Markdown).

For transactional data (orders, status history), use the tools.

## Configuration

### Environment variables

- `STATUSPRO_API_KEY` (required) — your bearer token.
- `STATUSPRO_BASE_URL` (optional) — defaults to `https://app.orderstatuspro.com/api/v1`.
- `STATUSPRO_MCP_LOG_LEVEL` (optional) — `DEBUG` / `INFO` / `WARNING` / `ERROR` (default
  `INFO`).
- `STATUSPRO_MCP_LOG_FORMAT` (optional) — `json` or `text` (default `json`).

### Endpoint authentication (HTTP transport)

When running over `http`, `sse`, or `streamable-http`, the MCP endpoint is
**unauthenticated by default**. Pick one of:

**Bearer token** (simple, for dev/personal use):

```bash
export MCP_AUTH_TOKEN=your-secret-token
```

Clients must send `Authorization: Bearer your-secret-token`. In Claude.ai, enter the
token in the connector's Advanced Settings.

**GitHub OAuth** (production):

```bash
export MCP_GITHUB_CLIENT_ID=your-github-client-id
export MCP_GITHUB_CLIENT_SECRET=your-github-client-secret
export MCP_BASE_URL=https://your-public-url.ngrok-free.app
```

Create a GitHub OAuth App at https://github.com/settings/developers with the callback
URL set to `<MCP_BASE_URL>/auth/callback`.

Auth is **not required** for stdio transport (local only).

### Logging

```bash
# Development
export STATUSPRO_MCP_LOG_LEVEL=DEBUG
export STATUSPRO_MCP_LOG_FORMAT=text
statuspro-mcp-server

# Production
export STATUSPRO_MCP_LOG_LEVEL=INFO
export STATUSPRO_MCP_LOG_FORMAT=json
statuspro-mcp-server
```

## Troubleshooting

### "STATUSPRO_API_KEY environment variable is required"

Set the variable or add it to `.env`:

```bash
export STATUSPRO_API_KEY=your-api-key-here
```

### 401 Unauthorized

Your API key is invalid or expired. Rotate it in your StatusPro account settings.

### Tools not showing in Claude Desktop

1. Check `~/Library/Logs/Claude/mcp*.log`.
1. Verify the config file is valid JSON.
1. Test standalone: `statuspro-mcp-server` (should start with no errors).
1. Restart Claude Desktop.

### Persistent 429 rate limiting

The client retries 429s with exponential backoff automatically. If you see persistent
rate limits, reduce your request frequency — especially around `add_order_comment` and
`bulk_update_order_status` (5/min each).

## Development

### Prerequisites

- **uv** package manager
  ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Python 3.12+**

### Install from source

```bash
git clone https://github.com/dougborg/statuspro-openapi-client.git
cd statuspro-openapi-client/statuspro_mcp_server
uv sync
```

### Run tests

```bash
# Unit tests only (no API key needed)
uv run pytest tests/ -m "not integration"

# All tests (requires STATUSPRO_API_KEY)
export STATUSPRO_API_KEY=your-key
uv run pytest tests/
```

### Hot-reload development

```bash
# Install mcp-hmr (requires Python 3.12+)
uv pip install mcp-hmr

# Run with hot reload
uv run mcp-hmr src/statuspro_mcp/server.py:mcp
```

Claude Desktop config for development:

```json
{
  "mcpServers": {
    "statuspro-dev": {
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

### Build and install locally

```bash
uv build
pipx install --force dist/statuspro_mcp_server-*.whl
```

## Links

- **Repo**: https://github.com/dougborg/statuspro-openapi-client
- **Issues**: https://github.com/dougborg/statuspro-openapi-client/issues
- **PyPI**: https://pypi.org/project/statuspro-mcp-server/
- **StatusPro API docs**: https://app.orderstatuspro.com/api/v1

## License

MIT License — see [LICENSE](../LICENSE).
