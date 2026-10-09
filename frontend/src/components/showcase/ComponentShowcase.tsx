import React, { useState } from 'react';
import { Button } from '../ui/Button/Button';
import { FormField, TextInput, NumberInput, Select } from '../ui/Input/Input';
import { FilterChip } from '../ui/FilterChip/FilterChip';
import {
  StatusBadge,
  EvidenceBadge,
  TechnicalMetadata,
  DataQualityWarning,
} from '../ui/Status/Status';
import { Surface, Divider, CodeSurface } from '../ui/Surface/Surface';
import { DataTable, Column } from '../ui/Table/DataTable';
import {
  CurrencyValue,
  EnvMetric,
  ProbabilityMetric,
  FinancialSummaryBlock,
} from '../ui/Financial/Financial';
import { ChartContainer } from '../ui/Chart/ChartContainer';
import {
  LoadingState,
  EmptyState,
  ErrorState,
  DegradedBanner,
} from '../ui/Feedback/Feedback';
import { Drawer, ConfirmationModal } from '../ui/Overlay/Overlay';
import './ComponentShowcase.css';

interface DemoRow {
  id: string;
  meterId: string;
  probability: string;
  revenue: string;
  cost: string;
  env: string;
  status: 'recommended' | 'review' | 'low';
}

const DEMO_TABLE_DATA: DemoRow[] = [
  {
    id: '1',
    meterId: 'SYNTH_METER_001',
    probability: '94.2%',
    revenue: '₹34,500.00',
    cost: '₹500.00',
    env: '+₹31,999.00',
    status: 'recommended',
  },
  {
    id: '2',
    meterId: 'SYNTH_METER_002',
    probability: '68.5%',
    revenue: '₹12,400.00',
    cost: '₹500.00',
    env: '+₹7,994.00',
    status: 'recommended',
  },
  {
    id: '3',
    meterId: 'SYNTH_METER_003',
    probability: '31.0%',
    revenue: '₹800.00',
    cost: '₹500.00',
    env: '−₹252.00',
    status: 'low',
  },
];

