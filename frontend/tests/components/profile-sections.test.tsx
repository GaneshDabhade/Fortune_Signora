/**
 * 🔴 **The design's `nav` declares NINE sections and the register held eight.**
 *
 * 📁 `Fortune Signora User Profile.dc.html` → `nav`: *Profile · Language &
 * region · Appearance · Accessibility · Keyboard shortcuts · AI preferences ·
 * **Notifications** · Connected accounts · Activity & security.*
 *
 * ⛔ **`Notifications` was absent from the register rather than marked absent in
 * it** — ⚠️ **which is indistinguishable from a bug to the next reader**, and is
 * the failure Account 360's own registry states in its words: *"a page that
 * omits a section nobody built is indistinguishable from a page with a bug, and
 * the next lane cannot tell which."*
 *
 * ⚡ **Measured before it was written**: `workspace_tenancy`'s `Notifier` port
 * publishes one verb and **no channel adapters**, and all three notification
 * routes — feed, read, unread — are in-app.
 */
import { describe, expect, it } from 'vitest';

import { PROFILE_SECTIONS } from '@/app/(app)/profile/profile-shell';

describe('🔴 every section the design’s nav declares is declared here', () => {
  it('declares the design’s nine, in the design’s order', () => {
    // 📁 `nav`, verbatim.
    expect(PROFILE_SECTIONS.map((section) => section.label)).toEqual([
      'Profile',
      'Language & region',
      'Appearance',
      'Accessibility',
      'Keyboard shortcuts',
      'AI preferences',
      'Notifications',
      'Connected accounts',
      'Activity & security',
    ]);
  });

  /**
   * ⛔ **An absent section that says nothing is an omission with a heading.**
   * ⚡ The same guard Account 360 carries, for the same reason.
   */
  it('⛔ says what each absent section cannot do, and never “not built”', () => {
    const absent = PROFILE_SECTIONS.filter((section) => section.supply === 'absent');
    expect(absent.length, 'nothing is marked absent — the guard would be vacuous').toBeGreaterThan(0);

    for (const section of absent) {
      expect(section.absence, `${section.id} is absent and says nothing`).toBeTruthy();
      // ⛔ **Never a status report about the engineering backlog** — 📁 the
      // registry rule: *what it would show, and what Signora cannot answer.*
      expect(section.absence).not.toMatch(/not built|coming soon/i);
    }
  });

  /**
   * 🔴 **[B-299](../../../docs/BUGS.md) ⑦'s rule, applied to a second
   * register**: an absence says what SIGNORA cannot do, never what the READER
   * has not connected.
   */
  it('⛔ and no absence describes the reader’s own setup', () => {
    for (const section of PROFILE_SECTIONS) {
      if (section.absence === undefined) continue;
      expect(section.absence).not.toMatch(
        /\b(none|no|nothing)\b[^.]*\bis (?:currently )?connected\b|\bconnected to your (?:organization|organisation)\b/i,
      );
    }
  });

  /** ⚠️ **Vacuity guard** — a supplied section must not carry absence copy. */
  it('⚠️ vacuity guard — supplied sections state no absence', () => {
    for (const section of PROFILE_SECTIONS) {
      if (section.supply !== 'supplied') continue;
      expect(section.absence, `${section.id} is supplied and states an absence`).toBeUndefined();
    }
  });
});
