import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { FeatureContributionSchema } from '../../types/api';
import { CounterEvidencePanel } from './CounterEvidencePanel';

describe('CounterEvidencePanel', () => {
  const mockNegative: FeatureContributionSchema[] = [
    {
      feature_name: 'rolling_mean_7d',
      display_name: '7-Day Trailing Average',
      category: 'Recent Consumption',
      feature_value: 12.1,
      baseline_value: 13.0,
      shap_value: -0.42,
      contribution_direction: 'negative',
      rank: 4,
      description: 'Recent usage level exhibits consistent load matching seasonal expectations.',
    },
  ];

  it('renders counter-evidence summary and negative drivers', () => {
    render(
      <CounterEvidencePanel
        counterEvidenceSummary="2 counter-evidence features moderated the overall risk margin."
        negativeContributors={mockNegative}
      />
    );

    expect(screen.getByText('Counter-Evidence & Normalization')).toBeInTheDocument();
    expect(
      screen.getByText('2 counter-evidence features moderated the overall risk margin.')
    ).toBeInTheDocument();
    expect(screen.getByText('7-Day Trailing Average')).toBeInTheDocument();
    expect(screen.getByText('-0.4200 Δz')).toBeInTheDocument();
  });

  it('distinguishes absence of supplied evidence honestly when none is provided', () => {
    render(
      <CounterEvidencePanel
        counterEvidenceSummary={null}
        negativeContributors={[]}
      />
    );

    expect(
      screen.getByText(
        /No moderating counter-evidence was provided by the model explanation service/i
      )
    ).toBeInTheDocument();
  });
});
