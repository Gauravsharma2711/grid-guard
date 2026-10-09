import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button Component', () => {
  it('renders with children text and default secondary variant', () => {
    render(<Button>Inspect Meter</Button>);
    const btn = screen.getByRole('button', { name: 'Inspect Meter' });
    expect(btn).toBeInTheDocument();
    expect(btn).toHaveClass('gg-btn--secondary');
    expect(btn).toHaveClass('gg-btn--normal');
  });

  it('renders primary variant with proper styling class', () => {
    render(<Button variant="primary">Confirm Action</Button>);
    const btn = screen.getByRole('button', { name: 'Confirm Action' });
    expect(btn).toHaveClass('gg-btn--primary');
  });

  it('renders text and destructive variants', () => {
    const { rerender } = render(<Button variant="text">Cancel</Button>);
    expect(screen.getByRole('button', { name: 'Cancel' })).toHaveClass('gg-btn--text');

    rerender(<Button variant="destructive">Delete Queue</Button>);
    expect(screen.getByRole('button', { name: 'Delete Queue' })).toHaveClass('gg-btn--destructive');
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Trigger</Button>);
    fireEvent.click(screen.getByRole('button', { name: 'Trigger' }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled and prevents click events when disabled prop is true', () => {
    const handleClick = vi.fn();
    render(<Button disabled onClick={handleClick}>Disabled Action</Button>);
    const btn = screen.getByRole('button', { name: 'Disabled Action' });
    expect(btn).toBeDisabled();
    fireEvent.click(btn);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('shows spinner and is aria-busy when loading is true', () => {
    const handleClick = vi.fn();
    render(<Button loading onClick={handleClick}>Evaluating</Button>);
    const btn = screen.getByRole('button', { name: 'Evaluating' });
    expect(btn).toHaveAttribute('aria-busy', 'true');
    expect(btn).toBeDisabled();
    fireEvent.click(btn);
    expect(handleClick).not.toHaveBeenCalled();
  });
});
