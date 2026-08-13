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
 * ⛔ **`STEPUP_REQUIRED`'s challenge is [TASK-1410](../../../docs/BACKLOG.md)'s**,
 * and the screen ships so that capability has somewhere to land.
 *
 * ## 🔴 `ACCOUNT_LOCKED` is NOT here, and the reason is a mistake worth recording
 *
 * ⚠️ **[TASK-1467](../../../docs/BACKLOG.md) already shipped `/auth/locked`**,
 * against `Authentication.dc.html` §11, **with copy this table could not
 * match**: it says the lock *"unlocks on its own"* and that **nobody has been
 * signed in** — 📁 *"the fear a lock actually creates"*. ⛔ **This lane
 * overwrote that file while moving its own route into place**, and
 * `account-locked.test.tsx` caught it. ✅ **The shipped screen is restored and
 * this table does not name the reason**, because **a generic gate is a
 * regression against a designed one.**
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

/**
 * 🔴 **WL-08 · a workspace scheduled for deletion, and the one rule the design
 * states twice as strongly as any other** —
 * [TASK-1423](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Workspace Lifecycle.dc.html`.
 *
 * > ***"The purge date is a DATE, never '30 days'. A relative window read on
 * > day 29 is indistinguishable from one read on day 1, and this is the last
 * > screen where that ambiguity is affordable."***
 *
 * ⛔ **So this contract carries an instant and no duration**, and there is no
 * field a caller could pass a *"30 days"* through. ⚡ **The rule is
 * unrepresentable rather than merely tested.**
 */
export interface ScheduledDeletion {
  /** 📁 *"Meridian Freight is scheduled for deletion"* — the organization's own name. */
  readonly organization: string;
  /** 📁 *"Deleted by K. Bruun"* — ⛔ a person, because *"deleted by the system"* is
   * a different sentence and this state is always somebody's decision. */
  readonly deletedBy: string;
  /** 📁 *"on 13 August"* — when the decision was taken. */
  readonly deletedOn: string;
  /**
   * 📁 *"Data is retained until 12 September, after which it cannot be
   * recovered."* ⛔ **An instant, never a window.** ⚡ A caller holding only
   * *"30 days"* cannot construct this, which is the point.
   */
  readonly retainedUntil: string;
}

/**
 * ⚡ **What a member may do about it, and it is not what an owner may do.**
 *
 * 📁 The design's own header: *"WL-08 · DELETING, member view"* with
 * ***"Owner sees a restore action"*** beside it. ⛔ **So restore is offered to
 * owners only** — and a member shown a restore button would be shown a control
 * that refuses them, on the screen telling them their data is going away.
 */
export function deletionActions(isOwner: boolean): readonly string[] {
  // 📁 The design lists three, and the first is owner-only.
  return isOwner
    ? ['Restore it', 'Export everything', 'Your other organizations']
    : ['Export everything', 'Your other organizations'];
}
