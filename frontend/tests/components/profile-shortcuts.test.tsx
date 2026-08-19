/**
 * **Screen `05 · Keyboard shortcuts`** — the finalized User Profile design,
 * built under [TASK-1478](../../../docs/BACKLOG.md).
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ShortcutsPanel } from '@/app/(app)/profile/shortcuts-panel';
import { SHORTCUT_GROUPS, allShortcuts, pressable } from '@/lib/shell/shortcuts';

describe('📁 it reads the registry, and publishes what the registry publishes', () => {
  /**
   * ⚠️ **This section said *"This section is not built yet"* and described what
   * it would hold**: *"the shortcuts Signora publishes, read from the same
   * registry the ⌘-overlay uses."* ✅ **The description was accurate and the
   * registry already existed.**
   */
  it('✅ every group the registry declares, in its order', () => {
    render(<ShortcutsPanel />);

    const headings = screen
      .getAllByRole('list')
      .map((list) => list.previousElementSibling?.textContent?.trim());
    expect(headings).toEqual(SHORTCUT_GROUPS.map((group) => group.label));
  });

  /**
   * ⛔ **Nothing is omitted for being unbound.** 📁 The registry's own
   * reasoning: *"a hidden destination teaches a person the feature does not
   * exist, so they ask for the wrong thing or ask nobody. Published and marked
   * beats absent, as long as the mark is honest."*
   */
  it('⛔ every shortcut, including the ones nothing binds', () => {
    render(<ShortcutsPanel />);

    for (const shortcut of allShortcuts()) {
      expect(screen.getByText(shortcut.what), `${shortcut.id} is missing`).toBeVisible();
    }

    const unbound = allShortcuts().filter((shortcut) => !pressable(shortcut));
    // ⚡ **The mark is TEXT, never only a dimming** — a person who cannot see
    // the contrast would read a dead key as live.
    expect(screen.getAllByText('Not bound')).toHaveLength(unbound.length);
  });

  it('✅ says how many of them work, once, at the top', () => {
    render(<ShortcutsPanel />);

    const working = allShortcuts().filter(pressable).length;
    expect(screen.getByText(new RegExp(`${working} of these ${allShortcuts().length}`))).toBeVisible();
  });
});

describe('⛔ what the section deliberately does not offer', () => {
  /**
   * 📁 **The design's spec line describes an EDITOR**: *"conflicts are refused
   * with the name of the command already holding the combination."* ⛔ **There
   * is none** — `PersonPreferences` carries no shortcut field and no endpoint
   * stores a binding — **so no control claims otherwise.**
   *
   * ⚡ **The same refusal this product has made three times**: the assistant's
   * absent input, the *"Notification settings"* link to an unbuilt screen, and
   * the rail's retired *"coming soon"*.
   */
  it('⛔ no way to change a binding, because nothing could store one', () => {
    render(<ShortcutsPanel />);

    expect(screen.queryByRole('button', { name: /custom|change|edit|record/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByText(/coming soon/i)).not.toBeInTheDocument();
  });

  it('✅ and it tells a reader the one thing they can act on now', () => {
    render(<ShortcutsPanel />);

    const line = screen.getByText(/Press/).closest('p')!;
    expect(within(line).getByText('?')).toBeVisible();
  });
});
