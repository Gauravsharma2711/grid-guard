import React from 'react';
import './FilterChip.css';

export interface FilterChipProps {
  label: string;
  selected?: boolean;
  count?: number;
  onToggle?: () => void;
  onRemove?: () => void;
  disabled?: boolean;
  className?: string;
}

export const FilterChip: React.FC<FilterChipProps> = ({
  label,
  selected = false,
  count,
  onToggle,
  onRemove,
  disabled = false,
  className = '',
}) => {
  return (
    <span
      className={`gg-filter-chip ${selected ? 'gg-filter-chip--selected' : ''} ${className}`}
    >
      <button
        type="button"
        className="gg-filter-chip__button"
        onClick={onToggle}
        disabled={disabled}
        aria-pressed={selected}
      >
        <span className="gg-filter-chip__label">{label}</span>
        {count !== undefined && (
          <span className="gg-filter-chip__count" aria-hidden="true">
            {count}
          </span>
        )}
      </button>
      {selected && onRemove && (
        <button
          type="button"
          className="gg-filter-chip__remove"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          disabled={disabled}
          aria-label={`Remove filter ${label}`}
        >
          ×
        </button>
      )}
    </span>
  );
};
