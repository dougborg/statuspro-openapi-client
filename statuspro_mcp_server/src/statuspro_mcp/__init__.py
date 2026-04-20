"""StatusPro MCP Server.

A Model Context Protocol (MCP) server for the StatusPro API. Exposes order
status lookup and update operations as tools for AI assistants.

Key Features:
- 9 tools across Orders and Statuses
- Two-step confirm pattern on mutations
- Built on statuspro-openapi-client — inherits retries, rate-limit awareness,
  and auto-pagination for free

Example:
    Configure in Claude Desktop's MCP settings:

    ```json
    {
      "mcpServers": {
        "statuspro": {
          "command": "uvx",
          "args": ["statuspro-mcp-server"],
          "env": {
            "STATUSPRO_API_KEY": "your-api-key"
          }
        }
      }
    }
    ```

See https://github.com/dougborg/statuspro-openapi-client for docs.
"""

from importlib.metadata import version

__version__ = version("statuspro-mcp-server")

__all__ = ["__version__"]
