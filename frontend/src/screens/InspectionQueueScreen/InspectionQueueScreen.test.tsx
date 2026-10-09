import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../../services/apiClient';
import * as exportUtils from '../../utils/exportUtils';
import { InspectionQueueScreen } from './InspectionQueueScreen';

vi.mock('../../services/apiClient', () => ({
  apiClient: {
    getInspectionQueue: vi.fn(),
  },
}));

describe('InspectionQueueScreen Component', () => {
  const mockTickets = [
    {
      ticket_id: 'TCK-001',
      meter_id: 'METER_ALPHA_101',
      evaluation_period: '2016-10-30',
      tamper_probability: 0.95,
      calibrated_probability: 0.95,
      estimated_leakage_kwh: 5000,
      estimated_recoverable_revenue: 30000,
      dispatch_cost: 500,
      expected_gross_recovery: 28500,
      env: 28000,
      tau_cost: 0.05,
      tau_env: 0.05,
      active_threshold: 0.05,
      decision_rule: 'env',
      inspection_recommended: true,
      priority_rank: 1,
      customer_type: 'residential',
      feeder_id: 'FEEDER_01',
      data_quality_status: 'good',
      signatures_summary: 'Sudden Step Down',
      safety_caveat: 'Requires physical inspection.',
    },
    {
      ticket_id: 'TCK-002',
      meter_id: 'METER_BETA_202',
      evaluation_period: '2016-10-30',
      tamper_probability: 0.85,
      calibrated_probability: 0.85,
      estimated_leakage_kwh: 4000,
      estimated_recoverable_revenue: 20000,
      dispatch_cost: 500,
      expected_gross_recovery: 17000,
      env: 16500,
      tau_cost: 0.05,
      tau_env: 0.05,
      active_threshold: 0.05,
      decision_rule: 'env',
      inspection_recommended: true,
      priority_rank: 2,
      customer_type: 'commercial',
      feeder_id: 'FEEDER_02',
      data_quality_status: 'good',
      signatures_summary: 'Flatline',
      safety_caveat: 'Verify on site.',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders queue header, filter controls, and table rows', async () => {
    vi.mocked(apiClient.getInspectionQueue).mockResolvedValueOnce({
      queue_size: 2,
      total_expected_recovery: 55000.0,
      total_dispatch_cost: 1000.0,
      total_net_value: 54000.0,
      decision_rule: 'env',
      tickets: mockTickets,
      processing_time_ms: 10.0,
    });

    render(<InspectionQueueScreen onSelectMeterForAnalysis={vi.fn()} />);

    expect(screen.getByText('Inspection Work Orders')).toBeInTheDocument();
    expect(screen.getByText('Search Meter ID or Feeder')).toBeInTheDocument();
    expect(await screen.findByText('METER_ALPHA_101')).toBeInTheDocument();
  });

  it('filters results client-side by meter ID search input', async () => {
    vi.mocked(apiClient.getInspectionQueue).mockResolvedValueOnce({
      queue_size: 2,
      total_expected_recovery: 50000.0,
      total_dispatch_cost: 1000.0,
      total_net_value: 49000.0,
      decision_rule: 'env',
      tickets: mockTickets,
      processing_time_ms: 8.0,
    });

    render(<InspectionQueueScreen onSelectMeterForAnalysis={vi.fn()} />);

    expect(await screen.findByText('METER_ALPHA_101')).toBeInTheDocument();
    expect(screen.getByText('METER_BETA_202')).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText('Search by meter ID, ticket ID, or feeder...');
    fireEvent.change(searchInput, { target: { value: 'BETA' } });

    expect(screen.queryByText('METER_ALPHA_101')).not.toBeInTheDocument();
    expect(screen.getByText('METER_BETA_202')).toBeInTheDocument();
  });

  it('triggers CSV export when Export Queue (CSV) button is clicked', async () => {
    vi.mocked(apiClient.getInspectionQueue).mockResolvedValueOnce({
      queue_size: 2,
      total_expected_recovery: 50000.0,
      total_dispatch_cost: 1000.0,
      total_net_value: 49000.0,
      decision_rule: 'env',
      tickets: mockTickets,
      processing_time_ms: 8.0,
    });
    const exportCsvSpy = vi.spyOn(exportUtils, 'exportQueueAsCsv').mockReturnValue(true);

    render(<InspectionQueueScreen onSelectMeterForAnalysis={vi.fn()} />);

    const exportBtn = await screen.findByRole('button', { name: /Export inspection queue as CSV/i });
    fireEvent.click(exportBtn);

    expect(exportCsvSpy).toHaveBeenCalled();
    exportCsvSpy.mockRestore();
  });

  it('opens drawer, triggers JSON ticket export and full work order view', async () => {
    vi.mocked(apiClient.getInspectionQueue).mockResolvedValueOnce({
      queue_size: 2,
      total_expected_recovery: 50000.0,
      total_dispatch_cost: 1000.0,
      total_net_value: 49000.0,
      decision_rule: 'env',
      tickets: mockTickets,
      processing_time_ms: 8.0,
    });
    const exportJsonSpy = vi.spyOn(exportUtils, 'exportTicketAsJson').mockReturnValue(true);

    render(<InspectionQueueScreen onSelectMeterForAnalysis={vi.fn()} />);

    // Click row action to open ticket drawer
    const viewTicketBtns = await screen.findAllByRole('button', { name: /View ticket for meter/i });
    fireEvent.click(viewTicketBtns[0]);

    // Drawer should display ticket details
    expect(screen.getByText('Operational Recommendation')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Download Ticket \(JSON\)/i })).toBeInTheDocument();

    // Click download ticket
    const downloadJsonBtn = screen.getByRole('button', { name: /Download Ticket \(JSON\)/i });
    fireEvent.click(downloadJsonBtn);
    expect(exportJsonSpy).toHaveBeenCalled();
    exportJsonSpy.mockRestore();

    // Click View Full Work Order
    const viewFullBtn = screen.getByRole('button', { name: /View Full Work Order/i });
    fireEvent.click(viewFullBtn);

    expect(screen.getByText('Forensic Field Inspection Ticket')).toBeInTheDocument();
    expect(screen.getByText('TCK-001')).toBeInTheDocument();
  });
});
