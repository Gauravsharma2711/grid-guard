import React, { useState } from 'react';
import type { FeatureContributionSchema } from '../../types/api';
import { Button } from '../ui/Button/Button';
import { Surface } from '../ui/Surface/Surface';
import './ShapContributionPanel.css';

export interface ShapContributionPanelProps {
  positiveContributors: FeatureContributionSchema[];
  negativeContributors?: FeatureContributionSchema[];
  baseLogOdds?: number;
  modelProbability?: number;
  rawMargin?: number;
}

export const ShapContributionPanel: React.FC<ShapContributionPanelProps> = ({
  positiveContributors,
  negativeContributors = [],
  baseLogOdds = -2.3713,
  modelProbability,
  rawMargin,
}) => {
  const [showTable, setShowTable] = useState<boolean>(false);

  // Compute maximum absolute SHAP value for proportional bar scaling
  const allContribs = [...positiveContributors, ...negativeContributors];
  const maxAbsShap = allContribs.reduce(
    (max, c) => Math.max(max, Math.abs(c.shap_value)),
    0.01
  );

  return (
    <Surface className="gg-shap-panel" padded elevation="flat">
      <div className="gg-shap-panel-header">
        <div>
          <span className="gg-type-label gg-shap-kicker">Local Tree-SHAP Attribution</span>
          <h3 className="gg-type-title gg-shap-title">Model Evidence & Feature Drivers</h3>
        </div>
        <Button
          variant="secondary"
          size="compact"
          onClick={() => setShowTable(!showTable)}
          aria-label={showTable ? 'Switch to visual bar view' : 'Switch to accessible table view'}
        >
          {showTable ? 'Visual Bars' : 'Accessible Table'}
        </Button>
      </div>

      {/* Output-Space Semantics & Baseline Context */}
      <div className="gg-shap-semantics-banner">
        <div className="gg-shap-semantics-item">
          <span className="gg-type-caption">Output Space</span>
          <span className="gg-type-mono">Log-Odds Margin (z)</span>
        </div>
        <div className="gg-shap-semantics-item">
          <span className="gg-type-caption">Base Expectation E[z]</span>
          <span className="gg-type-mono">{baseLogOdds.toFixed(4)}</span>
        </div>
        {rawMargin !== undefined && (
          <div className="gg-shap-semantics-item">
            <span className="gg-type-caption">Calculated Score z</span>
            <span className="gg-type-mono">{rawMargin.toFixed(4)}</span>
          </div>
        )}
        {modelProbability !== undefined && (
          <div className="gg-shap-semantics-item">
            <span className="gg-type-caption">Calibrated Risk p</span>
            <span className="gg-type-mono">{(modelProbability * 100).toFixed(1)}%</span>
          </div>
        )}
      </div>

      <p className="gg-type-caption gg-shap-note">
        Note: Feature attribution values represent additive shifts in margin score space (z = ln(p/(1-p))), not direct percentage changes in probability. Positive values elevate tampering risk; negative values moderate it.
      </p>

      {/* Accessible Table Representation */}
      {showTable ? (
        <div className="gg-shap-table-container">
          <table className="gg-shap-table" aria-label="Feature SHAP attributions table">
            <thead>
              <tr>
                <th scope="col">Rank</th>
                <th scope="col">Feature & Category</th>
                <th scope="col">Direction</th>
                <th scope="col" className="gg-text-right">Observed Value</th>
                <th scope="col" className="gg-text-right">Baseline Reference</th>
                <th scope="col" className="gg-text-right">Attribution (Δz)</th>
              </tr>
            </thead>
            <tbody>
              {allContribs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="gg-text-center">No feature attributions provided.</td>
                </tr>
              ) : (
                allContribs.map((feat) => {
                  const isPos = feat.shap_value >= 0;
                  return (
                    <tr key={`${feat.feature_name}-${feat.rank}`}>
                      <td className="gg-type-mono">#{feat.rank}</td>
                      <td>
                        <strong>{feat.display_name}</strong>
                        <div className="gg-type-caption">{feat.category} • {feat.feature_name}</div>
                      </td>
                      <td>
                        <span className={`gg-shap-badge ${isPos ? 'gg-shap-badge--pos' : 'gg-shap-badge--neg'}`}>
                          {isPos ? '+ Risk Driver' : '- Mitigating'}
                        </span>
                      </td>
                      <td className="gg-type-mono gg-text-right">
                        {feat.feature_value.toFixed(2)}
                      </td>
                      <td className="gg-type-mono gg-text-right">
                        {feat.baseline_value !== null && feat.baseline_value !== undefined
                          ? feat.baseline_value.toFixed(2)
                          : '—'}
                      </td>
                      <td className="gg-type-mono gg-text-right">
                        <span className={isPos ? 'gg-val--pos' : 'gg-val--neg'}>
                          {isPos ? `+${feat.shap_value.toFixed(4)}` : feat.shap_value.toFixed(4)}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      ) : (
        /* Visual Contribution Stack */
        <div className="gg-shap-visual-stack">
          {/* Top Positive Risk Drivers */}
          <div className="gg-shap-group">
            <h4 className="gg-type-section gg-group-title gg-group-title--pos">
              Primary Risk Drivers (Elevate Tampering Probability)
            </h4>
            {positiveContributors.length === 0 ? (
              <p className="gg-type-caption gg-empty-hint">No positive risk drivers attributed by model.</p>
            ) : (
              <div className="gg-shap-list">
                {positiveContributors.map((c) => {
                  const barPct = Math.min(100, Math.round((Math.abs(c.shap_value) / maxAbsShap) * 100));
                  return (
                    <div key={c.feature_name} className="gg-shap-card gg-shap-card--pos">
                      <div className="gg-shap-card-top">
                        <div className="gg-shap-meta">
                          <span className="gg-type-mono gg-shap-rank">#{c.rank}</span>
                          <span className="gg-shap-name">{c.display_name}</span>
                          <span className="gg-shap-cat">{c.category}</span>
                        </div>
                        <span className="gg-type-mono gg-shap-val gg-shap-val--pos">
                          +{c.shap_value.toFixed(4)} Δz
                        </span>
                      </div>

                      {/* Bar Meter */}
                      <div className="gg-shap-bar-track">
                        <div
                          className="gg-shap-bar-fill gg-shap-bar-fill--pos"
                          style={{ width: `${barPct}%` }}
                          aria-label={`Impact magnitude: ${barPct}%`}
                        />
                      </div>

                      <div className="gg-shap-card-bottom">
                        <span className="gg-type-caption gg-shap-context">
                          Observed: <strong className="gg-type-mono">{c.feature_value.toFixed(2)}</strong>
                          {c.baseline_value !== null && c.baseline_value !== undefined && (
                            <> (Baseline: <strong className="gg-type-mono">{c.baseline_value.toFixed(2)}</strong>)</>
                          )}
                        </span>
                        <span className="gg-type-caption gg-shap-desc">{c.description}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Top Negative Mitigating Factors */}
          {negativeContributors.length > 0 && (
            <div className="gg-shap-group">
              <h4 className="gg-type-section gg-group-title gg-group-title--neg">
                Mitigating Factors (Reduce Tampering Probability)
              </h4>
              <div className="gg-shap-list">
                {negativeContributors.map((c) => {
                  const barPct = Math.min(100, Math.round((Math.abs(c.shap_value) / maxAbsShap) * 100));
                  return (
                    <div key={c.feature_name} className="gg-shap-card gg-shap-card--neg">
                      <div className="gg-shap-card-top">
                        <div className="gg-shap-meta">
                          <span className="gg-type-mono gg-shap-rank">#{c.rank}</span>
                          <span className="gg-shap-name">{c.display_name}</span>
                          <span className="gg-shap-cat">{c.category}</span>
                        </div>
                        <span className="gg-type-mono gg-shap-val gg-shap-val--neg">
                          {c.shap_value.toFixed(4)} Δz
                        </span>
                      </div>

                      {/* Bar Meter */}
                      <div className="gg-shap-bar-track">
                        <div
                          className="gg-shap-bar-fill gg-shap-bar-fill--neg"
                          style={{ width: `${barPct}%` }}
                          aria-label={`Mitigating magnitude: ${barPct}%`}
                        />
                      </div>

                      <div className="gg-shap-card-bottom">
                        <span className="gg-type-caption gg-shap-context">
                          Observed: <strong className="gg-type-mono">{c.feature_value.toFixed(2)}</strong>
                          {c.baseline_value !== null && c.baseline_value !== undefined && (
                            <> (Baseline: <strong className="gg-type-mono">{c.baseline_value.toFixed(2)}</strong>)</>
                          )}
                        </span>
                        <span className="gg-type-caption gg-shap-desc">{c.description}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </Surface>
  );
};
