import { forwardRef, useId, type SelectHTMLAttributes } from 'react';

import { cn } from '@/lib/design/cn';

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends Omit<
  SelectHTMLAttributes<HTMLSelectElement>,
  'children'
> {
  label: string;
  options: readonly SelectOption[];
  /** Hides the label visually while keeping it for assistive technology —
   * for cases where surrounding context makes it redundant on screen. */
  labelHidden?: boolean;
}

/**
 * A native `<select>`.
 *
 * Not a custom listbox: the native control gets keyboard interaction,
 * mobile pickers, and form integration for free, and nothing in this
 * milestone needs styling the native control cannot provide.
 */
export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { className, label, labelHidden = false, options, id, ...props },
  ref,
) {
  const generatedId = useId();
  const selectId = id ?? generatedId;

  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={selectId}
        className={cn('text-sm font-medium text-content', labelHidden && 'sr-only')}
      >
        {label}
      </label>
      <select
        ref={ref}
        id={selectId}
        className={cn(
          'h-10 rounded border border-border-strong bg-surface px-3 text-sm text-content',
          'disabled:opacity-50',
          className,
        )}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
});
