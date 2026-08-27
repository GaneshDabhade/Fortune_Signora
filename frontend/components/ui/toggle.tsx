'use client';

import { useId } from 'react';

import { cn } from '@/lib/design/cn';

/**
 * **A labelled switch, as a real `<input type="checkbox">`.**
 *
 * ## ⛔ A checkbox rather than a styled `div`, and the reason is not purity
 *
 * ⚡ **The role, the state, the keyboard and the announcement all arrive with
 * the native control**, and none of them has to be remembered by whoever writes
 * the next panel. 📁 This is the choice both callers had already made
 * independently — **the same reason the choice grids are radios.**
 *
 * ## 🔴 Lifted from two page-local copies, which had drifted before anyone read them
 *
 * ⛔ **`profile/accessibility-panel.tsx` and `profile/ai-panel.tsx` each carried
 * a private `Toggle`**, and 📁 [§20c](../../CLAUDE.md) names that exactly:
 * *"add to the library rather than around it — a page-local variant of an
 * existing one does not"* belong in a page.
 *
 * ⚠️ **They had already diverged**, and one of the differences was inert:
 * the accessibility copy styled the box with `text-accent`, which does nothing
 * to a native checkbox without `@tailwindcss/forms` — **and that plugin is not
 * installed.** ✅ **`accent-accent` sets the `accent-color` property, which is
 * what actually tints the control**, and is what the AI copy used.
 *
 * ## ♿ The help text is a DESCRIPTION, never part of the name
 *
 * 🔴 **Both copies wrapped the label *and* the description in one `<label>`**,
 * which makes the whole paragraph the control's **accessible name** —
 * 📁 `User Profile` `1.3.1`: *"every control has a programmatic label **and its
 * help text via `aria-describedby`**."*
 *
 * ⛔ **A screen reader announced the entire explanation as the control's
 * name.** ⚡ **Everything was said and nothing was distinguishable** — a name
 * is what a form is scanned by, and a paragraph cannot be scanned.
 *
 * ⚠️ **The click target narrows from the whole block to the box and its label,
 * and that is the right way round**: a paragraph of explanation that silently
 * changes a setting when read with a pointer is a surprise, not an affordance.
 */
export interface ToggleProps {
  readonly label: string;
  /** ♿ Announced through `aria-describedby`. ⛔ Never part of the name. */
  readonly description: string;
  readonly checked: boolean;
  /**
   * ⚡ **A stated wait, never a dead control** — 📁
   * [B-255](../../../docs/BUGS.md): *a control that silently does nothing is
   * worse than one that is absent.* **A caller that disables this says why
   * beside it.**
   */
  readonly disabled?: boolean;
  /**
   * ⚡ **A further fact, announced with the description.** ⛔ **Not a second
   * description** — it exists for something true right now that the static help
   * text cannot know, such as what the reader's own device is doing.
   */
  readonly note?: string;
  readonly onChange: (value: boolean) => void;
  readonly className?: string;
}

export function Toggle({
  label,
  description,
  checked,
  disabled = false,
  note,
  onChange,
  className,
}: ToggleProps) {
  const id = useId();
  // ⛔ **The note joins the description rather than replacing it**, and the
  // order is the order it is read in.
  const describedBy = note === undefined ? `${id}-help` : `${id}-help ${id}-note`;

  return (
    <div className={cn('flex items-start gap-3', className)}>
      <input
        id={id}
        type="checkbox"
        checked={checked}
        disabled={disabled}
        aria-describedby={describedBy}
        onChange={(event) => onChange(event.target.checked)}
        className="mt-0.5 h-4 w-4 shrink-0 accent-accent disabled:cursor-not-allowed disabled:opacity-60"
      />
      <span className="flex flex-col gap-0.5">
        <label htmlFor={id} className="text-sm font-medium text-content">
          {label}
        </label>
        <span id={`${id}-help`} className="text-xs leading-5 text-content-muted">
          {description}
        </span>
        {note === undefined ? null : (
          <span id={`${id}-note`} className="text-xs leading-5 text-content">
            {note}
          </span>
        )}
      </span>
    </div>
  );
}
