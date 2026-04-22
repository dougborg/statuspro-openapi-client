# Architecture Decision Records — StatusPro MCP Server

This directory contains Architecture Decision Records (ADRs) specific to the
`statuspro-mcp-server` package.

> **Inherited from the parent project.** This repository was forked from
> `katana-openapi-client`. The decisions captured here still apply; some examples may
> still reference the original project's domain objects while this repository is new
> enough that new ADR write-ups haven't yet replaced them.

## Format

We use the format proposed by Michael Nygard in
[Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):

- **Title** — noun phrase describing the decision
- **Status** — Proposed | Accepted | Deprecated | Superseded
- **Context** — what is motivating this decision?
- **Decision** — what is the change being proposed?
- **Consequences** — what becomes easier or harder?

## Index

### Accepted

- [ADR-0016: Tool Interface Pattern](0016-tool-interface-pattern.md)
- [ADR-0017: Automated Tool Documentation](0017-automated-tool-documentation.md)

## Creating a new ADR

1. Copy the template from the shared ADR directory
1. Number it sequentially
1. Fill in the sections
1. Open a PR for discussion
1. Update status to "Accepted" after approval

## Related

- [Development Guide](../development.md)
- [Contributing Guide](../../../docs/CONTRIBUTING.md)
- [Monorepo ADRs](../../../docs/adr/README.md)
