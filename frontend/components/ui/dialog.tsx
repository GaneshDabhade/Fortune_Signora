'use client';

import { useEffect, useRef, type ReactNode } from 'react';

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
      aria-labelledby="dialog-title"
      className={cn(
        'w-full max-w-md rounded-lg border border-border bg-surface p-0 text-content shadow-lg',
        'backdrop:bg-backdrop/40',
      )}
      // Clicking the backdrop closes; clicking the panel must not. The
      // check compares the target to the dialog itself, which is the
      // backdrop area — children are separate targets.
      onClick={(event) => {
        if (event.target === ref.current) onClose();
      }}
    >
      <div className="flex flex-col gap-1 border-b border-border px-5 py-4">
        <h2 id="dialog-title" className="text-base font-semibold">
          {title}
        </h2>
        {description ? <p className="text-sm text-content-muted">{description}</p> : null}
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
