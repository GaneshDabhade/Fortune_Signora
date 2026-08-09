/**
 * **The top bar's closed slot set** — [TASK-1408](../../../docs/BACKLOG.md),
 * rule 2.
 *
 * ⚡ **The interesting assertion is the guard at the bottom**, which fails if a
 * module ever grows a way to put something in the top bar. **Rule 2 is the
 * shell rule most likely to be broken by somebody reasonable**, because every
 * module has one control it believes is global.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  BADGE_CAP,
  SEARCH_WIDTH,
  SLOT_SPEC,
  TOP_BAR_SLOTS,
  badgeLabel,
  statusLabelVisible,
} from '@/lib/shell/top-bar';

const DESIGN = readFileSync(
  join(process.cwd(), '../docs/design-snapshot/screens/Fortune Signora App Shell.dc.html'),
  'utf8',
);

describe('📁 the five slots are the design’s, and account is always last', () => {
  it('⚡ the design’s own note is the assertion', () => {
    // 📁 *"Help before account, always last."* Read from the document so a
    // change there fails here rather than drifting.
    expect(DESIGN).toMatch(/Help before account, always last/);
    expect(TOP_BAR_SLOTS[TOP_BAR_SLOTS.length - 1]).toBe('account');
    expect(TOP_BAR_SLOTS.indexOf('help')).toBeLessThan(TOP_BAR_SLOTS.indexOf('account'));
  });

  it('every slot has a spec, and the breadcrumb is the only flexible one', () => {
    for (const slot of TOP_BAR_SLOTS) expect(SLOT_SPEC[slot]).toBeDefined();
    const flexible = TOP_BAR_SLOTS.filter((s) => SLOT_SPEC[s].width === 'flex');
    // 📁 *"flex, min 0"* — one flexible slot, or the bar cannot truncate
    // predictably.
    expect(flexible).toEqual(['breadcrumb']);
  });
});

describe('🔴 a degraded system may not go quiet to save space', () => {
  it('📁 "green pill hides its label at <1280px; amber and red always show it"', () => {
    /**
     * ⚡ **The asymmetry is the rule.** ⛔ **Hiding *"degraded"* to reclaim
     * 60px is the platform choosing its own convenience over the customer
     * knowing why their data looks wrong.**
     */
    expect(statusLabelVisible('healthy', 1279)).toBe(false);
    expect(statusLabelVisible('healthy', 1280)).toBe(true);
    for (const narrow of [320, 1024, 1279]) {
      expect(statusLabelVisible('degraded', narrow)).toBe(true);
      expect(statusLabelVisible('down', narrow)).toBe(true);
    }
  });
});

describe('📁 the notification badge caps at 99+', () => {
  it('⛔ a four-digit badge would break a 32px slot', () => {
    expect(badgeLabel(0)).toBeNull();
    expect(badgeLabel(1)).toBe('1');
    expect(badgeLabel(BADGE_CAP)).toBe('99');
    expect(badgeLabel(100)).toBe('99+');
    expect(badgeLabel(4820)).toBe('99+');
  });
});

describe('📁 search widens only where both conditions hold', () => {
  it('⚡ "320px on focus at ≥1600px" is an AND, not an either', () => {
    expect(SEARCH_WIDTH.rest).toBe(224);
    expect(SEARCH_WIDTH.focused).toBe(320);
    expect(SEARCH_WIDTH.focusWidensAbove).toBe(1600);
  });
});

describe('🔴 rule 2 — no module may add anything to the top bar', () => {
  /**
   * ⛔ **The rule is enforced by absence**: the top bar exposes no `children`,
   * no `slots` prop and no registration function. ⚡ **This guard fails if one
   * ever appears**, which is the difference between a rule and a habit.
   */
  /** The APIs whose ABSENCE is the enforcement of rule 2. */
  const FORBIDDEN = /addTopBarItem|registerTopBar|topBarSlots\s*[:=]|useTopBar\b/;

  function sources(dir: string): { name: string; source: string }[] {
    const out: { name: string; source: string }[] = [];
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) out.push(...sources(full));
      else if (/\.tsx?$/.test(entry.name)) {
        out.push({ name: full, source: readFileSync(full, 'utf8') });
      }
    }
    return out;
  }

  it('⛔ nothing offers a way to register a top-bar item', () => {
    // ⚠️ **Comments are stripped before scanning, and that is not a
    // convenience.** The first version matched this module's own JSDoc, which
    // names `addTopBarItem` precisely to say it does not exist — ⛔ **a guard
    // that reads prose reports the documentation as the violation.** 📁 That
    // is [B-318](../../../docs/BUGS.md)'s class exactly: *"a Security
    // Invariant matches text, so a comment fails it."*
    const code = (src: string) =>
      src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');

    const offenders = sources(join(process.cwd(), 'lib', 'shell'))
      .concat(sources(join(process.cwd(), 'components')))
      .filter(({ source }) => FORBIDDEN.test(code(source)))
      .map(({ name }) => name.split('frontend/').pop());

    expect(
      offenders,
      'rule 2: no module may add anything to the top bar — the absence of an API is the enforcement',
    ).toEqual([]);
  });

  it('✅ and the guard is proved able to fire', () => {
    // ⚡ **§2 — *a guard that cannot fail is documentation pretending to be
    // code*.** The same pattern, run against a string that violates it.
    const violating = 'export function addTopBarItem(slot: string) {}';
    expect(FORBIDDEN.test(violating)).toBe(true);
    // ⛔ And it is proved NOT to fire on a comment saying the same words,
    // which is the defect this guard was just caught by.
    expect(FORBIDDEN.test('// there is no addTopBarItem here'.replace(/\/\/.*$/gm, ''))).toBe(false);
  });
});
