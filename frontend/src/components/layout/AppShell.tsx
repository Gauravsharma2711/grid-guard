import React from 'react';
import { AppHeader, NavDestination } from './AppHeader';
import './AppShell.css';

export interface AppShellProps {
  activeNav: NavDestination;
  onNavigate: (destination: NavDestination) => void;
  statusNode?: React.ReactNode;
  children: React.ReactNode;
  footerNode?: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  activeNav,
  onNavigate,
  statusNode,
  children,
  footerNode,
}) => {
  return (
    <div className="gg-app-shell">
      <AppHeader
        activeNav={activeNav}
        onNavigate={onNavigate}
        statusNode={statusNode}
      />
      <main className="gg-app-shell__main" role="main">
        {children}
      </main>
      {footerNode && (
        <footer className="gg-app-shell__footer" role="contentinfo">
          {footerNode}
        </footer>
      )}
    </div>
  );
};
