/**
 * **The rail's law** — [TASK-1408](../../../docs/BACKLOG.md).
 *
 * ⚡ **The assertion that matters is that a restricted destination is still
 * there.** Everything else in this file protects a number; that one protects
 * a person's ability to find out what they are missing.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  BREAKPOINTS,
  MAX_DEPTH,
  MAX_DESTINATIONS,
  RAIL_WIDTH,
  TAB_ORDER,
  bandFor,
  bandForcesCollapse,
  railIsCollapsed,
  collapseKey,
  deviceClassFor,
  railViolations,
  visibleDestinations,
  type RailDestination,
} from '@/lib/shell/rail';

const DESIGN = readFileSync(
  join(process.cwd(), '../docs/design-snapshot/screens/Fortune Signora App Shell.dc.html'),
  'utf8',
);

const dest = (id: string, over: Partial<RailDestination> = {}): RailDestination => ({
  id,
  label: id,
  depth: 1,
  ...over,
});

describe('🔴 a restricted destination stays visible', () => {
  it('📁 "restricted destinations stay visible at 45% with a lock and explain on click"', () => {
    /**
     * ⛔ **The instinct is to hide what somebody cannot reach, and the design
     * refuses it.** **A hidden destination teaches a person the feature does
     * not exist**, so they ask for the wrong thing or ask nobody. ⚡ **A
     * locked one that explains itself sends them to whoever can grant it.**
     */
    expect(DESIGN).toMatch(/Restricted destinations stay visible/);

    const rail = [dest('home'), dest('forecast', { restricted: true }), dest('accounts')];
    expect(visibleDestinations(rail)).toHaveLength(3);
    expect(visibleDestinations(rail).map((d) => d.id)).toContain('forecast');
  });
});

describe('📁 nine destinations, two levels, and no more', () => {
  it('⛔ a tenth top-level destination is a defect, not something to truncate', () => {
    const ten = Array.from({ length: 10 }, (_, i) => dest(`d${i}`));
    const problems = railViolations(ten);
    expect(problems).toHaveLength(1);
    // ⚡ It names the rule rather than returning false — a caller who added
    // the tenth needs to know which line they crossed.
    expect(problems[0]).toMatch(/scanning beats searching/);
  });

  it('second-level items do not count toward the nine', () => {
    // 📁 A second level is detail inside a destination, not another one.
    const rail = [
      ...Array.from({ length: 9 }, (_, i) => dest(`d${i}`)),
      dest('child', { depth: 2 }),
    ];
    expect(railViolations(rail)).toEqual([]);
  });

  it('⛔ refuses a third level — "depth lives in records"', () => {
    expect(MAX_DEPTH).toBe(2);
    const problems = railViolations([dest('deep', { depth: 3 })]);
    expect(problems[0]).toMatch(/never nests past 2/);
  });

  it('📁 only Signals shows an unread dot', () => {
    // *"Counts are neutral; a dot means unread and only Signals uses it."*
    expect(railViolations([dest('signals', { unread: true })])).toEqual([]);
    expect(railViolations([dest('accounts', { unread: true })])[0]).toMatch(/only Signals does/);
  });

  it('carries the design’s two widths', () => {
    expect(RAIL_WIDTH).toEqual({ expanded: 232, collapsed: 56 });
    expect(MAX_DESTINATIONS).toBe(9);
  });
});

describe('🔴 collapse persists per user AND per device class', () => {
  it('⚡ a laptop and a tablet are different answers to the same question', () => {
    /**
     * 📁 *"the state persists per user, per device class."* ⛔ **Dropping the
     * device half is the easy mistake**: collapsing the rail on a desktop
     * would then collapse it on the phone, where 56px of rail is the only
     * navigation there is.
     */
    expect(collapseKey('u1', 'regular')).not.toBe(collapseKey('u1', 'compact'));
  });

  it('⛔ refuses a blank user id rather than sharing one key', () => {
    // A key without the user is shared by every account on the machine —
    // which leaks a preference and, on a shared device, that somebody else
    // uses this product at all.
    expect(() => collapseKey('', 'regular')).toThrow(/per user/);
    expect(collapseKey('u1', 'regular')).not.toBe(collapseKey('u2', 'regular'));
  });

  it('classes the device at the design’s breakpoint', () => {
    /**
     * 🔴 **This test's NAME claimed the design's breakpoint and its BODY
     * asserted Tailwind's.** ⛔ It pinned `768`, which is `md:` — **a number
     * the App Shell never names** — while calling it the design's.
     *
     * 📁 **The design's boundary is 1024**: *"< 1024px: rail becomes a sheet
     * from a top-bar button."* ⚡ **That is the width at which a rail stops
     * existing**, which is exactly what a *device class* has to mean if the
     * remembered collapse state is to apply to the right thing.
     *
     * ⚠️ **A test whose title asserts one thing and whose body asserts another
     * is worse than no test** — it reads as coverage of the rule it names.
     */
    expect(deviceClassFor(1023)).toBe('compact');
    expect(deviceClassFor(1024)).toBe('regular');
    expect(BREAKPOINTS.smallLaptop).toBe(1024);
  });

  it('📁 the four bands are the design’s four, at the design’s widths', () => {
    // ⛔ **Four behaviours, not two.** A helper answering *is this small* would
    // have to be replaced the first time a caller told a laptop from a desktop.
    expect(bandFor(639)).toBe('phone');
    expect(bandFor(640)).toBe('phone');
    expect(bandFor(1024)).toBe('smallLaptop');
    expect(bandFor(1280)).toBe('laptop');
    expect(bandFor(1600)).toBe('desktop');
    expect(bandFor(1599)).toBe('laptop');
  });

  it('⛔ and the numbers come from the design document, not from this test', () => {
    /**
     * ⚡ **Parsed out of the App Shell's own `breakpoints`**, so a design
     * refresh that moves a boundary fails here rather than passing over a
     * frame that no longer matches — 📁 [D-137](../../../docs/DECISION_REGISTER.md):
     * *"the copy is always the one somebody reads."*
     */
    for (const width of Object.values(BREAKPOINTS)) {
      expect(DESIGN, `${width} is not a width the design names`).toContain(String(width));
    }
  });
});

