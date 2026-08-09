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
  MAX_DEPTH,
  MAX_DESTINATIONS,
  RAIL_WIDTH,
  TAB_ORDER,
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
    expect(deviceClassFor(767)).toBe('compact');
    expect(deviceClassFor(768)).toBe('regular');
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
