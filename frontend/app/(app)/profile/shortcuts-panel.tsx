'use client';

import { ShortcutList } from '@/components/shell/shortcut-list';
import { coverage } from '@/lib/shell/shortcuts';

/**
 * **Screen `05 · Keyboard shortcuts`** — the finalized User Profile design.
 *
 * > 📁 ***"Keyboard shortcuts · Press `?` anywhere"***, then the design's
 * > groups, each row a command and its combination.
 *
 * ## ✅ It reads the registry the `?` overlay reads, and adds nothing
 *
 * ⚠️ **This section said *"This section is not built yet"* and described what
 * it would hold**: *"the shortcuts Signora publishes, read from the same
 * registry the ⌘-overlay uses."* ⛔ **That description was accurate and the
 * registry already existed** — 📁 `lib/shell/shortcuts.ts`, which measures
 * itself against every `keydown` binding in the product. **What was missing was
 * this component.**
 *
 * ✅ **`ShortcutList` is shared with the overlay** rather than copied — 📁
 * [§2](../../../../CLAUDE.md): *behaviour exists exactly once*, and **two
 * renderings of one registry would disagree the first time one of them learned
 * something.**
 *
 * ## ⛔ Customising a binding is NOT built, and the design names the rule
 *
 * 📁 **The design's spec line**: *"Conflicts are refused with the name of the
 * command already holding the combination. Reserved browser combinations cannot
 * be captured."* ⚡ **That is a rule about an editor**, and there is none:
 * `PersonPreferences` carries no shortcut field and no endpoint stores one.
 *
 * ⛔ **So no *Customise* control is drawn.** 📁 A control that cannot do what it
 * says is the false-affordance class this product has refused repeatedly — the
 * assistant's absent input, the *"Notification settings"* link to an unbuilt
 * screen, and the rail's retired *"coming soon"*. ✅ **The section says what it
 * shows and stops.**
 */
export function ShortcutsPanel() {
  return (
    <section aria-labelledby="shortcuts-heading" className="flex flex-col gap-4">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h2 id="shortcuts-heading" className="text-base font-semibold text-content">
          Keyboard shortcuts
        </h2>
        {/* 📁 The design's own line, top right of the card. ⚡ It is the one
            thing on this page a reader can act on immediately. */}
        <p className="ml-auto text-xs text-content-muted">
          Press{' '}
          <kbd className="rounded border border-border bg-surface-sunken px-1.5 py-0.5 font-mono text-2xs text-content">
            ?
          </kbd>{' '}
          anywhere
        </p>
      </div>

      {/**
       * ⛔ **The honest total, once, at the top** — 📁 `coverage()`, the same
       * sentence the `?` overlay opens with. ⚡ **Published and marked beats
       * absent**: a reference that hid its unbound entries would teach a reader
       * the feature does not exist, so they ask for the wrong thing or ask
       * nobody.
       */}
      <p className="text-sm leading-6 text-content-muted">{coverage()}</p>

      <ShortcutList />
    </section>
  );
}
