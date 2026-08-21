import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';

import { cn } from '@/lib/design/cn';

/**
 * **The icon control** — the square target an icon sits in, extracted against
 * 📁 the [App Shell](../../../docs/design-snapshot/screens/) §04 `topBarSlots`
 * and §21 `a11yRules` ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Notifications — 32 × 32."*** · ***"Help & account — 32 + 32."***
 * > 📁 ***`2.5.8` — "Every top-bar control is a 32px target with 8px
 * > separation; 44px on touch."***
 *
 * ## 🔴 The frame had four of these and two of them were not 32px
 *
 * ⚠️ **Measured in the browser at 1440 × 900 and 390 × 844, not read off the
 * source:**
 *
 * | Control | Was | 📁 |
 * |---|---|---|
 * | Top-bar sheet trigger | `32 × 32` | ✅ |
 * | Top-bar help | `32 × 32` | ✅ |
 * | **Rail collapse toggle** | 🔴 **`18 × 32`** | ⛔ **26px under**, and under `2.5.8`'s 24px floor |
 * | **Sheet close** | 🔴 **`21 × 32`** | ⛔ **11px under**, on the one band where it is the only way out |
 *
 * ⛔ **Both used `rounded p-1` — padding around a glyph rather than a target
 * of a stated size** — so the control was as wide as whatever character was
 * inside it, and `«` and `✕` are narrow characters. ⚡ **That is the same
 * defect class the collapsed rail row had**, where a tooltip wrapper let the
 * row shrink to its icon: **a target must own its geometry, never inherit it
 * from its content.**
 *
 * ## ⚡ Why a component rather than a shared class string
 *
 * ⛔ **A string is copied and then edited.** The four call sites already
 * disagreed about radius (`rounded` against `rounded-md`), about hover, and
 * about which focus treatment they used — **and each of those disagreements
 * was invisible in review because no two of them are on one screen.**
 */
export type IconButtonSize = 'sm' | 'md';

/**
 * 📁 **`md` is the shell's own 32px furniture.** ⚡ **`sm` is 24px — `2.5.8`'s
 * floor** — ⛔ **and it is not a smaller default**: it exists for a control that
 * sits inside a dense row of content, and it still clears the minimum.
 */
const SIZES: Record<IconButtonSize, string> = {
  sm: 'h-6 w-6',
  md: 'h-8 w-8',
};

export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * ♿ **Required, and it names the OUTCOME rather than the glyph.** ⛔ A
   * screen-reader user cannot see which way a chevron points, so *"Collapse
   * navigation"* is the label and *"chevron"* is not.
   */
  label: string;
  /** ⚡ The glyph. ⛔ Rendered `aria-hidden` by this component — the label above
   * is the accessible name, and announcing both reads the control twice. */
  children: ReactNode;
  size?: IconButtonSize;
  /** ⚡ `true` when the control opens a surface that is currently open. */
  expanded?: boolean;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  function IconButton(
    { label, children, size = 'md', expanded, className, type, ...props },
    ref,
  ) {
    return (
      <button
        ref={ref}
        // ⛔ **`button` by default and never inferred.** A control inside a form
        // that omits this submits it, which is the quietest possible defect.
        type={type ?? 'button'}
        aria-label={label}
        aria-expanded={expanded}
        className={cn(
          // ⚡ **The geometry is the component's, not the glyph's.** `shrink-0` is
          // what stops a flex row shaving pixels off a target when space runs out.
          'inline-flex shrink-0 items-center justify-center rounded-md',
          SIZES[size],
          // ♿ 📁 `2.5.8` — *"44px on touch."* ⛔ A `min-*` pair rather than a size
          // step, so the design's 32px survives everywhere a mouse is pointing.
          'coarse:min-h-11 coarse:min-w-11',
          'text-content-subtle transition-colors',
          'hover:bg-surface-sunken hover:text-content',
          'disabled:pointer-events-none disabled:opacity-50',
          className,
        )}
        {...props}
      >
        <span aria-hidden className="grid place-items-center">
          {children}
        </span>
      </button>
    );
  },
);
