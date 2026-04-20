/**
 * StatusPro OpenAPI Client for TypeScript/JavaScript
 *
 * A resilient client for the StatusPro API with:
 * - Automatic retries with exponential backoff
 * - Rate limiting awareness (429 handling)
 * - Automatic pagination
 * - Typed error handling
 *
 * @example
 * ```typescript
 * import { StatusProClient } from 'statuspro-client';
 *
 * const client = await StatusProClient.create({ apiKey: 'your-api-key' });
 * const response = await client.get('/orders');
 * const data = await response.json();
 * ```
 *
 * @example Types-only import
 * ```typescript
 * import type { OrderListItem, Status } from 'statuspro-client/types';
 * ```
 */

// Re-export the main client
export { StatusProClient, type StatusProClientOptions } from './client.js';

// Re-export error types and utilities
export {
  AuthenticationError,
  NetworkError,
  parseError,
  RateLimitError,
  ServerError,
  StatusProError,
  ValidationError,
  type ValidationErrorDetail,
} from './errors.js';
// Re-export the Client type for advanced usage
export type { Client } from './generated/client/types.gen.js';
// Re-export generated SDK functions for direct API access
export * from './generated/sdk.gen.js';
export {
  createPaginatedFetch,
  DEFAULT_PAGINATION_CONFIG,
  type PaginatedResponse,
  type PaginationConfig,
} from './transport/pagination.js';
// Re-export transport utilities for advanced usage
export {
  createResilientFetch,
  DEFAULT_RETRY_CONFIG,
  type RetryConfig,
} from './transport/resilient.js';

// Re-export all generated types for convenience
export * from './types.js';
