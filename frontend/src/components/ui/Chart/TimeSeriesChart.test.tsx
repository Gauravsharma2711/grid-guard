import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { TimeSeriesChart } from './TimeSeriesChart';

describe('TimeSeriesChart Component', () => {
  const sampleReadings = [
    { timestamp: '2016-09-01', consumption_kwh: 12.0 },
    { timestamp: '2016-09-02', consumption_kwh: 15.5 },
    { timestamp: '2016-09-03', consumption_kwh: 11.2 },
  ];

  it('renders chart title, readings stats, and accessible description', () => {
    render(
      <TimeSeriesChart
        meterId="TEST_METER_001"
        readings={sampleReadings}
        baselineKwh={14.0}
      />
    );

    expect(screen.getByText('Consumption Time-Series')).toBeInTheDocument();
    expect(screen.getAllByText(/TEST_METER_001/)[0]).toBeInTheDocument();
    expect(screen.getByText('Daily Mean')).toBeInTheDocument();
    expect(screen.getByText('Peak Load')).toBeInTheDocument();
  });

  it('renders historical baseline label when provided', () => {
    render(
      <TimeSeriesChart
        meterId="TEST_METER_001"
        readings={sampleReadings}
        baselineKwh={14.0}
      />
    );

    expect(screen.getByText('Baseline: 14.0 kWh')).toBeInTheDocument();
  });

  it('renders calm empty state when readings array is empty', () => {
    render(
      <TimeSeriesChart
        meterId="EMPTY_METER"
        readings={[]}
      />
    );

    expect(
      screen.getByText('No time-series consumption readings supplied for this meter.')
    ).toBeInTheDocument();
  });
});
