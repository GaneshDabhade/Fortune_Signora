import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { COMPOSITION_QUESTION, type Composition } from '@/lib/home/composition';
import {
  CARD_IDS,
  COMPOSITION_CARDS,
  REGISTRY,
  cardsFor,
  forbidden,
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

describe('✅ the registry is no longer empty, and the day it changed was made loud on purpose', () => {
  /**
   * 🔴 **This block asserted `REGISTRY` was `[]`**, with its own note: *"this
   * test states today's truth so the day it changes is loud — when the first
   * module ships a card this fails, and whoever lands it updates the count
   * deliberately."*
   *
   * ✅ **[TASK-1425](../../../docs/BACKLOG.md) is that day**, and the
   * assertion did exactly its job: it went red the moment `pipeline-health`
   * was contributed. ⚡ **The device worked, so it is replaced by the rule it
   * was standing in for rather than deleted.**
   */
  it('🔴 the first contributed card is Pipeline health', () => {
    expect(REGISTRY.map((card) => card.id)).toContain('pipeline-health');
  });

  it('⛔ every contributed card names a module and the design’s own title', () => {
    // ⚡ **The contract's rule, not a style check** — *"the design's own words
    // for it. Never a module's paraphrase."*
    for (const card of REGISTRY) {
      expect(card.module.length).toBeGreaterThan(2);
      expect(card.title.length).toBeGreaterThan(2);
    }
  });

  it('⚠️ and a contributed card reaches at least one composition', () => {
    // ⛔ **A card in the registry that no composition shows is a module that
    // shipped something nobody will ever see.**
    const reachable = COMPOSITIONS.flatMap((c) => cardsFor(c, 'owner').map((card) => card.id));
    for (const card of REGISTRY) {
      expect(reachable, `${card.id} reaches no composition`).toContain(card.id);
    }
  });

  it('✅ every composition still resolves without throwing, for every role', () => {
    // ⚠️ **This asserted every composition resolved to NOTHING.** ⛔ That was a
    // statement about the registry rather than about `cardsFor`, and it stopped
    // being true by design. ✅ **What it was really guarding is that resolution
    // never throws and never leaks a card into a composition that does not name
    // it** — asserted directly now.
    for (const composition of COMPOSITIONS) {
      for (const role of ['owner', 'member', null] as const) {
        const placed = cardsFor(composition, role).map((card) => card.id);
        for (const id of placed) {
          expect(COMPOSITION_CARDS[composition]).toContain(id);
        }
      }
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
    /**
     * 📁 **The seller composition names FIVE cards**, and this asserted six.
     *
     * ⚠️ **Six was the Authenticated Entry document's list** — *"Daily
     * briefing, Needs you today, **Signals on my accounts**, Meetings, AI
     * drafts awaiting approval, Recent work"*. ⛔ **Home is the composition
     * authority**, and its registry carries `SE` on exactly five rows:
     * `card.briefing`, `card.attention`, `card.meetings`, `card.agentqueue`,
     * `card.recents`. **`Signals on my accounts` is not one of them.**
     *
     * ⚡ The fixture contributes three; the other two are absent rather than
     * present-and-blank, which is the property this test exists for.
     */
    expect(COMPOSITION_CARDS.seller).toHaveLength(5);
    expect(cardsFor('seller', 'owner', FIXTURE)).toHaveLength(3);
  });
});

describe('🔴 a card the caller cannot act on is MARKED, never removed', () => {
  /**
   * 🔴 **This asserted the opposite and the design says so by name.**
   *
   * 📁 **State 09**: *"the card is replaced in place by a same-footprint panel
   * naming the missing permission and the approvers. **Never hidden — hiding it
   * makes people think the capability is absent.**"* 📁 **P-11**: *"hidden
   * capability is the most common cause of 'the product does not do X' when it
   * does."*
   *
   * ⚡ **The old assertion was the RAIL's rule** — *"a link the caller cannot
   * follow is not rendered"* — **applied to a card, which is a different
   * object**: a dead link wastes a click, and an absent card teaches somebody
   * the product cannot do something it can.
   */
  it('🔴 the composition keeps a card whatever the role', () => {
    const owner = cardsFor('seller', 'owner', FIXTURE).map((c) => c.id);
    const member = cardsFor('seller', 'member', FIXTURE).map((c) => c.id);

    expect(member).toEqual(owner);
    expect(member).toContain('needs-you-today');
  });

  it('⚡ and says which one is barred', () => {
    const card = FIXTURE.find((entry) => entry.id === 'needs-you-today')!;

    // ⚡ **Vacuity guard.** If `needs-you-today` stopped requiring anything,
    // both answers would be `false` and this would assert nothing.
    expect(card.requires).not.toBeNull();
    expect(forbidden(card, 'owner')).toBe(false);
    expect(forbidden(card, 'member')).toBe(true);
  });

  it('⛔ a card needing nothing is barred from nobody', () => {
    const card = FIXTURE.find((entry) => entry.id === 'daily-briefing')!;

    expect(forbidden(card, 'member')).toBe(false);
    expect(forbidden(card, null)).toBe(false);
  });

  it('⛔ and an unresolved role fails closed', () => {
    // 📁 `can(null, …)` is false by construction — *"fail closed: showing a
    // control and then removing it reads as a bug."* ⚡ **The card still
    // renders**; what it renders is the forbidden panel until the role lands.
    const card = FIXTURE.find((entry) => entry.id === 'needs-you-today')!;

    expect(cardsFor('seller', null, FIXTURE).map((c) => c.id)).toContain('needs-you-today');
    expect(forbidden(card, null)).toBe(true);
  });
});


/**
 * 🔴 **Contract item 3, which asks for this in its own words.**
 *
 * > 📁 *"No code path navigates away from Home because a card has no data.
 * > **Grep for redirects in the Home module before merge.**"*
 *
 * ⚡ **A contract that names a grep is a contract asking to be a test.** ⛔ *"Before
 * merge"* is a person remembering, and 📁 `P-03` is what it protects: *"Home never
 * falls back to another surface… an undocumented alternate Home cannot be tested,
 * predicted or supported."*
 *
 * ⚠️ **`home.tsx` already says *"there is no `router.push` in this file and there
 * must never be one"*** — **a comment, which is the shape [§2](../../../CLAUDE.md)
 * calls documentation pretending to be code.**
 */
describe('📁 contract 3 — Home never navigates away', () => {
  const HOME_SOURCES = [
    ...readdirSync(join(process.cwd(), 'components', 'home'))
      .filter((file) => file.endsWith('.tsx'))
      .map((file) => ({
        name: `components/home/${file}`,
        source: readFileSync(join(process.cwd(), 'components', 'home', file), 'utf8'),
      })),
    ...readdirSync(join(process.cwd(), 'app', '(app)', 'w', '[workspace]', 'home'))
      .filter((file) => file.endsWith('.tsx'))
      .map((file) => ({
        name: `app/(app)/w/[workspace]/home/${file}`,
        source: readFileSync(
          join(process.cwd(), 'app', '(app)', 'w', '[workspace]', 'home', file),
          'utf8',
        ),
      })),
  ];

  /** ⛔ Comments quote the rule; **only code can break it.** */
  const code = (source: string) =>
    source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/[^\n]*/g, '$1');

  it('🔴 no file in the Home module calls a router', () => {
    const offenders = HOME_SOURCES.filter(({ source }) =>
      /\brouter\s*\.\s*(?:push|replace|back|forward)\s*\(/.test(code(source)),
    ).map(({ name }) => name);

    expect(
      offenders,
      'Home navigating away is the fallback P-03 forbids — a designed empty state, always',
    ).toEqual([]);
  });

  it('⛔ and none calls a server redirect either', () => {
    const offenders = HOME_SOURCES.filter(({ source }) => /\bredirect\s*\(/.test(code(source)))
      .map(({ name }) => name);

    expect(offenders).toEqual([]);
  });

  /**
   * ⚡ **The vacuity guard.** ⛔ If the file list ever came back empty — a renamed
   * directory, a changed layout — both assertions above would pass while checking
   * nothing.
   */
  it('⚡ and the check is looking at the Home module at all', () => {
    expect(HOME_SOURCES.length).toBeGreaterThan(10);
    expect(HOME_SOURCES.map((entry) => entry.name)).toContain(
      'app/(app)/w/[workspace]/home/home.tsx',
    );
  });
});

describe('🔴 the card registry names the module that actually produces the card', () => {
  /**
   * ⛔ **`top-risks` and `top-opportunities` said `signal_engine`** — the
   * module a note in the same file records a previous audit searching, finding
   * no risk/opportunity classification in, and wrongly concluding the cards
   * were unbuildable.
   *
   * ⚡ **Measured**: `GET /workspaces/{id}/scoring-model` is `buying_score_engine`'s,
   * and `signal_engine` serves triage, catalog, decisions and resolution —
   * **no posture among them.**
   *
   * ⚠️ **The correction was written and never applied to the two lines it
   * described**, because the note said *"the module named below"* and four
   * unrelated cards had grown in between. ⛔ **Nothing reads `module` at
   * runtime, so no behaviour broke** — but its stated purpose is *"so a broken
   * one has an owner without a `git blame`"*, and it pointed at the module with
   * no producer.
   */
  it('attributes the posture cards to the engine that judges posture', () => {
    for (const id of ['top-risks', 'top-opportunities'] as const) {
      const card = REGISTRY.find((c) => c.id === id);
      expect(card, `${id} is not registered`).toBeDefined();
      expect(card?.module, `${id} names the wrong producer`).toBe('buying_score_engine');
    }
  });
});
