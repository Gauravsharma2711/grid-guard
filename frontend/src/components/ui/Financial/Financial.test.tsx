import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  CurrencyValue,
  EnvMetric,
  ProbabilityMetric,
  FinancialSummaryBlock,
  formatCurrencyAmount,
} from './Financial';

describe('Financial Display Primitives', () => {
  it('formats currency correctly with Indian numbering and INR symbol', () => {
    expect(formatCurrencyAmount(125000, 'INR')).toBe('₹1,25,000.00');
    expect(formatCurrencyAmount(-500, 'INR', true)).toBe('−₹500.00');
    expect(formatCurrencyAmount(450.5, 'USD')).toBe('$450.50');
  });

  it('renders CurrencyValue with context qualifier without modifying underlying amount', () => {
    render(<CurrencyValue amount={28500} currency="INR" context="estimated" />);
    expect(screen.getByText('₹28,500.00')).toBeInTheDocument();
    expect(screen.getByText('(estimated)')).toBeInTheDocument();
  });

  it('renders EnvMetric with explicit sign and economic justification status', () => {
    render(<EnvMetric env={14200.5} currency="INR" />);
    expect(screen.getByText('+₹14,200.50')).toBeInTheDocument();
    expect(screen.getByText('Economically Justified')).toBeInTheDocument();
  });

  it('renders ProbabilityMetric with percentage and model disclaimer', () => {
    render(<ProbabilityMetric probability={0.7842} />);
    expect(screen.getByText('78.4%')).toBeInTheDocument();
    expect(screen.getByText('(Modeled Risk)')).toBeInTheDocument();
  });

  it('renders FinancialSummaryBlock displaying probability, recovery, cost, and ENV in distinct columns', () => {
    render(
      <FinancialSummaryBlock
        tamperProbability={0.885}
        estimatedRecovery={32000}
        dispatchCost={500}
        expectedNetValue={27820}
        currency="INR"
      />
    );

    expect(screen.getByText('88.5%')).toBeInTheDocument();
    expect(screen.getByText('₹32,000.00')).toBeInTheDocument();
    expect(screen.getByText('₹500.00')).toBeInTheDocument();
    expect(screen.getByText('+₹27,820.00')).toBeInTheDocument();
    expect(screen.getByText('Inspection Recommended')).toBeInTheDocument();
  });
});
