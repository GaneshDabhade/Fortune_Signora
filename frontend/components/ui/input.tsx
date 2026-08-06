import { forwardRef, useId, type InputHTMLAttributes } from 'react';

import { cn } from '@/lib/design/cn';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  /** Renders the field in its error state and announces the message. */
  error?: string;
  hint?: string;
}

/**
 * The label is a required prop, not an optional one.
 *
 * An unlabelled input is unusable with a screen reader and the omission is
 * invisible in review. Making it required means the accessible version is
 * the only version available.
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, label, error, hint, id, ...props },
  ref,
) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const messageId = `${inputId}-message`;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-sm font-medium text-content">
        {label}
      </label>
      <input
        ref={ref}
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error || hint ? messageId : undefined}
        className={cn(
          'h-control-md rounded border bg-surface px-3 text-sm text-content',
          'placeholder:text-content-subtle disabled:opacity-50',
          error ? 'border-danger' : 'border-border-strong',
          className,
        )}
        {...props}
      />
      {error ? (
        // role="alert" so the message is announced when it appears, not
        // only when focus happens to land on the field.
        <p id={messageId} role="alert" className="text-sm text-danger">
          {error}
        </p>
      ) : hint ? (
        <p id={messageId} className="text-sm text-content-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
});
