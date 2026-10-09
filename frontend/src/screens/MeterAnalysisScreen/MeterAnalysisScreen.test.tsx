import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../../services/apiClient';
import * as exportUtils from '../../utils/exportUtils';
import { MeterAnalysisScreen } from './MeterAnalysisScreen';

vi.mock('../../services/apiClient', () => ({
  apiClient: {
    predictSingle: vi.fn(),
  },
}));

describe('MeterAnalysisScreen Component', () => {
  const mockPredictionResponse = {
    meter_id: 'SAMPLE_SUSPICIOUS_STEPDOWN',
    evaluation_timestamp: '2016-09-30',
    model: {
      model_name: 'cost_sensitive_champion_lgb',
      model_version: 'phase6_cost_sensitive_v1',
      model_type: 'LightGBM Booster',
      objective_type: 'financially_weighted_logistic',
      feature_version: 'phase3_temporal_features_v1',
      feature_count: 60,
      base_log_odds: -2.3713,
      base_probability: 0.0853,
      calibration_method: 'isotonic_or_sigmoid',
      api_version: '0.1.0',
    },
    data_quality: {
      coverage_ratio: 1.0,
      missing_ratio: 0.0,
      imputation_ratio: 0.0,
      total_readings: 30,
      history_days: 30,
      status: 'good',
      warnings: [],
    },
    prediction: {
      raw_score: 2.8,
      tamper_probability: 0.94,
      calibrated_probability: 0.94,
      prediction_label: 1,
    },
    financial: {
      estimated_leakage_kwh: 4200.0,
      estimated_recoverable_revenue: 25200.0,
      expected_gross_recovery: 23688.0,
      dispatch_cost: 500.0,
      expected_net_value: 23188.0,
      tariff: 6.0,
      currency: 'INR',
    },
    decision: {
      decision_rule: 'env',
      active_threshold: 0.0198,
      tau_cost: 0.0194,
      tau_env: 0.0198,
      inspection_recommended: true,
      priority_context: 'Volume collapse. Recommend dispatch.',
    },
    explanation: {
      summary: 'Sudden 85% drop in consumption below historical baseline.',
      detailed_explanation: 'Rolling 14d mean dropped sharply from 16.4 kWh to 2.1 kWh.',
      top_positive_contributors: [
        {
          feature_name: 'rolling_std_60d',
          display_name: '60-Day Historical Volatility',
          category: 'Historical Baseline',
          feature_value: 14.8,
          baseline_value: 3.2,
          shap_value: 2.49,
          contribution_direction: 'positive',
          rank: 1,
          description: 'Elevated historical volatility contrasting recent flatline.',
        },
      ],
      top_negative_contributors: [
        {
          feature_name: 'rolling_mean_7d',
          display_name: '7-Day Trailing Average',
          category: 'Recent Consumption',
          feature_value: 2.1,
          baseline_value: 13.0,
          shap_value: -0.35,
          contribution_direction: 'negative',
          rank: 2,
          description: 'Slight seasonal load stabilization.',
        },
      ],
      detected_signatures: [
        {
          signature_type: 'sustained_step_down',
          detected: true,
          magnitude: 0.85,
          duration_days: 15,
          severity: 'high',
          description: '85% sustained drop in daily consumption.',
        },
      ],
      temporal_evidence: [
        {
          anchor_date: '2016-09-30',
          source_window_start: '2016-09-15',
          source_window_end: '2016-09-30',
          feature_name: 'ratio_14d_60d',
          display_name: 'Recent vs. Historical Window',
          observed_value: 2.15,
          reference_value: 16.4,
          relative_difference_pct: -86.9,
          shap_contribution: 1.62,
          interpretation: 'Recent 14-day average collapsed below baseline.',
        },
      ],
      counter_evidence_summary: '1 counter-evidence feature moderated risk margin.',
      safety_caveat: 'Model evidence indicates anomaly. Requires physical inspection.',
    },
    processing_time_ms: 12.0,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders meter header, evaluates telemetry, and displays SHAP evidence and signatures', async () => {
    vi.mocked(apiClient.predictSingle).mockResolvedValueOnce(mockPredictionResponse);

    render(<MeterAnalysisScreen initialMeterId="SAMPLE_SUSPICIOUS_STEPDOWN" />);

    expect(screen.getByText('Meter Analysis & Explainability')).toBeInTheDocument();
    expect(await screen.findByText('Model Evidence & Feature Drivers')).toBeInTheDocument();
    expect(screen.getByText('60-Day Historical Volatility')).toBeInTheDocument();
    expect(screen.getByText('+2.4900 Δz')).toBeInTheDocument();
    expect(screen.getByText('Historical Anomaly Windows')).toBeInTheDocument();
    expect(screen.getByText('2016-09-15 → 2016-09-30')).toBeInTheDocument();
    expect(screen.getByText('Detected Consumption Signatures')).toBeInTheDocument();
    expect(screen.getByText('Sustained Step Down')).toBeInTheDocument();
    expect(screen.getByText('Counter-Evidence & Normalization')).toBeInTheDocument();
    expect(screen.getByText(/1 counter-evidence feature moderated risk margin/i)).toBeInTheDocument();
  });

  it('displays data quality deficiency warning for short history meters', async () => {
    render(<MeterAnalysisScreen initialMeterId="SAMPLE_INVALID_SHORT" />);

    // Switch to short history preset
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'SAMPLE_INVALID_SHORT' } });

    expect(
      await screen.findByText(/A minimum of 14 continuous days is required/)
    ).toBeInTheDocument();
  });

  it('opens complete inspection ticket view when View Inspection Ticket button is clicked', async () => {
    vi.mocked(apiClient.predictSingle).mockResolvedValueOnce(mockPredictionResponse);

    render(<MeterAnalysisScreen initialMeterId="SAMPLE_SUSPICIOUS_STEPDOWN" />);

    const viewTicketBtn = await screen.findByRole('button', { name: /View complete inspection ticket/i });
    fireEvent.click(viewTicketBtn);

    expect(screen.getByText('Forensic Field Inspection Ticket')).toBeInTheDocument();
    expect(screen.getByText(/1. Financial Rationale & Cost-Benefit Analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/REGULATORY AND OPERATIONAL DISCLAIMER/i)).toBeInTheDocument();

    // Close ticket view back to workbench
    const closeBtn = screen.getByRole('button', { name: /Close ticket view/i });
    fireEvent.click(closeBtn);

    expect(screen.getByText('Meter Analysis & Explainability')).toBeInTheDocument();
  });

  it('triggers JSON export when Download Ticket button is clicked', async () => {
    vi.mocked(apiClient.predictSingle).mockResolvedValueOnce(mockPredictionResponse);
    const exportSpy = vi.spyOn(exportUtils, 'exportTicketAsJson').mockReturnValue(true);

    render(<MeterAnalysisScreen initialMeterId="SAMPLE_SUSPICIOUS_STEPDOWN" />);

    const downloadBtn = await screen.findByRole('button', { name: /Download inspection ticket JSON/i });
    fireEvent.click(downloadBtn);

    expect(exportSpy).toHaveBeenCalled();
    exportSpy.mockRestore();
  });
});
