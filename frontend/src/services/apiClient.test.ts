import { describe, expect, it, vi, beforeEach } from 'vitest';
import { ApiClient, ApiClientError } from './apiClient';

describe('ApiClient', () => {
  const client = new ApiClient('http://test-api:8000', 500);

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('successfully fetches health probe with correct headers', async () => {
    const mockHealth = { status: 'ok', service: 'grid-guard-api', api_version: '0.1.0' };
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(mockHealth), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );

    const result = await client.getHealth();
    expect(result).toEqual(mockHealth);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      'http://test-api:8000/health',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          Accept: 'application/json',
        }),
      })
    );
  });

  it('throws structured ApiClientError on HTTP 400 error response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Insufficient history: 10 readings' }), {
        status: 400,
        statusText: 'Bad Request',
        headers: { 'Content-Type': 'application/json' },
      })
    );

    await expect(
      client.predictSingle({
        meter_id: 'CONS_9999',
        readings: [],
      })
    ).rejects.toThrow(ApiClientError);
  });

  it('throws ApiClientError on network failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Connection refused'));

    await expect(client.getReady()).rejects.toThrow(/Network connection/);
  });

  it('handles request timeout via AbortController', async () => {
    const abortError = new DOMException('The operation was aborted', 'AbortError');
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(abortError);

    await expect(client.getHealth({ timeoutMs: 50 })).rejects.toThrow(/timed out/);
  });
});
