import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from './App';
import { apiClient } from './services/apiClient';

describe('App Component (Phase 3 Core Operational Screens & Navigation)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.location.hash = '';
  });

  it('renders the Grid-Guard brand header and Overview screen by default', async () => {
    vi.spyOn(apiClient, 'getReady').mockRejectedValue(new Error('Connection refused'));

    render(<App />);

    expect(screen.getByText('GRID-GUARD')).toBeInTheDocument();
    expect(screen.getByText('NTL Detection Platform')).toBeInTheDocument();
    expect(screen.getByText('Network Decision State')).toBeInTheDocument();
    expect(screen.getByText('Total Expected Net Value (ENV)')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('API DISCONNECTED')).toBeInTheDocument();
    });
  });

  it('navigates to Inspection Queue screen and renders table and filters', async () => {
    vi.spyOn(apiClient, 'getReady').mockResolvedValue({
      status: 'ready',
      model_loaded: true,
      explainer_loaded: true,
      features_configured: true,
      model_version: 'phase6_cost_sensitive_v1',
      feature_count: 60,
      api_version: '0.1.0',
    });

    render(<App />);

    const queueTab = screen.getByRole('button', { name: 'Inspection Queue' });
    fireEvent.click(queueTab);

    expect(screen.getByText('Inspection Work Orders')).toBeInTheDocument();
    expect(screen.getByText('Search Meter ID or Feeder')).toBeInTheDocument();
    expect(screen.getByText('Queue Size')).toBeInTheDocument();
  });

  it('navigates to Meter Analysis screen and renders workbench', async () => {
    vi.spyOn(apiClient, 'getReady').mockRejectedValue(new Error('Offline'));

    render(<App />);

    const meterTab = screen.getByRole('button', { name: 'Meter Analysis' });
    fireEvent.click(meterTab);

    expect(screen.getByRole('heading', { name: 'Meter Analysis' })).toBeInTheDocument();
    expect(screen.getByText('Consumption Time-Series')).toBeInTheDocument();
  });

  it('navigates to Model Insights screen and renders policy evaluation', async () => {
    vi.spyOn(apiClient, 'getReady').mockRejectedValue(new Error('Offline'));

    render(<App />);

    const insightsTab = screen.getByRole('button', { name: 'Model Insights' });
    fireEvent.click(insightsTab);

    expect(
      screen.getByRole('heading', { name: 'Model Insights & Policy Evaluation' })
    ).toBeInTheDocument();
    expect(screen.getByText('Financial Decision Policy Evaluation')).toBeInTheDocument();
  });

  it('navigates to System Info screen and renders runtime introspection', async () => {
    vi.spyOn(apiClient, 'getReady').mockRejectedValue(new Error('Offline'));

    render(<App />);

    const systemTab = screen.getByRole('button', { name: /System Status/i });
    fireEvent.click(systemTab);

    expect(
      screen.getByRole('heading', { name: 'FastAPI Architecture & Runtime' })
    ).toBeInTheDocument();
    expect(screen.getByText(/Readiness Probe/)).toBeInTheDocument();
    expect(screen.getByText(/Public Configuration/)).toBeInTheDocument();
  });

  it('navigates to Component Showcase development gallery', async () => {
    vi.spyOn(apiClient, 'getReady').mockRejectedValue(new Error('Offline'));

    render(<App />);

    const showcaseTab = screen.getByRole('button', { name: /Component Showcase/i });
    fireEvent.click(showcaseTab);

    expect(screen.getByText('Grid-Guard Design System & Component Gallery')).toBeInTheDocument();
    expect(screen.getByText('1. Reusable Buttons')).toBeInTheDocument();
  });
});
