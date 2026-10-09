import React from 'react';
import type { TamperingSignatureSchema } from '../../types/api';
import { StatusBadge } from '../ui/Status/Status';
import { Surface } from '../ui/Surface/Surface';
import './TamperingSignaturesPanel.css';

export interface TamperingSignaturesPanelProps {
  signatures: TamperingSignatureSchema[];
}

export const TamperingSignaturesPanel: React.FC<TamperingSignaturesPanelProps> = ({
  signatures,
}) => {
  // Only display detected signatures
  const detectedList = signatures.filter((s) => s.detected);

  return (
    <Surface className="gg-signatures-panel" padded elevation="flat">
      <div className="gg-signatures-panel-header">
        <div>
          <span className="gg-type-label gg-signatures-kicker">Electrical Anomaly Signatures</span>
          <h3 className="gg-type-title gg-signatures-title">Detected Consumption Signatures</h3>
        </div>
        <span className="gg-type-mono gg-signatures-count">
          {detectedList.length} Pattern{detectedList.length === 1 ? '' : 's'} Detected
        </span>
      </div>

      <p className="gg-type-caption gg-signatures-note">
        Rule-based behavioral signatures evaluated across telemetry time-series independent of tree boosting weights.
      </p>

      {detectedList.length === 0 ? (
        <div className="gg-signatures-empty">
          <p className="gg-type-caption">
            No anomalous consumption signatures were detected for this evaluation period.
          </p>
        </div>
      ) : (
        <div className="gg-signatures-grid">
          {detectedList.map((sig, idx) => {
            const formattedName = sig.signature_type
              .replace(/_/g, ' ')
              .replace(/\b\w/g, (l) => l.toUpperCase());

            const severityStatus =
              sig.severity.toLowerCase() === 'high'
                ? 'danger'
                : sig.severity.toLowerCase() === 'medium' || sig.severity.toLowerCase() === 'moderate'
                ? 'warning'
                : 'neutral';

            return (
              <div key={`${sig.signature_type}-${idx}`} className="gg-sig-item-card">
                <div className="gg-sig-item-header">
                  <div className="gg-sig-item-title-row">
                    <strong className="gg-sig-item-name">{formattedName}</strong>
                    <StatusBadge
                      status={severityStatus}
                      label={`Severity: ${sig.severity.toUpperCase()}`}
                    />
                  </div>
                </div>

                <p className="gg-type-body gg-sig-item-desc">{sig.description}</p>

                <div className="gg-sig-item-meta">
                  <span className="gg-type-caption">
                    Magnitude: <strong className="gg-type-mono">{(sig.magnitude * 100).toFixed(0)}%</strong>
                  </span>
                  {sig.duration_days !== null && sig.duration_days !== undefined && (
                    <span className="gg-type-caption">
                      Duration: <strong className="gg-type-mono">{sig.duration_days} Days</strong>
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Standard Regulatory & Safety Caveat */}
      <div className="gg-signatures-disclaimer">
        <span className="gg-type-mono gg-disclaimer-tag">[FIELD VERIFICATION REQUIRED]</span>
        <p className="gg-type-caption gg-disclaimer-text">
          Consumption patterns are consistent with an anomalous reduction or load distortion. Physical on-site inspection is required to determine whether an unauthorized bypass, physical tamper, or metering fault has occurred.
        </p>
      </div>
    </Surface>
  );
};
