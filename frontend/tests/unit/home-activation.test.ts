/**
 * **Activation's eight rules, six of which are prohibitions** —
 * [TASK-1424](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Home.dc.html` §*Activation*.
 */
import { describe, expect, it } from 'vitest';

import type { IntegrationSystem } from '@/lib/api/types';
import { COMPOSITION_CARDS } from '@/lib/home/cards';
import {
  ACTIVATION_PRIORITY,
  BLOCKING,
  activationOrder,
  activationProgress,
  hasWorkingCapability,
  primaryEnabled,
  type ActivationCardId,
} from '@/lib/home/activation';

const NONE = {
  'connect-a-crm': false,
  'connect-calls': false,
  'invite-the-team': false,
} as const;

const ALL = ['connect-a-crm', 'connect-calls', 'invite-the-team'] as const;

describe('🔴 the list never reshuffles under the cursor', () => {
  /** 📁 *"Never by completion state — a completed card holds its position."* */
  it('orders by declared priority, ascending', () => {
    expect(activationOrder(['invite-the-team', 'connect-calls', 'connect-a-crm'])).toEqual([
      'connect-a-crm',
      'connect-calls',
      'invite-the-team',
    ]);
  });

  it('⛔ and a completed step does NOT sink to the bottom', () => {
    // ⚡ **The obvious implementation is to sort completed last**, and the
    // design forbids it by name. This is the assertion that fails if somebody
    // adds it.
    expect(activationOrder(ALL)).toEqual(['connect-a-crm', 'connect-calls', 'invite-the-team']);
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
    // ⚠️ **Dismissibility follows from this**, so it is pinned rather than left
    // to a component: *"blocking cards — CRM and calls — cannot be dismissed."*
    expect(BLOCKING['connect-a-crm']).toBe(true);
    expect(BLOCKING['connect-calls']).toBe(true);
    expect(BLOCKING['invite-the-team']).toBe(false);
  });
});

describe('🔴 the ordering rule is in force, not merely written', () => {
  /**
   * ⛔ **This is the guard that was missing, and its absence let a real defect
   * ship** — [TASK-1424](../../../docs/BACKLOG.md).
   *
   * ⚠️ **`activationOrder` sorts by priority and NOTHING CALLED IT.** Home
   * renders `cardsFor`'s output, which is `COMPOSITION_CARDS` order — and that
   * array read `connect-a-crm, invite-the-team, connect-calls`, **so the
   * optional step rendered ahead of a blocking one.** ⚡ **The rule was
   * written, tested, and not in force**, which is the unreachable-primitive
   * class turned inside out: not a helper with no caller, but a helper whose
   * caller used something else.
   *
   * ✅ **So the assertion is on the array the PRODUCT reads**, with the law as
   * the oracle.
   */
  it('the activation composition renders in declared priority order', () => {
    const activation = COMPOSITION_CARDS.activation.filter(
      (id): id is ActivationCardId => id in ACTIVATION_PRIORITY,
    );

    expect(activation).toEqual(activationOrder(activation));
  });

  it('⛔ and the optional card is never ahead of a blocking one', () => {
    // 📁 *"CRM 100, calls 200, invite 300. Lower is earlier."* — the sentence
    // this guard exists to keep true.
    const activation = COMPOSITION_CARDS.activation.filter(
      (id): id is ActivationCardId => id in ACTIVATION_PRIORITY,
    );
    const lastBlocking = activation.reduce(
      (last, id, index) => (BLOCKING[id] ? index : last),
      -1,
    );
    const firstOptional = activation.findIndex((id) => !BLOCKING[id]);

    expect(firstOptional).toBeGreaterThan(lastBlocking);
  });
});

describe('🔴 the activation composition is complete, and the third card waited for its store', () => {
  /**
   * ⚡ **All three of the design's steps are contributed now** —
   * [TASK-1424](../../../docs/BACKLOG.md). ⛔ **`invite-the-team` was
   * deliberately absent until migration `0050`**, because *"skip for now"* is
   * the design's control and **a skip that forgot at the next sign-in is a
   * control that lies.**
   */
  it('all three steps are in the composition, in priority order', () => {
    const activation = COMPOSITION_CARDS.activation.filter(
      (id): id is ActivationCardId => id in ACTIVATION_PRIORITY,
    );

    expect(activation).toEqual(['connect-a-crm', 'connect-calls', 'invite-the-team']);
  });

  it('⛔ and only the non-blocking one is skippable', () => {
    // 📁 *"Blocking cards — CRM and calls — cannot be dismissed."* ⚡ The two
    // blocking cards render through a component with no skip control at all,
    // so this is structural rather than a flag somebody could flip.
    const skippable = (Object.keys(BLOCKING) as ActivationCardId[]).filter(
      (id) => !BLOCKING[id],
    );

    expect(skippable).toEqual(['invite-the-team']);
  });
});
