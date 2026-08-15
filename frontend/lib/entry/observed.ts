/**
 * **What this product can actually observe, and what it cannot** —
 * [TASK-1401](../../../docs/BACKLOG.md).
 *
 * ## 🔴 The engine is pure, so somebody has to tell it the truth
 *
 * 📁 [`session.ts`](./session.ts) is explicit about why every fact is a field:
 * *"Purity is not achieved by discipline inside the rules — it is achieved by
 * the shape of this type."* ⚡ **That moves the problem rather than solving it.**
 * **A pure engine cannot fetch, so the caller must supply twelve facts** — and
 * ⛔ **this product can produce two of them.**
 *
 * ⚠️ **Measured before this file was written, not assumed.** 📁 **`EntrySession`
 * and `Membership` appear in `lib/entry/**` and in three test files, and
 * nowhere else** — **before this slice the engine had no production caller at
 * all**, which is why nobody had to answer the question.
 *
 * | Fact | Where it comes from |
 * |---|---|
 * | `memberships[].workspaceId` | ✅ `useWorkspaces()` — the list the API returns |
 * | `lastUsedWorkspaceId` | ✅ `signora.activeWorkspaceId`, the provider's stored hint |
 * | **the other ten** | ⛔ **nothing. No endpoint, no claim, no store** |
 *
 * ## ⛔ Why a default with a comment beside it was the wrong answer
 *
 * ⚠️ **The tempting shape is `onboardingComplete: true, // no source yet`, ten
 * times.** 🔴 **Every one of those is a hidden input** ([§2](../../../CLAUDE.md)):
 * a value that decides behaviour without being part of any declared contract.
 * ⛔ **And the damage compounds** — **each constant makes its rule unreachable**,
 * so the engine would look like twenty-four rules deciding entry while **one
 * literal decides it**, which is the *decorative logic* class exactly.
 *
 * ✅ **So the ten are declared once, in one object, each with the reason it is
 * absent and the rules it costs.** ⚡ **The value is still supplied — the engine
 * must run — but it is supplied somewhere a reader can count it**, and
 * [`entry-observed.test.ts`](../../tests/unit/entry-observed.test.ts) asserts
 * every unobserved fact names the rules it suppresses.
 *
 * ## ✅ The part that is a type rather than a promise
 *
 * 🔴 **`Exclude<keyof EntrySession, ObservedKey>` is the whole guarantee.**
 * ⚡ **Add a field to `EntrySession` and this file stops compiling** until it is
 * either observed by {@link observedSession} or declared below with its reason.
 * ⛔ **A new rule input can therefore never arrive with a silent default** —
 * which is the failure this file exists to make unrepresentable, rather than
 * discouraged ([§2](../../../CLAUDE.md), *types make incorrect architecture
 * impossible*).
 */

import type { EntrySession, Membership } from './session';

/**
 * **A fact the engine reads that this product cannot yet produce.**
 *
 * ⛔ **`suppresses` is not documentation.** ⚡ **It is the cost of the absence,
 * stated in the unit that matters** — a rule that can never fire — and it is
 * what makes *"the engine decides entry"* a checkable claim rather than a
 * hopeful one.
 */
export interface Unobserved<T> {
  /** ⚠️ **What the engine is told meanwhile**, and it is always the value that preserves today's behaviour. */
  readonly value: T;
  /** Why the product cannot answer, in one sentence. */
  readonly because: string;
  /** ⛔ **The rules this makes unreachable.** `[]` means it costs no rule. */
  readonly suppresses: readonly string[];
}

/** The two facts the product genuinely knows. */
type ObservedKey = 'memberships' | 'lastUsedWorkspaceId';

/**
 * ⛔ **Ten facts, ten reasons.** ⚡ **The `Exclude` is what keeps this honest**:
 * a field added to `EntrySession` and not observed must appear here, or the
 * build fails.
 */
