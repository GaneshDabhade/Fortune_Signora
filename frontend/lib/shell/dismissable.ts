'use client';

/**
 * **A panel anchored to a control, and the three things that close it** —
 * [TASK-495](../../../docs/BACKLOG.md) slice ⓑ.
 *
 * ## ⛔ Why a hook and not a `Popover` component
 *
 * 📁 [§6](../../../CLAUDE.md): *"do not add abstractions… for hypothetical
 * future needs."* ⚡ **The markup of the two panels that need this is genuinely
 * different** — an account `menu` of 280px with `menuitem`s, and a 400px
 * notification panel with tabs and a scrolling day-grouped list — **so a shared
 * component would have to be configured into both shapes and would be worse
 * than either.**
 *
 * ⚠️ **What IS the same is the behaviour**, and it existed twice before this:
 * Escape, an outside click, and returning focus to the trigger. 📁 §2 —
 * *"behaviour exists exactly once"*.
 *
 * ## 🔴 Returning focus is the half that gets dropped
 *
 * ⛔ **Without it a keyboard user who presses Escape is returned to the top of
 * the document**, which is worse than not being able to close the panel at all:
 * they have lost their place as the price of dismissing something.
 */

import { useEffect, type RefObject } from 'react';

export interface Dismissable {
  readonly open: boolean;
  /** The element containing BOTH the trigger and the panel. */
  readonly container: RefObject<HTMLElement | null>;
  /** ♿ Focus returns here. */
  readonly trigger: RefObject<HTMLElement | null>;
  readonly onDismiss: () => void;
}

export function useDismissable({ open, container, trigger, onDismiss }: Dismissable): void {
  useEffect(() => {
    if (!open) return;

    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      onDismiss();
      // ♿ 📁 *"Esc closes and returns focus to the trigger."*
      trigger.current?.focus();
    };
    // ⚡ **`mousedown`, not `click`** — ⛔ a `click` listener fires after the
    // element under the pointer has already acted, so dismissing on click can
    // race with whatever was clicked outside.
    const onPointer = (event: MouseEvent) => {
      if (!container.current?.contains(event.target as Node)) onDismiss();
    };

    document.addEventListener('keydown', onKey);
    document.addEventListener('mousedown', onPointer);
    return () => {
      document.removeEventListener('keydown', onKey);
      document.removeEventListener('mousedown', onPointer);
    };
  }, [open, container, trigger, onDismiss]);
}
