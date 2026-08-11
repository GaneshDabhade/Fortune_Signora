'use client';

import { useEffect, useState } from 'react';

import { Dialog } from '@/components/ui/dialog';
import { cn } from '@/lib/design/cn';
import {
  SHORTCUT_GROUPS,
  coverage,
  isApplePlatform,
  keysFor,
  pressable,
  type Shortcut,
} from '@/lib/shell/shortcuts';

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
export function ShortcutsReference() {
  const [open, setOpen] = useState(false);
  // ⚡ **Resolved on mount, never during render.** ⛔ The server has no
  // keyboard, so asking there and answering here is a hydration mismatch.
  const [apple, setApple] = useState(true);

  useEffect(() => setApple(isApplePlatform()), []);

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

  return (
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
      <div className={cn('grid grid-cols-1 overflow-hidden rounded-xl border border-border')}>
        {SHORTCUT_GROUPS.map((group) => (
          <div key={group.label} className="border-border">
            <p className="border-b border-border bg-surface-sunken px-4 py-3 text-2xs font-semibold uppercase tracking-wide text-content-subtle">
              {group.label}
            </p>
            <ul>
              {group.items.map((shortcut) => (
                <ShortcutRow key={shortcut.id} shortcut={shortcut} apple={apple} />
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Dialog>
  );
}

/**
 * ⚡ **One shortcut, and the difference between the three states is text
 * rather than colour.**
 *
 * ⛔ **Dimming alone would carry the whole meaning in contrast**, which is the
 * accessibility defect class [§20c](../../../CLAUDE.md) refuses to defer —
 * **a person who cannot see the dimming would read thirteen dead keys as
 * live.** ✅ **So `Not bound` is a rendered sentence**, and the styling only
 * agrees with it.
 */
function ShortcutRow({ shortcut, apple }: { shortcut: Shortcut; apple: boolean }) {
  const works = pressable(shortcut);

  return (
    <li className="flex flex-col gap-1 border-b border-border px-4 py-2.5 last:border-b-0">
      <div className="flex items-center gap-3">
        <span className={cn('text-sm', works ? 'text-content' : 'text-content-subtle')}>
          {shortcut.what}
        </span>
        <kbd
          className={cn(
            'ml-auto rounded-md border px-2 py-0.5 font-mono text-2xs',
            works
              ? 'border-border bg-surface-sunken text-content'
              : 'border-dashed border-border text-content-subtle',
          )}
        >
          {keysFor(shortcut.keys, apple)}
        </kbd>
      </div>
      {/* ⛔ **Never *"coming soon"*.** 📁 The rail paid for that sentence once —
          *"at M12.3, three of six said `coming soon` on the screen a customer
          sees first"* — **and it tells somebody to wait without saying for
          what.** ✅ **`Not bound` says the only thing that is true.**

          ⚠️ **Two words, not a sentence — found by looking at it.** ⛔ **The
          first version read *"Not bound — pressing it does nothing"* on every
          one of the nine**, and 📁 {@link coverage} already says that once, at
          the top, for all of them. **Nine copies of an explanation is how a
          reference stops being read**, and the repetition buried the five
          shortcuts that do work. ✅ **The per-row mark stays TEXT** — the
          accessibility reason is unchanged — **it just stops re-explaining
          itself.** */}
      {shortcut.state === 'unbound' ? (
        <span className="text-2xs text-content-subtle">Not bound</span>
      ) : null}
      {/* ⚠️ **A `partial` shortcut works, and saying otherwise would be as
          wrong as claiming it works everywhere.** ✅ **So the row states WHERE**
          rather than downgrading it. */}
      {shortcut.limit === undefined ? null : (
        <span className="text-2xs text-content-muted">{shortcut.limit}</span>
      )}
    </li>
  );
}
