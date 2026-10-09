import React from 'react';
import './DataTable.css';

export interface Column<T> {
  key: string;
  header: string;
  align?: 'left' | 'center' | 'right';
  mono?: boolean;
  render?: (row: T, index: number) => React.ReactNode;
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  caption?: string;
  onRowClick?: (row: T) => void;
  selectedKey?: string;
  loading?: boolean;
  emptyMessage?: string;
  className?: string;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  caption,
  onRowClick,
  selectedKey,
  loading = false,
  emptyMessage = 'No records match the current filter criteria.',
  className = '',
}: DataTableProps<T>): React.ReactElement {
  return (
    <div className={`gg-table-container ${className}`}>
      <table className="gg-table">
        {caption && <caption className="gg-table__caption">{caption}</caption>}
        <thead>
          <tr className="gg-table__header-row">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`gg-table__th gg-table__cell--${col.align || 'left'}`}
                scope="col"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="gg-table__state-cell">
                <div className="gg-table__loading-indicator">
                  <span className="gg-table__spinner" aria-hidden="true" />
                  <span>Loading records...</span>
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="gg-table__state-cell">
                <span className="gg-table__empty-text">{emptyMessage}</span>
              </td>
            </tr>
          ) : (
            data.map((row, idx) => {
              const rowKey = keyExtractor(row);
              const isSelected = selectedKey === rowKey;
              const isClickable = Boolean(onRowClick);

              return (
                <tr
                  key={rowKey}
                  className={`gg-table__row ${isSelected ? 'gg-table__row--selected' : ''} ${
                    isClickable ? 'gg-table__row--clickable' : ''
                  }`}
                  onClick={() => onRowClick?.(row)}
                  tabIndex={isClickable ? 0 : undefined}
                  onKeyDown={(e) => {
                    if (isClickable && (e.key === 'Enter' || e.key === ' ')) {
                      e.preventDefault();
                      onRowClick?.(row);
                    }
                  }}
                  aria-selected={isSelected ? 'true' : undefined}
                >
                  {columns.map((col) => {
                    const cellContent = col.render
                      ? col.render(row, idx)
                      : (row as Record<string, unknown>)[col.key] !== undefined
                      ? String((row as Record<string, unknown>)[col.key])
                      : '—';

                    return (
                      <td
                        key={col.key}
                        className={`gg-table__td gg-table__cell--${col.align || 'left'} ${
                          col.mono ? 'gg-table__cell--mono' : ''
                        }`}
                      >
                        {cellContent}
                      </td>
                    );
                  })}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
