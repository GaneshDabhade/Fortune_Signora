/**
 * **The utility panel's law** — [TASK-1433](../../../docs/BACKLOG.md).
 *
 * ⚠️ **The row's risk is *"building the chrome because it is the easy half"***,
 * so these assert the two things the design actually decides — **the widths and
 * the three states** — and ⛔ **not that a panel slides.**
 */
import { describe, expect, it } from 'vitest';

import { BREAKPOINTS } from '@/lib/shell/rail';
import {
  PANEL_TABS,
  PANEL_WIDTH,
  panelKey,
  panelLabel,
  panelStateFor,
  surfaceFor,
} from '@/lib/shell/utility-panel';

describe("📁 the design's widths, at the design's own bands", () => {
  it('gives the panel 360 on a desktop and 300 on the reference laptop', () => {
    // 📁 *"≥ 1600 — rail 232px, utility panel 360px"* and *"1280–1599 — the
    // reference layout. Rail 232px, panel 300px."*
    expect(PANEL_WIDTH.desktop).toBe(360);
    expect(PANEL_WIDTH.laptop).toBe(300);
  });

  it('📁 closes it to a 28px tab rail on a small laptop', () => {
    expect(PANEL_WIDTH.smallLaptop).toBe(28);
  });

  it('⛔ gives it NO width below 1024 — null, never zero', () => {
    /**
     * ⚡ **A zero would still be a rendered `aside` with a landmark**, and a
     * screen-reader user on a phone would be offered a *complementary* region
     * containing nothing.
     */
    expect(PANEL_WIDTH.phone).toBeNull();
  });

  it('🔴 reads its bands from `rail.ts` rather than declaring its own', () => {
    // ⛔ A second breakpoint table is the duplicated truth §2 forbids, and the
    // two would disagree the first time the design moved one.
    expect(panelStateFor(BREAKPOINTS.desktop, true)).toBe('open');
    expect(panelStateFor(BREAKPOINTS.desktop - 1, true)).toBe('open');
    expect(panelStateFor(BREAKPOINTS.smallLaptop - 1, true)).toBe('absent');
  });
});

describe('🔴 three states, because a boolean would lose the tab rail', () => {
  it('is absent below 1024 whatever the person last preferred', () => {
    // ⛔ **The width decides absence BEFORE the preference is consulted.**
    // Somebody who opened the panel on a laptop and then picked up a phone is
    // not asking for a 360px panel on a 390px screen.
    expect(panelStateFor(390, true)).toBe('absent');
    expect(panelStateFor(1023, true)).toBe('absent');
  });

  it('📁 is a tab rail on a small laptop even when the preference is open', () => {
    // 📁 *"Utility panel closes to a 28px tab rail"* — ⚡ not the same as
    // closed: the tabs stay reachable, so the panel can still be opened.
    expect(panelStateFor(1100, true)).toBe('tab-rail');
    expect(panelStateFor(1100, false)).toBe('tab-rail');
  });

  it('honours the preference at the reference width and above', () => {
    expect(panelStateFor(1440, true)).toBe('open');
    expect(panelStateFor(1440, false)).toBe('tab-rail');
    expect(panelStateFor(1920, true)).toBe('open');
  });

  it('⛔ never returns `open` where the panel has no room', () => {
    // ⚡ Asserted as a sweep rather than at three chosen widths, because the
    // defect this prevents is an off-by-one at a band edge.
    for (let w = 320; w < 1024; w += 17) {
      expect(panelStateFor(w, true), `${w}px`).toBe('absent');
    }
  });
});

describe('📁 the tabs, and what the panel may not hold', () => {
  it("names the design's three, in its order", () => {
    expect([...PANEL_TABS]).toEqual(['Insights', 'Activity', 'Notes']);
  });

  it('🔴 labels the region with its ACTIVE TAB, not with a constant', () => {
    /**
     * 📁 ***"`aside[complementary]` — the utility panel, labelled with its
     * active tab."*** ⛔ **A constant *"Utility panel"* tells a screen-reader
     * user choosing between landmarks nothing about what they are entering.**
     */
    expect(panelLabel('Activity')).toBe('Activity panel');
    expect(panelLabel('Insights')).toBe('Insights panel');
  });

  it('⛔ sends anything with a Save to a drawer, by delegating rather than restating', () => {
    // 📁 *"A form in the panel is a form somebody loses by clicking a table
    // row."* ⚡ The rule lives in `scope.ts`; this proves the panel consults it.
    expect(surfaceFor({ hasSave: true })).toBe('drawer');
    expect(surfaceFor({ multiStep: true })).toBe('drawer');
    expect(surfaceFor({ destructive: true })).toBe('drawer');
    expect(surfaceFor({})).toBe('utility-panel');
  });

  it('⚡ remembers per MODULE, so one screen’s preference is not every screen’s', () => {
    // 📁 *"Remembers its open state per module"* — somebody who keeps it open
    // on an account record does not want it open on a settings page.
    expect(panelKey('u1', 'accounts')).not.toBe(panelKey('u1', 'settings'));
    expect(panelKey('u1', 'accounts')).not.toBe(panelKey('u2', 'accounts'));
  });
});
