import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusBadge, EvidenceBadge, TechnicalMetadata, DataQualityWarning } from './Status';

describe('Status & Evidence Components', () => {
  it('renders StatusBadge with label and correct semantic class', () => {
    render(<StatusBadge status="safe" label="API Online" />);
    const badge = screen.getByText('API Online');
    expect(badge).toBeInTheDocument();
    expect(badge.closest('.gg-status-badge')).toHaveClass('gg-status-badge--safe');
  });

  it('renders EvidenceBadge with violet SHAP evidence marker', () => {
    render(
      <EvidenceBadge
        label="step_down_ratio_14_60"
        direction="positive"
      />
    );
    expect(screen.getByText('SHAP')).toBeInTheDocument();
    expect(screen.getByText('step_down_ratio_14_60')).toBeInTheDocument();
    expect(screen.getByText('+ Risk')).toBeInTheDocument();
  });

  it('renders TechnicalMetadata with uppercase label and monospace value', () => {
    render(<TechnicalMetadata label="Model Version" value="phase6_cost_sensitive_v1" />);
    expect(screen.getByText('Model Version')).toBeInTheDocument();
    expect(screen.getByText('phase6_cost_sensitive_v1')).toBeInTheDocument();
  });

  it('renders DataQualityWarning with status role and content', () => {
    render(
      <DataQualityWarning
        title="Insufficient History"
        message="History contains 12 days; 14 required for rolling features."
      />
    );
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Insufficient History')).toBeInTheDocument();
    expect(
      screen.getByText('History contains 12 days; 14 required for rolling features.')
    ).toBeInTheDocument();
  });
});
