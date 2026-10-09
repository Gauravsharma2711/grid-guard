import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { InspectionTicketResponse } from '../../types/api';
import * as exportUtils from '../../utils/exportUtils';
import { InspectionTicketView } from './InspectionTicketView';

describe('InspectionTicketView', () => {
  const mockTicket: InspectionTicketResponse = {
    ticket_id: 'TCK-2016-10-30-EF550F26',
    meter_id: '620E9685A1D2F4C35855EF1A3E0968AB',
    evaluation_period: '2016-10-30',
    tamper_probability: 0.9931,
    calibrated_probability: 1.0,
    estimated_leakage_kwh: 17986.5,
    estimated_recoverable_revenue: 32375.68,
    dispatch_cost: 100.0,
    expected_gross_recovery: 32375.68,
    env: 32275.68,
    tau_cost: 0.0031,
    tau_env: 0.0031,
    active_threshold: 0.0031,
    decision_rule: 'env',
    inspection_recommended: true,
    priority_rank: 1,
    customer_type: 'commercial',
    feeder_id: 'FEEDER-SUB-04',
    data_quality_status: 'good',
    signatures_summary: 'Sustained Step Down (high); Behavior Shift (moderate)',
    safety_caveat: 'Model evidence indicates an anomalous consumption pattern and requires physical on-site inspection.',
    explanation: {
      summary: 'High tampering risk with positive Expected Net Value. Sudden week-over-week consumption collapse.',
      detailed_explanation: 'Rolling 14-day average dropped from 16.4 kWh to 2.1 kWh.',
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
          description: 'Historical volatility contrasting recent flatline.',
        },
      ],
      top_negative_contributors: [
        {
          feature_name: 'rolling_mean_7d',
          display_name: '7-Day Trailing Average',
          category: 'Recent Consumption',
          feature_value: 12.1,
          baseline_value: 13.0,
          shap_value: -0.35,
          contribution_direction: 'negative',
          rank: 2,
          description: 'Aligns with seasonal expectation.',
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
          anchor_date: '2016-10-30',
          source_window_start: '2016-09-01',
          source_window_end: '2016-10-30',
          feature_name: 'ratio_14d_60d',
          display_name: 'Recent vs. Historical Consumption Ratio',
          observed_value: 2.15,
          reference_value: 16.4,
          relative_difference_pct: -86.9,
          shap_contribution: 1.85,
          interpretation: 'Recent 14-day average collapsed below baseline.',
        },
      ],
      safety_caveat: 'Field inspection required for physical verification.',
    },
  };

  it('renders complete ticket with ID, recommendation, financial values, and SHAP drivers', () => {
    render(<InspectionTicketView ticket={mockTicket} />);

    expect(screen.getByText('Forensic Field Inspection Ticket')).toBeInTheDocument();
    expect(screen.getByText('TCK-2016-10-30-EF550F26')).toBeInTheDocument();
    expect(screen.getByText('620E9685A1D2F4C35855EF1A3E0968AB')).toBeInTheDocument();
    expect(screen.getByText('Physical Inspection Recommended')).toBeInTheDocument();
    expect(screen.getByText('Queue Rank: #1')).toBeInTheDocument();
    expect(screen.getByText('60-Day Historical Volatility')).toBeInTheDocument();
    expect(screen.getByText('SUSTAINED STEP DOWN')).toBeInTheDocument();
    expect(screen.getByText(/Recent 14-day average collapsed below baseline/i)).toBeInTheDocument();
    expect(screen.getByText(/REGULATORY AND OPERATIONAL DISCLAIMER/i)).toBeInTheDocument();
  });

  it('triggers exportTicketAsJson when Download Ticket button is clicked', () => {
    const exportSpy = vi.spyOn(exportUtils, 'exportTicketAsJson').mockReturnValue(true);

    render(<InspectionTicketView ticket={mockTicket} />);

    const downloadBtn = screen.getByRole('button', { name: /Download Ticket \(JSON\)/i });
    fireEvent.click(downloadBtn);

    expect(exportSpy).toHaveBeenCalledWith(mockTicket);
    exportSpy.mockRestore();
  });

  it('invokes onAnalyzeMeter when Analyze in Workbench button is clicked', () => {
    const analyzeSpy = vi.fn();

    render(<InspectionTicketView ticket={mockTicket} onAnalyzeMeter={analyzeSpy} />);

    const analyzeBtn = screen.getByRole('button', { name: /Analyze in Workbench/i });
    fireEvent.click(analyzeBtn);

    expect(analyzeSpy).toHaveBeenCalledWith(mockTicket.meter_id);
  });
});
