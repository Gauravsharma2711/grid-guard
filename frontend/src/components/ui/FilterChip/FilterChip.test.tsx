import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FilterChip } from './FilterChip';

describe('FilterChip Component', () => {
  it('renders with label and toggles on click', () => {
    const handleToggle = vi.fn();
    render(<FilterChip label="ENV > 0" onToggle={handleToggle} />);

    const btn = screen.getByRole('button', { name: 'ENV > 0' });
    expect(btn).toBeInTheDocument();
    expect(btn).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(btn);
    expect(handleToggle).toHaveBeenCalledTimes(1);
  });

  it('renders selected state with chartreuse styling and remove button', () => {
    const handleRemove = vi.fn();
    render(
      <FilterChip
        label="High Risk (p >= 0.75)"
        selected
        count={24}
        onRemove={handleRemove}
      />
    );

    const chipButton = screen.getByRole('button', { pressed: true });
    expect(chipButton).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText('24')).toBeInTheDocument();

    const removeBtn = screen.getByRole('button', { name: /Remove filter/ });
    expect(removeBtn).toBeInTheDocument();
    fireEvent.click(removeBtn);
    expect(handleRemove).toHaveBeenCalledTimes(1);
  });
});
