import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LoadingState, EmptyState, ErrorState, DegradedBanner } from './Feedback';

describe('Feedback States', () => {
  it('renders LoadingState with aria status role', () => {
    render(<LoadingState title="Scoring Meter Batch" />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Scoring Meter Batch')).toBeInTheDocument();
  });

  it('renders EmptyState with recovery action callback', () => {
    const handleAction = vi.fn();
    render(
      <EmptyState
        title="No Flagged Meters"
        description="All accounts in the selected feeder fall below active threshold."
        actionLabel="Reset Queue Filter"
        onAction={handleAction}
      />
    );

    expect(screen.getByText('No Flagged Meters')).toBeInTheDocument();
    const btn = screen.getByRole('button', { name: 'Reset Queue Filter' });
    fireEvent.click(btn);
    expect(handleAction).toHaveBeenCalledTimes(1);
  });

  it('renders ErrorState with alert role, retry button, and expandable diagnostics', () => {
    const handleRetry = vi.fn();
    render(
      <ErrorState
        title="API Server Unreachable"
        message="Could not connect to FastAPI at http://localhost:8000."
        technicalDetails="ECONNREFUSED 127.0.0.1:8000"
        onRetry={handleRetry}
      />
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('API Server Unreachable')).toBeInTheDocument();
    expect(screen.getByText('ECONNREFUSED 127.0.0.1:8000')).toBeInTheDocument();

    const retryBtn = screen.getByRole('button', { name: 'Retry Operation' });
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it('renders DegradedBanner with reconnect action', () => {
    const handleReconnect = vi.fn();
    render(
      <DegradedBanner
        title="Offline Mode"
        message="Showing cached fleet summary."
        onRetry={handleReconnect}
      />
    );

    expect(screen.getByText('Offline Mode')).toBeInTheDocument();
    const btn = screen.getByRole('button', { name: 'Reconnect' });
    fireEvent.click(btn);
    expect(handleReconnect).toHaveBeenCalledTimes(1);
  });
});
