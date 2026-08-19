'use client';

import { useEffect, useState } from 'react';

import { cn } from '@/lib/design/cn';
import {
  SHORTCUT_GROUPS,
  isApplePlatform,
  keysFor,
  pressable,
  type Shortcut,
} from '@/lib/shell/shortcuts';

/**
 * **Every shortcut Signora publishes, grouped as its design groups them** —
 * 📁 App Shell **§15**, and 📁 `Fortune Signora User Profile.dc.html`'s
 * *Keyboard shortcuts* section.
 *
 * ## 🔴 Extracted so two surfaces cannot drift into two answers
 *
 * ⚠️ **The `?` overlay drew this list, and the profile's section drew nothing.**
 * ⛔ **Building a second copy would be two renderings of one registry** —
 * 📁 [§2](../../../CLAUDE.md): *behaviour exists exactly once* — **and the
 * copies would disagree the first time one of them learned something.**
 *
 * ✅ **The registry was already the single source.** 📁 `lib/shell/shortcuts.ts`
 * measures itself against every `keydown` binding in the product; **what was
 * duplicated was the way of SAYING it**, which is what moved here.
 *
 * ## ⛔ Three states, and the difference between them is text
 *
 * ⚡ **Dimming alone would carry the whole meaning in contrast**, which is the
 * accessibility defect [§20c](../../../CLAUDE.md) refuses to defer — **a person
 * who cannot see the dimming would read the unbound ones as live.** ✅ So
 * *"Not bound"* is a rendered sentence and the styling only agrees with it.
 */
export function ShortcutList({ className }: { className?: string }) {
  /**
   * ⛔ **Resolved on mount, never during render.** 🔴 **`isApplePlatform()`
   * reads `navigator` and the server has no keyboard**, so asking there and
   * answering here is a hydration mismatch that loses the tree.
   *
   * ⚠️ **The extraction nearly dropped this.** The overlay carried it as a
   * `useEffect` and the first draft of this component called the function in
   * the render body — ⛔ **a correctness property living in the CALLER is one
   * an extraction silently discards**, which is why it moved with the markup
   * rather than being left behind.
   *
   * ⚡ **`true` until it knows** — 📁 the design writes Apple glyphs, so the
   * first paint matches the document and the correction is one frame.
   */
  const [apple, setApple] = useState(true);
  useEffect(() => setApple(isApplePlatform()), []);

  return (
    <div className={cn('grid grid-cols-1 overflow-hidden rounded-xl border border-border', className)}>
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
  );
}

/** ⚡ **One shortcut**, and the difference between its three states is text. */
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

          ⚠️ **Two words, not a sentence.** ⛔ The first version repeated the
          explanation on every unbound row, and 📁 `coverage()` already says it
          once, at the top, for all of them. */}
      {shortcut.state === 'unbound' ? (
        <span className="text-2xs text-content-subtle">Not bound</span>
      ) : null}
      {/* ⚠️ **A `partial` shortcut works, and saying otherwise would be as wrong
          as claiming it works everywhere.** ✅ So the row states WHERE rather
          than downgrading it. */}
      {shortcut.limit === undefined ? null : (
        <span className="text-2xs text-content-muted">{shortcut.limit}</span>
      )}
    </li>
  );
}
