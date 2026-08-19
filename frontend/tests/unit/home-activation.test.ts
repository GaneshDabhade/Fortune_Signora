/**
 * **Activation's eight rules, six of which are prohibitions** —
 * [TASK-1424](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Home.dc.html` §*Activation*.
 */
import { describe, expect, it } from 'vitest';

import type { IntegrationSystem } from '@/lib/api/types';
import { COMPOSITION_CARDS } from '@/lib/home/cards';
import {
  CARD_FOR_STEP,
  activationProgress,
  activationRegistry,
  hasWorkingCapability,
  primaryEnabled,
} from '@/lib/home/activation';
import type { ActivationStep } from '@/lib/api/types';

/**
 * 🔴 **What the two servers declare**, verbatim from the API tests that pin
 * them — 📁 contract 5, *"the activation registry is fetched from the server."*
 *
 * ⛔ **Written out rather than imported**, because the point of these
 * assertions is what Home does with a declaration it did not choose.
 */
const CONNECTIONS: readonly ActivationStep[] = [
  { id: 'crm_activity', priority: 100, blocking: true },
  { id: 'meetings', priority: 200, blocking: true },
];
const MEMBERSHIP: readonly ActivationStep[] = [
  { id: 'invite_members', priority: 300, blocking: false },
];

const NONE = {
  'connect-a-crm': false,
  'connect-calls': false,
  'invite-the-team': false,
} as const;

const ALL = activationRegistry(CONNECTIONS, MEMBERSHIP);

describe('🔴 the list never reshuffles under the cursor', () => {
  /** 📁 *"Never by completion state — a completed card holds its position."* */
  it('orders by declared priority, ascending', () => {
    // ⚡ **Deliberately handed to it backwards**, and from the membership
    // module first — 📁 *"card order comes from its priority integer, not from
    // array position"*, so the arrival order must not survive.
    expect(activationRegistry(MEMBERSHIP, CONNECTIONS).map((entry) => entry.card)).toEqual([
      'connect-a-crm',
      'connect-calls',
      'invite-the-team',
    ]);
  });

  it('⛔ takes no completion argument at all, so it cannot sink a finished step', () => {
    // ⚡ **The obvious implementation is to sort completed last**, and the
    // design forbids it by name. ✅ **Made unrepresentable rather than
    // asserted**: the function has nothing to sink them with.
    expect(activationRegistry(CONNECTIONS, MEMBERSHIP)).toEqual(
      activationRegistry(MEMBERSHIP, CONNECTIONS),
    );
  });

  it('⛔ a step Home has no card for is dropped rather than guessed at', () => {
    // ⚠️ **And dropped from the COUNT as well** — progress that included a
    // step nobody could see would read "1 of 3" beside two cards.
    const registry = activationRegistry(
      [...CONNECTIONS, { id: 'something_new', priority: 150, blocking: true }],
      MEMBERSHIP,
    );

    expect(registry.map((entry) => entry.card)).toEqual([
      'connect-a-crm',
      'connect-calls',
      'invite-the-team',
    ]);
  });

  it('🔴 an empty registry is empty, which is what makes state 12 reachable', () => {
    // 📁 `AC-H09` — *"return the activation registry as an empty array:
    // HM-COPY-11 renders and no progress bar is present."* ⛔ **A frozen
    // client-side array made this impossible**, which is why the design puts
    // the registry on the server.
    expect(activationRegistry([], [])).toEqual([]);
    expect(activationRegistry(undefined, undefined)).toEqual([]);
  });
});

describe('📁 completion is derived from the source of truth', () => {
  const system = (over: Partial<IntegrationSystem>): IntegrationSystem => ({
    integration: 'salesforce',
    capabilities: ['crm_activity'],
    connectable: true,
    working: true,
    needs_attention: false,
    connections: [],
    ...over,
  });

  it('a working system carrying the capability completes the step', () => {
    expect(hasWorkingCapability([system({})], 'crm_activity')).toBe(true);
    expect(hasWorkingCapability([system({ capabilities: ['meetings'] })], 'meetings')).toBe(true);
  });

  it('⛔ a connection that is present but not WORKING completes nothing', () => {
    // 📁 `ConnectionHealth`'s own sentence: *"a credential that quietly lost a
    // permission holds a perfect state and does not work."*
    expect(hasWorkingCapability([system({ working: false })], 'crm_activity')).toBe(false);
  });

  it('⚠️ and an absent read is not a completed step', () => {
    // ⛔ P-A: not-yet-known must never render as an answer.
    expect(hasWorkingCapability(undefined, 'crm_activity')).toBe(false);
    expect(hasWorkingCapability([], 'crm_activity')).toBe(false);
  });
});

