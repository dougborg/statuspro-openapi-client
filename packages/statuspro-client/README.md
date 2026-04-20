# statuspro-client

TypeScript/JavaScript client for the
[StatusPro API](https://app.orderstatuspro.com/api/v1) with automatic
resilience. The StatusPro API is a small REST surface for reading and
updating the status of orders.

## Features

- **Automatic retries** — exponential backoff with configurable retry limits.
- **Rate-limit awareness** — respects 429 + `Retry-After` (falls back to
  exponential backoff; StatusPro doesn't surface the header today).
- **Auto-pagination** — walks `GET /orders` using the `{data, meta}` envelope
  and stops at `meta.last_page`; raw-array endpoints (`/statuses`,
  `/orders/{id}/viable-statuses`) pass through untouched.
- **Type safety** — full TypeScript types generated from the OpenAPI spec via
  `@hey-api/openapi-ts`.
- **Browser & Node.js** — works in both environments.
- **Tree-shakeable** — only import what you need.

## Installation

```bash
npm install statuspro-client
# or
pnpm add statuspro-client
# or
yarn add statuspro-client
```

## Quick Start

```typescript
import { StatusProClient } from 'statuspro-client';

// API key from STATUSPRO_API_KEY env var (or .env)
const client = await StatusProClient.create();

// Or provide the key directly
const client = StatusProClient.withApiKey('your-api-key');

// GET /orders — auto-paginated
const response = await client.get('/orders');
const { data, meta } = await response.json();
console.log(`Found ${meta.total} orders across ${meta.last_page} pages`);
```

## Types-only import

```typescript
import type { OrderListItem, Status, OrderResponse } from 'statuspro-client/types';

function render(order: OrderListItem) {
  // ...
}
```

## Configuration

```typescript
const client = await StatusProClient.create({
  apiKey: 'your-api-key',                               // or STATUSPRO_API_KEY env var

  baseUrl: 'https://app.orderstatuspro.com/api/v1',     // default shown

  retry: {
    maxRetries: 5,
    backoffFactor: 1.0,       // 1s, 2s, 4s, 8s, 16s
    respectRetryAfter: true,
  },

  pagination: {
    maxPages: 100,
    maxItems: undefined,      // cap total items when set
    defaultPageSize: 100,     // StatusPro's max per_page
  },

  autoPagination: true,        // disable per-request with an explicit `page` param
});
```

## Retry Behavior

Mirrors the Python client:

| Status Code      | GET/PUT/DELETE | POST/PATCH |
| ---------------- | -------------- | ---------- |
| 429 (Rate limit) | Retry          | Retry      |
| 502, 503, 504    | Retry          | No retry   |
| Other 4xx        | No retry       | No retry   |
| Network error    | Retry          | Retry      |

**Key behavior**: POST/PATCH are retried on 429 because rate limits are
transient, not an idempotency problem.

## Auto-Pagination

Auto-pagination is ON by default for GET requests without an explicit `page`
parameter:

```typescript
const response = await client.get('/orders');
const { data, pagination } = await response.json();
console.log(`Collected ${pagination.total_items} orders from ${pagination.collected_pages} pages`);
```

To disable:

```typescript
// Explicit page param disables auto-pagination for that call
const response = await client.get('/orders', { page: 2, per_page: 50 });

// Or globally
const client = await StatusProClient.create({ autoPagination: false });
```

## Error Handling

```typescript
import {
  StatusProClient,
  parseError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
} from 'statuspro-client';

const response = await client.post('/orders/123/comment', {
  comment: 'Shipped.',
  public: true,
});

if (!response.ok) {
  const body = await response.json();
  const error = parseError(response, body);

  if (error instanceof AuthenticationError) {
    console.error('Invalid API key');
  } else if (error instanceof RateLimitError) {
    console.error(`Rate limited. Retry after ${error.retryAfter}s`);
  } else if (error instanceof ValidationError) {
    // StatusPro ValidationErrorResponse: { message, errors: { field: [msg, ...] } }
    console.error('Validation errors:', error.details);
  } else {
    console.error(`Error ${error.statusCode}: ${error.message}`);
  }
}
```

Available error classes:

- `AuthenticationError` (401)
- `RateLimitError` (429) — includes `retryAfter` seconds when present
- `ValidationError` (422) — includes per-field errors
- `ServerError` (5xx)
- `NetworkError` — connection failures
- `StatusProError` — base class

## HTTP Methods

```typescript
// GET (auto-paginated by default for /orders)
const orders = await client.get('/orders');
const order = await client.get('/orders/6110375248088');
const byStatus = await client.get('/orders', { status_code: 'st000002' });
const statuses = await client.get('/statuses');  // raw array, no pagination

// POST
const status = await client.post('/orders/6110375248088/status', {
  status_code: 'st000003',
  comment: 'Shipped.',
  email_customer: true,
});
```

StatusPro does not expose `PUT`, `PATCH`, or `DELETE` — all mutations are
POSTs.

## Advanced: Generated SDK

```typescript
import { StatusProClient, listOrders, updateOrderStatus } from 'statuspro-client';

const statuspro = await StatusProClient.create();

const { data, error } = await listOrders({ client: statuspro.sdk });
if (data) {
  console.log(`Got ${data.data.length} orders`);
}
```

The SDK functions give you:

- Full TypeScript types for every request/response body.
- Autocomplete on query parameters (page, per_page, search, status_code, …).
- Type-safe error paths.

## Environment Variables

- `STATUSPRO_API_KEY` — bearer token for authentication.
- `STATUSPRO_BASE_URL` — override the base URL (optional).

### Loading from `.env` files

**Node.js 20.6+** (recommended):

```bash
node --env-file=.env your-script.js
```

**Node.js 18–20.5** — use `dotenv`:

```bash
npm install dotenv
```

```typescript
import 'dotenv/config';
import { StatusProClient } from 'statuspro-client';

const client = StatusProClient.withApiKey(process.env.STATUSPRO_API_KEY!);
```

> This library supports Node.js 18+ but does not bundle `dotenv`. If you
> need `.env` loading on Node 18–20.5, install `dotenv` in your project.

## Documentation

- **[Client Guide](docs/guide.md)** — comprehensive usage guide
- **[Cookbook](docs/cookbook.md)** — common patterns and recipes
- **[Testing Guide](docs/testing.md)** — testing strategy
- **[Architecture Decisions](docs/adr/README.md)** — design rationale

## License

MIT
