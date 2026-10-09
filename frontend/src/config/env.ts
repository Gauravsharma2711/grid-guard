/**
 * Application environment configuration.
 *
 * Centralizes access to Vite environment variables with validation
 * and safe defaults for local development.
 */

export interface AppConfig {
  /** Base URL for the Grid-Guard FastAPI backend service */
  apiBaseUrl: string;
  /** Development mode indicator */
  isDev: boolean;
  /** Production mode indicator */
  isProd: boolean;
}

const DEFAULT_API_BASE_URL = 'http://localhost:8000';

/**
 * Validates and normalizes an API base URL string.
 * Strips trailing slashes to guarantee consistent endpoint concatenation.
 * In production mode, does not silently fall back to localhost.
 */
export function normalizeApiBaseUrl(url: string | undefined, isProd: boolean = false): string {
  if (!url || typeof url !== 'string' || url.trim() === '') {
    if (isProd) {
      // In production mode, do not silently point to developer localhost
      return '';
    }
    return DEFAULT_API_BASE_URL;
  }
  const trimmed = url.trim();
  // Strip any trailing slashes
  return trimmed.replace(/\/+$/, '');
}

/**
 * Resolves the application configuration from Vite environment variables.
 */
export function getAppConfig(
  env: Record<string, string | undefined> = import.meta.env
): AppConfig {
  const mode = env['MODE'] ?? 'development';
  const isDev = mode === 'development';
  const isProd = mode === 'production';

  const rawUrl = env['VITE_API_BASE_URL'];
  const apiBaseUrl = normalizeApiBaseUrl(rawUrl, isProd);

  return {
    apiBaseUrl,
    isDev,
    isProd,
  };
}

export const config: AppConfig = getAppConfig();
