/**
 * Type-safe HTTP client for communicating with the Grid-Guard FastAPI backend.
 * Provides timeout management, structured errors, and typed contracts.
 */

import { config } from '../config/env';
import type {
  BatchPredictionRequest,
  BatchPredictionResponse,
  HealthResponse,
  InspectionQueueRequest,
  InspectionQueueResponse,
  InspectionTicketResponse,
  ModelMetadataResponse,
  PublicConfigResponse,
  ReadyResponse,
  SingleMeterPredictionRequest,
  SingleMeterPredictionResponse,
} from '../types/api';

export class ApiClientError extends Error {
  public readonly status?: number;
  public readonly details?: unknown;

  constructor(message: string, status?: number, details?: unknown) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.details = details;
  }
}

export interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

export class ApiClient {
  private readonly baseUrl: string;
  private readonly defaultTimeoutMs: number;

  constructor(baseUrl: string = config.apiBaseUrl, defaultTimeoutMs: number = 10000) {
    this.baseUrl = baseUrl;
    this.defaultTimeoutMs = defaultTimeoutMs;
  }

  private async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { timeoutMs = this.defaultTimeoutMs, ...fetchOptions } = options;
    const url = `${this.baseUrl}${path.startsWith('/') ? path : `/${path}`}`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    // If caller provided a signal, link it
    if (fetchOptions.signal) {
      fetchOptions.signal.addEventListener('abort', () => controller.abort());
    }

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          ...fetchOptions.headers,
        },
      });

      if (!response.ok) {
        let errorDetails: unknown = null;
        try {
          errorDetails = await response.json();
        } catch {
          // Non-JSON response
        }

        throw new ApiClientError(
          `API request to ${path} failed with HTTP ${response.status}`,
          response.status,
          errorDetails
        );
      }

      return (await response.json()) as T;
    } catch (err) {
      if (err instanceof ApiClientError) {
        throw err;
      }

      if (err instanceof DOMException && err.name === 'AbortError') {
        throw new ApiClientError(`Request to ${path} timed out after ${timeoutMs}ms`);
      }

      const message = err instanceof Error ? err.message : 'Unknown network failure';
      throw new ApiClientError(`Network connection to ${url} failed: ${message}`);
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /* ------------------------------------------------------------------------
     1. System Health & Readiness
     ------------------------------------------------------------------------ */

  /**
   * Process liveness probe (GET /health).
   */
  public async getHealth(options?: RequestOptions): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health', { method: 'GET', ...options });
  }

  /**
   * Model & explainer readiness probe (GET /ready).
   */
  public async getReady(options?: RequestOptions): Promise<ReadyResponse> {
    return this.request<ReadyResponse>('/ready', { method: 'GET', ...options });
  }

  /* ------------------------------------------------------------------------
     2. Metadata & Introspection
     ------------------------------------------------------------------------ */

  /**
   * Checkpoint & feature introspection (GET /api/v1/metadata/model).
   */
  public async getModelMetadata(options?: RequestOptions): Promise<ModelMetadataResponse> {
    return this.request<ModelMetadataResponse>('/api/v1/metadata/model', {
      method: 'GET',
      ...options,
    });
  }

  /**
   * Operational limits & financial defaults (GET /api/v1/metadata/config).
   */
  public async getPublicConfig(options?: RequestOptions): Promise<PublicConfigResponse> {
    return this.request<PublicConfigResponse>('/api/v1/metadata/config', {
      method: 'GET',
      ...options,
    });
  }

  /* ------------------------------------------------------------------------
     3. Inference & Prediction
     ------------------------------------------------------------------------ */

  /**
   * Single meter evaluation (POST /api/v1/predict).
   */
  public async predictSingle(
    payload: SingleMeterPredictionRequest,
    options?: RequestOptions
  ): Promise<SingleMeterPredictionResponse> {
    return this.request<SingleMeterPredictionResponse>('/api/v1/predict', {
      method: 'POST',
      body: JSON.stringify(payload),
      ...options,
    });
  }

  /**
   * Batch meter evaluation (POST /api/v1/predict/batch).
   */
  public async predictBatch(
    payload: BatchPredictionRequest,
    options?: RequestOptions
  ): Promise<BatchPredictionResponse> {
    return this.request<BatchPredictionResponse>('/api/v1/predict/batch', {
      method: 'POST',
      body: JSON.stringify(payload),
      ...options,
    });
  }

  /* ------------------------------------------------------------------------
     4. Field Inspection Work Orders
     ------------------------------------------------------------------------ */

  /**
   * Generate forensic inspection ticket (POST /api/v1/inspection/ticket).
   */
  public async generateTicket(
    payload: SingleMeterPredictionRequest,
    options?: RequestOptions
  ): Promise<InspectionTicketResponse> {
    return this.request<InspectionTicketResponse>('/api/v1/inspection/ticket', {
      method: 'POST',
      body: JSON.stringify(payload),
      ...options,
    });
  }

  /**
   * Query prioritized inspection queue (POST /api/v1/inspection/queue).
   */
  public async getInspectionQueue(
    payload: InspectionQueueRequest = {},
    options?: RequestOptions
  ): Promise<InspectionQueueResponse> {
    return this.request<InspectionQueueResponse>('/api/v1/inspection/queue', {
      method: 'POST',
      body: JSON.stringify(payload),
      ...options,
    });
  }
}

export const apiClient = new ApiClient();
