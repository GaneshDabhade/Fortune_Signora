'use client';

import { useEffect, useId, useRef, type ReactNode } from 'react';

import { cn } from '@/lib/design/cn';

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children?: ReactNode;
  footer?: ReactNode;
}

/**
 * A modal built on the native `<dialog>` element.
 *
 * Chosen over a hand-rolled overlay because the platform already provides
 * focus trapping, top-layer stacking, and Escape handling. Reimplementing
 * those correctly is a surprising amount of code, and the usual result is a
 * modal that is nearly accessible.
 *
 * What still needs handling: `showModal()` throws if called on an already
 * open dialog, and the native Escape close fires `cancel` without telling
 * React — so both are bridged to `onClose`.
 *
 * ### The background is not as inert as this file used to claim
 *
 * This docstring said the platform provided *"inertness of the background"*.
 * **It does not provide all of it.** `showModal()` makes background content
 * inert to *pointer and keyboard interaction*, and leaves the root scroller
 * scrollable: a wheel gesture over an open modal scrolls the page underneath
 * it. A reader who scrolls while checking a citation returns to a page that
 * has moved, having lost their place in the argument they were reading.
 *
 * Found by driving it in a browser ([B-307](../../../docs/BUGS.md)) — and the
 * sentence above is the more useful half of the finding, because **a comment
 * asserting a property the code does not have is a false claim that survives
 * review** (`CLAUDE.md` §2).
 *
 * ### 🔴 Two accessibility defects, fixed here — [B-315](../../../docs/BUGS.md) · [B-312](../../../docs/BUGS.md)
 *
 * ⛔ **[§20c](../../../CLAUDE.md): an accessibility issue is a *defect class*,
 * not an enhancement, and never waits for a frozen foundation.**
 *
 * **[B-315] Every dialog claimed the same HTML id.** `aria-labelledby` pointed
 * at a literal `"dialog-title"`, so **two dialogs in one document meant the
 * screen reader could be told the wrong title** — invisible to a sighted user
 * and wrong for everybody else. ✅ **`useId()` now**, which is React's answer
 * to exactly this and is stable across server and client render.
 *
 * **[B-312] A dialog a keyboard could not reach anything inside.** ⚠️ **The
 * focus trap was never broken** — 📁 the probe showed `BODY · BODY · BODY …`
 * eight times, and the reason is sharper than a broken trap: **the evidence
 * drawer contained no focusable element at all**, so focus had nowhere to go.
 * 🔴 **A trap is normally tested by checking focus stays inside, and it did —
 * trivially.** 📁 *"The half nobody asserts is that a dialog contains
 * something."*
 *
 * ✅ **So the fix is structural: a close control in the header, so EVERY
 * dialog has something focusable** — ⛔ not only those whose footer happens to
 * carry a Cancel button. **The defect class is *a `Dialog` need not contain
 * anything focusable*, and this makes that unrepresentable** ([§2](../../../CLAUDE.md)).
 *
 * ⚠️ **Lane B wrote this fix and reverted it**, for a reason worth keeping:
 * it changes every dialog in the product, and **[§20c](../../../CLAUDE.md)
 * requires a human to look at a changed screen.** ⛔ **Five screens change at
 * once, and that review is the product owner's** — flagged on the row rather
 * than assumed granted.
 */
export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  footer,
}: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null);
  // 🔴 **[B-315]** — ⛔ **never a literal.** Two dialogs in one document sharing
  // an id is how a screen reader is told the wrong title.
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;

    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  // **Lock the page behind the modal.** The one part of background inertness
  // `showModal()` does not give us. Restored on close and on unmount, and the
  // previous value is kept rather than assumed: something else may legitimately
  // have set it, and clobbering it to `''` would be this component deciding a
  // page-level concern on the way out.
  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previous;
    };
  }, [open]);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;

    const handleCancel = (event: Event) => {
      // Prevent the default close so React remains the single source of
      // truth for `open`; otherwise the DOM closes and state says open.
      event.preventDefault();
      onClose();
    };
    dialog.addEventListener('cancel', handleCancel);
    return () => dialog.removeEventListener('cancel', handleCancel);
  }, [onClose]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      className={cn(
        'w-full max-w-md rounded-xl border border-border bg-surface p-0 text-content shadow-lg',
        'backdrop:bg-backdrop/40',
      )}
      // Clicking the backdrop closes; clicking the panel must not. The
      // check compares the target to the dialog itself, which is the
      // backdrop area — children are separate targets.
      onClick={(event) => {
        if (event.target === ref.current) onClose();
      }}
    >
      <div className="flex items-start gap-3 border-b border-border px-5 py-4">
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <h2 id={titleId} className="text-base font-semibold">
            {title}
          </h2>
          {description ? <p className="text-sm text-content-muted">{description}</p> : null}
        </div>
        {/* 🔴 **[B-312] — the reason this is in the HEADER and not left to the
            caller.** A dialog whose footer happens to carry a Cancel button was
            already reachable; one that carries only text was not, and **a
            component that is accessible depending on what it is passed is not
            accessible.** ⚡ This makes *contains something focusable* a property
            of `Dialog` rather than of its callers. */}
        <button
          type="button"
          onClick={onClose}
          // ♿ Names the outcome, not the glyph — and it is the first thing a
          // screen reader reaches after the title.
          aria-label="Close"
          className={cn(
            'shrink-0 rounded p-1 text-content-subtle transition-colors',
            'hover:text-content',
            'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
            'focus-visible:outline-accent',
          )}
        >
          <span aria-hidden>✕</span>
        </button>
      </div>
      {children ? <div className="px-5 py-4">{children}</div> : null}
      {footer ? (
        <div className="flex justify-end gap-2 border-t border-border px-5 py-3">
          {footer}
        </div>
      ) : null}
    </dialog>
  );
}
