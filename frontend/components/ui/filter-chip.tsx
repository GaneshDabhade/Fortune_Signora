import type { ReactNode } from 'react';

import { cn } from '@/lib/design/cn';

/**
 * **The filter chip** — the shared control the design's filter strip is made
 * of, against 📁 the [App Shell](../../../docs/design-snapshot/screens/) §06
 * *"Global filters"* ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Visual grammar — Tinted chip = global and persistent. Outlined chip
 * > = local and transient. Dashed = add."***
 *
 * ## 🔴 The chip existed four times and its target was 16px tall
 *
 * ⚠️ **Measured in the browser on `/accounts`, at every width from 320 to 1920:**
 * the `Group` chip's control is **`137 × 16`** and `Sort by` is **`120 × 16`**.
 * ⛔ **Sixteen pixels, against `2.5.8`'s 24px floor and the design's own 28–32px
 * chip** — and the chip *around* them was the right height the whole time, which
 * is why it looked correct and was not.
 *
 * ⚡ **The cause is one line**: the `<select>` carried `border-0 bg-transparent
 * p-0`, so it collapsed to its own text box and **the clickable region was a
 * strip through the middle of a control that looked 32px tall.** ⛔ **Growing
 * the select's font would not fix it** — the target has to be the chip.
 *
 * ## ⚡ How the whole chip becomes the target, without giving up the native menu
 *
 * 📁 The toolbar's own note is right and is kept: *"the native control carries
 * its own keyboard, focus and announcement, and this is not the place to
 * reimplement any of it."* ✅ **So the `<select>` stays and is stretched over
 * the chip** — `absolute inset-0`, transparent — **with the field, the value and
 * the chevron drawn underneath it.**
 *
 * ⛔ **Not `appearance-none` on an inline select**, which is the tempting
 * version: it leaves the control sized by its text and reintroduces exactly the
 * strip this replaces. ⚡ **A stretched overlay makes the geometry the chip's and
 * the behaviour the browser's**, which is the only split where neither half is
 * reimplemented.
 */
export type FilterChipTone =
  /** 📁 *"Tinted chip = global and persistent."* Also the design's applied
   * arrangement — *"`--sunken`, no border, 600 weight"* — because an APPLIED
   * control and an AVAILABLE one must not look the same. */
  | 'applied'
  /** 📁 *"Outlined chip = local and transient."* */
  | 'available';

const TONES: Record<FilterChipTone, string> = {
  applied: 'bg-surface-sunken text-content',
  available: 'border border-border text-content-muted',
};

export interface FilterChipProps {
  /** 📁 The design's quiet field name — *"Period"*, *"Group"*, *"Stage"*. */
  field: string;
  /**
   * ♿ **The accessible name of the control**, defaulting to `field`. ⛔ Three
   * unlabelled selects on one row are three identical controls to a screen
   * reader, and *"Sort by"* / *"Then sort by"* are two different questions.
   */
  label?: string;
  value: string;
  options: readonly { value: string; label: string }[];
  onChange: (value: string | null) => void;
  /** 📁 The design's placeholder option — *"None"*, *"then…"*. */
  placeholder?: string;
  tone?: FilterChipTone;
  /**
   * ⚡ **Rendered after the value, inside the chip and ABOVE the overlay** —
   * the sort direction's arrow and the remove `×`. ⛔ They must stay clickable,
   * so they sit in their own stacking context rather than under the select.
   */
  children?: ReactNode;
  className?: string;
}

export function FilterChip({
  field,
  label,
  value,
  options,
  onChange,
  placeholder = 'None',
  tone,
  children,
  className,
}: FilterChipProps) {
  const applied = value !== '';
  const resolved = tone ?? (applied ? 'applied' : 'available');

  return (
    <span
      className={cn(
        // ⚡ **`relative` is what the overlay is positioned against**, and
        // `h-control-sm` is the shell's own 32px target rather than a literal.
        'relative inline-flex h-control-sm items-center gap-1 rounded-md px-2.5',
        'text-xs font-semibold',
        // ⛔ **A chip never wraps mid-condition.** Its ROW scrolls or wraps —
        // which is §06's own responsive rule — and the chip stays one object.
        'whitespace-nowrap',
        // ♿ 📁 `2.5.8` — *"44px on touch."*
        'coarse:min-h-11',
        // ⚡ **Focus is drawn on the CHIP**, because the thing a keyboard user
        // is focusing is a 32px control, not the transparent overlay on it.
        // ♿ **`focus-proxy` is that move, and only that move** — 📁
        // [B-1058](../../../docs/BUGS.md): the same declaration, on the element
        // a person can actually see.
        'focus-proxy',
        TONES[resolved],
        className,
      )}
    >
      <span className={applied ? 'text-content-subtle' : undefined}>{field}</span>
      <span>
        {applied ? (options.find((o) => o.value === value)?.label ?? value) : placeholder}
      </span>
      {/* 📁 The design's chevron, on every chip in §06's strip. */}
      <svg
        aria-hidden
        viewBox="0 0 16 16"
        className="h-2.5 w-2.5 shrink-0"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.8}
      >
        <path d="M5 6.5 8 9.5l3-3" />
      </svg>

      {/* 🔴 **The control, stretched over the chip.** ⛔ `opacity-0` rather than
          `sr-only`: a screen-reader-only select would be removed from the
          pointer surface, which is the half of this that was broken. ⚡ It is
          still a real `<select>` — same keyboard, same menu, same announcement. */}
      <select
        aria-label={label ?? field}
        value={value}
        onChange={(event) =>
          onChange(event.target.value === '' ? null : event.target.value)
        }
        className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      {/* ⚡ **Above the overlay**, so the arrow and the remove stay clickable. */}
      {children === undefined ? null : (
        <span className="relative z-10 inline-flex items-center gap-1">{children}</span>
      )}
    </span>
  );
}
