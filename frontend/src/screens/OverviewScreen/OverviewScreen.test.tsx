import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../../services/apiClient';
import { OverviewScreen } from './OverviewScreen';

vi.mock('../../services/apiClient', () => ({
  apiClient: {
    getReady: vi.fn(),
    getInspectionQueue: vi.fn(),
  },
}));

describe('OverviewScreen Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders operational overview title and economic metrics', async () => {
    vi.mocked(apiClient.getReady).mockResolvedValueOnce({
      status: 'ready',
      model_loaded: true,
      explainer_loaded: true,
      features_configured: true,
      model_version: 'phase6_cost_sensitive_v1',
      feature_count: 60,
      api_version: '0.1.0',
    });

    vi.mocked(apiClient.getInspectionQueue).mockResolvedValueOnce({
      queue_size: 5,
      total_expected_recovery: 102000.0,
      total_dispatch_cost: 2500.0,
      total_net_value: 99500.0,
      decision_rule: 'env',
      tickets: [],
      processing_time_ms: 12.5,
    });

    render(
      <OverviewScreen
        onNavigateToQueue={vi.fn()}
        onSelectMeter={vi.fn()}
      />
    );

    expect(screen.getByText('Network Decision State')).toBeInTheDocument();
    expect(screen.getByText('Total Expected Net Value (ENV)')).toBeInTheDocument();
    expect(screen.getByText('Monitored Fleet')).toBeInTheDocument();
    expect(screen.getByText('Recommended Tickets')).toBeInTheDocument();
  });

  it('handles offline state truthfully when API fails', async () => {
    vi.mocked(apiClient.getReady).mockRejectedValueOnce(new Error('Network error'));
    vi.mocked(apiClient.getInspectionQueue).mockRejectedValueOnce(new Error('Network error'));

    render(
      <OverviewScreen
        onNavigateToQueue={vi.fn()}
        onSelectMeter={vi.fn()}
      />
    );

    // Verify offline badge appears
    expect(await screen.findByText('Offline (Validated Artifacts)')).toBeInTheDocument();
    // Validated fallback values are still displayed
    expect(screen.getByText('Dynamic ENV Rule (Champion)')).toBeInTheDocument();
  });
});
