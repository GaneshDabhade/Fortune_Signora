/**
 * **The activation composition's rules** — [TASK-1424](../../../docs/BACKLOG.md),
 * against 📁 `Fortune Signora Home.dc.html` §*Activation*.
 *
 * ⚡ **The design writes eight rules for activation and six of them are about
 * what must NOT happen.** ⛔ *"Never by completion state"* · *"it never
 * disappears"* · *"never stored on Home"* · *"Home never embeds a connection
 * wizard"* · *"nothing about activation lives in localStorage"* · *"never a
 * duplicate route to the same flow."* ✅ **A rule shaped like that needs a
 * function that can fail a test, not a comment in a component.**
 */

import type { IntegrationSystem } from '@/lib/api/types';

/**
 * 📁 ***"CRM 100, calls 200, invite 300. Lower is earlier. A new source
 * declares its own integer; Home does not know the set in advance."***
 *
 * ⚡ **The last sentence is why this is an integer and not an array index** —
 * **a source declares where it belongs**, and Home sorts what it is given.
 */
export const ACTIVATION_PRIORITY = {
  'connect-a-crm': 100,
  'connect-calls': 200,
  'invite-the-team': 300,
} as const;

export type ActivationCardId = keyof typeof ACTIVATION_PRIORITY;

/**
 * 📁 **The activation composition's whole set**, in the registry's order.
 *
 * ⚠️ **Two components each held a private copy of this array** and a third was
 * about to. ⛔ A set that must agree with {@link ACTIVATION_PRIORITY}'s keys and
 * is written out by hand beside it is the duplication §2 names.
 */
export const ACTIVATION_CARDS: readonly ActivationCardId[] = Object.freeze([
  'connect-a-crm',
  'connect-calls',
  'invite-the-team',
]);

/**
 * 🔴 **Ordering, and the rule that makes it safe.**
 *
 * 📁 ***"By the registry's declared priority integer, ascending. Ties broken by
 * registry order. NEVER by completion state — a completed card holds its
 * position rather than moving to the bottom, so the list does not reshuffle
 * under the cursor."***
 *
 * ⛔ **Sinking completed steps is the obvious implementation and the design
 * forbids it by name.** ⚡ A person who has just finished step 1 would watch it
 * move while their pointer was on it.
 */
export function activationOrder(
  cards: readonly ActivationCardId[],
): readonly ActivationCardId[] {
  // ⚠️ **A stable sort, and `toSorted` would be fine too** — what matters is
  // that ties keep registry order rather than becoming arbitrary.
  return [...cards].sort((a, b) => ACTIVATION_PRIORITY[a] - ACTIVATION_PRIORITY[b]);
}

/**
 * 📁 ***"Completion is derived from the source of truth, never stored on
 * Home."***
 *
 * ⚠️ **What the frontend can actually see, stated rather than glossed.** The
 * design's test is *"CRM complete means one sync has finished with a non-error
 * status"*. ⛔ **No read publishes a sync outcome per system**; what
 * `IntegrationSystem` publishes is `working`, whose own contract is **"at least
 * one connection Signora can currently use — not merely present"** — ✅ **which
 * is a stronger claim than a sync having finished, not a weaker one.**
 *
 * ⛔ **`state` is deliberately not used.** 📁 Its own type says why: *"a
 * credential that quietly lost a permission holds a perfect state and does not
 * work."*
 */
export function hasWorkingCapability(
  systems: readonly IntegrationSystem[] | undefined,
  capability: IntegrationSystem['capabilities'][number],
): boolean {
  return (systems ?? []).some(
    (system) => system.working && system.capabilities.includes(capability),
  );
}

/**
 * 🔴 **The soft dependency, and it is a rendering rule rather than a filter.**
 *
 * 📁 ***"Calls declares a soft dependency on CRM: it RENDERS before CRM
 * completes but its primary action is disabled with the reason 'connect a CRM
 * first, so calls can be matched to accounts'. Invite has none."***
 *
 * ⛔ **So an unmet dependency must never remove the card** — ⚡ hiding step 2
 * until step 1 is done is what makes a three-step list look like a one-step
 * list, and the design's whole activation model is that a person can see the
 * shape of what is ahead.
 */
export const DEPENDS_ON: Partial<Record<ActivationCardId, ActivationCardId>> = {
  'connect-calls': 'connect-a-crm',
};

/** 📁 The design's own sentence, verbatim, so the reason a control is disabled
 * is the reason the design gives. */
export const DEPENDENCY_REASON: Partial<Record<ActivationCardId, string>> = {
  'connect-calls': 'Connect a CRM first, so calls can be matched to accounts.',
};

export function primaryEnabled(
  card: ActivationCardId,
  complete: Readonly<Record<ActivationCardId, boolean>>,
): boolean {
  const needs = DEPENDS_ON[card];
  // ⛔ **A completed card has no primary at all** — 📁 *"it loses its
  // primary"* — so this answers only for the incomplete ones.
  if (complete[card]) return false;
  return needs === undefined || complete[needs];
}

/**
 * 🔴 **Which cards can be dismissed, and the answer is a property of the card
 * rather than a preference.**
 *
 * 📁 ***"Blocking cards — CRM and calls — cannot be dismissed. Non-blocking
 * cards can be skipped."***
 */
export const BLOCKING: Readonly<Record<ActivationCardId, boolean>> = {
  'connect-a-crm': true,
  'connect-calls': true,
  'invite-the-team': false,
};

/**
 * 📁 ***"Progress counts blocking cards only. 'Step 2 of 3' with an optional
 * card present reads 'Step 2 of 2 · 1 optional'."***
 *
 * ⚡ **The optional count is carried rather than dropped**, because the design
 * shows it in the same line.
 */
export interface ActivationProgress {
  readonly done: number;
  readonly total: number;
  readonly optional: number;
}

export function activationProgress(
  cards: readonly ActivationCardId[],
  complete: Readonly<Record<ActivationCardId, boolean>>,
): ActivationProgress {
  const blocking = cards.filter((card) => BLOCKING[card]);
  return {
    done: blocking.filter((card) => complete[card]).length,
    total: blocking.length,
    optional: cards.length - blocking.length,
  };
}
