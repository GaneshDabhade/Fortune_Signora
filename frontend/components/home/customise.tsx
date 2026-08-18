'use client';

import { SlidersHorizontal } from 'lucide-react';
import { useCallback, useEffect, useRef, useState, type RefObject } from 'react';

/**
 * 📁 **Home's *Customise* control** — `Fortune Signora Home.dc.html` §10's
 * keyboard table:
 *
 * > *"**Customise** — opens the card-order panel as a drawer. **Escape closes and
 * > returns focus to the trigger.**"* `⌘⇧H`
 *
 * ## 🔴 The trigger exists because the shortcut needs one
 *
 * ⚡ **The design names the shortcut and the drawer and not a button.** ⛔ **A
 * shortcut with no visible control is a capability only its author knows about**
 * — 📁 the same reasoning `P-11` gives for forbidden cards: *"hidden capability
 * is the most common cause of 'the product does not do X' when it does."*
 *
 * ⚠️ **And *"returns focus to the trigger"* requires a trigger to return it to.**
 * The design's own sentence settles this rather than a preference.
 *
 * ## ⛔ The state lives where the drawer is PLACED, not in the button
 *
 * 📁 `Drawer` *"renders in the flow its parent gives it"* and deliberately does
 * not push content itself — ⚡ **so a button that owned the panel would put a
 * 420px drawer inside the header row it sits in.** ✅ **Home holds the state and
 * places both**, which is exactly how `Copilot` mounts the same primitive at the
 * shell level.
 */
export interface CustomiseControls {
  readonly open: boolean;
  readonly openPanel: () => void;
  /** 📁 *"Escape closes and **returns focus to the trigger**."* */
  readonly close: () => void;
  readonly triggerRef: RefObject<HTMLButtonElement | null>;
}

export function useCustomise(enabled: boolean): CustomiseControls {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);

  /**
   * ⛔ **Focus lost to `<body>` drops a keyboard user at the top of the page** —
   * 📁 the same defect `R10-01` records for the brief. ⚡ `Drawer` owns Escape;
   * what it cannot own is where focus goes afterwards, because it does not know
   * what opened it.
   */
  const close = useCallback(() => {
    setOpen(false);
    triggerRef.current?.focus();
  }, []);

  /**
   * 📁 **`⌘⇧H`** — §10's keyboard table.
   *
   * ⛔ **Never while somebody is typing**, the same guard the `V` composition
   * shortcut carries: a shortcut that fires inside a field is what makes people
   * distrust every shortcut.
   *
   * ⚡ **`⌘⇧H` and `Ctrl⇧H`.** The design writes the Mac glyph; the gesture is the
   * same on every platform, and a Mac-only binding would be a capability half the
   * customers do not have.
   */
  useEffect(() => {
    if (!enabled) return;
    const onKey = (event: KeyboardEvent) => {
      if (!event.shiftKey || !(event.metaKey || event.ctrlKey)) return;
      if (event.key.toLowerCase() !== 'h') return;
      const target = event.target as HTMLElement | null;
      if (
        target !== null &&
        (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))
      ) {
        return;
      }
      event.preventDefault();
      setOpen((current) => !current);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [enabled]);

  return { open, openPanel: () => setOpen(true), close, triggerRef };
}

export interface CustomiseButtonProps {
  readonly controls: CustomiseControls;
  readonly className?: string;
}

export function CustomiseButton({ controls, className }: CustomiseButtonProps) {
  return (
    <button
      ref={controls.triggerRef}
      type="button"
      onClick={controls.openPanel}
      /* ⛔ **No `aria-haspopup="dialog"`.** 📁 `Drawer` is `complementary` on
         purpose — *"the ARIA dialog role carries an expectation of modality this
         panel deliberately does not meet, and announcing one the component does
         not honour is worse than announcing none."* ⚡ **Promising a dialog from
         the trigger would restore exactly that lie.** */
      aria-expanded={controls.open}
      className={className}
      title="Customise your home (⌘⇧H)"
    >
      <SlidersHorizontal className="h-3.5 w-3.5" aria-hidden />
      Customise
    </button>
  );
}
