import React from 'react';
import type { InspectionTicketResponse } from '../../types/api';
import { exportTicketAsJson } from '../../utils/exportUtils';
import { Button } from '../ui/Button/Button';
import { CurrencyValue, EnvMetric, ProbabilityMetric } from '../ui/Financial/Financial';
import { StatusBadge } from '../ui/Status/Status';
import { Surface } from '../ui/Surface/Surface';
import './InspectionTicketView.css';

export interface InspectionTicketViewProps {
  ticket: InspectionTicketResponse;
  onClose?: () => void;
  onAnalyzeMeter?: (meterId: string) => void;
}

export const InspectionTicketView: React.FC<InspectionTicketViewProps> = ({
  ticket,
  onClose,
  onAnalyzeMeter,
}) => {
  const explanation = ticket.explanation;
  const positiveDrivers = explanation?.top_positive_contributors ?? [];
  const negativeDrivers = explanation?.top_negative_contributors ?? [];
  const signatures = explanation?.detected_signatures ?? [];
  const temporal = explanation?.temporal_evidence ?? [];

  const handleDownload = () => {
    exportTicketAsJson(ticket);
  };

  return (
    <div className="gg-ticket-doc" data-testid="inspection-ticket-document">
      {/* Top Action Bar */}
      <div className="gg-ticket-action-bar">
        <div className="gg-ticket-action-left">
          <span className="gg-type-mono gg-ticket-badge">FIELD INSPECTION WORK ORDER</span>
          <span className="gg-type-mono gg-ticket-id-tag">{ticket.ticket_id}</span>
        </div>
        <div className="gg-ticket-action-right">
          <Button
            variant="primary"
            size="compact"
            onClick={handleDownload}
          >
            Download Ticket (JSON)
          </Button>
          {onAnalyzeMeter && (
            <Button
              variant="secondary"
              size="compact"
              onClick={() => onAnalyzeMeter(ticket.meter_id)}
            >
              Analyze in Workbench →
            </Button>
          )}
          {onClose && (
            <Button
              variant="text"
              size="compact"
              onClick={onClose}
              aria-label="Close ticket view"
            >
              Close
            </Button>
          )}
        </div>
      </div>

      {/* Main Ticket Surface */}
      <Surface className="gg-ticket-surface" padded elevation="flat">
        {/* Header Block */}
        <div className="gg-ticket-header-block">
          <div className="gg-ticket-header-main">
            <h2 className="gg-type-display gg-ticket-title">Forensic Field Inspection Ticket</h2>
            <p className="gg-type-body gg-ticket-lead">
              Revenue protection audit report and decision justification. Authorized for field verification dispatch.
            </p>
          </div>
          <div className="gg-ticket-header-meta">
            <div>
              <span className="gg-type-caption">Evaluation Period</span>
              <span className="gg-type-mono">{ticket.evaluation_period}</span>
            </div>
            <div>
              <span className="gg-type-caption">Meter Identifier</span>
              <span className="gg-type-mono gg-ticket-meta-id">{ticket.meter_id}</span>
            </div>
            <div>
              <span className="gg-type-caption">Distribution Feeder</span>
              <span className="gg-type-mono">{ticket.feeder_id}</span>
            </div>
            <div>
              <span className="gg-type-caption">Customer Classification</span>
              <span className="gg-type-mono">{ticket.customer_type}</span>
            </div>
          </div>
        </div>

        {/* Operational Recommendation Banner */}
        <div className="gg-ticket-decision-banner">
          <div className="gg-ticket-decision-status">
            <span className="gg-type-caption">Operational Recommendation</span>
            <div className="gg-ticket-status-row">
              <StatusBadge
                status={ticket.inspection_recommended ? 'danger' : 'neutral'}
                label={
                  ticket.inspection_recommended
                    ? 'Physical Inspection Recommended'
                    : 'Monitoring Only (No Dispatch)'
                }
              />
              <span className="gg-type-mono gg-ticket-rank">
                Queue Rank: #{ticket.priority_rank ?? '—'}
              </span>
            </div>
          </div>

          <div className="gg-ticket-decision-stats">
            <div>
              <span className="gg-type-caption">Calibrated Tamper Risk</span>
              <ProbabilityMetric probability={ticket.calibrated_probability} />
            </div>
            <div>
              <span className="gg-type-caption">Expected Net Value</span>
              <EnvMetric env={ticket.env} />
            </div>
            <div>
              <span className="gg-type-caption">Active Decision Rule</span>
              <span className="gg-type-mono gg-ticket-rule-name">
                {ticket.decision_rule.toUpperCase()} (tau = {(ticket.active_threshold * 100).toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>

        {/* Financial Assessment Section */}
        <div className="gg-ticket-section">
          <h3 className="gg-type-title gg-section-heading">1. Financial Rationale & Cost-Benefit Analysis</h3>
          <div className="gg-ticket-fin-grid">
            <div className="gg-fin-card">
              <span className="gg-type-caption">Estimated Unmetered Leakage</span>
              <span className="gg-type-mono gg-fin-val">
                {ticket.estimated_leakage_kwh.toLocaleString('en-IN', { maximumFractionDigits: 1 })} kWh
              </span>
              <span className="gg-type-caption gg-fin-desc">Unmetered loss during undetected cycles</span>
            </div>

            <div className="gg-fin-card">
              <span className="gg-type-caption">Projected Recoverable Revenue</span>
              <CurrencyValue amount={ticket.estimated_recoverable_revenue} />
              <span className="gg-type-caption gg-fin-desc">Gross utility revenue at risk</span>
            </div>

            <div className="gg-fin-card">
              <span className="gg-type-caption">Crew Dispatch Expense</span>
              <CurrencyValue amount={ticket.dispatch_cost} />
              <span className="gg-type-caption gg-fin-desc">Vehicle, labor, and safety cost (C_FP)</span>
            </div>

            <div className="gg-fin-card gg-fin-card--hero">
              <span className="gg-type-caption">Expected Net Value (ENV)</span>
              <EnvMetric env={ticket.env} />
              <span className="gg-type-caption gg-fin-desc">Probability-weighted net economic return</span>
            </div>
          </div>
        </div>

        {/* Forensic Audit Narrative */}
        <div className="gg-ticket-section">
          <h3 className="gg-type-title gg-section-heading">2. Forensic Audit Summary</h3>
          <div className="gg-ticket-narrative-box">
            <p className="gg-type-body gg-ticket-summary-text">
              {explanation?.summary ||
                `High-confidence consumption collapse detected. Estimated unmetered leakage volume is ${ticket.estimated_leakage_kwh.toFixed(1)} kWh with Expected Net Value of ₹${ticket.env.toFixed(2)}.`}
            </p>
            {explanation?.detailed_explanation && (
              <p className="gg-type-caption gg-ticket-detailed-text">
                {explanation.detailed_explanation}
              </p>
            )}
          </div>
        </div>

        {/* Primary Model Evidence (SHAP Drivers) */}
        {positiveDrivers.length > 0 && (
          <div className="gg-ticket-section">
            <h3 className="gg-type-title gg-section-heading">3. Primary Model Evidence (Tree-SHAP Attributions)</h3>
            <p className="gg-type-caption gg-section-sub">
              Key causal features pushing the LightGBM booster toward an anomalous classification (log-odds margin Δz):
            </p>
            <div className="gg-ticket-shap-list">
              {positiveDrivers.slice(0, 4).map((feat, i) => (
                <div key={i} className="gg-ticket-shap-row">
                  <div className="gg-ticket-shap-left">
                    <span className="gg-type-mono gg-ticket-shap-rank">#{feat.rank}</span>
                    <strong className="gg-ticket-shap-name">{feat.display_name}</strong>
                    <span className="gg-type-caption gg-ticket-shap-cat">({feat.category})</span>
                  </div>
                  <div className="gg-ticket-shap-right">
                    <span className="gg-type-caption">
                      Observed: <strong className="gg-type-mono">{feat.feature_value.toFixed(2)}</strong>
                    </span>
                    <span className="gg-type-mono gg-ticket-shap-delta">
                      +{feat.shap_value.toFixed(4)} Δz
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Historical Temporal Windows */}
        {temporal.length > 0 && (
          <div className="gg-ticket-section">
            <h3 className="gg-type-title gg-section-heading">4. Historical Temporal Windows</h3>
            <div className="gg-ticket-temporal-list">
              {temporal.map((t, idx) => (
                <div key={idx} className="gg-ticket-temporal-item">
                  <div className="gg-ticket-temporal-header">
                    <strong>{t.display_name}</strong>
                    <span className="gg-type-mono gg-ticket-window-tag">
                      {t.source_window_start} → {t.source_window_end}
                    </span>
                  </div>
                  <p className="gg-type-caption gg-ticket-temporal-interp">{t.interpretation}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Electrical Tampering Signatures */}
        {signatures.length > 0 && (
          <div className="gg-ticket-section">
            <h3 className="gg-type-title gg-section-heading">5. Physical Electrical Anomaly Signatures</h3>
            <div className="gg-ticket-sig-chips">
              {signatures.map((sig, i) => (
                <div key={i} className="gg-ticket-sig-card">
                  <div className="gg-ticket-sig-header">
                    <strong>{sig.signature_type.replace(/_/g, ' ').toUpperCase()}</strong>
                    <span className="gg-type-mono gg-ticket-sig-sev">[{sig.severity.toUpperCase()}]</span>
                  </div>
                  <p className="gg-type-caption">{sig.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Moderating Counter-Evidence */}
        {negativeDrivers.length > 0 && (
          <div className="gg-ticket-section">
            <h3 className="gg-type-title gg-section-heading">6. Moderating Counter-Evidence</h3>
            <p className="gg-type-caption gg-section-sub">
              Features moderating the risk score:
            </p>
            <div className="gg-ticket-counter-list">
              {negativeDrivers.slice(0, 3).map((feat, i) => (
                <div key={i} className="gg-ticket-counter-row">
                  <span className="gg-type-caption">
                    <strong>{feat.display_name}</strong> ({feat.category})
                  </span>
                  <span className="gg-type-mono gg-ticket-counter-delta">
                    {feat.shap_value.toFixed(4)} Δz
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Standard Safety Disclaimer */}
        <div className="gg-ticket-disclaimer-box">
          <strong className="gg-type-mono gg-disclaimer-title">REGULATORY AND OPERATIONAL DISCLAIMER</strong>
          <p className="gg-type-caption gg-disclaimer-body">
            {ticket.safety_caveat ||
              'Model evidence indicates an anomalous consumption pattern and requires physical on-site inspection. This ticket constitutes an operational dispatch recommendation based on expected economic net value; physical meter tampering, bypass, or hardware defect can only be confirmed through on-site field verification.'}
          </p>
        </div>
      </Surface>
    </div>
  );
};
