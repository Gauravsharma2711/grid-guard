import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { App } from './App';
import { apiClient } from './services/apiClient';

describe('App Component', () => {
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
      api_version: '1.0.0',
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('API ONLINE (v1.0.0)')).toBeInTheDocument();
      expect(screen.getByText('FastAPI Connected Successfully')).toBeInTheDocument();
    });
  });

  it('displays the verified architecture baseline details', async () => {
    vi.spyOn(apiClient, 'getHealth').mockRejectedValue(new Error('Offline'));

    render(<App />);

    expect(screen.getByText(/React 18 • TypeScript 5.6 • Vite 5.4/i)).toBeInTheDocument();
    expect(screen.getByText(/Calm Proof Flow \(\/designsystem\.md\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Active & Preserved \(:8501\)/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('API DISCONNECTED')).toBeInTheDocument();
    });
  });

  it('contains the primary action button to verify connection', async () => {
    vi.spyOn(apiClient, 'getHealth').mockRejectedValue(new Error('Offline'));

    render(<App />);

    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: /Verify Backend Connection/i })
      ).toBeInTheDocument();
    });
  });
});
