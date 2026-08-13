/**
 * **Activation's eight rules, six of which are prohibitions** —
 * [TASK-1424](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Home.dc.html` §*Activation*.
 */
import { describe, expect, it } from 'vitest';

import type { IntegrationSystem } from '@/lib/api/types';
import {
  BLOCKING,
  activationOrder,
  activationProgress,
  hasWorkingCapability,
  primaryEnabled,
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
