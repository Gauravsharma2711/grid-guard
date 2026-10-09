import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { DecisionOutput, FinancialOutput, PredictionOutput } from '../../types/api';
import { DecisionContextPanel } from './DecisionContextPanel';

describe('DecisionContextPanel', () => {
  const mockPrediction: PredictionOutput = {
    raw_score: 2.15,
    tamper_probability: 0.895,
    calibrated_probability: 0.895,
    prediction_label: 1,
  };

  const mockFinancial: FinancialOutput = {
    estimated_leakage_kwh: 4200.0,
    estimated_recoverable_revenue: 25200.0,
    expected_gross_recovery: 22554.0,
    dispatch_cost: 500.0,
    expected_net_value: 22054.0,
    tariff: 6.0,
    currency: 'INR',
  };

  const mockDecision: DecisionOutput = {
    decision_rule: 'env',
    active_threshold: 0.0198,
    tau_cost: 0.0194,
    tau_env: 0.0198,
    inspection_recommended: true,
    priority_context: 'Positive net recovery warrants priority physical dispatch.',
  };

  it('renders probability, leakage volume, recovery, dispatch cost, and ENV correctly', () => {
    render(
      <DecisionContextPanel
        prediction={mockPrediction}
        financial={mockFinancial}
        decision={mockDecision}
      />
    );

    expect(screen.getByText('Financial Decision & Threshold Comparison')).toBeInTheDocument();
    expect(screen.getByText('Inspection Justified')).toBeInTheDocument();
    expect(screen.getByText('4,200 kWh')).toBeInTheDocument();
    expect(screen.getByText('Positive net recovery warrants priority physical dispatch.')).toBeInTheDocument();
  });

  it('highlights the active decision policy and displays rule comparisons', () => {
    render(
      <DecisionContextPanel
        prediction={mockPrediction}
        financial={mockFinancial}
        decision={mockDecision}
      />
    );

    expect(screen.getByText('Active Policy')).toBeInTheDocument();
    expect(screen.getByText('Dynamic ENV Rule')).toBeInTheDocument();
    expect(screen.getByText('Bayes Cost Threshold')).toBeInTheDocument();
    expect(screen.getByText('Fixed Cutoff (0.50)')).toBeInTheDocument();
  });
});
