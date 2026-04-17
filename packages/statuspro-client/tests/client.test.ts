/**
 * Tests for StatusProClient
 *
 * Tests the main client class and its integration with
 * retry and pagination transport layers.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { StatusProClient } from '../src/client.js';

describe('StatusProClient', () => {
  let mockFetch: ReturnType<typeof vi.fn>;
  const TEST_API_KEY = 'test-api-key-12345';
  const BASE_URL = 'https://app.orderstatuspro.com/api/v1';

  beforeEach(() => {
    mockFetch = vi.fn();
  });

  describe('withApiKey', () => {
    it('should create client with explicit API key', () => {
      const client = StatusProClient.withApiKey(TEST_API_KEY);
      expect(client).toBeInstanceOf(StatusProClient);
      expect(client.getBaseUrl()).toBe(BASE_URL);
    });

    it('should use custom base URL', () => {
      const customUrl = 'https://custom.api.example.com';
      const client = StatusProClient.withApiKey(TEST_API_KEY, { baseUrl: customUrl });
      expect(client.getBaseUrl()).toBe(customUrl);
    });
  });

  describe('create', () => {
    it('should throw descriptive error when no API key is available', async () => {
      // Temporarily remove env var if present
      const originalEnv = process.env.STATUSPRO_API_KEY;
      // biome-ignore lint/performance/noDelete: Need to actually remove env var, not set to "undefined" string
      delete process.env.STATUSPRO_API_KEY;

      try {
        await expect(StatusProClient.create()).rejects.toThrow(
          /API key required.*apiKey option.*STATUSPRO_API_KEY.*--env-file/
        );
      } finally {
        // Restore env var
        if (originalEnv) {
          process.env.STATUSPRO_API_KEY = originalEnv;
        }
      }
    });

    it('should create client with API key from environment variable', async () => {
      const originalEnv = process.env.STATUSPRO_API_KEY;
      process.env.STATUSPRO_API_KEY = 'env-api-key';

      try {
        const client = await StatusProClient.create();
        expect(client).toBeInstanceOf(StatusProClient);
      } finally {
        if (originalEnv) {
          process.env.STATUSPRO_API_KEY = originalEnv;
        } else {
          // biome-ignore lint/performance/noDelete: Need to actually remove env var, not set to "undefined" string
          delete process.env.STATUSPRO_API_KEY;
        }
      }
    });
  });

  describe('fetch method', () => {
    it('should add Authorization header to requests', async () => {
      const response = new Response(JSON.stringify({ data: [] }), { status: 200 });
      mockFetch.mockResolvedValueOnce(response);

      // Disable auto-pagination to test basic fetch behavior
      const client = StatusProClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        autoPagination: false,
      });
      await client.fetch('/orders');

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const [url, options] = mockFetch.mock.calls[0];
      expect(url).toBe(`${BASE_URL}/orders`);
      expect(options.headers.get('Authorization')).toBe(`Bearer ${TEST_API_KEY}`);
    });

    it('should handle full URLs', async () => {
      const response = new Response(JSON.stringify({ data: [] }), { status: 200 });
      mockFetch.mockResolvedValueOnce(response);

      // Disable auto-pagination to test basic fetch behavior
      const client = StatusProClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        autoPagination: false,
      });
      await client.fetch('https://other.api.com/endpoint');

      const [url] = mockFetch.mock.calls[0];
      expect(url).toBe('https://other.api.com/endpoint');
    });

    it('should add Content-Type header for POST requests with body', async () => {
      const response = new Response(JSON.stringify({ id: 1 }), { status: 201 });
      mockFetch.mockResolvedValueOnce(response);

      const client = StatusProClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      await client.fetch('/orders', {
        method: 'POST',
        body: JSON.stringify({ comment: 'Test comment' }),
      });

      const [, options] = mockFetch.mock.calls[0];
      expect(options.headers.get('Content-Type')).toBe('application/json');
    });
  });

  describe('HTTP method shortcuts', () => {
    it('should make GET requests', async () => {
      const response = new Response(JSON.stringify({ data: [] }), { status: 200 });
      mockFetch.mockResolvedValueOnce(response);

      const client = StatusProClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      await client.get('/orders');

      const [url, options] = mockFetch.mock.calls[0];
      expect(url).toContain('/orders');
      expect(options.method).toBe('GET');
    });

    it('should make GET requests with query params', async () => {
      const response = new Response(JSON.stringify({ data: [] }), { status: 200 });
      mockFetch.mockResolvedValueOnce(response);

      const client = StatusProClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      await client.get('/orders', { status_code: 'st000002', exclude_cancelled: true });

      const [url] = mockFetch.mock.calls[0];
      expect(url).toContain('category=widgets');
      expect(url).toContain('active=true');
    });

    it('should make POST requests', async () => {
      const response = new Response(JSON.stringify({ id: 1 }), { status: 201 });
      mockFetch.mockResolvedValueOnce(response);

      const client = StatusProClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      await client.post('/orders', { status_code: "st000003", comment: "Shipped" });

      const [, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('POST');
      expect(options.body).toBe(JSON.stringify({ status_code: "st000003", comment: "Shipped" }));
    });

    it('should make PUT requests', async () => {
      const response = new Response(JSON.stringify({ id: 1 }), { status: 200 });
      mockFetch.mockResolvedValueOnce(response);

      const client = StatusProClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      await client.put('/orders/6110375248088', { status_code: 'st000003' });

      const [, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('PUT');
    });

    it('should make PATCH requests', async () => {
      const response = new Response(JSON.stringify({ id: 1 }), { status: 200 });
      mockFetch.mockResolvedValueOnce(response);

      const client = StatusProClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      await client.patch('/orders/6110375248088', { comment: 'Patched' });

      const [, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('PATCH');
    });

    it('should make DELETE requests', async () => {
      const response = new Response(null, { status: 204 });
      mockFetch.mockResolvedValueOnce(response);

      const client = StatusProClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      await client.delete('/orders/6110375248088');

      const [, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('DELETE');
    });
  });

  describe('sdk property', () => {
    it('should return SDK client', () => {
      const client = StatusProClient.withApiKey(TEST_API_KEY);
      expect(client.sdk).toBeDefined();
      expect(typeof client.sdk.request).toBe('function');
    });
  });

  describe('getConfig', () => {
    it('should return config object with client', () => {
      const client = StatusProClient.withApiKey(TEST_API_KEY);
      const config = client.getConfig();
      expect(config).toHaveProperty('client');
      expect(config.client).toBe(client.sdk);
    });
  });

  describe('configuration options', () => {
    it('should apply custom retry configuration', async () => {
      // Mock fetch that returns 429 to test retry
      const rateLimitResponse = new Response(null, { status: 429 });
      const successResponse = new Response(JSON.stringify({ data: [] }), { status: 200 });

      mockFetch.mockResolvedValueOnce(rateLimitResponse).mockResolvedValueOnce(successResponse);

      // Use real timers with minimal delay for this test
      vi.useFakeTimers();

      const client = StatusProClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        retry: { maxRetries: 1, backoffFactor: 0.001 },
      });

      const responsePromise = client.fetch('/orders', { method: 'POST' });

      // Advance timer to trigger retry
      await vi.advanceTimersByTimeAsync(10);

      const response = await responsePromise;
      expect(response.status).toBe(200);
      expect(mockFetch).toHaveBeenCalledTimes(2);

      vi.useRealTimers();
    });

    it('should disable auto-pagination when configured', async () => {
      const response = new Response(
        JSON.stringify({
          data: [{ id: 1 }],
          pagination: { page: 1, total_pages: 5 },
        }),
        { status: 200 }
      );
      mockFetch.mockResolvedValueOnce(response);

      const client = StatusProClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        autoPagination: false,
      });
      await client.get('/orders');

      // Should only make one request (no pagination)
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should apply custom pagination configuration', async () => {
      // Create responses for 3 pages
      const createPageResponse = (page: number) =>
        new Response(
          JSON.stringify({
            data: [{ id: page }],
            pagination: { page, total_pages: 10, per_page: 1 },
          }),
          { status: 200 }
        );

      mockFetch.mockImplementation(() => {
        const callCount = mockFetch.mock.calls.length;
        return Promise.resolve(createPageResponse(callCount));
      });

      const client = StatusProClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        pagination: { maxPages: 2 },
      });
      await client.get('/orders');

      // Should stop at maxPages=2
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });
});
