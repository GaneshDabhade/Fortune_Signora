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
  /**
   * 🔴 **Mirrors [`Input`](./input.tsx)'s prop of the same name, exactly** —
   * same name, same placement, same `aria-describedby` wiring.
   *
   * ⛔ **Its absence was a foundation inconsistency, not a missing feature for
   * one caller.** ⚡ 📁 **Every one of `User Profile` §02's six `localeFields`
   * carries a `help` string** and the product rendered **none of them**,
   * because the primitive the panel uses had nowhere to put one while its
   * sibling did.
   *
   * ✅ **Added under the UI Migration Program** — 📁 [§20c](../../../CLAUDE.md):
   * *"the direction of the change: toward the finalized design is the
   * migration."* ⛔ **Not a fork and not a variant**: `Input`'s contract is
   * reused rather than a second one invented beside it.
   */
  hint?: string;
}

/**
 * A native `<select>`.
 *
 * Not a custom listbox: the native control gets keyboard interaction,
 * mobile pickers, and form integration for free, and nothing in this
 * milestone needs styling the native control cannot provide.
 */
export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { className, label, labelHidden = false, options, hint, id, ...props },
  ref,
) {
  const generatedId = useId();
  const selectId = id ?? generatedId;
  const messageId = `${selectId}-message`;

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
        aria-describedby={hint === undefined ? undefined : messageId}
        className={cn(
          'h-control-md rounded border border-border-strong bg-surface px-3 text-sm text-content',
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
      {/* ⚡ **Beneath the control, in `Input`'s own words and classes** — 📁
          `input.tsx` renders its hint as `text-sm text-content-muted` below
          the field, and two sibling primitives placing help text differently
          is the inconsistency this prop exists to end. */}
      {hint === undefined ? null : (
        <p id={messageId} className="text-sm text-content-muted">
          {hint}
        </p>
      )}
    </div>
  );
});
