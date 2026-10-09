import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { TemporalEvidenceSchema } from '../../types/api';
import { TemporalEvidencePanel } from './TemporalEvidencePanel';

describe('TemporalEvidencePanel', () => {
  const mockEvidence: TemporalEvidenceSchema[] = [
    {
      anchor_date: '2016-09-30',
      source_window_start: '2016-09-01',
      source_window_end: '2016-09-30',
      feature_name: 'ratio_14d_60d',
      display_name: 'Recent vs. Historical Consumption Ratio',
      observed_value: 2.15,
      reference_value: 16.4,
      relative_difference_pct: -86.9,
      shap_contribution: 1.85,
      interpretation: 'Recent 14-day average (2.15 kWh/day) is 86.9% below 60-day baseline (16.40 kWh/day).',
    },
  ];

  it('renders historical intervals and observed vs reference values accurately', () => {
    render(<TemporalEvidencePanel evidenceList={mockEvidence} />);

    expect(screen.getByText('Historical Anomaly Windows')).toBeInTheDocument();
    expect(screen.getByText('Recent vs. Historical Consumption Ratio')).toBeInTheDocument();
    expect(screen.getByText('2016-09-01 → 2016-09-30')).toBeInTheDocument();
    expect(screen.getByText('2.15')).toBeInTheDocument();
    expect(screen.getByText('16.40')).toBeInTheDocument();
    expect(screen.getByText('-86.9%')).toBeInTheDocument();
    expect(screen.getByText('+1.8500 Δz')).toBeInTheDocument();
  });

  it('invokes onSelectInterval callback when zoom button is clicked', () => {
    const handleSelect = vi.fn();
    render(
      <TemporalEvidencePanel
        evidenceList={mockEvidence}
        onSelectInterval={handleSelect}
      />
    );

    const zoomBtn = screen.getByRole('button', { name: /Highlight Window in Chart/i });
    fireEvent.click(zoomBtn);

    expect(handleSelect).toHaveBeenCalledWith('2016-09-01', '2016-09-30');
  });

  it('handles empty evidence list with an honest message', () => {
    render(<TemporalEvidencePanel evidenceList={[]} />);

    expect(
      screen.getByText(/No temporal attribution windows were provided for this evaluation/i)
    ).toBeInTheDocument();
  });
});
