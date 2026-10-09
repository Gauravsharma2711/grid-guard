import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { FeatureContributionSchema } from '../../types/api';
import { ShapContributionPanel } from './ShapContributionPanel';

describe('ShapContributionPanel', () => {
  const mockPositive: FeatureContributionSchema[] = [
    {
      feature_name: 'rolling_std_60d',
      display_name: '60-Day Historical Volatility',
      category: 'Historical Baseline',
      feature_value: 14.8,
      baseline_value: 3.2,
      shap_value: 2.49,
      contribution_direction: 'positive',
      rank: 1,
      description: 'Elevated historical volatility contrasting recent flatlining readings.',
    },
    {
      feature_name: 'missing_ratio',
      display_name: 'Data Missingness Ratio',
      category: 'Data Quality',
      feature_value: 0.15,
      baseline_value: 0.0,
      shap_value: 0.64,
      contribution_direction: 'positive',
      rank: 2,
      description: 'Telemetry gaps present in recent evaluation interval.',
    },
  ];

  const mockNegative: FeatureContributionSchema[] = [
    {
      feature_name: 'rolling_mean_7d',
      display_name: '7-Day Trailing Average',
      category: 'Recent Consumption',
      feature_value: 12.1,
      baseline_value: 13.0,
      shap_value: -0.35,
      contribution_direction: 'negative',
      rank: 3,
      description: 'Recent 7-day average partially aligns with seasonal expectation.',
    },
  ];

  it('renders positive and negative contributors with human-readable labels', () => {
    render(
      <ShapContributionPanel
        positiveContributors={mockPositive}
        negativeContributors={mockNegative}
        baseLogOdds={-2.3713}
        modelProbability={0.88}
        rawMargin={1.99}
      />
    );

    expect(screen.getByText('Model Evidence & Feature Drivers')).toBeInTheDocument();
    expect(screen.getByText('60-Day Historical Volatility')).toBeInTheDocument();
    expect(screen.getByText('+2.4900 Δz')).toBeInTheDocument();
    expect(screen.getByText('7-Day Trailing Average')).toBeInTheDocument();
    expect(screen.getByText('-0.3500 Δz')).toBeInTheDocument();
  });

  it('displays output space semantics in log-odds space', () => {
    render(
      <ShapContributionPanel
        positiveContributors={mockPositive}
        baseLogOdds={-2.3713}
      />
    );

    expect(screen.getByText('Log-Odds Margin (z)')).toBeInTheDocument();
    expect(screen.getByText('-2.3713')).toBeInTheDocument();
  });

  it('toggles to accessible table view and displays all feature rows', () => {
    render(
      <ShapContributionPanel
        positiveContributors={mockPositive}
        negativeContributors={mockNegative}
      />
    );

    const toggleBtn = screen.getByRole('button', { name: /Switch to accessible table view/i });
    fireEvent.click(toggleBtn);

    expect(screen.getByRole('table', { name: /Feature SHAP attributions table/i })).toBeInTheDocument();
    expect(screen.getAllByText('+ Risk Driver').length).toBeGreaterThan(0);
    expect(screen.getByText('- Mitigating')).toBeInTheDocument();

    // Toggle back to visual bars
    fireEvent.click(screen.getByRole('button', { name: /Switch to visual bar view/i }));
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('handles empty contributor lists gracefully', () => {
    render(
      <ShapContributionPanel
        positiveContributors={[]}
        negativeContributors={[]}
      />
    );

    expect(screen.getByText('No positive risk drivers attributed by model.')).toBeInTheDocument();
  });
});
