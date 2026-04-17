# StatusPro — API Client Ecosystem

Multi-language client ecosystem for the
[StatusPro API](https://app.orderstatuspro.com/api/v1). Production-ready
clients with automatic resilience, rate-limit awareness, and pagination for
order status lookup and update workflows.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![OpenAPI 3.1.0](https://img.shields.io/badge/OpenAPI-3.1.0-green.svg)](https://spec.openapis.org/oas/v3.1.0)

## Packages

| Package                                                  | Language   | Version | Description                                        |
| -------------------------------------------------------- | ---------- | ------- | -------------------------------------------------- |
| [statuspro-openapi-client](statuspro_public_api_client/) | Python     | 0.0.1   | API client with transport-layer resilience         |
| [statuspro-mcp-server](statuspro_mcp_server/)            | Python     | 0.0.1   | Model Context Protocol server for AI assistants    |
| [@statuspro/client](packages/statuspro-client/)          | TypeScript | 0.0.1   | TypeScript/JavaScript client with full type safety |

## Features Comparison

| Feature             | Python Client   | TypeScript Client | MCP Server              |
| ------------------- | --------------- | ----------------- | ----------------------- |
| Automatic retries   | Yes             | Yes               | Yes (via Python client) |
| Rate limit handling | Yes             | Yes               | Yes                     |
| Auto-pagination     | Yes             | Yes               | Yes                     |
| Type safety         | Full (Pydantic) | Full (TypeScript) | Full (Pydantic)         |
| Sync + Async        | Yes             | Async only        | Async only              |
| Browser support     | No              | Yes               | No                      |
| AI Integration      | -               | -                 | Claude, Cursor, etc.    |

## Quick Start

### Python Client

```bash
pip install statuspro-openapi-client
```

```python
import asyncio
from statuspro_public_api_client import StatusProClient

async def main():
    async with StatusProClient() as client:
        orders = await client.orders.list(per_page=25)
        for order in orders:
            status = order.status.name if order.status else "(no status)"
            print(f"{order.name}: {status}")

asyncio.run(main())
```

### TypeScript Client

```bash
npm install @statuspro/client
```

```typescript
import { StatusProClient } from '@statuspro/client';

const client = await StatusProClient.create();
const response = await client.get('/orders');
const { data, meta } = await response.json();
console.log(`Found ${meta.total} orders (page ${meta.current_page}/${meta.last_page})`);
```

### MCP Server (Claude Desktop)

```bash
pip install statuspro-mcp-server
```

Add to Claude Desktop config
(`~/Library/Application Support/Claude/claude_desktop_config.json`):

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

## Configuration

All packages support the same authentication methods:

1. **Environment variable**: `STATUSPRO_API_KEY`
1. **`.env` file**: Create with `STATUSPRO_API_KEY=your-key`
1. **Direct parameter**: Pass `api_key` to client constructor

```bash
# .env file
STATUSPRO_API_KEY=your-api-key-here
STATUSPRO_BASE_URL=https://app.orderstatuspro.com/api/v1  # Optional
```

## API Coverage

All clients provide access to the complete StatusPro API:

| Category             | Endpoints | Description                                 |
| -------------------- | --------- | ------------------------------------------- |
| Products & Inventory | 25+       | Products, variants, materials, stock levels |
| Orders               | 20+       | Sales orders, purchase orders, fulfillment  |
| Manufacturing        | 15+       | BOMs, manufacturing orders, operations      |
| Business Relations   | 10+       | Customers, suppliers, addresses             |
| Configuration        | 6+        | Locations, webhooks, custom fields          |

**Total**: 76+ endpoints with 150+ fully-typed data models

## Project Structure

```text
statuspro-openapi-client/               # Monorepo root
├── pyproject.toml                   # Workspace configuration (uv)
├── uv.lock                          # Unified lock file
├── docs/
│   ├── statuspro-openapi.yaml          # OpenAPI 3.1.0 specification
│   ├── adr/                         # Shared architecture decisions
│   └── *.md                         # Shared documentation
├── statuspro_public_api_client/        # Python client package
│   ├── statuspro_client.py             # Resilient client with retries
│   ├── api/                         # Generated API modules (76+)
│   ├── models/                      # Generated data models (150+)
│   └── docs/                        # Package documentation
├── statuspro_mcp_server/               # MCP server package
│   ├── src/statuspro_mcp/
│   │   ├── server.py                # FastMCP server
│   │   ├── tools/                   # MCP tools (12)
│   │   └── resources/               # MCP resources (5)
│   └── docs/                        # Package documentation
└── packages/
    └── statuspro-client/               # TypeScript client package
        ├── src/
        │   ├── client.ts            # Resilient client
        │   └── generated/           # Generated SDK
        └── docs/                    # Package documentation
```

## Documentation

### Package Documentation

Each package has its own documentation in its `docs/` directory:

- **[Python Client Guide](statuspro_public_api_client/docs/guide.md)** - Complete usage
  guide
- **[Python Client Cookbook](statuspro_public_api_client/docs/cookbook.md)** - Practical
  recipes
- **[MCP Server Architecture](statuspro_mcp_server/docs/architecture.md)** - MCP design
  patterns
- **[MCP Server Development](statuspro_mcp_server/docs/development.md)** - Development
  guide
- **[TypeScript Client Guide](packages/statuspro-client/docs/guide.md)** - TypeScript usage

### Architecture Decisions

Key architectural decisions are documented as ADRs (Architecture Decision Records):

**Python Client ADRs**
([statuspro_public_api_client/docs/adr/](statuspro_public_api_client/docs/adr/)):

- [ADR-001](statuspro_public_api_client/docs/adr/0001-transport-layer-resilience.md):
  Transport-Layer Resilience
- [ADR-002](statuspro_public_api_client/docs/adr/0002-openapi-code-generation.md): OpenAPI
  Code Generation
- [ADR-003](statuspro_public_api_client/docs/adr/0003-transparent-pagination.md):
  Transparent Pagination
- [ADR-006](statuspro_public_api_client/docs/adr/0006-response-unwrapping-utilities.md):
  Response Unwrapping

**MCP Server ADRs** ([statuspro_mcp_server/docs/adr/](statuspro_mcp_server/docs/adr/)):

- [ADR-010](statuspro_mcp_server/docs/adr/0010-statuspro-mcp-server.md): MCP Server
  Architecture

**TypeScript Client ADRs**
([packages/statuspro-client/docs/adr/](packages/statuspro-client/docs/adr/)):

- [ADR-001](packages/statuspro-client/docs/adr/0001-composable-fetch-wrappers.md):
  Composable Fetch Wrappers
- [ADR-002](packages/statuspro-client/docs/adr/0002-hey-api-code-generation.md): Hey API
  Code Generation
- [ADR-003](packages/statuspro-client/docs/adr/0003-biome-for-linting.md): Biome for
  Linting

**Shared/Monorepo ADRs** ([docs/adr/](docs/adr/)):

- [ADR-009](docs/adr/0009-migrate-from-poetry-to-uv.md): Migrate to uv

### Shared Documentation

- **[Contributing Guide](docs/CONTRIBUTING.md)** - How to contribute
- **[uv Usage Guide](docs/UV_USAGE.md)** - Package manager guide
- **[Monorepo Release Guide](docs/MONOREPO_SEMANTIC_RELEASE.md)** - Semantic release
  setup

## Development

### Prerequisites

- **Python 3.12+** for Python packages
- **Node.js 18+** for TypeScript package
- **uv** package manager
  ([install](https://docs.astral.sh/uv/getting-started/installation/))

### Setup

```bash
# Clone repository
git clone https://github.com/dougborg/statuspro-openapi-client.git
cd statuspro-openapi-client

# Install all dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Create .env file
cp .env.example .env  # Add your STATUSPRO_API_KEY
```

### Common Commands

```bash
# Run all checks (lint, type-check, test)
uv run poe check

# Run tests
uv run poe test

# Format code
uv run poe format

# Regenerate Python client from OpenAPI spec
uv run poe regenerate-client
```

### Commit Standards

This project uses semantic-release with conventional commits:

```bash
# Python client changes
git commit -m "feat(client): add new inventory helper"
git commit -m "fix(client): handle pagination edge case"

# MCP server changes
git commit -m "feat(mcp): add manufacturing order tools"
git commit -m "fix(mcp): improve error handling"

# TypeScript client changes
git commit -m "feat(ts): add browser support"

# Documentation only (no release)
git commit -m "docs: update README"
```

See [MONOREPO_SEMANTIC_RELEASE.md](docs/MONOREPO_SEMANTIC_RELEASE.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.
