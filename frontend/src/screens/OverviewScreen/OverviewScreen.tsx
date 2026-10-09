import React, { useCallback, useEffect, useState } from 'react';
import { Button } from '../../components/ui/Button/Button';
import { CurrencyValue, EnvMetric, ProbabilityMetric } from '../../components/ui/Financial/Financial';
import { StatusBadge } from '../../components/ui/Status/Status';
import { Surface } from '../../components/ui/Surface/Surface';
import { DataTable } from '../../components/ui/Table/DataTable';
import {
  VALIDATED_POLICY_COMPARISON,
  VALIDATED_TOP_TICKETS,
} from '../../data/validatedArtifacts';
import { apiClient } from '../../services/apiClient';
import type {
  InspectionTicketResponse,
  ReadyResponse,
} from '../../types/api';
import './OverviewScreen.css';

export interface OverviewScreenProps {
  onNavigateToQueue: () => void;
  onSelectMeter: (meterId: string) => void;
}

export const OverviewScreen: React.FC<OverviewScreenProps> = ({
  onNavigateToQueue,
  onSelectMeter,
}) => {
  const [isLiveConnected, setIsLiveConnected] = useState<boolean | null>(null);
  const [readyInfo, setReadyInfo] = useState<ReadyResponse | null>(null);
  const [topTickets, setTopTickets] = useState<InspectionTicketResponse[]>(VALIDATED_TOP_TICKETS);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>('');

  const primaryPolicy = VALIDATED_POLICY_COMPARISON[0];

  const fetchOverviewData = useCallback(async () => {
    setIsLoading(true);
    try {
      // Probe readiness
      const ready = await apiClient.getReady();
      setReadyInfo(ready);
      setIsLiveConnected(ready.status === 'ready');

      // Fetch top inspection queue from live API
      try {
        const queueRes = await apiClient.getInspectionQueue({
          max_inspections: 5,
          min_env: 0.0,
          min_probability: 0.0,
        });
        if (queueRes.tickets && queueRes.tickets.length > 0) {
          setTopTickets(queueRes.tickets);
        }
      } catch {
        // Fall back gracefully to verified top tickets
        setTopTickets(VALIDATED_TOP_TICKETS);
      }
    } catch {
      setIsLiveConnected(false);
      setReadyInfo(null);
      setTopTickets(VALIDATED_TOP_TICKETS);
    } finally {
      setIsLoading(false);
      setLastRefreshed(new Date().toLocaleTimeString());
    }
  }, []);

  useEffect(() => {
    fetchOverviewData();
  }, [fetchOverviewData]);

  const queueColumns = [
    {
      key: 'priority_rank',
      header: 'Rank',
      render: (t: InspectionTicketResponse) => (
        <span className="gg-type-mono gg-rank-pill">#{t.priority_rank ?? 1}</span>
      ),
    },
    {
      key: 'meter_id',
      header: 'Meter Identifier',
      render: (t: InspectionTicketResponse) => (
        <span className="gg-type-mono gg-meter-id-cell">{t.meter_id}</span>
      ),
    },
    {
      key: 'calibrated_probability',
      header: 'Tamper Risk',
      align: 'right' as const,
      render: (t: InspectionTicketResponse) => (
        <ProbabilityMetric probability={t.calibrated_probability} />
      ),
    },
    {
      key: 'estimated_recoverable_revenue',
      header: 'Est. Leakage',
      align: 'right' as const,
      render: (t: InspectionTicketResponse) => (
        <CurrencyValue amount={t.estimated_recoverable_revenue} />
      ),
    },
    {
      key: 'env',
      header: 'Expected Net Value',
      align: 'right' as const,
      render: (t: InspectionTicketResponse) => (
        <EnvMetric env={t.env} />
      ),
    },
    {
      key: 'actions',
      header: 'Action',
      align: 'right' as const,
      render: (t: InspectionTicketResponse) => (
        <Button
          variant="secondary"
          size="compact"
          onClick={() => onSelectMeter(t.meter_id)}
          aria-label={`Analyze meter ${t.meter_id}`}
        >
          Analyze
        </Button>
      ),
    },
  ];

  return (
    <div className="gg-overview-screen">
      {/* Page Title & Status Header */}
      <div className="gg-overview-header">
        <div className="gg-overview-title-block">
          <span className="gg-type-label gg-overview-kicker">Operational Command</span>
          <h1 className="gg-type-display gg-overview-title">Network Decision State</h1>
          <p className="gg-type-body gg-overview-subtitle">
            Non-technical loss detection, dynamic thresholding, and Expected Net Value prioritization.
          </p>
        </div>

        <div className="gg-overview-actions">
          <div className="gg-overview-conn-status">
            {isLiveConnected ? (
              <StatusBadge status="safe" label="Live FastAPI Connected" />
            ) : (
              <StatusBadge status="warning" label="Offline (Validated Artifacts)" />
            )}
            {lastRefreshed && (
              <span className="gg-type-caption gg-overview-timestamp">
                Refreshed {lastRefreshed}
              </span>
            )}
          </div>
          <Button
            variant="secondary"
            size="compact"
            onClick={fetchOverviewData}
            loading={isLoading}
            aria-label="Refresh operational data"
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Hero Financial Banner */}
      <Surface className="gg-overview-hero-surface">
        <div className="gg-overview-hero-content">
          <div className="gg-overview-hero-main">
            <span className="gg-type-label gg-hero-label">Total Expected Net Value (ENV)</span>
            <div className="gg-hero-value-row">
              <span className="gg-hero-value">
                ₹{primaryPolicy.expected_net_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className="gg-hero-badge">
                ENV &gt; 0 Economically Justified
              </span>
            </div>
            <p className="gg-type-caption gg-hero-desc">
              Cumulative economic benefit across {primaryPolicy.inspections_recommended.toLocaleString()} recommended field inspections after deducting ₹{primaryPolicy.expected_dispatch_cost.toLocaleString('en-IN')} in crew dispatch costs.
            </p>
          </div>

          <div className="gg-overview-hero-policy">
            <span className="gg-type-label gg-policy-kicker">Active Policy Rule</span>
            <span className="gg-type-section gg-policy-name">{primaryPolicy.name}</span>
            <span className="gg-type-mono gg-policy-formula">ENV = p × R - C_dispatch</span>
            <Button
              variant="primary"
              size="compact"
              onClick={onNavigateToQueue}
              className="gg-hero-queue-btn"
            >
              Open Inspection Queue →
            </Button>
          </div>
        </div>
      </Surface>

      {/* 4-Column Operational Summary Strip */}
      <div className="gg-overview-kpi-grid">
        <Surface className="gg-kpi-card">
          <span className="gg-type-label gg-kpi-label">Monitored Fleet</span>
          <span className="gg-type-section gg-kpi-value gg-type-mono">
            {primaryPolicy.total_candidates.toLocaleString()}
          </span>
          <span className="gg-type-caption gg-kpi-sub">Smart meters under evaluation</span>
        </Surface>

        <Surface className="gg-kpi-card">
          <span className="gg-type-label gg-kpi-label">Recommended Tickets</span>
          <span className="gg-type-section gg-kpi-value gg-type-mono">
            {primaryPolicy.inspections_recommended.toLocaleString()}
          </span>
          <span className="gg-type-caption gg-kpi-sub">
            {primaryPolicy.inspection_rate_pct}% network inspection rate
          </span>
        </Surface>

        <Surface className="gg-kpi-card">
          <span className="gg-type-label gg-kpi-label">Projected Gross Recovery</span>
          <span className="gg-type-section gg-kpi-value gg-type-mono">
            ₹{primaryPolicy.expected_gross_recovery.toLocaleString('en-IN', { minimumFractionDigits: 0 })}
          </span>
          <span className="gg-type-caption gg-kpi-sub">Probability-weighted revenue</span>
        </Surface>

        <Surface className="gg-kpi-card">
          <span className="gg-type-label gg-kpi-label">Crew Dispatch Cost</span>
          <span className="gg-type-section gg-kpi-value gg-type-mono">
            ₹{primaryPolicy.expected_dispatch_cost.toLocaleString('en-IN', { minimumFractionDigits: 0 })}
          </span>
          <span className="gg-type-caption gg-kpi-sub">₹500 fixed cost per inspection</span>
        </Surface>
      </div>

      {/* Model & System Health Probe */}
      <Surface className="gg-overview-system-bar">
        <div className="gg-system-bar-items">
          <div className="gg-system-metric">
            <span className="gg-type-label">Model Booster</span>
            <span className="gg-type-mono">
              {readyInfo?.model_version ?? 'phase6_cost_sensitive_v1'}
            </span>
          </div>
          <div className="gg-system-metric">
            <span className="gg-type-label">Engineered Features</span>
            <span className="gg-type-mono">{readyInfo?.feature_count ?? 60} causal inputs</span>
          </div>
          <div className="gg-system-metric">
            <span className="gg-type-label">SHAP Explainer</span>
            <span className="gg-type-mono">
              {readyInfo?.explainer_loaded ? 'Tree-SHAP Ready' : 'Loaded on Demand'}
            </span>
          </div>
          <div className="gg-system-metric">
            <span className="gg-type-label">Data Cadence</span>
            <span className="gg-type-mono">Daily AMI Aggregations</span>
          </div>
        </div>
      </Surface>

      {/* Prioritized Inspection Queue Preview */}
      <div className="gg-overview-section">
        <div className="gg-section-header-row">
          <div>
            <h2 className="gg-type-section">Top Inspection Work Orders</h2>
            <p className="gg-type-caption">
              Prioritized by Expected Net Value descending. Physical on-site verification required.
            </p>
          </div>
          <Button
            variant="secondary"
            size="compact"
            onClick={onNavigateToQueue}
          >
            View All ({primaryPolicy.inspections_recommended}) →
          </Button>
        </div>

        <DataTable<InspectionTicketResponse>
          data={topTickets}
          columns={queueColumns}
          keyExtractor={(t) => t.ticket_id}
          loading={isLoading}
          emptyMessage="No prioritized inspection candidates available."
          onRowClick={(t) => onSelectMeter(t.meter_id)}
        />
      </div>
    </div>
  );
};
