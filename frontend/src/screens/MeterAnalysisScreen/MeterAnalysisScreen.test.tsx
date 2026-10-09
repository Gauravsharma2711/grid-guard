import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../../services/apiClient';
import { MeterAnalysisScreen } from './MeterAnalysisScreen';

vi.mock('../../services/apiClient', () => ({
  apiClient: {
    predictSingle: vi.fn(),
  },
}));

describe('MeterAnalysisScreen Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders meter header and evaluates sample meter telemetry', async () => {
    vi.mocked(apiClient.predictSingle).mockResolvedValueOnce({
      meter_id: 'SAMPLE_SUSPICIOUS_STEPDOWN',
      evaluation_timestamp: '2016-09-30',
      model: {
        model_name: 'cost_sensitive_champion_lgb',
        model_version: 'phase6_cost_sensitive_v1',
        model_type: 'LightGBM Booster',
        objective_type: 'financially_weighted_logistic',
        feature_version: 'phase3_temporal_features_v1',
        feature_count: 60,
        base_log_odds: -2.37,
        base_probability: 0.085,
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
        tau_cost: 0.0198,
        tau_env: 0.0198,
        inspection_recommended: true,
        priority_context: 'Volume collapse. Recommend dispatch.',
      },
      explanation: {
        summary: 'Sudden 85% drop in consumption.',
        detailed_explanation: 'Rolling 14d mean dropped sharply.',
        top_positive_contributors: [],
        top_negative_contributors: [],
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
        temporal_evidence: [],
        safety_caveat: 'Model evidence indicates anomaly. Requires physical inspection.',
      },
      processing_time_ms: 12.0,
    });

    render(<MeterAnalysisScreen initialMeterId="SAMPLE_SUSPICIOUS_STEPDOWN" />);

    expect(screen.getByText('Meter Analysis')).toBeInTheDocument();
    expect(await screen.findByText('Tampering Risk')).toBeInTheDocument();
    expect(screen.getByText('Dispatch Recommended')).toBeInTheDocument();
    expect(screen.getByText('Telemetry Data Quality')).toBeInTheDocument();
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
});
