'use client';

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { ShortcutList } from '@/components/shell/shortcut-list';
import { Dialog } from '@/components/ui/dialog';
import { coverage } from '@/lib/shell/shortcuts';

/**
 * **The shortcut reference `?` opens from anywhere** —
 * [TASK-1445](../../../docs/BACKLOG.md), against 📁 `Fortune Signora App
 * Shell.dc.html` §15.
 *
 * ## ⛔ Why the reference states what does NOT work
 *
 * 📁 **The design's own sentence is the hazard**: *"a cheat sheet nobody opens
 * is not a feature."* ⚠️ **The failure one step past that is a cheat sheet
 * everybody opens and half of it is false** — 🔴 **and a person who presses a
 * published shortcut and gets silence concludes the PRODUCT is broken, not
 * that the shortcut is unbuilt.** ⛔ **Silence is the worst possible failure
 * mode for a key**: there is nothing to read, nothing to retry and nothing to
 * report.
 *
 * ✅ **So thirteen unbound shortcuts are listed and marked**, and
 * [`shortcuts.ts`](../../lib/shell/shortcuts.ts) counts them rather than
 * anybody writing the number down.
 */
/**
 * ⚡ **The overlay's open state, lifted so it has TWO doors and ONE surface.**
 *
 * 📁 **The design gives the rail entry `meta: '?'`** — ⛔ **which literally says
 * *this is the thing `?` opens*.** ⚠️ **So the rail must drive the same dialog
 * the key does**, and the alternative — a `/shortcuts` route beside the overlay
 * — would be **two representations of one truth** ([§2](../../../CLAUDE.md)),
 * diverging the first time somebody edited one.
 *
 * ⛔ **Lifted to a context rather than held in the rail**, because the rail is
 * one of the doors and not the owner. 📁 The same split
 * [`utility-panel.tsx`](utility-panel.tsx) already draws after
 * [B-234](../../../docs/BUGS.md): **state is the provider's, placement is the
 * shell's.**
 */
const ShortcutsContext = createContext<{ open: () => void } | null>(null);

/**
 * ⚡ **What a rail entry, a menu item or any other door calls.**
 *
 * ⛔ **Returns `null` outside the provider rather than throwing** — 📁 the rail
 * renders in tests and stories that mount no shell, and **a navigation that
 * crashes because an overlay is absent is a worse failure than a button that
 * does nothing.** ✅ **The caller decides**, and `navigation.tsx` omits the
 * entry entirely rather than rendering a dead one.
 */
export function useShortcutsReference(): { open: () => void } | null {
  return useContext(ShortcutsContext);
}

export function ShortcutsReference({ children }: { children?: ReactNode }) {
  const [open, setOpen] = useState(false);

  /**
   * 📁 *"`?` opens the reference from anywhere."*
   *
   * ⛔ **Ignored while a field has focus**, on the same rule `[` and `⌘.`
   * already carry: **`?` is a character somebody types**, and a reference that
   * opens mid-sentence is a reference people learn to fear.
   *
   * ⚡ **`?` and `/` are one physical key.** 📁 The design binds `/` to *Search
   * in view* and [`shortcuts.ts`](../../lib/shell/shortcuts.ts) records it
   * `unbound` — ⚠️ **so this handler must test `event.key`, which is already
   * the shifted character, rather than `code` plus a shift flag.** Otherwise
   * building `/` later would silently take `?` with it.
   */
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== '?' || event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || target?.isContentEditable === true) return;
      event.preventDefault();
      setOpen((was) => !was);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const controls = useMemo(() => ({ open: () => setOpen(true) }), []);

  return (
    <ShortcutsContext.Provider value={controls}>
      {children}
      <Dialog
      open={open}
      onClose={() => setOpen(false)}
      title="Keyboard shortcuts"
      // 🔴 **Counted, not written.** 📁 [§2](../../../CLAUDE.md) — a document
      // asserting something untrue of the thing it documents is the defect,
      // and a hand-typed tally goes stale on the next binding.
      description={coverage()}
    >
      {/**
       * ⚠️ **The design's §15 card is THREE COLUMNS and this is one, and the
       * divergence is recorded rather than absorbed.**
       *
       * 📁 **[`Dialog`](../ui/dialog.tsx) is `max-w-md` — 448px** — and 🔴
       * **`components/ui` is the frontend foundation in the Change Budget**, so
       * widening it for one caller is precisely what
       * [§20c](../../../CLAUDE.md) forbids: *"never restyle a shared component
       * for one page's benefit."* ⛔ **Ten other dialogs read that width.**
       *
       * ✅ **The CONTENT is identical** — the same eighteen, the same three
       * groups, the same order — **and the design specifies a spec-page card
       * rather than the shape of the overlay `?` opens.** ⚡ **Raised as
       * [C-286](../../../docs/LANE_COORDINATION.md)** so a wide variant is
       * ruled on rather than assumed.
       */}
      <ShortcutList />
      </Dialog>
    </ShortcutsContext.Provider>
  );
}

