import React, { useId, useMemo, useState } from 'react';
import type { MeterReading } from '../../../types/api';
import { ChartContainer } from './ChartContainer';
import './TimeSeriesChart.css';

export interface TimeSeriesChartProps {
  readings: MeterReading[];
  meterId: string;
  baselineKwh?: number;
  anomalyStartDate?: string;
  unit?: string;
  title?: string;
  subtitle?: string;
  isLoading?: boolean;
}

export const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({
  readings,
  meterId,
  baselineKwh,
  anomalyStartDate,
  unit = 'kWh',
  title = 'Consumption Time-Series',
  subtitle,
  isLoading = false,
}) => {
  const chartId = useId();
  const [activePoint, setActivePoint] = useState<MeterReading | null>(null);

  // Filter valid readings and sort chronologically
  const sortedReadings = useMemo(() => {
    return [...readings]
      .filter((r) => r && !Number.isNaN(r.consumption_kwh))
      .sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  }, [readings]);

  // Compute metrics
  const stats = useMemo(() => {
    if (sortedReadings.length === 0) {
      return { min: 0, max: 0, mean: 0, count: 0, startDate: '', endDate: '' };
    }
    const vals = sortedReadings.map((r) => r.consumption_kwh);
    const min = Math.min(...vals);
    const max = Math.max(...vals, baselineKwh ?? 0);
    const mean = vals.reduce((acc, curr) => acc + curr, 0) / vals.length;
    return {
      min,
      max: max > 0 ? max : 1,
      mean,
      count: sortedReadings.length,
      startDate: sortedReadings[0].timestamp,
      endDate: sortedReadings[sortedReadings.length - 1].timestamp,
    };
  }, [sortedReadings, baselineKwh]);

  // Dimensions
  const viewBoxWidth = 800;
  const viewBoxHeight = 260;
  const padding = { top: 24, right: 32, bottom: 40, left: 56 };
  const graphWidth = viewBoxWidth - padding.left - padding.right;
  const graphHeight = viewBoxHeight - padding.top - padding.bottom;

  // Coordinate scales
  const points = useMemo(() => {
    if (sortedReadings.length === 0) return [];
    const yMax = stats.max * 1.15;
    return sortedReadings.map((r, index) => {
      const x =
        sortedReadings.length === 1
          ? padding.left + graphWidth / 2
          : padding.left + (index / (sortedReadings.length - 1)) * graphWidth;
      const y = padding.top + graphHeight - (r.consumption_kwh / yMax) * graphHeight;
      return { x, y, reading: r };
    });
  }, [sortedReadings, stats.max, graphWidth, graphHeight, padding.left, padding.top]);

  const polylinePoints = useMemo(() => {
    return points.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
  }, [points]);

  // Baseline Y position
  const baselineY = useMemo(() => {
    if (baselineKwh === undefined || baselineKwh <= 0) return null;
    const yMax = stats.max * 1.15;
    return padding.top + graphHeight - (baselineKwh / yMax) * graphHeight;
  }, [baselineKwh, stats.max, graphHeight, padding.top]);

  // Y-axis grid ticks (4 ticks: 0, 33%, 66%, 100%)
  const yTicks = useMemo(() => {
    const yMax = stats.max * 1.15;
    return [0, 0.33, 0.66, 1].map((pct) => {
      const val = yMax * pct;
      const y = padding.top + graphHeight - pct * graphHeight;
      return { val, y };
    });
  }, [stats.max, graphHeight, padding.top]);

  // X-axis date milestones (start, mid, end)
  const xTicks = useMemo(() => {
    if (sortedReadings.length < 2) return [];
    const first = sortedReadings[0];
    const midIdx = Math.floor(sortedReadings.length / 2);
    const mid = sortedReadings[midIdx];
    const last = sortedReadings[sortedReadings.length - 1];

    return [
      { date: first.timestamp, x: padding.left },
      { date: mid.timestamp, x: padding.left + graphWidth / 2 },
      { date: last.timestamp, x: padding.left + graphWidth },
    ];
  }, [sortedReadings, graphWidth, padding.left]);

  const evaluationPeriod =
    stats.startDate && stats.endDate ? `${stats.startDate} → ${stats.endDate}` : undefined;

  const accessibleSummary = `Daily electricity consumption telemetry for meter ${meterId}. Contains ${stats.count} daily intervals from ${stats.startDate} to ${stats.endDate}. Mean consumption is ${stats.mean.toFixed(2)} ${unit}, peak is ${stats.max.toFixed(2)} ${unit}, and minimum is ${stats.min.toFixed(2)} ${unit}.`;

  const legendItems = useMemo(() => {
    const items = [{ label: `Daily Consumption (${unit})`, color: 'var(--gg-text)' }];
    if (baselineKwh !== undefined) {
      items.push({ label: `Historical Baseline (${baselineKwh.toFixed(1)} ${unit})`, color: 'var(--gg-text-muted)' });
    }
    if (anomalyStartDate) {
      items.push({ label: `Anomaly Window (${anomalyStartDate}+)`, color: 'var(--gg-danger)' });
    }
    return items;
  }, [unit, baselineKwh, anomalyStartDate]);

  return (
    <ChartContainer
      title={title}
      subtitle={subtitle || `Telemetry verification for meter ${meterId}`}
      period={evaluationPeriod}
      legend={legendItems}
      loading={isLoading}
      empty={sortedReadings.length === 0}
      emptyMessage="No time-series consumption readings supplied for this meter."
      accessibleSummary={accessibleSummary}
    >
      <div className="gg-timeseries-wrapper" aria-label={`Chart for meter ${meterId}`}>
        <svg
          viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
          className="gg-timeseries-svg"
          role="img"
          aria-labelledby={`${chartId}-desc`}
        >
          <desc id={`${chartId}-desc`}>{accessibleSummary}</desc>

          {/* Horizontal Gridlines & Y-Axis Labels */}
          {yTicks.map((tick, i) => (
            <g key={i} className="gg-chart-gridline-group">
              <line
                x1={padding.left}
                y1={tick.y}
                x2={padding.left + graphWidth}
                y2={tick.y}
                className="gg-chart-gridline"
              />
              <text
                x={padding.left - 10}
                y={tick.y + 4}
                className="gg-chart-axis-label gg-chart-y-label"
              >
                {tick.val.toFixed(1)}
              </text>
            </g>
          ))}

          {/* Historical Baseline Line */}
          {baselineY !== null && (
            <g className="gg-chart-baseline-group">
              <line
                x1={padding.left}
                y1={baselineY}
                x2={padding.left + graphWidth}
                y2={baselineY}
                className="gg-chart-baseline-line"
              />
              <text
                x={padding.left + graphWidth - 4}
                y={baselineY - 6}
                className="gg-chart-baseline-tag"
              >
                Baseline: {baselineKwh?.toFixed(1)} {unit}
              </text>
            </g>
          )}

          {/* Time-Series Area Fill */}
          {points.length > 1 && (
            <polygon
              points={`
                ${padding.left},${padding.top + graphHeight}
                ${polylinePoints}
                ${padding.left + graphWidth},${padding.top + graphHeight}
              `}
              className="gg-chart-area-fill"
            />
          )}

          {/* Time-Series Line */}
          {points.length > 1 && (
            <polyline
              points={polylinePoints}
              className="gg-chart-line"
              vectorEffect="non-scaling-stroke"
            />
          )}

          {/* Interactive Hover Data Points */}
          {points.map((p, idx) => (
            <circle
              key={idx}
              cx={p.x}
              cy={p.y}
              r={activePoint?.timestamp === p.reading.timestamp ? 5 : 2.5}
              className={`gg-chart-point ${
                activePoint?.timestamp === p.reading.timestamp ? 'gg-chart-point-active' : ''
              }`}
              onMouseEnter={() => setActivePoint(p.reading)}
              onMouseLeave={() => setActivePoint(null)}
              tabIndex={0}
              onFocus={() => setActivePoint(p.reading)}
              onBlur={() => setActivePoint(null)}
              aria-label={`${p.reading.timestamp}: ${p.reading.consumption_kwh.toFixed(2)} ${unit}`}
            />
          ))}

          {/* X-Axis Milestones */}
          {xTicks.map((tick, i) => (
            <text
              key={i}
              x={tick.x}
              y={padding.top + graphHeight + 22}
              className="gg-chart-axis-label gg-chart-x-label"
              textAnchor={i === 0 ? 'start' : i === 2 ? 'end' : 'middle'}
            >
              {tick.date}
            </text>
          ))}
        </svg>

        {/* Hover / Active Reading Callout */}
        {activePoint && (
          <div className="gg-chart-tooltip" role="tooltip">
            <span className="gg-chart-tooltip-date">{activePoint.timestamp}</span>
            <span className="gg-chart-tooltip-val">
              {activePoint.consumption_kwh.toFixed(2)} {unit}
            </span>
          </div>
        )}

        {/* Statistical Summary Row */}
        <div className="gg-timeseries-metrics-bar">
          <div className="gg-timeseries-stat">
            <span className="gg-timeseries-stat-label">Daily Mean</span>
            <span className="gg-timeseries-stat-value">
              {stats.mean.toFixed(2)} <span className="gg-timeseries-unit">{unit}</span>
            </span>
          </div>
          <div className="gg-timeseries-stat">
            <span className="gg-timeseries-stat-label">Peak Load</span>
            <span className="gg-timeseries-stat-value">
              {stats.max.toFixed(2)} <span className="gg-timeseries-unit">{unit}</span>
            </span>
          </div>
          <div className="gg-timeseries-stat">
            <span className="gg-timeseries-stat-label">Minimum</span>
            <span className="gg-timeseries-stat-value">
              {stats.min.toFixed(2)} <span className="gg-timeseries-unit">{unit}</span>
            </span>
          </div>
          <div className="gg-timeseries-stat">
            <span className="gg-timeseries-stat-label">Telemetry Days</span>
            <span className="gg-timeseries-stat-value">{stats.count}</span>
          </div>
        </div>
      </div>
    </ChartContainer>
  );
};