describe('🔴 the soft dependency disables a control, it never hides a card', () => {
  /** 📁 *"It RENDERS before CRM completes but its primary action is disabled."* */
  it('calls cannot be started until the CRM is connected', () => {
    expect(primaryEnabled('connect-calls', NONE)).toBe(false);
    expect(primaryEnabled('connect-calls', { ...NONE, 'connect-a-crm': true })).toBe(true);
  });

  it('the CRM step and the invite step depend on nothing', () => {
    expect(primaryEnabled('connect-a-crm', NONE)).toBe(true);
    expect(primaryEnabled('invite-the-team', NONE)).toBe(true);
  });

  it('⛔ a completed card has no primary at all', () => {
    // 📁 *"It keeps a secondary action into the owning module, and loses its
    // primary."*
    expect(primaryEnabled('connect-a-crm', { ...NONE, 'connect-a-crm': true })).toBe(false);
  });
});

describe('📁 progress counts blocking cards only', () => {
  it('"Step 1 of 2 · 1 optional" rather than "1 of 3"', () => {
    expect(activationProgress(ALL, { ...NONE, 'connect-a-crm': true })).toEqual({
      done: 1,
      total: 2,
      optional: 1,
    });
  });

  it('⛔ and the optional card can never block completion', () => {
    const bothBlocking = { ...NONE, 'connect-a-crm': true, 'connect-calls': true };
    const progress = activationProgress(ALL, bothBlocking);
    expect(progress.done).toBe(progress.total);
  });

  it('🔴 the two blocking steps are the two the design names', () => {
    // ⚠️ **Dismissibility follows from this** — *"blocking cards — CRM and
    // calls — cannot be dismissed"* — ⚡ **and it is the declaring module's
    // answer now**, so what this pins is that Home carries it through rather
    // than deciding it.
    const blocking = ALL.filter((entry) => entry.blocking).map((entry) => entry.card);

    expect(blocking).toEqual(['connect-a-crm', 'connect-calls']);
  });
});

describe('🔴 the ordering rule is in force, not merely written', () => {
  /**
   * ⛔ **This is the guard that was missing, and its absence let a real defect
   * ship** — [TASK-1424](../../../docs/BACKLOG.md).
   *
   * ⚠️ **The order helper sorted by priority and NOTHING CALLED IT.** Home
   * rendered `COMPOSITION_CARDS` order, and that array read `connect-a-crm,
   * invite-the-team, connect-calls`, **so the optional step rendered ahead of a
   * blocking one.** ⚡ **The rule was written, tested, and not in force.**
   *
   * ✅ **Now the product reads exactly what this function returns**, so the
   * assertion and the render path are the same thing.
   */
  it('the optional step is never ahead of a blocking one', () => {
    const registry = activationRegistry(CONNECTIONS, MEMBERSHIP);
    const lastBlocking = registry.reduce(
      (last, entry, index) => (entry.blocking ? index : last),
      -1,
    );
    const firstOptional = registry.findIndex((entry) => !entry.blocking);

    expect(firstOptional).toBeGreaterThan(lastBlocking);
  });

  /**
   * 🔴 **The server may only ask for cards the design drew.**
   *
   * ⚡ `contractsFor` drops an id no module has contributed, so a step for a
   * card that does not exist is already harmless — ⛔ **this is the assertion
   * that says so out loud**, because a silently dropped step is a step nobody
   * would notice was missing.
   */
  it('every step the two modules declare maps to a card in the composition', () => {
    const declared = [...CONNECTIONS, ...MEMBERSHIP].map((step) => CARD_FOR_STEP[step.id]);

    expect(declared.every((card) => card !== undefined)).toBe(true);
    for (const card of declared) {
      expect(COMPOSITION_CARDS.activation).toContain(card!);
    }
  });

  it('⛔ and only the non-blocking one is skippable', () => {
    // 📁 *"Blocking cards — CRM and calls — cannot be dismissed."* ⚡ The two
    // blocking cards render through a component with no skip control at all,
    // so this is structural rather than a flag somebody could flip.
    const skippable = activationRegistry(CONNECTIONS, MEMBERSHIP)
      .filter((entry) => !entry.blocking)
      .map((entry) => entry.card);

    expect(skippable).toEqual(['invite-the-team']);
  });
});
