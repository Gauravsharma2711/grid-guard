import React, { useId } from 'react';
import './Input.css';

export interface FormFieldProps {
  label: string;
  htmlFor?: string;
  error?: string;
  helperText?: string;
  required?: boolean;
  children: React.ReactNode;
  className?: string;
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  htmlFor,
  error,
  helperText,
  required,
  children,
  className = '',
}) => {
  const generatedId = useId();
  const inputId = htmlFor || generatedId;
  const errorId = `${inputId}-error`;
  const helperId = `${inputId}-helper`;

  return (
    <div className={`gg-form-field ${error ? 'gg-form-field--error' : ''} ${className}`}>
      <label htmlFor={inputId} className="gg-form-label">
        {label}
        {required && <span className="gg-form-required" aria-hidden="true">*</span>}
      </label>
      <div className="gg-form-control-wrapper">
        {React.isValidElement(children)
          ? React.cloneElement(children as React.ReactElement<React.HTMLAttributes<HTMLElement>>, {
              id: inputId,
              'aria-invalid': error ? 'true' : undefined,
              'aria-describedby': [
                error ? errorId : undefined,
                helperText ? helperId : undefined,
              ]
                .filter(Boolean)
                .join(' ') || undefined,
            })
          : children}
      </div>
      {error && (
        <p id={errorId} className="gg-form-error" role="alert">
          {error}
        </p>
      )}
      {!error && helperText && (
        <p id={helperId} className="gg-form-helper">
          {helperText}
        </p>
      )}
    </div>
  );
};

export interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  mono?: boolean;
}

export const TextInput: React.FC<TextInputProps> = ({
  mono = false,
  className = '',
  ...props
}) => {
  return (
    <input
      type="text"
      className={`gg-input ${mono ? 'gg-input--mono' : ''} ${className}`}
      {...props}
    />
  );
};

export interface NumberInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  suffix?: string;
}

export const NumberInput: React.FC<NumberInputProps> = ({
  suffix,
  className = '',
  ...props
}) => {
  if (suffix) {
    return (
      <div className="gg-input-with-suffix">
        <input
          type="number"
          className={`gg-input ${className}`}
          {...props}
        />
        <span className="gg-input-suffix" aria-hidden="true">{suffix}</span>
      </div>
    );
  }

  return (
    <input
      type="number"
      className={`gg-input ${className}`}
      {...props}
    />
  );
};

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  options: SelectOption[];
}

export const Select: React.FC<SelectProps> = ({
  options,
  className = '',
  ...props
}) => {
  return (
    <div className="gg-select-wrapper">
      <select className={`gg-select ${className}`} {...props}>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <span className="gg-select-arrow" aria-hidden="true">▾</span>
    </div>
  );
};
