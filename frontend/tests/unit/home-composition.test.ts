import { describe, expect, it } from 'vitest';

import {
  COMPOSITION_NAME,
  COMPOSITION_QUESTION,
  resolveComposition,
  switchableCompositions,
  type Composition,
  type StatedRole,
} from '@/lib/home/composition';

/**
 * **Home's composition resolution** — 📁 `Fortune Signora Home.dc.html` §04.
 *
 * > 📁 ***"Resolution is a pure function of three inputs. Activation state, then
 * > a stored preference, then the primary role. Evaluated in that order, first
 * > match wins."***
 *
 * ⚠️ **This file was rewritten when the Home document became the composition
 * authority.** ⛔ It asserted a two-input resolver whose fallback was
 * `activation`; **the design's rule 5 makes the fallback SELLER** — *"the default
 * and the most common outcome"* — and state 04 forbids a fully activated
 * workspace rendering a setup sequence.
 */

const NOTHING = { neverSynced: false, preference: null, statedRole: null } as const;

describe('📁 rule 1 · activation precedes everything', () => {
  it('resolves activation when no integration has ever synced', () => {
    expect(resolveComposition({ ...NOTHING, neverSynced: true })).toBe('activation');
  });

  it('🔴 outranks a stored preference', () => {
    /**
     * 📁 The design's own reason: *"a workspace with no connected source cannot
     * render a data composition regardless of who is looking at it."* ⛔ **A
     * preference must not be able to hide setup** from somebody who still has to
     * do it.
     */
    expect(
      resolveComposition({ neverSynced: true, preference: 'executive', statedRole: null }),
    ).toBe('activation');
  });

  it('🔴 outranks a role — P-01, the worst first impression available', () => {
    /**
     * 📁 P-01 verbatim: *"A CRO looking at an unconnected workspace gets the same
     * three steps as anyone else. Rendering an empty executive dashboard to an
     * executive is the worst first impression available."*
     */
    expect(
      resolveComposition({ neverSynced: true, preference: null, statedRole: 'revenue_leader' }),
    ).toBe('activation');
  });
});

describe('📁 rule 2 · a stored preference is honoured over role', () => {
  it.each<[StatedRole, Composition]>([
    ['revenue_leader', 'seller'],
    ['sales_operations', 'executive'],
  ])('a %s who prefers %s gets it', (statedRole, preference) => {
    expect(resolveComposition({ neverSynced: false, preference, statedRole })).toBe(preference);
  });

  it('⛔ null means NOT SET and falls through, rather than meaning seller', () => {
    /**
     * 🔴 **The distinction rule 3 depends on.** If `null` were read as a value,
     * every executive would be pinned to the seller composition and rule 3 would
     * be unreachable — a defect no screenshot would show.
     */
    expect(
      resolveComposition({ neverSynced: false, preference: null, statedRole: 'revenue_leader' }),
    ).toBe('executive');
  });
});

describe('📁 rules 3, 4 and 5 · the stated role', () => {
  it.each<[StatedRole, Composition]>([
    // 📁 Rule 3 — *"CRO, CEO, VP or Sales Director"*.
    ['revenue_leader', 'executive'],
    ['executive', 'executive'],
    // 📁 Rule 4 — *"RevOps, workspace admin or integration admin"*.
    ['sales_operations', 'revenue_operations'],
    // 📁 Rule 5 — *"AE, AM, CSM, analyst, guest with membership"*.
    ['account_executive', 'seller'],
    ['customer_success', 'seller'],
    // ⚠️ The one role the design does not name. Rule 5 takes it.
    ['marketing', 'seller'],
  ])('%s resolves %s', (statedRole, expected) => {
    expect(resolveComposition({ ...NOTHING, statedRole })).toBe(expected);
  });

  it('🔴 falls back to SELLER, not activation, when no role was stated', () => {
    /**
     * 📁 **Rule 5 is *"the default and the most common outcome"***, and 📁 state
     * 04 requires a fully activated workspace to render a role composition.
     * ⛔ **Returning `activation` here would show a setup sequence for a product
     * that is already set up** — the defect this rewrite exists to fix.
     */
    expect(resolveComposition(NOTHING)).toBe('seller');
  });
});

describe('⚡ total, because the App Shell depends on it', () => {
  it('📁 "a composition always resolves, so Home ALWAYS renders"', () => {
    const roles: readonly (StatedRole | null)[] = [
      null,
      'revenue_leader',
      'account_executive',
      'sales_operations',
      'customer_success',
      'marketing',
      'executive',
    ];
    const prefs: readonly (Composition | null)[] = [
      null,
      'executive',
      'seller',
      'revenue_operations',
      'activation',
    ];

    for (const neverSynced of [true, false]) {
      for (const preference of prefs) {
        for (const statedRole of roles) {
          const got = resolveComposition({ neverSynced, preference, statedRole });
          // ⛔ Every input returns one of the design's four, never undefined.
          expect(COMPOSITION_NAME[got]).toBeTruthy();
          expect(COMPOSITION_QUESTION[got]).toBeTruthy();
        }
      }
    }
  });
});

describe('📁 the switcher only exists where there is a choice', () => {
  it('⛔ a seller has one option, so the control is absent', () => {
    // 📁 *"single-role people do not see an unnecessary switcher"*, and a control
    // with one option is [B-255](../../../docs/BUGS.md)'s dead control.
    expect(switchableCompositions('account_executive')).toEqual(['seller']);
    expect(switchableCompositions(null)).toEqual(['seller']);
  });

  it('✅ an executive may switch to seller and back', () => {
    // 📁 *"a person with two roles gets the narrower one and may switch once."*
    expect(switchableCompositions('revenue_leader')).toEqual(['executive', 'seller']);
    expect(switchableCompositions('sales_operations')).toEqual(['revenue_operations', 'seller']);
  });

  it('⛔ activation is never switchable', () => {
    // 📁 It is resolved by a fact about the workspace. Offering a way out would
    // offer a way to hide setup from somebody who still has to do it.
    for (const role of [null, 'revenue_leader', 'sales_operations', 'marketing'] as const) {
      expect(switchableCompositions(role)).not.toContain('activation');
    }
  });
});
