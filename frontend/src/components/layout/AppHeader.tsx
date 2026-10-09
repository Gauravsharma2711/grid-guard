import React from 'react';
import './AppHeader.css';

export type NavDestination =
  | 'overview'
  | 'queue'
  | 'meter'
  | 'insights'
  | 'system'
  | 'showcase';

export interface NavItem {
  id: NavDestination;
  label: string;
  badge?: string;
  disabled?: boolean;
}

export interface AppHeaderProps {
  activeNav: NavDestination;
  onNavigate: (destination: NavDestination) => void;
  statusNode?: React.ReactNode;
  showShowcaseTab?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'queue', label: 'Inspection Queue' },
  { id: 'meter', label: 'Meter Analysis' },
  { id: 'insights', label: 'Model Insights' },
  { id: 'system', label: 'System Status' },
];

export const AppHeader: React.FC<AppHeaderProps> = ({
  activeNav,
  onNavigate,
  statusNode,
  showShowcaseTab = true,
}) => {
  const allNavItems: NavItem[] = showShowcaseTab
    ? [...NAV_ITEMS, { id: 'showcase', label: 'Component Showcase', badge: 'PHASE 2' }]
    : NAV_ITEMS;

  return (
    <header className="gg-app-header" role="banner">
      <div className="gg-app-header__container">
        {/* Brand */}
        <div className="gg-app-header__brand" onClick={() => onNavigate('overview')} role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === 'Enter') onNavigate('overview'); }}>
          <span className="gg-app-header__logo" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path
                d="M13 2L3 14H12L11 22L21 10H12L13 2Z"
                fill="var(--gg-signal)"
                stroke="var(--gg-ink)"
                strokeWidth="1.75"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <div className="gg-app-header__wordmark">
            <span className="gg-app-header__title">GRID-GUARD</span>
            <span className="gg-app-header__subtitle">NTL Detection Platform</span>
          </div>
        </div>

        {/* Quiet Horizontal Navigation */}
        <nav className="gg-app-header__nav" aria-label="Main Navigation">
          {allNavItems.map((item) => {
            const isActive = activeNav === item.id;
            return (
              <button
                key={item.id}
                type="button"
                className={`gg-app-header__nav-btn ${isActive ? 'gg-app-header__nav-btn--active' : ''}`}
                onClick={() => onNavigate(item.id)}
                aria-current={isActive ? 'page' : undefined}
                disabled={item.disabled}
              >
                <span>{item.label}</span>
                {item.badge && (
                  <span className="gg-app-header__nav-badge">{item.badge}</span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Compact Right-Side Status */}
        <div className="gg-app-header__status">
          {statusNode}
        </div>
      </div>
    </header>
  );
};
