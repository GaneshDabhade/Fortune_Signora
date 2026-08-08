'use client';

import { forwardRef, useState, type ComponentPropsWithoutRef } from 'react';

import { Input } from './input';

/**
 * `Input` requires a label and this does not — **it already knows what it
 * labels.** Screen `09 · Set a new password` draws two of these in one card,
 * *New password* and *Confirm password*, so the prop stays overridable.
 */
export type PasswordFieldProps = Omit<ComponentPropsWithoutRef<typeof Input>, 'type' | 'label'> & {
  label?: string;
};

/**
 * A password input with the design's reveal control.
 *
 * **Extracted rather than written twice** ([§20c](../../../CLAUDE.md)). This
 * markup was local to `sign-in-form.tsx` and screen `06 · Create account`
 * needs the same control; screen `09 · Set a new password` draws it twice
 * more. **The second caller is what makes it a library component** — the rule
 * is *add to the library, never beside it*, and a copy in the sign-up form
 * would have been the copy that drifts.
 *
 * ⚡ **The toggle is a real `button`, not an icon with a click handler** — the
 * design's 2.1.1, *reachable and operable by keyboard*, and `aria-pressed`
 * carries the state so a screen reader hears it change rather than inferring
 * it from a swapped glyph.
 *
 * ⛔ **Nothing here blocks paste** (the design's 3.3.8). A field that fights a
 * password manager is a field people type weaker passwords into.
 */
export const PasswordField = forwardRef<HTMLInputElement, PasswordFieldProps>(
  function PasswordField({ label = 'Password', className, ...props }, ref) {
    const [reveal, setReveal] = useState(false);

    return (
      <div className="relative">
        <Input
          ref={ref}
          label={label}
          type={reveal ? 'text' : 'password'}
          className={['pr-16', className].filter(Boolean).join(' ')}
          {...props}
        />
        <button
          type="button"
          onClick={() => setReveal((shown) => !shown)}
          aria-pressed={reveal}
          className="absolute right-2 top-8 rounded px-2 py-1 text-xs font-medium text-content-muted transition-colors hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2"
        >
          {reveal ? 'Hide' : 'Show'}
        </button>
      </div>
    );
  },
);
