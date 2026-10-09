import React from 'react';
import type { FeatureContributionSchema } from '../../types/api';
import { Surface } from '../ui/Surface/Surface';
import './CounterEvidencePanel.css';

export interface CounterEvidencePanelProps {
  counterEvidenceSummary?: string | null;
  negativeContributors?: FeatureContributionSchema[];
}

export const CounterEvidencePanel: React.FC<CounterEvidencePanelProps> = ({
  counterEvidenceSummary,
  negativeContributors = [],
}) => {
  const hasCounterEvidence =
    Boolean(counterEvidenceSummary) || negativeContributors.length > 0;

  return (
    <Surface className="gg-counter-panel" padded elevation="flat">
      <div className="gg-counter-panel-header">
        <div>
          <span className="gg-type-label gg-counter-kicker">Moderating Factors</span>
          <h3 className="gg-type-title gg-counter-title">Counter-Evidence & Normalization</h3>
        </div>
      </div>

      <p className="gg-type-caption gg-counter-sub">
        Features and behavioral patterns that moderate or push back against the model's tampering risk score.
      </p>

      {!hasCounterEvidence ? (
        <div className="gg-counter-empty">
          <p className="gg-type-caption">
            No moderating counter-evidence was provided by the model explanation service for this evaluation period.
          </p>
        </div>
      ) : (
        <div className="gg-counter-content">
          {counterEvidenceSummary && (
            <div className="gg-counter-summary-banner">
              <span className="gg-type-label">Summary Finding:</span>
              <p className="gg-type-body gg-counter-summary-text">
                {counterEvidenceSummary}
              </p>
            </div>
          )}

          {negativeContributors.length > 0 && (
            <div className="gg-counter-drivers-list">
              <span className="gg-type-label">Negative SHAP Attributions (Mitigating Drivers):</span>
              <div className="gg-counter-items">
                {negativeContributors.map((item, idx) => (
                  <div key={`${item.feature_name}-${idx}`} className="gg-counter-item-card">
                    <div className="gg-counter-item-top">
                      <div>
                        <strong className="gg-counter-item-name">{item.display_name}</strong>
                        <span className="gg-type-caption gg-counter-cat">{item.category}</span>
                      </div>
                      <span className="gg-type-mono gg-counter-val">
                        {item.shap_value.toFixed(4)} Δz
                      </span>
                    </div>

                    <p className="gg-type-caption gg-counter-desc">
                      {item.description}
                    </p>

                    <div className="gg-counter-item-bottom">
                      <span className="gg-type-caption">
                        Observed: <strong className="gg-type-mono">{item.feature_value.toFixed(2)}</strong>
                      </span>
                      {item.baseline_value !== null && item.baseline_value !== undefined && (
                        <span className="gg-type-caption">
                          Baseline: <strong className="gg-type-mono">{item.baseline_value.toFixed(2)}</strong>
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Surface>
  );
};
