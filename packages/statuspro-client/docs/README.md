# StatusPro TypeScript Client Documentation

This directory contains all documentation specific to the `statuspro-openapi-client`
TypeScript package.

## Documentation Index

### User Guides

- **[Client Guide](guide.md)** - Comprehensive guide to using the TypeScript client
- **[Cookbook](cookbook.md)** - Common usage patterns and recipes
- **[Testing Guide](testing.md)** - Testing strategy and patterns

### Reference

- **[ADRs](adr/README.md)** - Architecture Decision Records

## Quick Links

- **[Package README](../README.md)** - Quick start and API overview
- **[Main Repository README](../../../README.md)** - Project overview
- **[Contributing Guide](../../../docs/CONTRIBUTING.md)** - How to contribute

## Related Packages

This monorepo also contains:

- **[statuspro-openapi-client (Python)](../../../statuspro_public_api_client/docs/README.md)**
  \- Python client with the same features
- **[statuspro-mcp-server](../../../statuspro_mcp_server/docs/README.md)** - MCP server
  for Claude Code integration

## Feature Comparison

The TypeScript client mirrors the Python client's feature set:

| Feature             | TypeScript | Python |
| ------------------- | ---------- | ------ |
| Auto-retries        | ✅         | ✅     |
| Rate limit handling | ✅         | ✅     |
| Auto-pagination     | ✅         | ✅     |
| Typed errors        | ✅         | ✅     |
| Generated SDK       | ✅         | ✅     |
| Browser support     | ✅         | ❌     |
| Tree-shakeable      | ✅         | N/A    |
