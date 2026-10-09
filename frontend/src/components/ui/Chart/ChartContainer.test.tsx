import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChartContainer } from './ChartContainer';

describe('ChartContainer Component', () => {
  it('renders title, subtitle, evaluation period, and legend', () => {
    render(
      <ChartContainer
        title="180-Day Active Consumption History"
        subtitle="Daily kilowatt-hour telemetry"
        period="2025-09-01 — 2026-02-28"
        legend={[
          { label: 'Observed Daily Consumption', color: '#121512' },
          { label: '14-Day Rolling Baseline', color: '#737B74', lineStyle: 'dashed' },
        ]}
      >
        <div data-testid="chart-canvas">Canvas Mock</div>
      </ChartContainer>
    );

    expect(screen.getByText('180-Day Active Consumption History')).toBeInTheDocument();
    expect(screen.getByText('Daily kilowatt-hour telemetry')).toBeInTheDocument();
    expect(screen.getByText('PERIOD: 2025-09-01 — 2026-02-28')).toBeInTheDocument();
    expect(screen.getByText('Observed Daily Consumption')).toBeInTheDocument();
    expect(screen.getByText('14-Day Rolling Baseline')).toBeInTheDocument();
    expect(screen.getByTestId('chart-canvas')).toBeInTheDocument();
  });

  it('renders loading indicator when loading is true', () => {
    render(
      <ChartContainer title="Model PR Curve" loading>
        <div>Content</div>
      </ChartContainer>
    );
    expect(screen.getByText('Rendering chart series...')).toBeInTheDocument();
    expect(screen.queryByText('Content')).not.toBeInTheDocument();
  });

  it('renders accessible text summary for screen readers when provided', () => {
    render(
      <ChartContainer
        title="Feature Importance"
        accessibleSummary="Step-down ratio accounts for 42% of tree split gains."
      >
        <div>Content</div>
      </ChartContainer>
    );
    expect(
      screen.getByText('Step-down ratio accounts for 42% of tree split gains.')
    ).toBeInTheDocument();
  });
});