describe('♿ the tab order is a contract, not a consequence of DOM order', () => {
  it('📁 "rail → filter strip → content → utility panel"', () => {
    // ⚡ The utility panel sits visually beside the content and comes AFTER
    // it — the one pair a source-order layout gets backwards.
    expect([...TAB_ORDER]).toEqual(['rail', 'filter-strip', 'content', 'utility-panel']);
    expect(DESIGN).toMatch(/Tab order is rail → filter strip → content → utility panel/);
  });
});

describe('the band at 1024–1279 forces the rail, and the preference governs above it', () => {
  /**
   * 🔴 **[TASK-1473](../../../docs/BACKLOG.md), 📁 [D-233](../../../docs/DECISION_REGISTER.md)
   * rule ⓐ** — ruled after Lane C found the design ambiguous and QE challenged
   * the premise.
   *
   * ⚠️ **Two-sided on purpose.** 📁 The row asks for exactly this: *"under ① the
   * assertion must fail at 232px@1279 **and** at 56px@1280."* ⛔ **A test that
   * only checked the forced side would pass against a rail that is collapsed
   * everywhere**, which is the opposite defect and just as wrong.
   */

  it('forces the collapsed rail below 1280, whatever the person prefers', () => {
    // 📁 *"Small laptop 1024–1279 — Rail collapses to 56px icons with
    // tooltips."* ⚡ The evidence it is a FORCED state is the utility panel:
    // the same band entry carries `panelDisplay: 'none'`, overriding that
    // component's own stored preference.
    expect(railIsCollapsed('smallLaptop', false)).toBe(true);
    expect(railIsCollapsed('smallLaptop', true)).toBe(true);
  });

  it('lets the person decide at 1280 and above', () => {
    // ⚡ **The preference does real work between Laptop and Desktop**, which is
    // what defeats the objection that a band-forced state makes it pointless.
    expect(railIsCollapsed('laptop', false)).toBe(false);
    expect(railIsCollapsed('laptop', true)).toBe(true);
    expect(railIsCollapsed('desktop', false)).toBe(false);
    expect(railIsCollapsed('desktop', true)).toBe(true);
  });

  it('does not force the sheet, which is neither expanded nor collapsed', () => {
    // ⛔ Below 1024 *"the rail becomes a sheet from a top-bar button"*.
    // Returning `true` here would render the sheet at 56px — a third state
    // nobody drew.
    expect(railIsCollapsed('phone', false)).toBe(false);
    expect(bandForcesCollapse('phone')).toBe(false);
  });

  it('holds the rule at the exact pixels the row names', () => {
    // ⚡ **The boundary, from a viewport width rather than a band name** —
    // 📁 the row's own two-sided requirement.
    expect(railIsCollapsed(bandFor(1279), false)).toBe(true);
    expect(railIsCollapsed(bandFor(1280), false)).toBe(false);
    expect(railIsCollapsed(bandFor(1024), false)).toBe(true);
    expect(railIsCollapsed(bandFor(1023), false)).toBe(false);
  });

  it('names which bands take the decision away, in one place', () => {
    // ⛔ **A rule with a name a reviewer can search for**, rather than a
    // comparison repeated in a hook and a component.
    const forced = (['phone', 'smallLaptop', 'laptop', 'desktop'] as const).filter(
      bandForcesCollapse,
    );

    expect(forced).toEqual(['smallLaptop']);
  });
});
