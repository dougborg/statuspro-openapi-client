"""StatusPro Manufacturing ERP MCP Server.

This package provides a Model Context Protocol (MCP) server for the StatusPro
Manufacturing ERP system. It enables natural language interactions with StatusPro
through Claude Code and other MCP clients.

Key Features:
- 12 tools covering inventory, sales orders, purchase orders, and manufacturing
- Resource endpoints for read-only data access
- Workflow prompts for common manufacturing scenarios
- Built on statuspro-openapi-client with automatic retries and rate limiting

Example:
    Configure in Claude Code's MCP settings:

    ```json
    {
      "mcpServers": {
        "statuspro-erp": {
          "command": "uvx",
          "args": ["statuspro-mcp-server"],
          "env": {
            "STATUSPRO_API_KEY": "your-api-key",
            "STATUSPRO_BASE_URL": "https://app.orderstatuspro.com/api/v1"
          }
        }
      }
    }
    ```

For more information, see the documentation at:
https://dougborg.github.io/statuspro-openapi-client/
"""

from importlib.metadata import version

__version__ = version("statuspro-mcp-server")

__all__ = ["__version__"]
