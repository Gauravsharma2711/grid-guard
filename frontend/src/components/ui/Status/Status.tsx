import React from 'react';
import './Status.css';

export type StatusType = 'safe' | 'warning' | 'danger' | 'neutral';

export interface StatusBadgeProps {
  status: StatusType;
  label: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  className = '',
}) => {
  return (
    <span className={`gg-status-badge gg-status-badge--${status} ${className}`}>
      <span className="gg-status-badge__dot" aria-hidden="true" />
      <span className="gg-status-badge__text">{label}</span>
    </span>
  );
};

export interface EvidenceBadgeProps {
  label: string;
  direction?: 'positive' | 'negative';
  className?: string;
}

export const EvidenceBadge: React.FC<EvidenceBadgeProps> = ({
  label,
  direction,
  className = '',
}) => {
  return (
    <span className={`gg-evidence-badge ${direction ? `gg-evidence-badge--${direction}` : ''} ${className}`}>
      <span className="gg-evidence-badge__tag" aria-hidden="true">SHAP</span>
      <span className="gg-evidence-badge__label">{label}</span>
      {direction && (
        <span className="gg-evidence-badge__dir" aria-label={`Contribution direction: ${direction}`}>
          {direction === 'positive' ? '+ Risk' : '- Counter'}
        </span>
      )}
    </span>
  );
};

export interface TechnicalMetadataProps {
  label: string;
  value: string | number;
  className?: string;
}

export const TechnicalMetadata: React.FC<TechnicalMetadataProps> = ({
  label,
  value,
  className = '',
}) => {
  return (
    <div className={`gg-tech-meta ${className}`}>
      <span className="gg-tech-meta__label">{label}</span>
      <span className="gg-tech-meta__value">{value}</span>
    </div>
  );
};

export interface DataQualityWarningProps {
  title?: string;
  message: string;
  className?: string;
}

export const DataQualityWarning: React.FC<DataQualityWarningProps> = ({
  title = 'Data Quality Warning',
  message,
  className = '',
}) => {
  return (
    <div className={`gg-quality-warning ${className}`} role="status">
      <span className="gg-quality-warning__icon" aria-hidden="true">⚠</span>
      <div className="gg-quality-warning__content">
        <strong className="gg-quality-warning__title">{title}</strong>
        <p className="gg-quality-warning__message">{message}</p>
      </div>
    </div>
  );
};
