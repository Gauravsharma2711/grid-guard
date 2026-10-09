/**
 * Type-safe HTTP client for communicating with the Grid-Guard FastAPI service.
 */

import { config } from '../config/env';
import type { HealthResponse, PublicConfigResponse, ReadyResponse } from '../types/api';

export class ApiClientError extends Error {
  public readonly status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
  }
}

export class ApiClient {
  private readonly baseUrl: string;

  constructor(baseUrl: string = config.apiBaseUrl) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        throw new ApiClientError(
          `Request to ${path} failed with HTTP ${response.status} (${response.statusText})`,
          response.status
        );
      }

      return (await response.json()) as T;
    } catch (err) {
      if (err instanceof ApiClientError) {
        throw err;
      }
      const message = err instanceof Error ? err.message : 'Unknown network failure';
      throw new ApiClientError(`Network connection to ${url} failed: ${message}`);
    }
  }

  /**
   * Health liveness probe (GET /health).
   */
  public async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  /**
   * Service readiness probe (GET /ready).
   */
  public async getReady(): Promise<ReadyResponse> {
    return this.request<ReadyResponse>('/ready');
  }

  /**
   * Public operational config introspection (GET /api/v1/metadata/config).
   */
  public async getPublicConfig(): Promise<PublicConfigResponse> {
    return this.request<PublicConfigResponse>('/api/v1/metadata/config');
  }
}

export const apiClient = new ApiClient();
