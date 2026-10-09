import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Button } from '../../components/ui/Button/Button';
import { FilterChip } from '../../components/ui/FilterChip/FilterChip';
import {
  CurrencyValue,
  EnvMetric,
  FinancialSummaryBlock,
  ProbabilityMetric,
} from '../../components/ui/Financial/Financial';
import { FormField, NumberInput, TextInput } from '../../components/ui/Input/Input';
import { Drawer } from '../../components/ui/Overlay/Overlay';
import { StatusBadge } from '../../components/ui/Status/Status';
import { Surface } from '../../components/ui/Surface/Surface';
import { DataTable } from '../../components/ui/Table/DataTable';
import { InspectionTicketView } from '../../components/tickets/InspectionTicketView';
import { VALIDATED_TOP_TICKETS } from '../../data/validatedArtifacts';
import { apiClient } from '../../services/apiClient';
import type { InspectionTicketResponse } from '../../types/api';
import { exportQueueAsCsv, exportTicketAsJson } from '../../utils/exportUtils';
import './InspectionQueueScreen.css';

export interface InspectionQueueScreenProps {
  onSelectMeterForAnalysis: (meterId: string) => void;
}

export const InspectionQueueScreen: React.FC<InspectionQueueScreenProps> = ({
  onSelectMeterForAnalysis,
}) => {
  // Query state
  const [minEnv, setMinEnv] = useState<number>(0);
  const [minProb, setMinProb] = useState<number>(0.0);
  const [maxInspections, setMaxInspections] = useState<number>(50);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Results state
  const [tickets, setTickets] = useState<InspectionTicketResponse[]>(VALIDATED_TOP_TICKETS);
  const [totalExpectedRecovery, setTotalExpectedRecovery] = useState<number>(0);
  const [totalDispatchCost, setTotalDispatchCost] = useState<number>(0);
  const [totalNetValue, setTotalNetValue] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLiveApi, setIsLiveApi] = useState<boolean>(false);
  const [selectedTicket, setSelectedTicket] = useState<InspectionTicketResponse | null>(null);
  const [fullDocTicket, setFullDocTicket] = useState<InspectionTicketResponse | null>(null);

  const fetchQueue = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.getInspectionQueue({
        min_env: minEnv,
        min_probability: minProb,
        max_inspections: maxInspections,
      });

      if (res.tickets && res.tickets.length > 0) {
        setTickets(res.tickets);
        setTotalExpectedRecovery(res.total_expected_recovery);
        setTotalDispatchCost(res.total_dispatch_cost);
        setTotalNetValue(res.total_net_value);
        setIsLiveApi(true);
      } else {
        setTickets([]);
        setTotalExpectedRecovery(0);
        setTotalDispatchCost(0);
        setTotalNetValue(0);
        setIsLiveApi(true);
      }
    } catch {
      // Offline fallback: filter validated top tickets client-side
      const filtered = VALIDATED_TOP_TICKETS.filter(
        (t) => t.env >= minEnv && t.calibrated_probability >= minProb
      ).slice(0, maxInspections);

      setTickets(filtered);
      setTotalExpectedRecovery(
        filtered.reduce((sum, t) => sum + t.expected_gross_recovery, 0)
      );
      setTotalDispatchCost(filtered.reduce((sum, t) => sum + t.dispatch_cost, 0));
      setTotalNetValue(filtered.reduce((sum, t) => sum + t.env, 0));
      setIsLiveApi(false);
    } finally {
      setIsLoading(false);
    }
  }, [minEnv, minProb, maxInspections]);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  // Client-side text search by Meter ID
  const displayTickets = useMemo(() => {
    if (!searchQuery.trim()) return tickets;
    const q = searchQuery.toLowerCase().trim();
    return tickets.filter(
      (t) =>
        t.meter_id.toLowerCase().includes(q) ||
        t.ticket_id.toLowerCase().includes(q) ||
        t.feeder_id.toLowerCase().includes(q)
    );
  }, [tickets, searchQuery]);

  const queueColumns = [
    {
      key: 'priority_rank',
      header: 'Rank',
      render: (t: InspectionTicketResponse) => (
        <span className="gg-type-mono gg-queue-rank">#{t.priority_rank ?? '-'}</span>
      ),
    },
    {
      key: 'meter_id',
      header: 'Meter Identifier',
      render: (t: InspectionTicketResponse) => (
        <div className="gg-meter-cell-group">
          <span className="gg-type-mono gg-meter-id-text">{t.meter_id}</span>
          <span className="gg-type-caption gg-meter-sub">{t.feeder_id} • {t.customer_type}</span>
        </div>
      ),
    },
    {
      key: 'calibrated_probability',
      header: 'Risk Probability',
      align: 'right' as const,
      render: (t: InspectionTicketResponse) => (
        <ProbabilityMetric probability={t.calibrated_probability} />
      ),
    },
    {
      key: 'estimated_recoverable_revenue',
      header: 'Projected Revenue',
      align: 'right' as const,
      render: (t: InspectionTicketResponse) => (
        <CurrencyValue amount={t.estimated_recoverable_revenue} />
      ),
    },
    {
      key: 'dispatch_cost',
      header: 'Dispatch Cost',
      align: 'right' as const,
      render: (t: InspectionTicketResponse) => (
        <CurrencyValue amount={t.dispatch_cost} />
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
      key: 'signatures_summary',
      header: 'Anomaly Signatures',
      render: (t: InspectionTicketResponse) => (
        <span className="gg-type-caption gg-sig-summary-text" title={t.signatures_summary}>
          {t.signatures_summary}
        </span>
      ),
    },
    {
      key: 'data_quality_status',
      header: 'Data Quality',
      render: (t: InspectionTicketResponse) => (
        <StatusBadge
          status={t.data_quality_status === 'good' ? 'safe' : 'warning'}
          label={t.data_quality_status}
        />
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
          onClick={(e) => {
            e.stopPropagation();
            setSelectedTicket(t);
          }}
          aria-label={`View ticket for meter ${t.meter_id}`}
        >
          View Ticket
        </Button>
      ),
    },
  ];

  if (fullDocTicket) {
    return (
      <div className="gg-queue-screen">
        <InspectionTicketView
          ticket={fullDocTicket}
          onClose={() => setFullDocTicket(null)}
          onAnalyzeMeter={(mId) => {
            setFullDocTicket(null);
            onSelectMeterForAnalysis(mId);
          }}
        />
      </div>
    );
  }

  return (
    <div className="gg-queue-screen">
      {/* Screen Header */}
      <div className="gg-queue-header">
        <div className="gg-queue-title-group">
          <span className="gg-type-label gg-queue-kicker">Field Prioritization</span>
          <h1 className="gg-type-display gg-queue-title">Inspection Work Orders</h1>
          <p className="gg-type-body gg-queue-subtitle">
            Ranked strictly by Expected Net Value (ENV = p × R - C_dispatch) descending.
          </p>
        </div>

        <div className="gg-queue-header-actions">
          <Button
            variant="secondary"
            size="compact"
            onClick={() => exportQueueAsCsv(displayTickets)}
            aria-label="Export inspection queue as CSV"
          >
            Export Queue (CSV)
          </Button>
          <div className="gg-queue-header-status">
            {isLiveApi ? (
              <StatusBadge status="safe" label="Live API Queue" />
            ) : (
              <StatusBadge status="warning" label="Offline Validated Candidates" />
            )}
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <Surface className="gg-queue-filter-surface">
        <div className="gg-filter-bar-grid">
          <div className="gg-filter-search">
            <FormField label="Search Meter ID or Feeder" htmlFor="queue-search">
              <TextInput
                id="queue-search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by meter ID, ticket ID, or feeder..."
                mono
              />
            </FormField>
          </div>

          <div className="gg-filter-item">
            <FormField label="Min Expected Net Value" htmlFor="min-env-input">
              <NumberInput
                id="min-env-input"
                value={minEnv}
                onChange={(e) => setMinEnv(Number(e.target.value) || 0)}
                suffix="₹"
                min={0}
                step={500}
              />
            </FormField>
          </div>

          <div className="gg-filter-item">
            <FormField label="Crew Capacity Limit" htmlFor="capacity-select">
              <div className="gg-capacity-buttons">
                {[25, 50, 100].map((cap) => (
                  <Button
                    key={cap}
                    variant={maxInspections === cap ? 'primary' : 'secondary'}
                    size="compact"
                    onClick={() => setMaxInspections(cap)}
                  >
                    {cap} Tickets
                  </Button>
                ))}
              </div>
            </FormField>
          </div>
        </div>

        {/* Probability Threshold Chips */}
        <div className="gg-filter-chips-row">
          <span className="gg-type-label gg-chips-label">Risk Cutoff:</span>
          <FilterChip
            label="All Candidates (0%+)"
            selected={minProb === 0.0}
            onToggle={() => setMinProb(0.0)}
          />
          <FilterChip
            label="Moderate Risk (50%+)"
            selected={minProb === 0.5}
            onToggle={() => setMinProb(0.5)}
          />
          <FilterChip
            label="High Risk (75%+)"
            selected={minProb === 0.75}
            onToggle={() => setMinProb(0.75)}
          />
          <FilterChip
            label="Extreme Risk (90%+)"
            selected={minProb === 0.9}
            onToggle={() => setMinProb(0.9)}
          />
        </div>
      </Surface>

      {/* Queue Aggregate KPI Strip */}
      <div className="gg-queue-kpi-strip">
        <div className="gg-queue-kpi-item">
          <span className="gg-type-label">Queue Size</span>
          <span className="gg-type-mono gg-queue-kpi-val">{displayTickets.length} candidate tickets</span>
        </div>
        <div className="gg-queue-kpi-item">
          <span className="gg-type-label">Expected Gross Recovery</span>
          <span className="gg-type-mono gg-queue-kpi-val">
            ₹{totalExpectedRecovery.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="gg-queue-kpi-item">
          <span className="gg-type-label">Crew Dispatch Cost</span>
          <span className="gg-type-mono gg-queue-kpi-val">
            ₹{totalDispatchCost.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="gg-queue-kpi-item">
          <span className="gg-type-label">Total Expected Net Value</span>
          <span className="gg-type-mono gg-queue-kpi-val gg-queue-env-val">
            ₹{totalNetValue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
      </div>

      {/* Primary Ranked Table */}
      <DataTable<InspectionTicketResponse>
        data={displayTickets}
        columns={queueColumns}
        keyExtractor={(t) => t.ticket_id}
        loading={isLoading}
        emptyMessage="No inspection candidates meet the selected risk and net value filters."
        onRowClick={(t) => setSelectedTicket(t)}
      />

      {/* Slide-out Inspection Ticket Drawer */}
      <Drawer
        isOpen={selectedTicket !== null}
        onClose={() => setSelectedTicket(null)}
        title={selectedTicket ? `Ticket: ${selectedTicket.ticket_id}` : 'Inspection Ticket'}
      >
        {selectedTicket && (
          <div className="gg-ticket-drawer-body">
            {/* Meter Header */}
            <div className="gg-drawer-section">
              <span className="gg-type-label">Meter Account</span>
              <span className="gg-type-mono gg-drawer-meter-id">{selectedTicket.meter_id}</span>
              <div className="gg-drawer-meta-row">
                <span>Evaluation Date: {selectedTicket.evaluation_period}</span>
                <span>Feeder: {selectedTicket.feeder_id}</span>
                <span>Type: {selectedTicket.customer_type}</span>
              </div>
            </div>

            {/* Decision Status */}
            <div className="gg-drawer-section">
              <span className="gg-type-label">Operational Recommendation</span>
              <div className="gg-drawer-decision-row">
                <StatusBadge
                  status={selectedTicket.inspection_recommended ? 'danger' : 'neutral'}
                  label={
                    selectedTicket.inspection_recommended
                      ? 'Physical Inspection Recommended'
                      : 'Monitoring Only'
                  }
                />
                <span className="gg-type-mono">
                  Rank #{selectedTicket.priority_rank ?? '-'}
                </span>
              </div>
            </div>

            {/* Risk Probability & Thresholds */}
            <div className="gg-drawer-section">
              <span className="gg-type-label">Model Risk & Economic Threshold</span>
              <div className="gg-drawer-metric-grid">
                <div>
                  <span className="gg-type-caption">Calibrated Risk</span>
                  <ProbabilityMetric probability={selectedTicket.calibrated_probability} />
                </div>
                <div>
                  <span className="gg-type-caption">Active Tau</span>
                  <span className="gg-type-mono">{(selectedTicket.active_threshold * 100).toFixed(2)}%</span>
                </div>
                <div>
                  <span className="gg-type-caption">Bayes Tau Cost</span>
                  <span className="gg-type-mono">{(selectedTicket.tau_cost * 100).toFixed(2)}%</span>
                </div>
              </div>
            </div>

            {/* Financial Summary */}
            <div className="gg-drawer-section">
              <span className="gg-type-label">Financial Assessment</span>
              <FinancialSummaryBlock
                tamperProbability={selectedTicket.calibrated_probability}
                estimatedRecovery={selectedTicket.estimated_recoverable_revenue}
                dispatchCost={selectedTicket.dispatch_cost}
                expectedNetValue={selectedTicket.env}
              />
            </div>

            {/* Anomaly Signatures */}
            <div className="gg-drawer-section">
              <span className="gg-type-label">Physical Tampering Signatures</span>
              <div className="gg-drawer-signatures">
                {selectedTicket.signatures_summary.split(';').map((sig, i) => (
                  <div key={i} className="gg-signature-tag">
                    {sig.trim()}
                  </div>
                ))}
              </div>
            </div>

            {/* Forensic Narrative / Caveat */}
            <div className="gg-drawer-section">
              <span className="gg-type-label">Audit Narrative</span>
              <p className="gg-type-body gg-drawer-narrative">
                {selectedTicket.explanation?.summary ??
                  `High-confidence consumption collapse detected. Estimated unmetered leakage volume is ${selectedTicket.estimated_leakage_kwh.toFixed(1)} kWh.`}
              </p>
              <p className="gg-type-caption gg-drawer-caveat">
                {selectedTicket.safety_caveat}
              </p>
            </div>

            {/* Drawer Actions */}
            <div className="gg-drawer-action-row">
              <Button
                variant="primary"
                onClick={() => {
                  const mId = selectedTicket.meter_id;
                  setSelectedTicket(null);
                  onSelectMeterForAnalysis(mId);
                }}
              >
                Analyze Meter in Workbench →
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setFullDocTicket(selectedTicket);
                  setSelectedTicket(null);
                }}
              >
                View Full Work Order
              </Button>
              <Button
                variant="secondary"
                onClick={() => exportTicketAsJson(selectedTicket)}
              >
                Download Ticket (JSON)
              </Button>
              <Button
                variant="text"
                onClick={() => setSelectedTicket(null)}
              >
                Close Drawer
              </Button>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};
