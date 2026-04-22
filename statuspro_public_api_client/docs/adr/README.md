# Architecture Decision Records — StatusPro OpenAPI Client

This directory contains Architecture Decision Records (ADRs) specific to the
`statuspro-openapi-client` package.

> **Inherited from the parent project.** This repository was forked from
> `katana-openapi-client`. The decisions captured here still apply to StatusPro
> (transport-layer resilience, OpenAPI codegen, response unwrapping, Pydantic domain
> models); some examples may still reference the original project's domain objects until
> the ADRs are rewritten.

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

- [ADR-001: Transport-Layer Resilience](0001-transport-layer-resilience.md)
- [ADR-002: Generate Client from OpenAPI Specification](0002-openapi-code-generation.md)
- [ADR-003: Transparent Automatic Pagination](0003-transparent-pagination.md)
- [ADR-004: Defer Observability to httpx](0004-defer-observability-to-httpx.md)
- [ADR-005: Provide Both Sync and Async APIs](0005-sync-async-apis.md)
- [ADR-006: Utility Functions for Response Unwrapping](0006-response-unwrapping-utilities.md)
- [ADR-011: Pydantic Domain Models for Business Entities](0011-pydantic-domain-models.md)
- [ADR-012: Validation Tiers for Agent Workflows](0012-validation-tiers-for-agent-workflows.md)

### Proposed

- [ADR-008: Avoid Traditional Builder Pattern](0008-avoid-builder-pattern.md)

## Related

- [Testing Guide](../testing.md)
- [Client Guide](../guide.md)
- [Contributing Guide](../../../docs/CONTRIBUTING.md)
- [Monorepo ADRs](../../../docs/adr/README.md)
