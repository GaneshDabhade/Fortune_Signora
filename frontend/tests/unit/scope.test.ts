/**
 * **Global scope, and what a module may do to it** —
 * [TASK-1408](../../../docs/BACKLOG.md), rules 4, 5 and 8.
 *
 * ⚡ **The defect this protects against is invisible when it happens**: a
 * number correct for a period nobody selected, under a chip naming the period
 * they did.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  SCOPE_DIMENSIONS,
  ScopeWidenedError,
  chipStyle,
  narrow,
  surfaceFor,
} from '@/lib/shell/scope';

const DESIGN = readFileSync(
  join(process.cwd(), '../docs/design-snapshot/screens/Fortune Signora App Shell.dc.html'),
  'utf8',
);

describe('🔴 a module may narrow global scope and may never widen it', () => {
  it('📁 "a module cannot silently leave the global period"', () => {
    expect(DESIGN).toMatch(/A module cannot silently leave the global period/);
  });

  it('narrows within the global set', () => {
    const global = { period: ['Q3'], region: ['EMEA', 'AMER'] };
    expect(narrow(global, { region: ['EMEA'] })).toEqual({
      period: ['Q3'],
      region: ['EMEA'],
    });
  });

  it('⛔ REFUSES a widening rather than clamping it', () => {
    /**
     * ⚡ **A clamp would produce the correct scope and hide that a module
     * tried to leave it** — and the module would go on believing it had the
     * period it asked for. **That belief is what reaches a customer**, as a
     * figure computed over twelve months sitting under a chip reading Q3.
     */
    const global = { period: ['Q3'] };
    expect(() => narrow(global, { period: ['Q1', 'Q2', 'Q3'] })).toThrow(ScopeWidenedError);
    expect(() => narrow(global, { period: ['Q1', 'Q2', 'Q3'] })).toThrow(/only narrow/);
  });

  it('names the dimension and the offending members, not just "invalid"', () => {
    try {
      narrow({ region: ['EMEA'] }, { region: ['APAC'] });
      expect.unreachable('should have refused');
    } catch (e) {
      expect(e).toBeInstanceOf(ScopeWidenedError);
      expect((e as ScopeWidenedError).message).toMatch(/region: module admits \[APAC\]/);
    }
  });

  it('an unconstrained global dimension admits anything — absence is not a constraint', () => {
    // ⚠️ The subtle case: global says nothing about `owner`, so a module may
    // constrain it. That is narrowing, not widening.
    expect(narrow({ period: ['Q3'] }, { owner: ['me'] })).toEqual({
      period: ['Q3'],
      owner: ['me'],
    });
  });

  it('📁 four dimensions, and a fifth belongs to a module', () => {
    expect([...SCOPE_DIMENSIONS]).toEqual(['period', 'region', 'segment', 'owner']);
    expect(DESIGN).toMatch(/A fifth belongs to a module, not the shell/);
  });
});

describe('📁 the chip’s tint says whether the filter survives navigation', () => {
  it('⛔ a module filter rendered tinted claims persistence it does not have', () => {
    // 📁 *"Tinted chip = global and persistent. Outlined chip = local and
    // transient."* ⚡ A customer returns expecting a tinted filter still on.
    expect(chipStyle('global')).toBe('tinted');
    expect(chipStyle('module')).toBe('outlined');
  });
});

describe('📁 rule 8 — a Save belongs in a drawer, never in the utility panel', () => {
  it('⚡ the reason is dismissal, not taxonomy', () => {
    /**
     * **The panel has no confirm step and the drawer does** — 📁 *"Escape and
     * scrim click close only when nothing is lost. Otherwise a confirm offers
     * Keep editing, Discard, Save draft."* ⛔ **So a form in the panel is a
     * form somebody loses by clicking a table row**, which is the exact move
     * the panel exists to make cheap.
     */
    expect(surfaceFor({})).toBe('utility-panel');
    expect(surfaceFor({ hasSave: true })).toBe('drawer');
    expect(surfaceFor({ multiStep: true })).toBe('drawer');
    expect(surfaceFor({ destructive: true })).toBe('drawer');
  });

  it('📁 the panel’s own "Never" list is the source', () => {
    expect(DESIGN).toMatch(/No forms with a Save, no multi-step flows, no destructive actions/);
  });
});
