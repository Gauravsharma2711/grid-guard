import React, { useCallback, useEffect, useState } from 'react';
import { AppShell } from './components/layout/AppShell';
import { OperationsCanvas } from './components/layout/LayoutPrimitives';
import { ComponentShowcase } from './components/showcase/ComponentShowcase';
import { Button } from './components/ui/Button/Button';
import { CodeSurface } from './components/ui/Surface/Surface';
import { InspectionQueueScreen } from './screens/InspectionQueueScreen/InspectionQueueScreen';
import { MeterAnalysisScreen } from './screens/MeterAnalysisScreen/MeterAnalysisScreen';
import { ModelInsightsScreen } from './screens/ModelInsightsScreen/ModelInsightsScreen';
import { OverviewScreen } from './screens/OverviewScreen/OverviewScreen';
import { apiClient } from './services/apiClient';
import type { PublicConfigResponse, ReadyResponse } from './types/api';

type NavigationTab = 'overview' | 'queue' | 'meter' | 'insights' | 'system' | 'showcase';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavigationTab>('overview');
  const [isApiOnline, setIsApiOnline] = useState<boolean | null>(null);
  const [selectedMeterId, setSelectedMeterId] = useState<string>('SAMPLE_SUSPICIOUS_STEPDOWN');

  // System info state
  const [systemReady, setSystemReady] = useState<ReadyResponse | null>(null);
  const [systemConfig, setSystemConfig] = useState<PublicConfigResponse | null>(null);
  const [isSystemLoading, setIsSystemLoading] = useState<boolean>(false);

  // Synchronize hash with active tab
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '') as NavigationTab;
      const validTabs: NavigationTab[] = [
        'overview',
        'queue',
        'meter',
        'insights',
        'system',
        'showcase',
      ];
      if (validTabs.includes(hash)) {
        setActiveTab(hash);
      }
    };

    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigateTo = (tab: NavigationTab) => {
    setActiveTab(tab);
    window.location.hash = `#${tab}`;
  };

  // Connection probe
  const probeConnection = useCallback(async () => {
    try {
      const ready = await apiClient.getReady();
      setIsApiOnline(ready.status === 'ready');
      setSystemReady(ready);
    } catch {
      setIsApiOnline(false);
      setSystemReady(null);
    }
  }, []);

  useEffect(() => {
    probeConnection();
    const interval = setInterval(probeConnection, 30000);
    return () => clearInterval(interval);
  }, [probeConnection]);

  // Load system config when system tab is opened
  useEffect(() => {
    if (activeTab === 'system') {
      setIsSystemLoading(true);
      Promise.allSettled([apiClient.getReady(), apiClient.getPublicConfig()])
        .then(([readyResult, configResult]) => {
          if (readyResult.status === 'fulfilled') setSystemReady(readyResult.value);
          if (configResult.status === 'fulfilled') setSystemConfig(configResult.value);
        })
        .finally(() => setIsSystemLoading(false));
    }
  }, [activeTab]);

  return (
    <AppShell
      activeNav={activeTab}
      onNavigate={(dest) => navigateTo(dest)}
      statusNode={
        isApiOnline ? (
          <span className="gg-header-probe gg-header-probe--online">
            <span className="gg-probe-dot gg-probe-dot--online" />
            API ONLINE
          </span>
        ) : (
          <span className="gg-header-probe gg-header-probe--offline">
            <span className="gg-probe-dot gg-probe-dot--offline" />
            API DISCONNECTED
          </span>
        )
      }
    >
      <OperationsCanvas>
        {activeTab === 'overview' && (
          <OverviewScreen
            onNavigateToQueue={() => navigateTo('queue')}
            onSelectMeter={(mId) => {
              setSelectedMeterId(mId);
              navigateTo('meter');
            }}
          />
        )}

        {activeTab === 'queue' && (
          <InspectionQueueScreen
            onSelectMeterForAnalysis={(mId) => {
              setSelectedMeterId(mId);
              navigateTo('meter');
            }}
          />
        )}

        {activeTab === 'meter' && (
          <MeterAnalysisScreen
            initialMeterId={selectedMeterId}
            onNavigateToQueue={() => navigateTo('queue')}
          />
        )}

        {activeTab === 'insights' && <ModelInsightsScreen />}

        {activeTab === 'system' && (
          <div className="gg-system-tab-container">
            <div className="gg-overview-header">
              <div className="gg-overview-title-block">
                <span className="gg-type-label gg-overview-kicker">System Introspection</span>
                <h1 className="gg-type-display gg-overview-title">FastAPI Architecture & Runtime</h1>
                <p className="gg-type-body gg-overview-subtitle">
                  Verified operational limits, inference readiness probes, and backend configuration contracts.
                </p>
              </div>

              <Button
                variant="secondary"
                size="compact"
                onClick={probeConnection}
                loading={isSystemLoading}
              >
                Probe Endpoints
              </Button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 'var(--gg-space-4)', marginTop: 'var(--gg-space-4)' }}>
              <div>
                <h3 className="gg-type-title" style={{ marginBottom: 'var(--gg-space-2)' }}>
                  Readiness Probe (/ready)
                </h3>
                <CodeSurface>
                  {JSON.stringify(
                    systemReady ?? {
                      status: 'unready',
                      model_loaded: false,
                      explainer_loaded: false,
                      note: 'FastAPI backend is offline or model booster is uninitialized.',
                    },
                    null,
                    2
                  )}
                </CodeSurface>
              </div>

              <div>
                <h3 className="gg-type-title" style={{ marginBottom: 'var(--gg-space-2)' }}>
                  Public Configuration (/api/v1/metadata/config)
                </h3>
                <CodeSurface>
                  {JSON.stringify(
                    systemConfig ?? {
                      api_version: '0.1.0',
                      input_cadence: 'daily',
                      limits: {
                        min_readings_per_meter: 14,
                        max_readings_per_meter: 730,
                        max_batch_size: 50,
                      },
                      financial_defaults: {
                        default_tariff: 6.0,
                        default_dispatch_cost: 500.0,
                        currency: 'INR',
                        recovery_factor: 1.0,
                        undetected_cycles: 12,
                      },
                      supported_decision_rules: ['env', 'cost_threshold', 'fixed_threshold'],
                      default_decision_rule: 'env',
                    },
                    null,
                    2
                  )}
                </CodeSurface>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'showcase' && <ComponentShowcase />}
      </OperationsCanvas>
    </AppShell>
  );
};
