import React from 'react';
import './Surface.css';

export interface SurfaceProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  elevation?: 'flat' | 'subtle';
  padded?: boolean;
}

export const Surface: React.FC<SurfaceProps> = ({
  children,
  elevation = 'flat',
  padded = true,
  className = '',
  ...props
}) => {
  return (
    <div
      className={`gg-surface-container gg-surface--${elevation} ${padded ? 'gg-surface--padded' : ''} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export interface DividerProps {
  spacing?: 'none' | 'sm' | 'md' | 'lg';
  className?: string;
}

export const Divider: React.FC<DividerProps> = ({
  spacing = 'md',
  className = '',
}) => {
  return <hr className={`gg-divider gg-divider--${spacing} ${className}`} />;
};

export interface CodeSurfaceProps extends React.HTMLAttributes<HTMLPreElement> {
  children: React.ReactNode;
  caption?: string;
}

export const CodeSurface: React.FC<CodeSurfaceProps> = ({
  children,
  caption,
  className = '',
  ...props
}) => {
  return (
    <div className="gg-code-surface-wrapper">
      {caption && <div className="gg-code-caption">{caption}</div>}
      <pre className={`gg-code-surface ${className}`} {...props}>
        <code>{children}</code>
      </pre>
    </div>
  );
};