export const UNOBSERVED: {
  readonly [K in Exclude<keyof EntrySession, ObservedKey>]: Unobserved<EntrySession[K]>;
} = {
  /**
   * 📁 **Gate 1's owner is the *identity service*** and the design's own
   * outcomes are *Active · Locked · Suspended · Deleted*.
   *
   * ✅ **`active` is a MEASUREMENT here rather than an optimistic default**:
   * **no account lifecycle exists** — `authClient` is configured with
   * `twoFactorClient()` and `multiSessionClient()` and no ban or lockout
   * plugin, and no endpoint publishes a standing. ⚡ **There is no way for an
   * account to be anything else**, so telling the engine `active` states what
   * is true rather than what is convenient.
   */
  account: {
    value: 'active',
    because:
      'no account lifecycle exists — Better Auth is configured without a ban or lockout plugin, and no endpoint publishes a standing',
    suppresses: ['01', '02', '03'],
  },

  /**
   * 📁 **Gate 2's owner is the *shell*.** ⚠️ **`valid` is true by construction
   * at the only place this is called**: the caller has a session, because a
   * caller without one never reaches the engine at all.
   *
   * 🔴 **And that is the finding this slice reports rather than papers over** —
   * see the note on `(app)/layout` in the commit: **there is no reason code for
   * *never signed in*.** ⛔ **Mapping it to `SESSION_EXPIRED` would write a
   * false answer into the record support reads.**
   */
  session: {
    value: 'valid',
    because:
      'true by construction — the engine is only reached with a live session, and no step-up or freshness policy exists to make a live session insufficient',
    suppresses: ['04', '05'],
  },

  /**
   * 📁 **Rule 18 · `ONBOARDING`, and this is the one that would have hurt.**
   *
   * ⚠️ **The onboarding flow EXISTS** — `/onboarding/company`, `/you`,
   * `/goals` — ⛔ **but nothing records whether a person finished it.**
   * ⚡ **`true` preserves today's behaviour exactly**: nothing routes anybody to
   * onboarding today either. 🔴 **`false` would send every person on every
   * sign-in to a flow they may have completed months ago.**
   */
  onboardingComplete: {
    value: true,
    because:
      'the onboarding flow exists but no field records completion — routing on a fact nobody stores would send finished people back through it',
    suppresses: ['18'],
  },

  /**
   * ⛔ **Paired with the field above and unreachable while it is `true`.**
   * ⚠️ **Worth its own entry rather than folding into one**: rule 18's route is
   * `` `/onboarding/${step ?? ''}` ``, **so a missing step produces
   * `/onboarding/` — a trailing-slash route that is not `/onboarding`** and
   * matches nothing.
   */
  onboardingStep: {
    value: null,
    because: "no field records progress; rule 18's route would build /onboarding/ with an empty step",
    suppresses: [],
  },

  /** 📁 **Rule 20 · `FIRST_RUN`.** Nothing distinguishes a first sign-in from any other. */
  firstLogin: {
    value: false,
    because: 'no field distinguishes a first sign-in from any later one',
    suppresses: ['20'],
  },

  /**
   * 📁 **Rule 21 · `ROLE_CHANGED`.** ⚡ **Role changes ARE recorded** — the
   * capability roster reads them — ⛔ **but nothing compares a role against
   * what it was at the previous session**, which is the fact the rule needs.
   */
  roleChangedSinceLastSession: {
    value: false,
    because:
      'role changes are recorded, but nothing compares a role against its value at the previous session',
    suppresses: ['21'],
  },

  /** 📁 **Rule 22 · `INVITE_ACCEPTED`** — 📁 *"while signed in"*. The join flow does not mark the session. */
  invitationAcceptedFor: {
    value: null,
    because: 'the join flow does not mark the session with the workspace it just joined',
    suppresses: ['22'],
  },

  /** 📁 **Rule 23 · `USER_DEFAULT`** — 📁 *"available in profile preferences"*, which has no such control. */
  startPage: {
    value: null,
    because: 'profile preferences has no custom start page control',
    suppresses: ['23'],
  },
};

/**
 * ⛔ **A membership's two health facts, absent for different reasons** — and
 * the difference is worth keeping, because one of them is nearly buildable.
 */
