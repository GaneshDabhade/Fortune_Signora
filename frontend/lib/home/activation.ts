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

import type { ActivationStep, IntegrationSystem } from '@/lib/api/types';

/**
 * 🔴 **The card each declared step is drawn as.**
 *
 * 📁 **The registry now comes from the server** — contract 5, *"the activation
 * registry is fetched from the server; card order comes from its priority
 * integer, not from array position"* — so this file no longer holds the set,
 * the order or which steps block. ⚡ **What stays here is the translation**: the
 * server speaks capabilities and membership, a customer reads *"connect a
 * CRM"*, and 📁 [ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)
 * puts that at the frontend edge and nowhere further in.
 *
 * ⚠️ **A step with no entry here is dropped rather than guessed at.** ⛔ A card
 * needs its own heading, its reason and the flow it opens, and none of those
 * can be invented from an identifier. **The backend's own registry test asserts
 * its exact contents**, so adding a step there fails a test that says to add a
 * card here.
 */
export const CARD_FOR_STEP: Readonly<Record<string, ActivationCardId>> = {
  crm_activity: 'connect-a-crm',
  meetings: 'connect-calls',
  invite_members: 'invite-the-team',
};

export type ActivationCardId = 'connect-a-crm' | 'connect-calls' | 'invite-the-team';

/**
 * 🔴 **The registry as Home reads it** — the two servers' declarations,
 * translated, ordered, and with anything Home cannot draw removed.
 */
export interface ActivationEntry {
  readonly card: ActivationCardId;
  readonly priority: number;
  readonly blocking: boolean;
}

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
 * move while their pointer was on it — which is also why this takes no
 * completion argument at all: it has nothing to sink them with.
 *
 * ⚡ **Two modules declare, and neither can see the other's integers.** 📁 The
 * design's *"a new source declares its own integer; Home does not know the set
 * in advance"* is exactly what makes composing them safe — Home sorts what it
 * is given rather than knowing where anything belongs.
 */
export function activationRegistry(
  ...declarations: readonly (readonly ActivationStep[] | undefined)[]
): readonly ActivationEntry[] {
  const entries = declarations
    .flatMap((steps) => steps ?? [])
    .flatMap((step) => {
      const card = CARD_FOR_STEP[step.id];
      // ⛔ **A step Home has no card for is dropped, and it is dropped from the
      // COUNT as well** — 📁 progress that included a step nobody could see
      // would read *"1 of 3"* beside two cards, which is worse than the step
      // being absent.
      return card === undefined ? [] : [{ card, priority: step.priority, blocking: step.blocking }];
    });
  // ⚠️ **A stable sort**, so ties keep the order the declarations arrived in
  // rather than becoming arbitrary.
  return entries.sort((a, b) => a.priority - b.priority);
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
  registry: readonly ActivationEntry[],
  complete: Readonly<Record<ActivationCardId, boolean>>,
): ActivationProgress {
  // 📁 *"Blocking cards — CRM and calls — cannot be dismissed."* ⚡ **Which
  // cards those are is the declaring module's answer now**, not a constant
  // here, so a step that stops blocking stops being counted without Home
  // shipping.
  const blocking = registry.filter((entry) => entry.blocking);
  return {
    done: blocking.filter((entry) => complete[entry.card]).length,
    total: blocking.length,
    optional: registry.length - blocking.length,
  };
}
