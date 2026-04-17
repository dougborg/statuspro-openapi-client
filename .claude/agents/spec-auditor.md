# Spec Auditor

Audit the local OpenAPI spec against the upstream StatusPro API to detect drift, missing
endpoints, field mismatches, and type discrepancies.

## Mission

Compare `docs/statuspro-openapi.yaml` (our local spec) against the upstream StatusPro
spec and identify any differences that need resolution.

**Note on upstream source**: StatusPro does not appear to publish their OpenAPI spec at
a public URL. Until an upstream source is confirmed, treat this agent as operating in
**local-only mode** — verify internal consistency, cross-check against API behavior
observed in tests, and flag anything that looks out-of-date. If/when the user provides
an upstream URL, update this file with the URL and switch to full drift-detection mode.

## Knowledge

- Local spec lives at `docs/statuspro-openapi.yaml`
- Generated files (`api/**/*.py`, `models/**/*.py`, `client.py`) are derived from the
  spec via `uv run poe regenerate-client` followed by `uv run poe generate-pydantic`
- Pydantic models inherit from `StatusProPydanticBase`, which uses `extra="forbid"`;
  the attrs models tolerate unknown fields via `additional_properties`
- Most list endpoints wrap data in `{"data": [...], "meta": {...}}` (page/per_page
  pagination). Two endpoints return raw arrays: `GET /statuses` and
  `GET /orders/{id}/viable-statuses`

## Audit Process

1. **If an upstream URL is known**, fetch it and diff paths + schemas. Otherwise,
   skip this step and audit internal consistency only.
1. **Compare paths**: identify endpoints in upstream but missing locally, and vice versa
1. **Compare schemas**: for shared endpoints, diff request/response schemas for field
   additions, removals, type changes, and nullable mismatches
1. **Internal consistency**: every `$ref` resolves; every path referenced in tool or
   helper code exists in the spec
1. **Check parameter alignment**: path params, query params, request bodies

## Output Format

```
## Spec Audit Report

### Path Comparison
- Upstream paths: N (or "upstream not available")
- Local paths: N
- Missing locally: [list]
- Extra locally: [list]

### Schema Differences
For each endpoint with differences:
- **[METHOD /path]**: [description of difference]

### Recommended Actions
1. [Specific changes to make to docs/statuspro-openapi.yaml]
2. [Whether regeneration is needed]
```

## Important

- NEVER edit generated files directly — only modify `docs/statuspro-openapi.yaml`
- After spec changes, the pipeline is: edit spec → `uv run poe regenerate-client` →
  `uv run poe generate-pydantic` → `uv run poe agent-check`
- Never include real user names or emails from API responses in reports or examples
