import React from 'react';
import './Financial.css';

export interface CurrencyValueProps {
  amount: number;
  currency?: string;
  sign?: boolean;
  context?: 'estimated' | 'expected' | 'realized';
  className?: string;
}

export function formatCurrencyAmount(
  amount: number,
  currency: string = 'INR',
  showSign: boolean = false
): string {
  const isNegative = amount < 0;
  const absAmount = Math.abs(amount);

  const formattedNum = new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(absAmount);

  const symbol = currency === 'INR' ? '₹' : currency === 'USD' ? '$' : `${currency} `;
  const signPrefix = showSign ? (isNegative ? '−' : '+') : isNegative ? '−' : '';

  return `${signPrefix}${symbol}${formattedNum}`;
}

export const CurrencyValue: React.FC<CurrencyValueProps> = ({
  amount,
  currency = 'INR',
  sign = false,
  context,
  className = '',
}) => {
  const formatted = formatCurrencyAmount(amount, currency, sign);

  return (
    <span className={`gg-currency ${className}`}>
      <span className="gg-currency__amount">{formatted}</span>
      {context && (
        <span className="gg-currency__context" aria-label={`Context: ${context}`}>
          ({context})
        </span>
      )}
    </span>
  );
};

export interface EnvMetricProps {
  env: number;
  currency?: string;
  label?: string;
  className?: string;
}

export const EnvMetric: React.FC<EnvMetricProps> = ({
  env,
  currency = 'INR',
  label = 'Expected Net Value (ENV)',
  className = '',
}) => {
  const isPositive = env > 0;
  const isZero = env === 0;

  return (
    <div className={`gg-env-metric ${isPositive ? 'gg-env-metric--positive' : isZero ? 'gg-env-metric--neutral' : 'gg-env-metric--negative'} ${className}`}>
      <span className="gg-env-metric__label">{label}</span>
      <span className="gg-env-metric__value">
        {formatCurrencyAmount(env, currency, true)}
      </span>
      <span className="gg-env-metric__meta">
        {isPositive ? 'Economically Justified' : 'Below Breakeven Threshold'}
      </span>
    </div>
  );
};

export interface ProbabilityMetricProps {
  probability: number;
  label?: string;
  className?: string;
}

export const ProbabilityMetric: React.FC<ProbabilityMetricProps> = ({
  probability,
  label = 'Tamper Probability',
  className = '',
}) => {
  const pct = (probability * 100).toFixed(1);

  return (
    <div className={`gg-prob-metric ${className}`}>
      <span className="gg-prob-metric__label">{label}</span>
      <span className="gg-prob-metric__value">{pct}%</span>
      <span className="gg-prob-metric__context">(Modeled Risk)</span>
    </div>
  );
};

export interface FinancialSummaryBlockProps {
  tamperProbability: number;
  estimatedRecovery: number;
  dispatchCost: number;
  expectedNetValue: number;
  currency?: string;
  className?: string;
}

export const FinancialSummaryBlock: React.FC<FinancialSummaryBlockProps> = ({
  tamperProbability,
  estimatedRecovery,
  dispatchCost,
  expectedNetValue,
  currency = 'INR',
  className = '',
}) => {
  return (
    <div className={`gg-fin-summary-grid ${className}`}>
      <div className="gg-fin-col">
        <span className="gg-fin-col__label">TAMPER PROBABILITY</span>
        <span className="gg-fin-col__value">{(tamperProbability * 100).toFixed(1)}%</span>
        <span className="gg-fin-col__meta">Cost-sensitive LightGBM</span>
      </div>

      <div className="gg-fin-col">
        <span className="gg-fin-col__label">ESTIMATED RECOVERY</span>
        <span className="gg-fin-col__value">{formatCurrencyAmount(estimatedRecovery, currency)}</span>
        <span className="gg-fin-col__meta">12 billing cycles estimate</span>
      </div>

      <div className="gg-fin-col">
        <span className="gg-fin-col__label">DISPATCH COST</span>
        <span className="gg-fin-col__value">{formatCurrencyAmount(dispatchCost, currency)}</span>
        <span className="gg-fin-col__meta">Crew field verification</span>
      </div>

      <div className="gg-fin-col gg-fin-col--env">
        <span className="gg-fin-col__label">EXPECTED NET VALUE (ENV)</span>
        <span className="gg-fin-col__value gg-fin-col__value--env">
          {formatCurrencyAmount(expectedNetValue, currency, true)}
        </span>
        <span className="gg-fin-col__meta">
          {expectedNetValue > 0 ? 'Inspection Recommended' : 'Do Not Dispatch'}
        </span>
      </div>
    </div>
  );
};
