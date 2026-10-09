import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AppHeader } from './AppHeader';
import { AppShell } from './AppShell';
import { DecisionCanvas, OperationsCanvas, SectionHeader } from './LayoutPrimitives';

describe('Layout & Shell Components', () => {
  it('renders AppHeader with brand wordmark and nav items', () => {
    const handleNav = vi.fn();
    render(
      <AppHeader
        activeNav="overview"
        onNavigate={handleNav}
        statusNode={<span>ONLINE</span>}
      />
    );

    expect(screen.getByText('GRID-GUARD')).toBeInTheDocument();
    expect(screen.getByText('NTL Detection Platform')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Overview' })).toBeInTheDocument();
    expect(screen.getByText('ONLINE')).toBeInTheDocument();

    const queueBtn = screen.getByRole('button', { name: 'Inspection Queue' });
    fireEvent.click(queueBtn);
    expect(handleNav).toHaveBeenCalledWith('queue');
  });

  it('renders DecisionCanvas with constrained reading width', () => {
    const { container } = render(
      <DecisionCanvas>
        <p>Focused Analysis Content</p>
      </DecisionCanvas>
    );

    expect(screen.getByText('Focused Analysis Content')).toBeInTheDocument();
    expect(container.querySelector('.gg-decision-column')).toBeInTheDocument();
  });

  it('renders OperationsCanvas with wide container and SectionHeader', () => {
    render(
      <OperationsCanvas>
        <SectionHeader
          title="Field Inspection Work Orders"
          description="Candidates sorted by Expected Net Value."
          badge="ENV RANKED"
        />
      </OperationsCanvas>
    );

    expect(screen.getByText('Field Inspection Work Orders')).toBeInTheDocument();
    expect(screen.getByText('Candidates sorted by Expected Net Value.')).toBeInTheDocument();
    expect(screen.getByText('ENV RANKED')).toBeInTheDocument();
  });

  it('renders AppShell with header, main content, and footer', () => {
    render(
      <AppShell
        activeNav="overview"
        onNavigate={vi.fn()}
        footerNode={<div data-testid="test-footer">Footer Content</div>}
      >
        <div data-testid="main-content">Shell Body</div>
      </AppShell>
    );

    expect(screen.getByTestId('main-content')).toBeInTheDocument();
    expect(screen.getByTestId('test-footer')).toBeInTheDocument();
  });
});
