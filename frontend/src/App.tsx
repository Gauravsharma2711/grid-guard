import React, { useEffect, useState } from 'react';
import { config } from './config/env';
import { apiClient } from './services/apiClient';
import type { HealthResponse } from './types/api';
import './App.css';

interface HealthState {
  status: 'checking' | 'connected' | 'disconnected';
  data?: HealthResponse;
  error?: string;
}

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthState>({ status: 'checking' });

  const checkConnection = async () => {
    setHealth({ status: 'checking' });
    try {
      const data = await apiClient.getHealth();
      setHealth({ status: 'connected', data });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Backend unreachable';
      setHealth({ status: 'disconnected', error: message });
    }
  };

  useEffect(() => {
    void checkConnection();
  }, []);

  return (
    <div className="gg-app">
      {/* 5. Navigation System & 6.1 Header */}
      <header className="gg-header" role="banner">
        <div className="gg-header-container">
          <div className="gg-brand">
            <span className="gg-logo-mark" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path
                  d="M13 2L3 14H12L11 22L21 10H12L13 2Z"
                  fill="var(--gg-signal)"
                  stroke="var(--gg-ink)"
                  strokeWidth="1.75"
                  strokeLinejoin="round"
                />
              </svg>
            </span>
            <div className="gg-wordmark">
              <span className="gg-product-name">GRID-GUARD</span>
              <span className="gg-product-tagline">NTL Detection Platform</span>
            </div>
          </div>

          <nav className="gg-nav" aria-label="Operational Views">
            <span className="gg-nav-item gg-nav-item--active" aria-current="page">
              Overview
            </span>
            <span className="gg-nav-item gg-nav-item--disabled" title="Phase 3 Deliverable">
              Inspection Queue
            </span>
            <span className="gg-nav-item gg-nav-item--disabled" title="Phase 3 Deliverable">
              Meter Analysis
            </span>
            <span className="gg-nav-item gg-nav-item--disabled" title="Phase 4 Deliverable">
              Model Insights
            </span>
            <span className="gg-nav-item gg-nav-item--disabled" title="Phase 4 Deliverable">
              System Status
            </span>
          </nav>

          <div className="gg-header-status">
            {health.status === 'checking' && (
              <span className="gg-status-pill gg-status-pill--checking" aria-live="polite">
                <span className="gg-status-dot" aria-hidden="true" />
                <span className="gg-mono-meta">PROBING BACKEND</span>
              </span>
            )}
            {health.status === 'connected' && (
              <span className="gg-status-pill gg-status-pill--safe" aria-live="polite">
                <span className="gg-status-dot" aria-hidden="true" />
                <span className="gg-mono-meta">
                  API ONLINE (v{health.data?.api_version ?? '1.0.0'})
                </span>
              </span>
            )}
            {health.status === 'disconnected' && (
              <span className="gg-status-pill gg-status-pill--warning" aria-live="polite">
                <span className="gg-status-dot" aria-hidden="true" />
                <span className="gg-mono-meta">API DISCONNECTED</span>
              </span>
            )}
          </div>
        </div>
      </header>

      {/* 4.3 Decision Canvas Layout */}
      <main className="gg-main-canvas" role="main">
        <div className="gg-content-column">
          <div className="gg-section-meta">
            <span className="gg-meta-badge">PHASE 1 FOUNDATION</span>
            <span className="gg-meta-separator">•</span>
            <span className="gg-meta-text">REACT + TYPESCRIPT MIGRATION</span>
          </div>

          <h1 className="gg-display-title">
            Calm, financially rational smart-meter inspection analytics.
          </h1>

          <p className="gg-lead-text">
            Grid-Guard evaluates non-technical loss risks using cost-sensitive learning,
            temporal feature engineering, and dynamic Expected Net Value (ENV) optimization.
          </p>

          {/* Operational Foundation Card */}
          <section className="gg-foundation-surface" aria-labelledby="foundation-status-heading">
            <div className="gg-surface-header">
              <h2 id="foundation-status-heading" className="gg-surface-title">
                Frontend Architecture Baseline
              </h2>
              <span className="gg-tag">VERIFIED</span>
            </div>

            <div className="gg-spec-grid">
              <div className="gg-spec-item">
                <span className="gg-spec-label">RUNTIME FOUNDATION</span>
                <span className="gg-spec-value">React 18 • TypeScript 5.6 • Vite 5.4</span>
              </div>
              <div className="gg-spec-item">
                <span className="gg-spec-label">DESIGN SYSTEM</span>
                <span className="gg-spec-value">Calm Proof Flow (/designsystem.md)</span>
              </div>
              <div className="gg-spec-item">
                <span className="gg-spec-label">BACKEND TARGET</span>
                <span className="gg-spec-value gg-spec-value--mono">{config.apiBaseUrl}</span>
              </div>
              <div className="gg-spec-item">
                <span className="gg-spec-label">STREAMLIT STATUS</span>
                <span className="gg-spec-value">Active &amp; Preserved (:8501)</span>
              </div>
            </div>

            <div className="gg-divider" />

            <div className="gg-action-row">
              <button
                type="button"
                className="gg-btn gg-btn--primary"
                onClick={() => void checkConnection()}
                disabled={health.status === 'checking'}
              >
                {health.status === 'checking' ? 'Checking Connection...' : 'Verify Backend Connection'}
              </button>

              <a
                href={`${config.apiBaseUrl}/docs`}
                target="_blank"
                rel="noopener noreferrer"
                className="gg-btn gg-btn--secondary"
              >
                Open FastAPI Swagger
              </a>
            </div>

            {health.status === 'disconnected' && (
              <div className="gg-callout gg-callout--neutral" role="status">
                <div className="gg-callout-header">
                  <span className="gg-callout-title">FastAPI Backend Offline</span>
                </div>
                <p className="gg-callout-body">
                  The React frontend is running independently without mock data. To connect to
                  live inference, start the backend with:
                </p>
                <pre className="gg-code-block">
                  <code>uv run uvicorn grid_guard.api.main:app --port 8000</code>
                </pre>
              </div>
            )}

            {health.status === 'connected' && (
              <div className="gg-callout gg-callout--safe" role="status">
                <div className="gg-callout-header">
                  <span className="gg-callout-title">FastAPI Connected Successfully</span>
                </div>
                <p className="gg-callout-body">
                  Service <code>{health.data?.service}</code> is responsive at {config.apiBaseUrl}.
                  Ready to serve Phase 2 component integrations.
                </p>
              </div>
            )}
          </section>

          {/* Phase Roadmap Note */}
          <footer className="gg-roadmap-note">
            <span className="gg-mono-meta">PHASE BOUNDARY</span>
            <p>
              Phase 1 establishes the verified React + TypeScript runtime, strict compiler checks,
              testing harness, and design token integration. Full operational dashboards, inspection
              tables, and SHAP explainers are scheduled for delivery in Phases 2–4.
            </p>
          </footer>
        </div>
      </main>
    </div>
  );
};
