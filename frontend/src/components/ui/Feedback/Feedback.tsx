import React from 'react';
import { Button } from '../Button/Button';
import './Feedback.css';

export interface LoadingStateProps {
  title?: string;
  description?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  title = 'Evaluating smart meter telemetry',
  description = 'Processing causal temporal features and computing cost-sensitive risk score...',
  className = '',
}) => {
  return (
    <div className={`gg-feedback-state gg-loading-state ${className}`} role="status">
      <span className="gg-feedback-spinner" aria-hidden="true" />
      <h3 className="gg-feedback-title">{title}</h3>
      <p className="gg-feedback-desc">{description}</p>
    </div>
  );
};

export interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionLabel,
  onAction,
  className = '',
}) => {
  return (
    <div className={`gg-feedback-state gg-empty-state ${className}`}>
      <div className="gg-empty-icon" aria-hidden="true">∅</div>
      <h3 className="gg-feedback-title">{title}</h3>
      <p className="gg-feedback-desc">{description}</p>
      {actionLabel && onAction && (
        <div className="gg-feedback-action">
          <Button variant="secondary" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      )}
    </div>
  );
};

export interface ErrorStateProps {
  title?: string;
  message: string;
  technicalDetails?: string;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Operational Error Encountered',
  message,
  technicalDetails,
  onRetry,
  retryLabel = 'Retry Operation',
  className = '',
}) => {
  return (
    <div className={`gg-feedback-state gg-error-state ${className}`} role="alert">
      <div className="gg-error-icon" aria-hidden="true">⚠</div>
      <h3 className="gg-feedback-title gg-feedback-title--error">{title}</h3>
      <p className="gg-feedback-desc">{message}</p>
      {onRetry && (
        <div className="gg-feedback-action">
          <Button variant="primary" onClick={onRetry}>
            {retryLabel}
          </Button>
        </div>
      )}
      {technicalDetails && (
        <details className="gg-error-details">
          <summary className="gg-error-summary">Diagnostic Information</summary>
          <pre className="gg-error-code">
            <code>{technicalDetails}</code>
          </pre>
        </details>
      )}
    </div>
  );
};

export interface DegradedBannerProps {
  title: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const DegradedBanner: React.FC<DegradedBannerProps> = ({
  title,
  message,
  onRetry,
  className = '',
}) => {
  return (
    <div className={`gg-degraded-banner ${className}`} role="status">
      <span className="gg-degraded-icon" aria-hidden="true">⚡</span>
      <div className="gg-degraded-content">
        <strong className="gg-degraded-title">{title}</strong>
        <span className="gg-degraded-message">{message}</span>
      </div>
      {onRetry && (
        <Button variant="secondary" size="compact" onClick={onRetry}>
          Reconnect
        </Button>
      )}
    </div>
  );
};
