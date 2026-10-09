import { describe, expect, it } from 'vitest';
import { getAppConfig, normalizeApiBaseUrl } from './env';

describe('Environment Configuration', () => {
  describe('normalizeApiBaseUrl', () => {
    it('returns default URL when undefined or empty', () => {
      expect(normalizeApiBaseUrl(undefined)).toBe('http://localhost:8000');
      expect(normalizeApiBaseUrl('')).toBe('http://localhost:8000');
      expect(normalizeApiBaseUrl('   ')).toBe('http://localhost:8000');
    });

    it('strips trailing slashes from valid URLs', () => {
      expect(normalizeApiBaseUrl('http://localhost:8000/')).toBe('http://localhost:8000');
      expect(normalizeApiBaseUrl('https://api.gridguard.internal///')).toBe(
        'https://api.gridguard.internal'
      );
    });

    it('preserves valid custom port and host without slashes', () => {
      expect(normalizeApiBaseUrl('http://127.0.0.1:5678')).toBe('http://127.0.0.1:5678');
    });
  });

  describe('getAppConfig', () => {
    it('uses default fallback values when env is empty', () => {
      const cfg = getAppConfig({});
      expect(cfg.apiBaseUrl).toBe('http://localhost:8000');
      expect(cfg.isDev).toBe(true);
      expect(cfg.isProd).toBe(false);
    });

    it('correctly reads custom VITE_API_BASE_URL', () => {
      const cfg = getAppConfig({
        VITE_API_BASE_URL: 'http://custom-host:9000',
        MODE: 'production',
      });
      expect(cfg.apiBaseUrl).toBe('http://custom-host:9000');
      expect(cfg.isDev).toBe(false);
      expect(cfg.isProd).toBe(true);
    });
  });
});
