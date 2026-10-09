import React, { useEffect, useState } from 'react';
import { AppShell } from './components/layout/AppShell';
import { NavDestination } from './components/layout/AppHeader';
import { DecisionCanvas } from './components/layout/LayoutPrimitives';
import { Button } from './components/ui/Button/Button';
import { StatusBadge } from './components/ui/Status/Status';
import { Surface, Divider, CodeSurface } from './components/ui/Surface/Surface';
import { EmptyState } from './components/ui/Feedback/Feedback';
import { ComponentShowcase } from './components/showcase/ComponentShowcase';
import { config } from './config/env';
import { apiClient } from './services/apiClient';
import type { HealthResponse } from './types/api';

interface HealthState {
  status: 'checking' | 'connected' | 'disconnected';
  data?: HealthResponse;
  error?: string;
}

export const App: React.FC = () => {
  const [currentNav, setCurrentNav] = useState<NavDestination>('overview');
  const [health, setHealth] = useState<HealthState>({ status: 'checking' });

  const checkConnection = async () => {
    setHealth({ status: 'checking' });
    try {
      const data = await apiClient.getHealth({ timeoutMs: 4000 });
      setHealth({ status: 'connected', data });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Backend unreachable';
      setHealth({ status: 'disconnected', error: message });
    }
  };

  useEffect(() => {
    void checkConnection();

    // Check if URL hash specifies #showcase
    if (window.location.hash === '#showcase') {
      setCurrentNav('showcase');
    }
  }, []);

  const renderStatusBadge = () => {
    if (health.status === 'checking') {
      return <StatusBadge status="neutral" label="PROBING BACKEND" />;
    }
    if (health.status === 'connected') {
      return (
        <StatusBadge
          status="safe"
          label={`API ONLINE (v${health.data?.api_version ?? '0.1.0'})`}
        />
      );
    }
    return <StatusBadge status="warning" label="API DISCONNECTED" />;
  };

  const renderContent = () => {
    if (currentNav === 'showcase') {
      return <ComponentShowcase />;
    }

    if (currentNav === 'queue') {
      return (
        <DecisionCanvas>
          <EmptyState
            title="Inspection Queue View"
            description="The prioritized work order queue table will be connected to live FastAPI endpoints (/api/v1/inspection/queue) in Phase 3."
            actionLabel="Return to Overview"
            onAction={() => setCurrentNav('overview')}
          />
        </DecisionCanvas>
      );
    }

    if (currentNav === 'meter') {
      return (
        <DecisionCanvas>
          <EmptyState
            title="Meter Analysis & Workbench"
            description="The 180-day consumption visualizer and forensic evidence drawer will be delivered in Phase 3."
            actionLabel="Return to Overview"
            onAction={() => setCurrentNav('overview')}
          />
        </DecisionCanvas>
      );
    }

    if (currentNav === 'insights') {
      return (
        <DecisionCanvas>
          <EmptyState
            title="Model Insights & Benchmarks"
            description="Comparative PR-AUC, Tree-SHAP global importance, and financial policy comparisons will be delivered in Phase 4."
            actionLabel="Return to Overview"
            onAction={() => setCurrentNav('overview')}
          />
        </DecisionCanvas>
      );
    }

    if (currentNav === 'system') {
      return (
        <DecisionCanvas>
          <EmptyState
            title="System Status & Introspection"
            description="Deep model booster diagnostics, feature schema, and FastAPI introspection (/api/v1/metadata) will be delivered in Phase 4."
            actionLabel="Return to Overview"
            onAction={() => setCurrentNav('overview')}
          />
        </DecisionCanvas>
      );
    }

    // Default: 'overview'
    return (
      <DecisionCanvas>
        <div className="gg-section-meta" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <span style={{ fontFamily: 'var(--gg-font-mono)', fontSize: '10px', fontWeight: 600, letterSpacing: '0.06em', color: 'var(--gg-ink)', backgroundColor: 'var(--gg-signal)', padding: '2px 6px', borderRadius: '4px' }}>
            PHASE 2 ARCHITECTURE
          </span>
          <span style={{ color: 'var(--gg-muted)', fontSize: '12px' }}>•</span>
          <span style={{ fontFamily: 'var(--gg-font-mono)', fontSize: '10px', color: 'var(--gg-muted)', letterSpacing: '0.05em' }}>
            DESIGN SYSTEM &amp; REUSABLE COMPONENTS
          </span>
        </div>

        <h1 className="gg-type-display" style={{ marginBottom: '16px' }}>
          Calm, financially rational smart-meter inspection analytics.
        </h1>

        <p className="gg-type-body" style={{ marginBottom: '32px' }}>
          Grid-Guard evaluates non-technical loss risks using cost-sensitive learning,
          temporal feature engineering, and dynamic Expected Net Value (ENV) optimization.
        </p>

        {/* Foundation & Architecture Surface */}
        <Surface elevation="subtle" padded style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
            <h2 className="gg-type-record-title">Frontend Architecture Baseline</h2>
            <span style={{ fontFamily: 'var(--gg-font-mono)', fontSize: '10px', fontWeight: 600, padding: '2px 8px', borderRadius: '4px', backgroundColor: 'var(--gg-canvas)', border: '1px solid var(--gg-rule)', color: 'var(--gg-ink-soft)' }}>
              PHASE 2 COMPLETE
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span className="gg-type-metadata">DESIGN SYSTEM</span>
              <span className="gg-type-body-sm" style={{ fontWeight: 600, color: 'var(--gg-ink)' }}>
                Calm Proof Flow (/designsystem.md)
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span className="gg-type-metadata">COMPONENT SYSTEM</span>
              <span className="gg-type-body-sm" style={{ fontWeight: 600, color: 'var(--gg-ink)' }}>
                11 Primitives + Shared Shell
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span className="gg-type-metadata">BACKEND TARGET</span>
              <span className="gg-type-code" style={{ color: 'var(--gg-ink)' }}>
                {config.apiBaseUrl}
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span className="gg-type-metadata">STREAMLIT STATUS</span>
              <span className="gg-type-body-sm" style={{ fontWeight: 600, color: 'var(--gg-ink)' }}>
                Active &amp; Preserved (:8501)
              </span>
            </div>
          </div>

          <Divider spacing="md" />

          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
            <Button
              variant="primary"
              onClick={() => void checkConnection()}
              loading={health.status === 'checking'}
            >
              Verify Backend Connection
            </Button>

            <Button
              variant="secondary"
              onClick={() => setCurrentNav('showcase')}
            >
              View Component Showcase
            </Button>

            <a
              href={`${config.apiBaseUrl}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ textDecoration: 'none' }}
            >
              <Button variant="text">Open FastAPI Swagger ↗</Button>
            </a>
          </div>

          {health.status === 'disconnected' && (
            <div style={{ padding: '16px', borderRadius: '6px', backgroundColor: 'var(--gg-canvas)', border: '1px solid var(--gg-rule)', marginTop: '16px' }}>
              <div style={{ marginBottom: '8px' }}>
                <strong style={{ fontFamily: 'var(--gg-font-body)', fontSize: '13px', color: 'var(--gg-ink)' }}>
                  FastAPI Backend Offline
                </strong>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--gg-ink-soft)', lineHeight: 1.5, marginBottom: '12px' }}>
                The React frontend is running independently without mock data. To connect to
                live inference, launch the backend service:
              </p>
              <CodeSurface>
                uv run uvicorn grid_guard.api.main:app --port 8000
              </CodeSurface>
            </div>
          )}

          {health.status === 'connected' && (
            <div style={{ padding: '16px', borderRadius: '6px', backgroundColor: '#f6faf7', border: '1px solid rgba(63, 139, 97, 0.25)', marginTop: '16px' }}>
              <strong style={{ fontFamily: 'var(--gg-font-body)', fontSize: '13px', color: 'var(--gg-safe)' }}>
                FastAPI Connected Successfully
              </strong>
              <p style={{ fontSize: '12px', color: 'var(--gg-ink-soft)', lineHeight: 1.5, marginTop: '4px' }}>
                Service <code>{health.data?.service}</code> is responsive at {config.apiBaseUrl}.
                Ready to serve Phase 3 core dashboard views.
              </p>
            </div>
          )}
        </Surface>

        {/* Phase Boundary Note */}
        <footer style={{ borderTop: '1px solid var(--gg-rule)', paddingTop: '24px' }}>
          <span className="gg-type-metadata">PHASE BOUNDARY</span>
          <p className="gg-type-body-sm" style={{ color: 'var(--gg-muted)', marginTop: '8px' }}>
            Phase 2 establishes the complete reusable component system, design tokens, responsive
            shell, and typed API client. Core operational dashboard views (Fleet Overview, Ranked
            Queue, Single-Meter Workbench) will be connected to live inference in Phase 3.
          </p>
        </footer>
      </DecisionCanvas>
    );
  };

  return (
    <AppShell
      activeNav={currentNav}
      onNavigate={(dest) => setCurrentNav(dest)}
      statusNode={renderStatusBadge()}
    >
      {renderContent()}
    </AppShell>
  );
};
