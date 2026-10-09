import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { App } from './App';
import { apiClient } from './services/apiClient';

describe('App Component (Phase 2 Shell & Navigation)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the Grid-Guard brand header and main title', async () => {
    vi.spyOn(apiClient, 'getHealth').mockRejectedValue(new Error('Connection refused'));

    render(<App />);

    expect(screen.getByText('GRID-GUARD')).toBeInTheDocument();
    expect(screen.getByText('NTL Detection Platform')).toBeInTheDocument();
    expect(
      screen.getByText(/Calm, financially rational smart-meter inspection analytics/i)
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('API DISCONNECTED')).toBeInTheDocument();
    });
  });

  it('renders disconnected state gracefully without crashing when backend is offline', async () => {
    vi.spyOn(apiClient, 'getHealth').mockRejectedValue(new Error('Failed to fetch'));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('API DISCONNECTED')).toBeInTheDocument();
      expect(screen.getByText('FastAPI Backend Offline')).toBeInTheDocument();
    });

    expect(
      screen.getByText(/The React frontend is running independently without mock data/i)
    ).toBeInTheDocument();
  });

  it('renders connected state when backend responds to health check', async () => {
    vi.spyOn(apiClient, 'getHealth').mockResolvedValue({
      status: 'ok',
      service: 'grid-guard-api',
      api_version: '0.1.0',
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('API ONLINE (v0.1.0)')).toBeInTheDocument();
      expect(screen.getByText('FastAPI Connected Successfully')).toBeInTheDocument();
    });
  });

  it('displays the verified architecture baseline details', async () => {
    vi.spyOn(apiClient, 'getHealth').mockRejectedValue(new Error('Offline'));

    render(<App />);

    expect(screen.getByText(/11 Primitives \+ Shared Shell/i)).toBeInTheDocument();
    expect(screen.getByText(/Calm Proof Flow \(\/designsystem\.md\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Active & Preserved \(:8501\)/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('API DISCONNECTED')).toBeInTheDocument();
    });
  });

  it('navigates to Component Showcase and renders gallery sections', async () => {
    vi.spyOn(apiClient, 'getHealth').mockRejectedValue(new Error('Offline'));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('API DISCONNECTED')).toBeInTheDocument();
    });

    const showcaseBtn = screen.getByRole('button', { name: /View Component Showcase/i });
    fireEvent.click(showcaseBtn);

    expect(screen.getByText('Grid-Guard Design System & Component Gallery')).toBeInTheDocument();
    expect(screen.getByText('1. Reusable Buttons')).toBeInTheDocument();
    expect(screen.getByText('5. Financial Presentation Primitives')).toBeInTheDocument();
  });

  it('navigates to Inspection Queue view showing Phase 3 boundary state', async () => {
    vi.spyOn(apiClient, 'getHealth').mockRejectedValue(new Error('Offline'));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('API DISCONNECTED')).toBeInTheDocument();
    });

    const queueTab = screen.getByRole('button', { name: 'Inspection Queue' });
    fireEvent.click(queueTab);

    expect(screen.getByText('Inspection Queue View')).toBeInTheDocument();
    expect(
      screen.getByText(/The prioritized work order queue table will be connected to live FastAPI endpoints/i)
    ).toBeInTheDocument();

    const returnBtn = screen.getByRole('button', { name: 'Return to Overview' });
    fireEvent.click(returnBtn);

    expect(
      screen.getByText(/Calm, financially rational smart-meter inspection analytics/i)
    ).toBeInTheDocument();
  });
});
