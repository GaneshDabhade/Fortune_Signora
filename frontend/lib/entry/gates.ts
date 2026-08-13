/**
 * **What a refused gate says** — [TASK-1423](../../../docs/BACKLOG.md), against
 * 📁 `Fortune Signora Security Gates.dc.html`, `Workspace Lifecycle` and
 * `System States`.
 *
 * ## 🔴 The defect this closes
 *
 * 📁 **The spec's central promise: *"each gate depends on the one before it
 * resolving, and a gate that FAILS produces a designed screen."*** ⛔ **Today
 * `resolveEntry` returns a route for eleven terminal reasons and NOT ONE of
 * those routes exists** — measured, not assumed — **so every refusal resolves
 * to a 404.** ⚡ **A person is told nothing about why, on the one screen where
 * the product is refusing them.**
 *
 * ## ⛔ Why this is not [`system-states/ladder.ts`](../system-states/ladder.ts)
 *
 * 📁 **System States are failures of the SYSTEM** — `404`, `403`, `500`.
 * ⚡ **These are refusals of an ENTRY DECISION, and the person is
 * authenticated.** 🔴 **Conflating them produces a `403` where the truth is
 * *your organization is archived***, which tells somebody they lack permission
 * when what they lack is a workspace that still exists.
 *
 * ## ⚠️ Two of these states are currently unreachable, and they still ship
 *
 * ⛔ **`ACCOUNT_LOCKED` has no lockout capability** ([C-431](../../../docs/LANE_COORDINATION.md))
 * and **`STEPUP_REQUIRED`'s challenge is [TASK-1410](../../../docs/BACKLOG.md)'s.**
 * ✅ **The screens exist so that the capability, when it arrives, has somewhere
 * to land** — 📁 and the alternative is the [C-1405](../../../docs/LANE_COORDINATION.md)
 * shape: a rule that resolves to a route nobody built.
 */

/** ⚡ **The terminal reasons this module answers for.** ⛔ Not every reason —
 * `INTENT_HONOURED`, `ONBOARDING` and the composition rules resolve to real
 * destinations and are nobody's refusal. */
export const GATE_REASONS = [
  'ACCOUNT_DELETED',
  'ACCOUNT_SUSPENDED',
  'ACCOUNT_LOCKED',
  'STEPUP_REQUIRED',
  'NO_WORKSPACE',
  'INTENT_NOT_MEMBER',
] as const;

export type GateReason = (typeof GATE_REASONS)[number];

export interface GateCopy {
  /** 📁 **What happened, in the customer's words** — ⛔ never the reason code. */
  readonly title: string;
  /** ⚡ **Why, at the level a person can act on.** */
  readonly body: string;
  /**
   * 🔴 **What they can do, and it is the half a refusal usually omits.**
   * 📁 The spec: *"each states what happened AND what the person can do."*
   * ⛔ **`null` only where the honest answer is *nothing you can do here***,
   * and then the body has to say who can.
   */
  readonly action: { readonly label: string; readonly href: string } | null;
}

/**
 * 📁 **The copy, keyed by the reason the engine already returns.**
 *
 * ⚠️ **Deliberately a table rather than a component per screen.** ⚡ **Eleven
 * screens that differ only in two sentences would drift in their layout, their
 * heading level and their focus order** — 📁 and [`SystemState`](../../components/ui/system-state.tsx)
 * records the same choice one ladder down: *"one presentation of a system
 * state"*.
 */
export const GATE_COPY: Readonly<Record<GateReason, GateCopy>> = {
  ACCOUNT_DELETED: {
    title: 'This account has been deleted',
    body: 'Signora no longer holds a profile for this address. If this was a mistake, the person who administers your organization can invite you again.',
    // ⛔ **No action, and that is the honest answer.** ⚡ There is no self-serve
    // undelete, and offering *"contact support"* as a button would dress a dead
    // end as a route.
    action: null,
  },
  ACCOUNT_SUSPENDED: {
    title: 'This account is suspended',
    body: 'Signora has suspended access to this account. Your organization’s data is untouched, and an administrator can tell you why and restore it.',
    action: null,
  },
  ACCOUNT_LOCKED: {
    title: 'This account is locked',
    body: 'Too many sign-in attempts failed, so Signora locked the account to protect it. Resetting your password unlocks it.',
    // ✅ **A real route** — the reset flow ships, so this refusal has a way out.
    action: { label: 'Reset your password', href: '/forgot-password' },
  },
  STEPUP_REQUIRED: {
    title: 'Confirm it is you',
    body: 'This organization asks for a second check before you go further. It takes a moment and only happens when the policy requires it.',
    // ⚠️ **The route exists as a screen and the CHALLENGE does not yet**
    // (TASK-1410). ⛔ Declared in the row rather than hidden behind a control
    // that would appear to work.
    action: null,
  },
  NO_WORKSPACE: {
    title: 'You are not in an organization yet',
    body: 'Signora works inside an organization. Ask a colleague to invite you, or create one of your own to get started.',
    action: { label: 'Create an organization', href: '/onboarding' },
  },
  INTENT_NOT_MEMBER: {
    title: 'You are not a member of that organization',
    body: 'The link you followed belongs to an organization you are not in. Anyone who administers it can add you.',
    // ✅ **Somewhere real to go**, because this person does have access to
    // something — which is what makes this different from the two above.
    action: { label: 'Go to your organizations', href: '/workspaces' },
  },
};
