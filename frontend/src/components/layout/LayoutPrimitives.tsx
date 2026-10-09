import React from 'react';
import './LayoutPrimitives.css';

export interface PageContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export const PageContainer: React.FC<PageContainerProps> = ({
  children,
  className = '',
  ...props
}) => {
  return (
    <div className={`gg-page-container ${className}`} {...props}>
      {children}
    </div>
  );
};

export interface DecisionCanvasProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

/**
 * Decision Canvas Layout Pattern:
 * Focuses on one central question in a 560-680px reading column with generous whitespace.
 */
export const DecisionCanvas: React.FC<DecisionCanvasProps> = ({
  children,
  className = '',
  ...props
}) => {
  return (
    <div className={`gg-decision-canvas ${className}`} {...props}>
      <div className="gg-decision-column">{children}</div>
    </div>
  );
};

export interface OperationsCanvasProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

/**
 * Operations Canvas Layout Pattern:
 * Restrained full-width content area (up to 1440px) with clear hierarchy for inspection queues and analytics.
 */
export const OperationsCanvas: React.FC<OperationsCanvasProps> = ({
  children,
  className = '',
  ...props
}) => {
  return (
    <div className={`gg-operations-canvas ${className}`} {...props}>
      {children}
    </div>
  );
};

export interface SectionHeaderProps {
  title: string;
  description?: string;
  badge?: string;
  action?: React.ReactNode;
  className?: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  description,
  badge,
  action,
  className = '',
}) => {
  return (
    <div className={`gg-section-header ${className}`}>
      <div className="gg-section-header__titles">
        <div className="gg-section-header__lead-row">
          <h2 className="gg-section-header__title">{title}</h2>
          {badge && <span className="gg-section-header__badge">{badge}</span>}
        </div>
        {description && <p className="gg-section-header__desc">{description}</p>}
      </div>
      {action && <div className="gg-section-header__action">{action}</div>}
    </div>
  );
};
