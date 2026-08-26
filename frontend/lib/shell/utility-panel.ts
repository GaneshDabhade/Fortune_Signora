/**
 * **The utility panel's law** — [TASK-1433](../../../docs/BACKLOG.md), against
 * 📁 `Fortune Signora App Shell.dc.html` §13 and its anatomy table.
 *
 * ## 🔴 The row names its own risk, and this file is not where it is taken
 *
 * > ⚠️ ***"Building the chrome because it is the easy half. The chrome is not
 * > the deliverable."***
 *
 * ⚡ **So this file is deliberately small.** **It holds the four numbers and
 * the two rules the design states, and nothing else** — 📁 the widths, the
 * bands, the tab set and what the panel may not contain. ✅ **The deliverable
 * is the Activity tab rendering real history on the account record**, and that
 * lives with the account, not here.
 *
 * ## ⛔ Nothing here is a new band
 *
 * 📁 **[`rail.ts`](rail.ts) already publishes `BREAKPOINTS` and `bandFor`**,
 * from the same four design numbers — **1600 · 1280 · 1024 · 640** — and
 * ⚠️ **it already carries the panel's own widths in a comment**: *"≥ 1600 —
 * rail 232px, utility panel 360px, both open."* ⛔ **A second breakpoint table
 * here would be the duplicated truth [§2](../../../CLAUDE.md) forbids**, and
 * the two would disagree the first time the design moved one.
 *
 * ## ⚠️ This is the EIGHTH law in this shell that existed with no caller
 *
 * 📁 [`navigation.tsx`](../../components/shell/navigation.tsx) counted seven —
 * *the entry engine, the narrowing law, the top-bar slot set, the command
 * palette, `confidence.tsx`, `drawer.tsx`, and the rail's own rules.* ⛔ **And
 * `surfaceFor` in [`scope.ts`](scope.ts) is the eighth**: it decides
 * *utility panel or drawer* and **nothing has ever asked it**, because there
 * was no panel. ✅ **This row is what gives it a caller.**
 */

import { bandFor, type Band } from './rail';

/**
 * 📁 **The design's anatomy row**: ***"Utility panel · 300–360px · Non-modal,
 * pushes content, remembers its open state per module. Docked context, not a
 * task surface."***
 *
 * ⛔ **`null` is *the panel does not exist at this width*, not zero.** ⚡ **A
 * zero width would still be a rendered `aside` with a landmark**, and a screen
 * reader on a phone would be offered a *complementary* region containing
 * nothing.
 */
export const PANEL_WIDTH: Readonly<Record<Band, number | null>> = {
  /** 📁 *"≥ 1600 — rail 232px, utility panel 360px, both open."* */
  desktop: 360,
  /** 📁 *"1280–1599 — the reference layout. Rail 232px, panel 300px."* */
  laptop: 300,
  /** 📁 *"1024–1279 — utility panel closes to a 28px tab rail."* */
  smallLaptop: 28,
  /** 📁 *"< 1024px"* — the breakpoint table gives the panel no width at all. */
  phone: null,
};

/**
 * ⚡ **What the panel IS at a given width**, and it is three states rather than
 * open/closed.
 *
 * 🔴 **`tab-rail` is the one that would be lost to a boolean.** 📁 The design
 * is specific — *"closes to a 28px tab rail"* — ⛔ **which is not the same as
 * closed**: the tabs stay reachable, so somebody on a 1100px laptop can still
 * open the panel. **A boolean would have made that width either a full panel
 * that does not fit or nothing at all.**
 */
/**
 * 🔴 **The design's default, and [B-1076](../../../docs/BUGS.md) is that it was
 * not honoured.**
 *
 * 📁 **`App Shell`'s `breakpoints` array leaves no room**: at ≥1600 the line is
 * ***"Rail 232px, utility panel 360px, **both open**"***, and at 1280–1599 it is
 * ***"Reference layout. Rail 232px, panel 300px"*** with `panelDisplay: 'block'`.
 * ⚡ **The band below says the panel *"closes to a 28px tab rail"*** — **which
 * only means anything if it was open above it.**
 *
 * ⚠️ **QE recorded a competing reading and could not rule on it** — the same
 * table says *"utility panel remembers per-module state"*, so
 * closed-until-opened-once was possible intent. ⛔ **It does not survive the
 * other two lines**: *"remembers"* describes **persistence**, and *"both open"*
 * describes the **initial value**. **They answer different questions.**
 *
 * ⛔ **This is the DEFAULT, never an override.** ⚡ A stored preference — in
 * either direction — wins, which is what *"remembers per-module state"* asks
 * for.
 */
export const PANEL_OPEN_BY_DEFAULT = true;

export type PanelState = 'open' | 'tab-rail' | 'absent';

export function panelStateFor(viewportWidth: number, openPreference: boolean): PanelState {
  const band = bandFor(viewportWidth);

  // ⛔ **The width decides absence before the preference is consulted.** A
  // person who opened the panel on a laptop and then picked up a phone is not
  // asking for a 360px panel on a 390px screen.
  if (PANEL_WIDTH[band] === null) return 'absent';
  if (band === 'smallLaptop') return 'tab-rail';
  return openPreference ? 'open' : 'tab-rail';
}

/**
 * 📁 **The design's three tabs**, in its order.
 *
 * ⛔ **A closed list.** ⚡ **A module cannot add a fourth**: the panel is the
 * shell's, and 📁 the shell's own constitution says *"the frame owns no product
 * decision"* — **which cuts the other way too, so a module does not get to
 * change the frame's shape either.**
 */
export const PANEL_TABS = ['Insights', 'Activity', 'Notes'] as const;

export type PanelTab = (typeof PANEL_TABS)[number];

/**
 * ⚡ **Where a module's open-state memory lives.**
 *
 * 📁 ***"Remembers its open state per module"*** — ⛔ **per MODULE, not per
 * user alone**, which is a real product statement: **somebody who keeps the
 * panel open on an account record does not want it open on a settings page**,
 * and one key for both would make them choose once for everything.
 */
export function panelKey(userId: string, module: string): string {
  return `signora:utility-panel:${userId}:${module}`;
}

/**
 * 🔴 **What the panel refuses to contain**, and it delegates rather than
 * restating.
 *
 * 📁 **[`scope.ts`](scope.ts)'s `surfaceFor` already holds this rule** —
 * *"context that describes content goes in the utility panel; anything with a
 * Save goes in a drawer"* — ⛔ **and the reason is dismissal rather than
 * taxonomy**: the panel has no confirm step, so *"a form in the panel is a
 * form somebody loses by clicking a table row."*
 *
 * ⚡ **Re-exported here so a panel author finds it**, ⛔ **never re-implemented**
 * ([§2](../../../CLAUDE.md): *behaviour exists exactly once*).
 */
export { surfaceFor, type Surface } from './scope';

/**
 * ⚡ **The accessible name of the panel**, which the design ties to its state.
 *
 * 📁 ***"`aside[complementary]` — the utility panel, labelled with its active
 * tab."*** ⛔ **So the label is not the constant *"Utility panel"***: a screen
 * reader user choosing between landmarks is told *which* context they are
 * about to enter, which is the only thing that makes the region worth
 * offering.
 */
export function panelLabel(tab: PanelTab): string {
  return `${tab} panel`;
}
