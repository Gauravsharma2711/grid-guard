import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Drawer, ConfirmationModal } from './Overlay';

describe('Overlay Components (Drawer & ConfirmationModal)', () => {
  it('renders Drawer when isOpen is true and calls onClose on Escape', () => {
    const handleClose = vi.fn();
    render(
      <Drawer
        isOpen={true}
        onClose={handleClose}
        title="Meter Audit Diagnostics"
        subtitle="CONS_0042 Evidence Review"
      >
        <p>Drawer Diagnostic Body</p>
      </Drawer>
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Meter Audit Diagnostics')).toBeInTheDocument();
    expect(screen.getByText('CONS_0042 Evidence Review')).toBeInTheDocument();
    expect(screen.getByText('Drawer Diagnostic Body')).toBeInTheDocument();

    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('does not render Drawer when isOpen is false', () => {
    render(
      <Drawer isOpen={false} onClose={vi.fn()} title="Hidden Drawer">
        <p>Hidden</p>
      </Drawer>
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders ConfirmationModal with title, description, and action callbacks', () => {
    const handleConfirm = vi.fn();
    const handleCancel = vi.fn();

    render(
      <ConfirmationModal
        isOpen={true}
        title="Discard Inspection Filter"
        message="This will reset all capacity and probability limits."
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    );

    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
    expect(screen.getByText('Discard Inspection Filter')).toBeInTheDocument();

    const confirmBtn = screen.getByRole('button', { name: 'Confirm' });
    fireEvent.click(confirmBtn);
    expect(handleConfirm).toHaveBeenCalledTimes(1);

    const cancelBtn = screen.getByRole('button', { name: 'Cancel' });
    fireEvent.click(cancelBtn);
    expect(handleCancel).toHaveBeenCalledTimes(1);
  });
});
