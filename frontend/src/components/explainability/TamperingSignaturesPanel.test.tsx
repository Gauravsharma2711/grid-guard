import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { TamperingSignatureSchema } from '../../types/api';
import { TamperingSignaturesPanel } from './TamperingSignaturesPanel';

describe('TamperingSignaturesPanel', () => {
  const mockSignatures: TamperingSignatureSchema[] = [
    {
      signature_type: 'sustained_step_down',
      detected: true,
      magnitude: 0.85,
      duration_days: 15,
      severity: 'high',
      description: 'Recent 14-day load collapsed by 85% relative to the 60-day baseline average.',
    },
    {
      signature_type: 'flatline',
      detected: true,
      magnitude: 0.92,
      duration_days: 12,
      severity: 'moderate',
      description: 'Daily consumption variance collapsed to near-zero.',
    },
    {
      signature_type: 'zero_streak',
      detected: false,
      magnitude: 0.0,
      duration_days: 0,
      severity: 'none',
      description: 'No consecutive zeros detected.',
    },
  ];

  it('renders detected signatures with magnitude, duration, and severity', () => {
    render(<TamperingSignaturesPanel signatures={mockSignatures} />);

    expect(screen.getByText('Detected Consumption Signatures')).toBeInTheDocument();
    expect(screen.getByText('2 Patterns Detected')).toBeInTheDocument();
    expect(screen.getByText('Sustained Step Down')).toBeInTheDocument();
    expect(screen.getByText('Flatline')).toBeInTheDocument();
    expect(screen.queryByText('Zero Streak')).not.toBeInTheDocument(); // not detected

    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('15 Days')).toBeInTheDocument();
  });

  it('displays the field verification disclaimer stating physical inspection is required', () => {
    render(<TamperingSignaturesPanel signatures={mockSignatures} />);

    expect(screen.getByText(/\[FIELD VERIFICATION REQUIRED\]/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Physical on-site inspection is required to determine whether an unauthorized bypass/i)
    ).toBeInTheDocument();
  });

  it('handles empty signatures list gracefully', () => {
    render(<TamperingSignaturesPanel signatures={[]} />);

    expect(
      screen.getByText(/No anomalous consumption signatures were detected for this evaluation period/i)
    ).toBeInTheDocument();
  });
});
