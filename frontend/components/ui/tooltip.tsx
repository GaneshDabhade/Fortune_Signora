'use client';

import { useEffect, useId, useRef, useState, type ReactNode } from 'react';

import { cn } from '@/lib/design/cn';

/**
 * **Tooltip** — [TASK-1448](../../../docs/BACKLOG.md), against 📁 the App
 * Shell's rule for the collapsed rail
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Collapsed items expose their label as an accessible name and a
 * > 300ms tooltip."***
 *
 * ## 🔴 The 300ms is the whole specification, and `title` cannot honour it
 *
 * ⛔ **The collapsed rail uses the native `title` attribute today**, which is
 * the honest thing to have shipped without this component — but it is not what
 * the design asks for: **the browser's delay is its own, unconfigurable, and
 * varies between engines.** ⚡ **A rule that names a duration needs something
 * that can hold one.**
 *
 * ## ⚠️ It is a HINT, never the only source of a name
 *
 * 📁 The design's own wording puts the accessible name FIRST and the tooltip
 * second, and the order matters: ⛔ **a tooltip that is the only place a label
 * exists is unreachable by touch and by keyboard-with-no-hover.** ✅ **So this
 * component requires the trigger to carry its own accessible name** and adds
 * `aria-describedby` rather than `aria-labelledby` — **describing, not naming.**
 *
 * ⚡ **Escape dismisses it**, which the design does not state and every
 * transient surface in this product already does.
 */

/** 📁 *"a 300ms tooltip"* — the design's number, not a convention. */
export const TOOLTIP_DELAY_MS = 300;

export interface TooltipProps {
  /** What the tooltip says. ⛔ **A hint** — never the trigger's only name. */
  content: string;
  children: ReactNode;
  className?: string;
}

export function Tooltip({ content, children, className }: TooltipProps) {
  const [open, setOpen] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const id = useId();

  const cancel = () => {
    if (timer.current !== null) {
      clearTimeout(timer.current);
      timer.current = null;
    }
  };

  const schedule = () => {
    cancel();
    timer.current = setTimeout(() => setOpen(true), TOOLTIP_DELAY_MS);
  };

  const hide = () => {
    cancel();
    setOpen(false);
  };

  // ⛔ **Clear on unmount.** A pending timer that fires into an unmounted tree
  // is the leak every delayed surface introduces if nobody says otherwise.
  useEffect(() => cancel, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') hide();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open]);

  return (
    <span
      className={cn('relative inline-flex', className)}
      onMouseEnter={schedule}
      onMouseLeave={hide}
      // ⚡ **Focus shows it immediately, without the delay.** The delay exists
      // so a pointer crossing the control does not flash a tooltip; a keyboard
      // user who has deliberately focused it is not passing through.
      onFocus={() => setOpen(true)}
      onBlur={hide}
      // ⛔ **`aria-describedby`, not `aria-labelledby`** — see the note above.
      aria-describedby={open ? id : undefined}
    >
      {children}
      {open ? (
        <span
          id={id}
          role="tooltip"
          className={cn(
            'pointer-events-none absolute left-1/2 top-[calc(100%+6px)] z-40 -translate-x-1/2',
            'whitespace-nowrap rounded-md bg-content px-2 py-1 text-2xs text-surface shadow-lg',
          )}
        >
          {content}
        </span>
      ) : null}
    </span>
  );
}
