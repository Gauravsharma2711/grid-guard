import React from 'react';
import type { DecisionOutput, FinancialOutput, PredictionOutput } from '../../types/api';
import { CurrencyValue, EnvMetric, ProbabilityMetric } from '../ui/Financial/Financial';
import { StatusBadge } from '../ui/Status/Status';
import { Surface } from '../ui/Surface/Surface';
import './DecisionContextPanel.css';

export interface DecisionContextPanelProps {
  prediction: PredictionOutput;
  financial: FinancialOutput;
  decision: DecisionOutput;
}

export const DecisionContextPanel: React.FC<DecisionContextPanelProps> = ({
  prediction,
  financial,
  decision,
}) => {
  const isEnvActive = decision.decision_rule.toLowerCase() === 'env';
  const isCostActive = decision.decision_rule.toLowerCase() === 'cost_threshold';
  const isFixedActive = decision.decision_rule.toLowerCase() === 'fixed_threshold' || decision.decision_rule.toLowerCase() === 'fixed';

  return (
    <Surface className="gg-decision-panel" padded elevation="flat">
      <div className="gg-decision-panel-header">
        <div>
          <span className="gg-type-label gg-decision-kicker">Economic Justification</span>
          <h3 className="gg-type-title gg-decision-title">Financial Decision & Threshold Comparison</h3>
        </div>
        <StatusBadge
          status={decision.inspection_recommended ? 'danger' : 'safe'}
          label={decision.inspection_recommended ? 'Inspection Justified' : 'Inspection Not Justified'}
        />
      </div>

      <p className="gg-type-caption gg-decision-sub">
        Calculated strictly by the backend decision engine. Recommends dispatch when projected recovery exceeds crew cost under the active economic policy.
      </p>

      {/* Primary Financial Metric Strip */}
      <div className="gg-decision-kpi-strip">
        <div className="gg-decision-kpi-box">
          <span className="gg-type-caption">Calibrated Probability</span>
          <ProbabilityMetric probability={prediction.calibrated_probability} />
          <span className="gg-type-caption gg-kpi-hint">Model Risk Estimate</span>
        </div>

        <div className="gg-decision-kpi-box">
          <span className="gg-type-caption">Estimated Leakage</span>
          <span className="gg-type-mono gg-leakage-val">
            {financial.estimated_leakage_kwh.toLocaleString('en-IN', { maximumFractionDigits: 1 })} kWh
          </span>
          <span className="gg-type-caption gg-kpi-hint">Unmetered Volume</span>
        </div>

        <div className="gg-decision-kpi-box">
          <span className="gg-type-caption">Projected Recoverable Revenue</span>
          <CurrencyValue amount={financial.estimated_recoverable_revenue} />
          <span className="gg-type-caption gg-kpi-hint">Gross Exposure (R)</span>
        </div>

        <div className="gg-decision-kpi-box">
          <span className="gg-type-caption">Crew Dispatch Cost</span>
          <CurrencyValue amount={financial.dispatch_cost} />
          <span className="gg-type-caption gg-kpi-hint">Vehicle & Crew (C_FP)</span>
        </div>

        <div className="gg-decision-kpi-box gg-decision-kpi-box--hero">
          <span className="gg-type-caption">Expected Net Value (ENV)</span>
          <EnvMetric env={financial.expected_net_value} />
          <span className="gg-type-caption gg-kpi-hint">E[R] - C_dispatch</span>
        </div>
      </div>

      {/* Decision-Rule Threshold Comparison */}
      <div className="gg-threshold-comparison">
        <span className="gg-type-label">Decision Policy Threshold Comparison:</span>
        <div className="gg-threshold-cards">
          {/* Dynamic ENV Rule */}
          <div className={`gg-rule-card ${isEnvActive ? 'gg-rule-card--active' : ''}`}>
            <div className="gg-rule-card-header">
              <strong className="gg-rule-name">Dynamic ENV Rule</strong>
              {isEnvActive && <span className="gg-rule-active-tag">Active Policy</span>}
            </div>
            <p className="gg-type-caption gg-rule-formula">
              tau_ENV = C_dispatch / R = <strong>{(decision.tau_env * 100).toFixed(2)}%</strong>
            </p>
            <p className="gg-type-caption gg-rule-desc">
              Requires Expected Net Value &gt; 0. Breakeven threshold where probability-weighted recovery exceeds crew dispatch cost.
            </p>
            <div className="gg-rule-status">
              Result:{' '}
              <strong>
                {prediction.calibrated_probability >= decision.tau_env ? 'Recommend Inspection' : 'Do Not Inspect'}
              </strong>
            </div>
          </div>

          {/* Bayes Cost Threshold */}
          <div className={`gg-rule-card ${isCostActive ? 'gg-rule-card--active' : ''}`}>
            <div className="gg-rule-card-header">
              <strong className="gg-rule-name">Bayes Cost Threshold</strong>
              {isCostActive && <span className="gg-rule-active-tag">Active Policy</span>}
            </div>
            <p className="gg-type-caption gg-rule-formula">
              tau_cost = C_dispatch / (C_dispatch + C_FN) = <strong>{(decision.tau_cost * 100).toFixed(2)}%</strong>
            </p>
            <p className="gg-type-caption gg-rule-desc">
              Minimizes total expected operational loss balancing false-positive dispatches against undetected leakage loss.
            </p>
            <div className="gg-rule-status">
              Result:{' '}
              <strong>
                {prediction.calibrated_probability >= decision.tau_cost ? 'Recommend Inspection' : 'Do Not Inspect'}
              </strong>
            </div>
          </div>

          {/* Fixed Probability Threshold */}
          <div className={`gg-rule-card ${isFixedActive ? 'gg-rule-card--active' : ''}`}>
            <div className="gg-rule-card-header">
              <strong className="gg-rule-name">Fixed Cutoff (0.50)</strong>
              {isFixedActive && <span className="gg-rule-active-tag">Active Policy</span>}
            </div>
            <p className="gg-type-caption gg-rule-formula">
              tau_fixed = <strong>50.00%</strong>
            </p>
            <p className="gg-type-caption gg-rule-desc">
              Static 50% probability threshold ignoring monetary exposure volume, customer tariff, and crew dispatch expense.
            </p>
            <div className="gg-rule-status">
              Result:{' '}
              <strong>
                {prediction.calibrated_probability >= 0.5 ? 'Recommend Inspection' : 'Do Not Inspect'}
              </strong>
            </div>
          </div>
        </div>
      </div>

      {decision.priority_context && (
        <div className="gg-decision-context-note">
          <span className="gg-type-label">Operational Dispatch Context:</span>
          <p className="gg-type-body gg-decision-context-text">
            {decision.priority_context}
          </p>
        </div>
      )}
    </Surface>
  );
};
