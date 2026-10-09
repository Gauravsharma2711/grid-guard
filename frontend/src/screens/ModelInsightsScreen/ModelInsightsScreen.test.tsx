import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../../services/apiClient';
import { ModelInsightsScreen } from './ModelInsightsScreen';

vi.mock('../../services/apiClient', () => ({
  apiClient: {
    getModelMetadata: vi.fn(),
  },
}));

describe('ModelInsightsScreen Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders model insights title, checkpoint card, and policy evaluation table', async () => {
    vi.mocked(apiClient.getModelMetadata).mockResolvedValueOnce({
      model_name: 'cost_sensitive_champion_lgb',
      model_version: 'cost-sensitive-v1',
      model_type: 'LightGBM Booster',
      objective_type: 'financially_weighted_logistic',
      feature_version: 'phase3_temporal_features_v1',
      feature_count: 60,
      base_log_odds: -2.3713,
      base_probability: 0.0853,
      calibration_method: 'isotonic_or_sigmoid',
      api_version: '0.1.0',
    });

    render(<ModelInsightsScreen />);

    expect(screen.getByText('Model Insights & Policy Evaluation')).toBeInTheDocument();
    expect(await screen.findByText('phase6_cost_sensitive_v1')).toBeInTheDocument();
    expect(screen.getByText('Financial Decision Policy Evaluation')).toBeInTheDocument();
    expect(screen.getByText('Dynamic ENV Rule (Champion)')).toBeInTheDocument();
  });

  it('switches between tabs cleanly (evolution and top-k yield)', async () => {
    vi.mocked(apiClient.getModelMetadata).mockResolvedValueOnce({
      model_name: 'cost_sensitive_champion_lgb',
      model_version: 'phase6_cost_sensitive_v1',
      model_type: 'LightGBM Booster',
      objective_type: 'financially_weighted_logistic',
      feature_version: 'phase3_temporal_features_v1',
      feature_count: 60,
      base_log_odds: -2.3713,
      base_probability: 0.0853,
      calibration_method: 'isotonic_or_sigmoid',
      api_version: '0.1.0',
    });

    render(<ModelInsightsScreen />);

    const evolutionTabBtn = screen.getByText('Model Progression (Phases 4–6)');
    fireEvent.click(evolutionTabBtn);

    expect(screen.getByText('Model Architecture Evolution')).toBeInTheDocument();
    expect(screen.getByText('Phase 4: Unweighted Baseline')).toBeInTheDocument();
    expect(screen.getByText('Phase 6: Cost-Sensitive Champion')).toBeInTheDocument();

    const topKTabBtn = screen.getByText('Top-K Precision Trade-Off');
    fireEvent.click(topKTabBtn);

    expect(screen.getByText('Top-K Inspection Queue Yield')).toBeInTheDocument();
    expect(screen.getByText('Top 10 Inspections')).toBeInTheDocument();
  });
});
