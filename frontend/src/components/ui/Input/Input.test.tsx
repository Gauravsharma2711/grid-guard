import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FormField, TextInput, NumberInput, Select } from './Input';

describe('Form Controls', () => {
  it('renders FormField with accessible label and input binding', () => {
    render(
      <FormField label="Meter Serial Number" htmlFor="meter-input">
        <TextInput id="meter-input" placeholder="e.g. CONS_0042" />
      </FormField>
    );

    const input = screen.getByLabelText('Meter Serial Number');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('placeholder', 'e.g. CONS_0042');
  });

  it('renders accessible error message with role="alert"', () => {
    render(
      <FormField label="Dispatch Cost" htmlFor="cost-input" error="Cost cannot be negative">
        <NumberInput id="cost-input" />
      </FormField>
    );

    const error = screen.getByRole('alert');
    expect(error).toBeInTheDocument();
    expect(error).toHaveTextContent('Cost cannot be negative');

    const input = screen.getByLabelText('Dispatch Cost');
    expect(input).toHaveAttribute('aria-invalid', 'true');
  });

  it('renders NumberInput with suffix unit correctly', () => {
    render(<NumberInput suffix="kWh/day" defaultValue={45} aria-label="Consumption" />);
    expect(screen.getByText('kWh/day')).toBeInTheDocument();
    expect(screen.getByLabelText('Consumption')).toHaveValue(45);
  });

  it('renders Select with accessible options', () => {
    const options = [
      { value: 'env', label: 'Expected Net Value (ENV)' },
      { value: 'cost_threshold', label: 'Bayes Cost Threshold' },
      { value: 'fixed_threshold', label: 'Fixed Cutoff (p >= 0.5)' },
    ];

    render(
      <FormField label="Decision Rule" htmlFor="rule-select">
        <Select id="rule-select" options={options} defaultValue="env" />
      </FormField>
    );

    const select = screen.getByLabelText('Decision Rule');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('env');
    expect(screen.getAllByRole('option')).toHaveLength(3);
  });
});
