import React from 'react';
import './Button.css';

export type ButtonVariant = 'primary' | 'secondary' | 'text' | 'destructive';
export type ButtonSize = 'normal' | 'compact';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'secondary',
  size = 'normal',
  loading = false,
  icon,
  iconPosition = 'left',
  children,
  className = '',
  disabled,
  type = 'button',
  ...props
}) => {
  const isDisabled = disabled || loading;

  const classNames = [
    'gg-btn',
    `gg-btn--${variant}`,
    `gg-btn--${size}`,
    loading ? 'gg-btn--loading' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      type={type}
      className={classNames}
      disabled={isDisabled}
      aria-busy={loading ? 'true' : undefined}
      {...props}
    >
      {loading ? (
        <span className="gg-btn__spinner" aria-hidden="true" />
      ) : (
        icon && iconPosition === 'left' && <span className="gg-btn__icon">{icon}</span>
      )}
      <span className="gg-btn__label">{children}</span>
      {!loading && icon && iconPosition === 'right' && (
        <span className="gg-btn__icon">{icon}</span>
      )}
    </button>
  );
};
