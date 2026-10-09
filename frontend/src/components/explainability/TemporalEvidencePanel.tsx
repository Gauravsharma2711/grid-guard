import React from 'react';
import type { TemporalEvidenceSchema } from '../../types/api';
import { Surface } from '../ui/Surface/Surface';
import './TemporalEvidencePanel.css';

export interface TemporalEvidencePanelProps {
  evidenceList: TemporalEvidenceSchema[];
  onSelectInterval?: (startDate: string, endDate: string) => void;
}

export const TemporalEvidencePanel: React.FC<TemporalEvidencePanelProps> = ({
  evidenceList,
  onSelectInterval,
}) => {
  return (
    <Surface className="gg-temporal-panel" padded elevation="flat">
      <div className="gg-temporal-panel-header">
        <div>
          <span className="gg-type-label gg-temporal-kicker">Temporal Attribution</span>
          <h3 className="gg-type-title gg-temporal-title">Historical Anomaly Windows</h3>
        </div>
      </div>

      <p className="gg-type-caption gg-temporal-sub">
        Explicit calendar intervals and baseline comparisons corresponding to the model's primary temporal features.
      </p>

      {evidenceList.length === 0 ? (
        <div className="gg-temporal-empty">
          <p className="gg-type-caption">
            No temporal attribution windows were provided for this evaluation. (Source intervals were either unmapped or not returned by the model explainer).
          </p>
        </div>
      ) : (
        <div className="gg-temporal-cards">
          {evidenceList.map((item, index) => {
            const hasDates = item.source_window_start && item.source_window_end;
            const diffPct = item.relative_difference_pct;
            const isNegative = diffPct !== null && diffPct !== undefined && diffPct < 0;

            return (
              <div key={`${item.feature_name}-${index}`} className="gg-temporal-card">
                <div className="gg-temporal-card-top">
                  <div className="gg-temporal-feature-info">
                    <span className="gg-type-mono gg-temporal-index">#{index + 1}</span>
                    <strong className="gg-temporal-feature-name">{item.display_name}</strong>
                  </div>
                  {hasDates && (
                    <div className="gg-temporal-badge">
                      <span className="gg-type-mono">
                        {item.source_window_start} → {item.source_window_end}
                      </span>
                    </div>
                  )}
                </div>

                {/* Values comparison row */}
                <div className="gg-temporal-values-row">
                  <div className="gg-temporal-val-box">
                    <span className="gg-type-caption">Observed Value</span>
                    <span className="gg-type-mono gg-temporal-val">
                      {item.observed_value.toFixed(2)}
                    </span>
                  </div>

                  {item.reference_value !== null && item.reference_value !== undefined && (
                    <div className="gg-temporal-val-box">
                      <span className="gg-type-caption">Historical Baseline</span>
                      <span className="gg-type-mono gg-temporal-val">
                        {item.reference_value.toFixed(2)}
                      </span>
                    </div>
                  )}

                  {diffPct !== null && diffPct !== undefined && (
                    <div className="gg-temporal-val-box">
                      <span className="gg-type-caption">Deviation</span>
                      <span className={`gg-type-mono gg-temporal-diff ${isNegative ? 'gg-diff--neg' : 'gg-diff--pos'}`}>
                        {diffPct > 0 ? `+${diffPct.toFixed(1)}%` : `${diffPct.toFixed(1)}%`}
                      </span>
                    </div>
                  )}

                  <div className="gg-temporal-val-box">
                    <span className="gg-type-caption">SHAP Push</span>
                    <span className="gg-type-mono gg-temporal-shap">
                      {item.shap_contribution > 0 ? `+${item.shap_contribution.toFixed(4)}` : item.shap_contribution.toFixed(4)} Δz
                    </span>
                  </div>
                </div>

                {/* Interpretation narrative */}
                <p className="gg-type-body gg-temporal-interpretation">
                  {item.interpretation}
                </p>

                {hasDates && onSelectInterval && (
                  <button
                    type="button"
                    className="gg-temporal-zoom-btn"
                    onClick={() => onSelectInterval(item.source_window_start, item.source_window_end)}
                  >
                    Highlight Window in Chart →
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </Surface>
  );
};
