'use client';

import { useEffect, useId, useRef, type ReactNode } from 'react';

import { cn } from '@/lib/design/cn';

export interface DrawerProps {
  open: boolean;
  onClose: () => void;
  title: string;
  /** The scope the drawer is answering within — §14's *"Scoped to EMEA
   * enterprise · Q3 · 2 filters"*. Rendered beneath the title because a
   * panel that answers questions must say what it was asked about. */
  scope?: string;
  children?: ReactNode;
  footer?: ReactNode;
  /**
   * 📁 **§12 — *"a non-modal **420px** drawer that pushes content"*.**
   *
   * ⛔ **Required-by-convention rather than optional-by-default is deliberate
   * the other way**: this stays optional because **a caller with no width is a
   * caller in a container that already has one**, and forcing a number would
   * make the panel fight its own layout.
   *
   * ⚠️ **But the absence was the defect.** 🔴 **`copilot.tsx` quoted §12's
   * 420px in prose and passed nothing**, so the assistant opened at whatever
   * width the shell gave it — ⚡ **which is why the number now travels as a
   * value from [`overlays.ts`](../../lib/shell/overlays.ts)** rather than
   * living in a sentence.
   */
  width?: number;
}

/**
 * A side panel for a task that has an end.
 *
 * **Design System v2 §12 names four overlays sharing one language** — dialog,
 * drawer, palette and toast — *"16px radius, hairline border, `--e4`"*. Two of
 * the four existed. This is one of the two that did not.
 *
 * ### Why this is not `Dialog` with different padding
 *
 * ⚡ **§14 states the mechanism, not just the look**: the assistant drawer is
 * *"Non-modal · pushes content"*. **A modal and a non-modal panel differ in
 * what the rest of the page may do**, which is a behavioural contract rather
 * than a width:
 *
 * - **`Dialog` uses `<dialog>.showModal()`** — the platform inerts the
 *   background, traps focus, and puts the element in the top layer. Correct
 *   for §12's *"dialogs are for decisions"*, where continuing to work behind
 *   the decision is precisely what must not happen.
 * - **A drawer must leave the page usable.** §12: *"drawers hold tasks with an
 *   end"* — the user reads the record while the panel discusses it. Trapping
 *   focus here would break the one interaction the panel exists to support.
 *
 * ⛔ **So there is no scrim.** §12 gives the four a *"24%-ink scrim"*, and a
 * scrim is the visual statement that the content behind is unavailable. **On a
 * panel that pushes content rather than covering it, a scrim would assert
 * something untrue** — the shared language is the plane, not the dimming.
 *
 * ### What it does not do, and why that is the caller's
 *
 * ⛔ **It does not push the content itself.** The drawer renders in the flow
 * its parent gives it; *pushing* is a layout decision belonging to whichever
 * shell places it, and a component that reached out to reflow the page would
 * be a design-system primitive taking a page-level decision. **Escape and the
 * close control are handled here, because both are the panel's own.**
 */
export function Drawer({ open, onClose, title, scope, children, footer, width }: DrawerProps) {
  const headingId = useId();
  const panel = useRef<HTMLDivElement>(null);

  // Escape closes. `<dialog>` gives this for free and this element cannot use
  // `<dialog>` without also becoming modal, so the one behaviour worth keeping
  // is reimplemented and the rest is deliberately not.
  useEffect(() => {
    if (!open) return;
    const handle = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handle);
    return () => document.removeEventListener('keydown', handle);
  }, [open, onClose]);

  // Focus moves into the panel when it opens, so a keyboard user reaches the
  // content without traversing the page behind it. **Focus is not trapped** —
  // leaving is the point of a non-modal surface.
  useEffect(() => {
    if (open) panel.current?.focus();
  }, [open]);

  if (!open) return null;

  return (
    <aside
      ref={panel}
      tabIndex={-1}
      // `complementary`, not `dialog`: the ARIA dialog role carries an
      // expectation of modality that this panel deliberately does not meet,
      // and announcing one the component does not honour is worse than
      // announcing none.
      aria-labelledby={headingId}
      className={cn(
        // §12's shared plane: 16px radius, hairline border, --e4.
        'flex h-full w-full flex-col rounded-xl border border-border-soft bg-surface',
        'text-content shadow-lg outline-none',
      )}
      // ⛔ **A style, not a Tailwind arbitrary value** — the number belongs to
      // the design's contract and a class would put it in a second place.
      style={width === undefined ? undefined : { maxWidth: width }}
    >
      <header className="flex items-start justify-between gap-3 border-b border-border-soft px-5 py-4">
        <div className="flex flex-col gap-1">
          <h2 id={headingId} className="text-base font-semibold">
            {title}
          </h2>
          {scope ? <p className="text-xs text-content-subtle">{scope}</p> : null}
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label={`Close ${title}`}
          className={cn(
            'rounded p-1 text-content-muted transition-colors',
            'hover:bg-surface-sunken hover:text-content',
          )}
        >
          <span aria-hidden>✕</span>
        </button>
      </header>

      {children ? <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div> : null}

      {footer ? (
        <footer className="border-t border-border-soft px-5 py-3">{footer}</footer>
      ) : null}
    </aside>
  );
}
