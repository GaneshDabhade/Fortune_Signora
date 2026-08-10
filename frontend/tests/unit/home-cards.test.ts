import { describe, expect, it } from 'vitest';

import { COMPOSITION_QUESTION, type Composition } from '@/lib/home/composition';
import {
  CARD_IDS,
  COMPOSITION_CARDS,
  REGISTRY,
  cardsFor,
  type CardContract,
} from '@/lib/home/cards';

/**
 * **The card registry** — [TASK-1406](../../../docs/BACKLOG.md).
 *
 * ⛔ **The discipline copied from `tenancy_policy.py` is that a
 * misclassification is a BUILD FAILURE rather than a silent exemption.** ⚡ So
 * these are consistency assertions over the declarations, not examples.
 */

const COMPOSITIONS = Object.keys(COMPOSITION_QUESTION) as Composition[];

describe('📁 the catalogue is the design\'s, and it is closed', () => {
  it('✅ every composition names only cards the catalogue has', () => {
    // ⚡ TypeScript already refuses an unknown id. **This asserts the runtime
    // shape too**, because `CARD_IDS` and `COMPOSITION_CARDS` are two
    // declarations and a compile-time union does not prove they agree.
    const known = new Set<string>(CARD_IDS);
    for (const composition of COMPOSITIONS) {
      for (const id of COMPOSITION_CARDS[composition]) {
        expect(known.has(id), `${composition} names an unknown card: ${id}`).toBe(true);
      }
    }
  });

  it('⛔ every card in the catalogue is placed in at least one composition', () => {
    /**
     * 📁 **`tenancy_policy.py`'s rule, transposed**: *"a table appearing in
     * neither list fails `test_every_table_is_classified`."* ⚡ **A card in the
     * catalogue and in no composition is a card no person will ever see**, and
     * the point of declaring it is that the absence is loud.
     */
    const placed = new Set(Object.values(COMPOSITION_CARDS).flat());
    const orphans = CARD_IDS.filter((id) => !placed.has(id));
    expect(orphans, 'catalogued cards that no composition shows').toEqual([]);
  });

  it('⛔ all four compositions have a card list, and none is empty', () => {
    // ⚡ 📁 *"A composition always resolves, so Home ALWAYS renders."* A
    // composition with no cards declared could never satisfy that.
    expect(Object.keys(COMPOSITION_CARDS).sort()).toEqual([...COMPOSITIONS].sort());
    for (const composition of COMPOSITIONS) {
      expect(COMPOSITION_CARDS[composition].length).toBeGreaterThan(0);
    }
  });

  it('⛔ no card is declared twice inside one composition', () => {
    for (const composition of COMPOSITIONS) {
      const ids = COMPOSITION_CARDS[composition];
      expect(new Set(ids).size, `${composition} repeats a card`).toBe(ids.length);
    }
  });
});

describe('⚠️ the registry is empty, and the emptiness is asserted rather than assumed', () => {
  it('⛔ no module contributes a card yet', () => {
    /**
     * 🔴 **This test states today's truth so the day it changes is loud** — the
     * device `route-map.test.ts` uses for the absent `/w/` tree. **When the
     * first module ships a card this fails, and whoever lands it updates the
     * count deliberately.**
     */
    expect(REGISTRY).toEqual([]);
  });

  it('✅ so every composition resolves to nothing, and does so without throwing', () => {
    for (const composition of COMPOSITIONS) {
      expect(cardsFor(composition, 'owner')).toEqual([]);
      expect(cardsFor(composition, 'member')).toEqual([]);
      expect(cardsFor(composition, null)).toEqual([]);
    }
  });
});

/**
 * ⚡ **A fixture registry, so the resolver is tested against contributions that
 * do not exist yet.** ⛔ **Not added to `REGISTRY`** — a test fixture reaching
 * production is how a placeholder ships.
 */
const FIXTURE: readonly CardContract[] = [
  { id: 'daily-briefing', title: 'Your briefing', module: 'signal_engine', requires: null },
  { id: 'meetings', title: 'Today', module: 'timeline', requires: null },
  {
    id: 'needs-you-today',
    title: 'Needs you today',
    module: 'buying_score_engine',
    requires: 'member:add',
  },
  // ⚡ Registered, and named by the EXECUTIVE composition — so it must not
  // appear when the seller composition is resolved.
  { id: 'top-risks', title: 'Top risks', module: 'opportunity_engine', requires: null },
];

describe('📁 a composition is a filtered, ordered read of the registry', () => {
  it('✅ returns only cards the composition names', () => {
    const seller = cardsFor('seller', 'owner', FIXTURE).map((c) => c.id);
    expect(seller).not.toContain('top-risks');
    expect(seller).toContain('daily-briefing');
  });

  it('⛔ order is the DESIGN\'s, never the registry\'s', () => {
    /**
     * ⚡ **The fixture is deliberately out of order**: it lists `daily-briefing`,
     * `meetings`, then `needs-you-today`. 📁 The design's seller order puts
     * `needs-you-today` SECOND and `meetings` fourth. **If this returned the
     * registry's order the assertion below would read `meetings` first.**
     */
    const seller = cardsFor('seller', 'owner', FIXTURE).map((c) => c.id);
    expect(seller).toEqual(['daily-briefing', 'needs-you-today', 'meetings']);
  });

  it('⛔ a card the composition names but nobody contributed is SKIPPED, not rendered empty', () => {
    // 📁 The seller composition names six cards; the fixture contributes three
    // of them. ⚡ The other three are absent rather than present-and-blank.
    expect(COMPOSITION_CARDS.seller).toHaveLength(6);
    expect(cardsFor('seller', 'owner', FIXTURE)).toHaveLength(3);
  });
});

describe('🔴 the filter is presentational, and it fails closed', () => {
  it('⛔ a card requiring a capability is hidden from a role without it', () => {
    const owner = cardsFor('seller', 'owner', FIXTURE).map((c) => c.id);
    const member = cardsFor('seller', 'member', FIXTURE).map((c) => c.id);

    // ⚡ **Vacuity guard.** If `needs-you-today` stopped requiring anything,
    // both lists would match and this test would assert nothing.
    expect(owner).toContain('needs-you-today');
    expect(member).not.toContain('needs-you-today');
    expect(member).toContain('daily-briefing');
  });

  it('⛔ an unresolved role sees only what needs no capability', () => {
    // 📁 `can(null, …)` is false by construction — *"fail closed: showing a
    // control and then removing it reads as a bug."* ⚡ A card with
    // `requires: null` is still shown, because null means *every member*, and
    // withholding it would blank Home during every page load.
    const unresolved = cardsFor('seller', null, FIXTURE).map((c) => c.id);
    expect(unresolved).toEqual(['daily-briefing', 'meetings']);
  });

});