export const UNOBSERVED_MEMBERSHIP: {
  readonly [K in Exclude<keyof Membership, 'workspaceId'>]: Unobserved<Membership[K]>;
} = {
  /**
   * 📁 **Gate 4's owner is the *workspace service*** and its outcomes are
   * *Active · Read-only · Archived · Suspended · Deleted*. ⛔ **`Workspace` in
   * [`lib/api/types.ts`](../api/types.ts) carries `id · name · created_at ·
   * updated_at` and nothing else.**
   *
   * 🔴 **This one pairs with an absence on the other side, and they must be
   * fixed together**: **rules 15, 16 and 17 route to `/w/:id/suspended`,
   * `/archived` and `/deleted`, and none of those routes exists.** ⚡ **The
   * engine is safe today only because the fact that would reach them cannot be
   * produced** — ⛔ **so whichever slice adds the standing MUST add the three
   * screens in the same change**, or it turns three unreachable rules into
   * three 404s on the same day.
   */
  standing: {
    value: 'active',
    because:
      'the workspace API publishes id, name and timestamps only — there is no lifecycle field, and rules 15-17 route to three screens that do not exist yet',
    suppresses: ['15', '16', '17'],
  },

  /**
   * 📁 **Rule 19 · `ACTIVATION`.** ⚠️ **This is the one that is genuinely
   * observable and deliberately not observed here.**
   *
   * ⚡ **`useIntegrations(workspaceId)` answers it** — `ActivationChecklist`
   * already uses exactly that. ⛔ **But it answers for ONE workspace, and the
   * engine reads it for EVERY membership**, so honouring it would mean one
   * query per workspace before a single routing decision could be made.
   *
   * ✅ **And the product already answers this by COMPOSITION rather than by
   * routing**: `/` renders `ActivationChecklist`. ⚡ **Rule 19 would move that
   * answer from a card to a redirect, which is a product change and not this
   * row's.**
   */
  hasConnectedSource: {
    value: true,
    because:
      'observable per workspace via useIntegrations, but the engine reads it for every membership — and the product already answers activation with a card on Home rather than a redirect',
    suppresses: ['19'],
  },
};

/** **The two facts the product genuinely knows**, in the caller's terms. */
export interface ObservedFacts {
  /**
   * ⚡ **The workspaces the API returned**, in the order it returned them.
   * 📁 [`session.ts`](./session.ts): *"Order is the caller's and is preserved"*
   * — rule 14 falls through to *the next healthy membership*, and *next* is
   * only meaningful against a stable order.
   */
  readonly workspaceIds: readonly string[];
  /**
   * ⛔ **The stored hint, and it is EXACTLY as untrusted as the provider
   * treats it.** ⚡ **The engine is safe by construction**: it only routes to a
   * workspace found in `memberships`, so an id that is no longer there falls to
   * rule 13 or 14 rather than being honoured.
   */
  readonly lastUsedWorkspaceId: string | null;
}

/**
 * **The engine's input, built from what is known and what is declared absent.**
 *
 * ⛔ **There is no second way to construct an `EntrySession` in production.**
 * ⚡ **That is the point** — a caller that assembled one by hand would be
 * choosing ten values with nothing recording that it had.
 */
export function observedSession(facts: ObservedFacts): EntrySession {
  return {
    memberships: facts.workspaceIds.map((workspaceId) => ({
      workspaceId,
      standing: UNOBSERVED_MEMBERSHIP.standing.value,
      hasConnectedSource: UNOBSERVED_MEMBERSHIP.hasConnectedSource.value,
    })),
    lastUsedWorkspaceId: facts.lastUsedWorkspaceId,
    account: UNOBSERVED.account.value,
    session: UNOBSERVED.session.value,
    onboardingComplete: UNOBSERVED.onboardingComplete.value,
    onboardingStep: UNOBSERVED.onboardingStep.value,
    firstLogin: UNOBSERVED.firstLogin.value,
    roleChangedSinceLastSession: UNOBSERVED.roleChangedSinceLastSession.value,
    invitationAcceptedFor: UNOBSERVED.invitationAcceptedFor.value,
    startPage: UNOBSERVED.startPage.value,
  };
}

/**
 * ⚡ **Which rules can fire today**, derived from the declarations above rather
 * than listed by hand.
 *
 * ⛔ **Two representations of one fact is the defect [§2](../../../CLAUDE.md)
 * names** — so this is computed, and the test that reports coverage reads it
 * rather than a second list somebody would have to maintain.
 */
export function suppressedRules(): readonly string[] {
  const all = [
    ...Object.values(UNOBSERVED).flatMap((u) => u.suppresses),
    ...Object.values(UNOBSERVED_MEMBERSHIP).flatMap((u) => u.suppresses),
  ];
  return [...new Set(all)].sort();
}