export const ComponentShowcase: React.FC = () => {
  const [chipSelected, setChipSelected] = useState<boolean>(true);
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false);
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [selectedTableId, setSelectedTableId] = useState<string>('1');

  const tableColumns: Column<DemoRow>[] = [
    { key: 'meterId', header: 'Meter ID', mono: true },
    { key: 'probability', header: 'Probability', align: 'right' },
    { key: 'revenue', header: 'Est. Recovery', align: 'right' },
    { key: 'cost', header: 'Dispatch Cost', align: 'right' },
    { key: 'env', header: 'Expected Net Value', align: 'right' },
    {
      key: 'status',
      header: 'Decision State',
      align: 'center',
      render: (row) =>
        row.status === 'recommended' ? (
          <StatusBadge status="safe" label="DISPATCH" />
        ) : (
          <StatusBadge status="neutral" label="REJECT" />
        ),
    },
  ];

  return (
    <div className="gg-showcase">
      <div className="gg-showcase__banner">
        <span className="gg-showcase__tag">DEVELOPMENT SHOWCASE</span>
        <h2 className="gg-showcase__heading">
          Grid-Guard Design System &amp; Component Gallery
        </h2>
        <p className="gg-showcase__sub">
          Authoritative interactive reference for Calm Proof Flow design tokens and UI primitives (/designsystem.md).
          All values below are synthetic demonstration specimens.
        </p>
      </div>

      {/* 1. BUTTONS */}
      <section className="gg-showcase__section">
        <h3 className="gg-showcase__section-title">1. Reusable Buttons</h3>
        <p className="gg-showcase__section-desc">
          Restrained 44px buttons adhering to Section 6.2 with visible focus rings and quiet hover timings.
        </p>
        <Surface padded>
          <div className="gg-showcase__row">
            <Button variant="primary">Primary Action</Button>
            <Button variant="secondary">Secondary Action</Button>
            <Button variant="text">Text Link Action</Button>
            <Button variant="destructive">Destructive Action</Button>
            <Button variant="secondary" size="compact">Compact (32px)</Button>
            <Button variant="primary" loading>Loading</Button>
            <Button variant="secondary" disabled>Disabled State</Button>
          </div>
        </Surface>
      </section>

      {/* 2. FORM CONTROLS */}
      <section className="gg-showcase__section">
        <h3 className="gg-showcase__section-title">2. Form Inputs &amp; Selects</h3>
        <p className="gg-showcase__section-desc">
          High-contrast inputs with associated labels, error states, and unit suffixes (Section 6.3).
        </p>
        <Surface padded>
          <div className="gg-showcase__form-grid">
            <FormField label="Smart Meter Identifier" htmlFor="showcase-meter" helperText="Canonical 10-digit utility identifier">
              <TextInput id="showcase-meter" mono placeholder="e.g. CONS_004281" defaultValue="CONS_004281" />
            </FormField>

            <FormField label="Standard Tariff Rate" htmlFor="showcase-tariff">
              <NumberInput id="showcase-tariff" suffix="₹/kWh" defaultValue={6.0} />
            </FormField>

            <FormField label="Field Inspection Cost" htmlFor="showcase-cost">
              <NumberInput id="showcase-cost" suffix="₹" defaultValue={500} />
            </FormField>

            <FormField label="Economic Decision Rule" htmlFor="showcase-rule">
              <Select
                id="showcase-rule"
                defaultValue="env"
                options={[
                  { value: 'env', label: 'Dynamic Expected Net Value (ENV > 0)' },
                  { value: 'cost_threshold', label: 'Bayes Cost-Sensitive Threshold' },
                  { value: 'fixed_threshold', label: 'Conventional Fixed Cutoff (p >= 0.5)' },
                ]}
              />
            </FormField>

            <FormField label="Invalid Parameter Example" htmlFor="showcase-err" error="Tariff cannot be less than zero.">
              <NumberInput id="showcase-err" defaultValue={-2.5} />
            </FormField>
          </div>
        </Surface>
      </section>

      {/* 3. FILTER CHIPS */}
      <section className="gg-showcase__section">
        <h3 className="gg-showcase__section-title">3. Filter Chips</h3>
        <p className="gg-showcase__section-desc">
          Chartreuse signal highlight (--gg-signal) used strictly when active with high-contrast signal-ink text.
        </p>
        <Surface padded>
          <div className="gg-showcase__row">
            <FilterChip
              label="Expected Net Value (ENV > 0)"
              selected={chipSelected}
              count={42}
              onToggle={() => setChipSelected(!chipSelected)}
              onRemove={() => setChipSelected(false)}
            />
            <FilterChip label="High Probability (p >= 0.70)" count={18} onToggle={() => {}} />
            <FilterChip label="Commercial Accounts" count={7} onToggle={() => {}} />
            <FilterChip label="Disabled Filter" disabled />
          </div>
        </Surface>
      </section>

      {/* 4. STATUS & EVIDENCE */}
      <section className="gg-showcase__section">
        <h3 className="gg-showcase__section-title">4. Status, Evidence &amp; Metadata</h3>
        <p className="gg-showcase__section-desc">
          Restrained semantic status labels and violet evidence badges reserved strictly for Tree-SHAP attributions.
        </p>
        <Surface padded>
          <div className="gg-showcase__row">
            <StatusBadge status="safe" label="API ONLINE" />
            <StatusBadge status="warning" label="INSUFFICIENT HISTORY" />
            <StatusBadge status="danger" label="MODEL UNREADY" />
            <StatusBadge status="neutral" label="REJECTED BY ENV" />
          </div>

          <Divider spacing="md" />

          <div className="gg-showcase__row">
            <EvidenceBadge label="step_down_ratio_14_60" direction="positive" />
            <EvidenceBadge label="zero_consumption_ratio_30" direction="positive" />
            <EvidenceBadge label="recent_mean_consumption_14" direction="negative" />
          </div>

          <Divider spacing="md" />

          <div className="gg-showcase__row">
            <TechnicalMetadata label="Active Model" value="phase6_cost_sensitive_v1" />
            <TechnicalMetadata label="Feature Set" value="60 causal temporal dimensions" />
            <TechnicalMetadata label="Base Value" value="-2.3713 log-odds" />
          </div>

          <Divider spacing="md" />

          <DataQualityWarning
            title="Telemetry Warning"
            message="Meter record has 12 consecutive zeros. Ensure physical verification tests for total disconnect."
          />
        </Surface>
      </section>

      {/* 5. FINANCIAL VALUES */}
      <section className="gg-showcase__section">
        <h3 className="gg-showcase__section-title">5. Financial Presentation Primitives</h3>
        <p className="gg-showcase__section-desc">
          Pure presentation components strictly separating probability, estimated recovery, dispatch cost, and ENV.
        </p>
        <Surface padded>
          <FinancialSummaryBlock
            tamperProbability={0.842}
            estimatedRecovery={34500}
            dispatchCost={500}
            expectedNetValue={28549}
            currency="INR"
          />

          <Divider spacing="md" />

          <div className="gg-showcase__row">
            <EnvMetric env={28549} currency="INR" />
            <EnvMetric env={-250} currency="INR" />
            <ProbabilityMetric probability={0.842} />
            <CurrencyValue amount={34500} currency="INR" context="estimated" />
          </div>
        </Surface>
      </section>

      {/* 6. DATA TABLE */}
      <section className="gg-showcase__section">
        <h3 className="gg-showcase__section-title">6. Inspection Data Table</h3>
        <p className="gg-showcase__section-desc">
          Quiet borders, monospace identifiers, right-aligned monetary values, and keyboard row selection.
        </p>
        <DataTable
          columns={tableColumns}
          data={DEMO_TABLE_DATA}
          keyExtractor={(r) => r.id}
          selectedKey={selectedTableId}
          onRowClick={(r) => setSelectedTableId(r.id)}
          caption="Synthetic Candidate Inspection Table (Click a row or press Enter)"
        />
      </section>

      {/* 7. CHART CONTAINER */}
      <section className="gg-showcase__section">
        <h3 className="gg-showcase__section-title">7. Chart Container Foundation</h3>
        <p className="gg-showcase__section-desc">
          Structured presentation frame for upcoming Phase 3 Plotly / SVG time-series visualizers.
        </p>
        <ChartContainer
          title="Synthetic Meter Daily Consumption History"
          subtitle="Observed telemetry vs 14-day rolling baseline"
          period="2025-09-01 — 2026-02-28"
          yAxisLabel="Active Energy (kWh/day)"
          xAxisLabel="Date (Daily Ingestion Cadence)"
          legend={[
            { label: 'Observed Daily Consumption', color: '#121512' },
            { label: '14-Day Rolling Baseline', color: '#737B74', lineStyle: 'dashed' },
            { label: 'Detected Step-Down Window', color: '#7D6DB2' },
          ]}
          accessibleSummary="Consumption drops from 28.5 kWh/day baseline down to 1.2 kWh/day on day 62, persisting for 31 days."
        >
          <div className="gg-showcase__chart-placeholder">
            <span>[Phase 3 Time-Series Chart Component Insertion Zone]</span>
          </div>
        </ChartContainer>
      </section>

      {/* 8. OVERLAYS */}
      <section className="gg-showcase__section">
        <h3 className="gg-showcase__section-title">8. Accessible Overlays (Drawer &amp; Modal)</h3>
        <p className="gg-showcase__section-desc">
          Right-hand slide-out drawer (max 480px) and confirmation modal with focus trapping and Escape handling.
        </p>
        <Surface padded>
          <div className="gg-showcase__row">
            <Button variant="secondary" onClick={() => setDrawerOpen(true)}>
              Open Right Inspection Drawer
            </Button>
            <Button variant="destructive" onClick={() => setModalOpen(true)}>
              Open Confirmation Modal
            </Button>
          </div>
        </Surface>

        <Drawer
          isOpen={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          title="Inspection Ticket Forensic Details"
          subtitle="Meter ID: SYNTH_METER_001"
          footer={
            <Button variant="primary" onClick={() => setDrawerOpen(false)}>
              Done Reviewing
            </Button>
          }
        >
          <p className="gg-showcase__text">
            This right-hand drawer displays secondary diagnostic information, feature definitions,
            and raw JSON payloads while preserving inspection context underneath.
          </p>
          <CodeSurface caption="SYNTHETIC_SHAP_PAYLOAD">
            {JSON.stringify(
              {
                meter_id: 'SYNTH_METER_001',
                signatures: ['sustained_step_down', 'flatline_invariance'],
                shap_base_value: -2.3713,
                active_env: 31999.0,
              },
              null,
              2
            )}
          </CodeSurface>
        </Drawer>

        <ConfirmationModal
          isOpen={modalOpen}
          title="Reset Active Queue Filter?"
          message="This action will clear capacity thresholds and reload the unconstrained candidate fleet."
          confirmLabel="Reset Filter"
          cancelLabel="Keep Current View"
          destructive
          onConfirm={() => setModalOpen(false)}
          onCancel={() => setModalOpen(false)}
        />
      </section>

      {/* 9. FEEDBACK STATES */}
      <section className="gg-showcase__section">
        <h3 className="gg-showcase__section-title">9. Feedback States</h3>
        <p className="gg-showcase__section-desc">
          Honest loading, empty, and error feedback states without fake progress bars or giant alert stacks.
        </p>
        <DegradedBanner
          title="FastAPI Backend Disconnected"
          message="The frontend is operating in offline mode. Live inference endpoints will become available once the backend process is started."
          onRetry={() => alert('Retrying connection...')}
        />

        <div className="gg-showcase__feedback-grid">
          <LoadingState
            title="Evaluating Candidate Meter"
            description="Computing 60 causal temporal features and querying champion LightGBM booster..."
          />
          <EmptyState
            title="No Candidates Found"
            description="No smart meters in the current feeder partition satisfy ENV > 0."
            actionLabel="Relax Filter Cutoff"
            onAction={() => alert('Resetting filter')}
          />
          <ErrorState
            title="Prediction Pipeline Failure"
            message="Smart meter telemetry has missing dates in the required 60-day baseline window."
            technicalDetails="ValueError: Missing 14 readings between 2025-11-01 and 2025-11-15."
            onRetry={() => alert('Retrying')}
          />
        </div>
      </section>
    </div>
  );
};
