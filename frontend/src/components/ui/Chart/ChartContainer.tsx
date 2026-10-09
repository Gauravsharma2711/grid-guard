import React from 'react';
import './ChartContainer.css';

export interface ChartLegendItem {
  label: string;
  color: string;
  lineStyle?: 'solid' | 'dashed' | 'dotted';
}

export interface ChartContainerProps {
  title: string;
  subtitle?: string;
  period?: string;
  yAxisLabel?: string;
  xAxisLabel?: string;
  legend?: ChartLegendItem[];
  loading?: boolean;
  error?: string;
  empty?: boolean;
  emptyMessage?: string;
  accessibleSummary?: string;
  children?: React.ReactNode;
  className?: string;
}

export const ChartContainer: React.FC<ChartContainerProps> = ({
  title,
  subtitle,
  period,
  yAxisLabel,
  xAxisLabel,
  legend,
  loading = false,
  error,
  empty = false,
  emptyMessage = 'No time-series data available for the selected interval.',
  accessibleSummary,
  children,
  className = '',
}) => {
  return (
    <div className={`gg-chart-container ${className}`}>
      {/* Chart Header */}
      <div className="gg-chart-header">
        <div className="gg-chart-titles">
          <h3 className="gg-chart-title">{title}</h3>
          {subtitle && <p className="gg-chart-subtitle">{subtitle}</p>}
        </div>
        {period && (
          <span className="gg-chart-period" aria-label={`Evaluation period: ${period}`}>
            PERIOD: {period}
          </span>
        )}
      </div>

      {/* Legend */}
      {legend && legend.length > 0 && (
        <div className="gg-chart-legend" role="list" aria-label="Chart series legend">
          {legend.map((item) => (
            <div key={item.label} className="gg-chart-legend__item" role="listitem">
              <span
                className={`gg-chart-legend__swatch gg-chart-legend__swatch--${item.lineStyle || 'solid'}`}
                style={{ backgroundColor: item.color }}
                aria-hidden="true"
              />
              <span className="gg-chart-legend__label">{item.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* Chart Content Area */}
      <div className="gg-chart-body">
        {loading ? (
          <div className="gg-chart-state" role="status">
            <span className="gg-chart-spinner" aria-hidden="true" />
            <span className="gg-chart-state__text">Rendering chart series...</span>
          </div>
        ) : error ? (
          <div className="gg-chart-state gg-chart-state--error" role="alert">
            <span className="gg-chart-state__icon" aria-hidden="true">⚠</span>
            <span className="gg-chart-state__text">{error}</span>
          </div>
        ) : empty ? (
          <div className="gg-chart-state" role="status">
            <span className="gg-chart-state__text">{emptyMessage}</span>
          </div>
        ) : (
          <div className="gg-chart-canvas-wrapper">
            {yAxisLabel && (
              <div className="gg-chart-axis-label gg-chart-axis-label--y" aria-hidden="true">
                {yAxisLabel}
              </div>
            )}
            <div className="gg-chart-content">{children}</div>
            {xAxisLabel && (
              <div className="gg-chart-axis-label gg-chart-axis-label--x" aria-hidden="true">
                {xAxisLabel}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Accessible text alternative for screen readers */}
      {accessibleSummary && (
        <details className="gg-chart-a11y-details">
          <summary className="gg-chart-a11y-summary">Data summary for screen readers</summary>
          <p className="gg-chart-a11y-text">{accessibleSummary}</p>
        </details>
      )}
    </div>
  );
};
