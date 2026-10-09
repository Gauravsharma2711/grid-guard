import { describe, expect, it } from 'vitest';
import { getAppConfig, normalizeApiBaseUrl } from './env';

describe('Environment Configuration', () => {
  describe('normalizeApiBaseUrl', () => {
    it('returns default URL when undefined or empty in development', () => {
      expect(normalizeApiBaseUrl(undefined)).toBe('http://localhost:8000');
      expect(normalizeApiBaseUrl('')).toBe('http://localhost:8000');
      expect(normalizeApiBaseUrl('   ')).toBe('http://localhost:8000');
    });

    it('does not fall back to localhost in production mode', () => {
      expect(normalizeApiBaseUrl(undefined, true)).toBe('');
      expect(normalizeApiBaseUrl('', true)).toBe('');
      expect(normalizeApiBaseUrl('   ', true)).toBe('');
    });

    it('strips trailing slashes from valid URLs', () => {
      expect(normalizeApiBaseUrl('http://localhost:8000/')).toBe('http://localhost:8000');
      expect(normalizeApiBaseUrl('https://api.gridguard.internal///')).toBe(
        'https://api.gridguard.internal'
      );
      expect(normalizeApiBaseUrl('https://grid-guard-api.onrender.com/', true)).toBe(
        'https://grid-guard-api.onrender.com'
      );
    });

    it('preserves valid custom port and host without slashes', () => {
      expect(normalizeApiBaseUrl('http://127.0.0.1:5678')).toBe('http://127.0.0.1:5678');
    });
  });

  describe('getAppConfig', () => {
    it('uses default fallback values when env is empty in development', () => {
      const cfg = getAppConfig({});
      expect(cfg.apiBaseUrl).toBe('http://localhost:8000');
      expect(cfg.isDev).toBe(true);
      expect(cfg.isProd).toBe(false);
    });

    it('does not fall back to localhost in production mode when VITE_API_BASE_URL is not set', () => {
      const cfg = getAppConfig({ MODE: 'production' });
      expect(cfg.apiBaseUrl).toBe('');
      expect(cfg.isDev).toBe(false);
      expect(cfg.isProd).toBe(true);
    });

    it('correctly reads custom VITE_API_BASE_URL in production', () => {
      const cfg = getAppConfig({
        VITE_API_BASE_URL: 'https://grid-guard-api.onrender.com',
        MODE: 'production',
      });
      expect(cfg.apiBaseUrl).toBe('https://grid-guard-api.onrender.com');
      expect(cfg.isDev).toBe(false);
      expect(cfg.isProd).toBe(true);
    });
  });
});
