/**
 * **What the engine is told, and therefore what it never asks** —
 * [TASK-1400](../../../docs/BACKLOG.md).
 *
 * ## 🔴 This file is where purity is won or lost
 *
 * **The row names the risk before it is met:**
 *
 * > ⚠️ ***"The temptation is to fetch inside a rule — 'just look up whether the
 * > workspace is archived.' That destroys purity, testability and the
 * > diagnostics guarantee at once, and the spec forbids it in one sentence."***
 *
 * **The design's sentence:** 📁 ***"Rules are pure: same inputs, same
 * destination, no network call inside the decision."***
 *
 * ⚡ **Purity is not achieved by discipline inside the rules — it is achieved
 * by the shape of this type.** Every fact the 24 rules need is a *field*, so a
 * rule has nothing to fetch: there is no client, no reader and no promise
 * anywhere in the module, and **a rule that wanted to fetch would have to
 * import something this module does not have.**
 *
 * ⛔ **`IntentAccess` is the sharpest case.** Whether a deep link is permitted
 * is a *server* decision — Casbin's, per [§20c](../../../CLAUDE.md), where
 * *a client check is a courtesy, never enforcement*. **So the answer arrives as
 * an input.** ✅ **That is what keeps rules 06–09 pure**, and it is also what
 * keeps this engine honestly subordinate: **it chooses a screen; it never
 * decides whether access is granted.**
 */

/**
 * **Gate 1 — account standing.** 📁 *"Can this identity use the product at all?
 * Evaluated before any workspace is loaded, because a suspended account must
 * not see workspace names it no longer has rights to."*
 *
 * ⚡ **`pending_deletion` is separate from `deleted` in the input and joins it
 * in the decision** — rule 01 reads *"Account deleted **or pending deletion**"*
 * and both produce `ACCOUNT_DELETED`. ⛔ **They are kept apart here because the
 * destination differs in content**: the design's screen shows *"recovery window
 * and date… if within it"*, which only one of the two has.
 */
export type AccountStanding =
  | 'active'
  | 'locked'
  | 'suspended'
  | 'deleted'
  | 'pending_deletion';

/**
 * **Gate 2 — session validity.** 📁 *"Is the session current, and does it
 * satisfy the workspace policy — MFA, IdP freshness, device trust? A session
 * valid yesterday may be insufficient today."*
 */
export type SessionStanding = 'valid' | 'expired' | 'step_up_required';

/**
 * **Gate 4 — workspace standing.** The design's outcomes are *Active,
 * Read-only, Archived, Suspended, Deleted*; **`archived` IS the read-only
 * one** — rule 16 says *"Read-only, exports enabled, a restore route for
 * owners"* — so there is no separate member.
 */
export type WorkspaceStanding = 'active' | 'suspended' | 'archived' | 'deleted';

/**
 * How a deep link resolved, **decided by the server and handed in**.
 *
 * ⛔ **Never computed here.** Rules 06–09 each read one of these values, and
 * the engine has no way to produce them — which is the point.
 */
export type IntentAccess = 'granted' | 'forbidden' | 'missing' | 'not_member';

/** One workspace a person belongs to, with the facts gate 4 and rule 19 need. */
export interface Membership {
  readonly workspaceId: string;
  readonly standing: WorkspaceStanding;
  /**
   * Rule 19 · `ACTIVATION` — 📁 *"Workspace has no connected source."*
   * ⚡ **A property of the workspace, not of the person**, so it lives here
   * rather than on the session.
   */
  readonly hasConnectedSource: boolean;
}

/**
 * **The route the person was trying to reach**, or `null` for a plain sign-in.
 *
 * 📁 *"Authentication hands over an identity and an intent — the route the
 * person was trying to reach."*
 */
export interface Intent {
  /** The path as the customer asked for it. */
  readonly path: string;
  /** The workspace the link names, when it names one. */
  readonly workspaceId: string | null;
  /** ⛔ The server's answer, never this module's. */
  readonly access: IntentAccess;
}

/**
 * **Everything the twenty-four rules read.**
 *
 * ⛔ **No methods, no getters, no lazy fields.** `readonly` throughout, because
 * a rule that could mutate the session would make *same inputs, same
 * destination* untrue in the one way tests would not catch.
 */
export interface EntrySession {
  /** Gate 1. */
  readonly account: AccountStanding;
  /** Gate 2. */
  readonly session: SessionStanding;

  /**
   * Gate 3. ⚡ **Order is the caller's and is preserved** — rule 14 falls
   * through to *"the next healthy membership"*, and *next* is only meaningful
   * against a stable order.
   */
  readonly memberships: readonly Membership[];

  /**
   * Rules 12 and 14. **`null` means never recorded**, which is a different
   * fact from *recorded and now unavailable* — rule 13 needs the first and
   * rule 14 needs the second.
   *
   * ⚠️ **[D-196](../../../docs/DECISION_REGISTER.md) names the hazard this
   * field carries**: *"last-used workspace is a stored preference that OUTLIVES
   * membership — if it is not cleared on removal, a departed member's next
   * login routes at a workspace they can no longer see."* ⛔ **The engine is
   * safe by construction**: it only ever routes to a workspace found in
   * `memberships`, so an id that is no longer there falls to rule 13 or 14
   * rather than being honoured.
   */
  readonly lastUsedWorkspaceId: string | null;

  /**
   * Rule 18 · `ONBOARDING`. 📁 *"Progress is per person, not per workspace."*
   */
  readonly onboardingComplete: boolean;
  /** Rule 18's destination — 📁 *"Resume at the last incomplete step."* */
  readonly onboardingStep: string | null;

  /** Rule 20 · `FIRST_RUN`. */
  readonly firstLogin: boolean;
  /** Rule 21 · `ROLE_CHANGED`. */
  readonly roleChangedSinceLastSession: boolean;
  /**
   * Rule 22 · `INVITE_ACCEPTED` — the workspace just joined, 📁 *"while signed
   * in"*. `null` when no invitation was accepted this session.
   */
  readonly invitationAcceptedFor: string | null;

  /**
   * Rule 23 · `USER_DEFAULT` — 📁 *"Person set a custom start page… Available
   * in profile preferences."* `null` when they have expressed no preference.
   */
  readonly startPage: string | null;
}

/**
 * **What the engine returns. Always both halves.**
 *
 * 🔴 **Never a route without a reason.** The row makes that the property that
 * decides correctness, and `entry-engine.test.ts` asserts it over every
 * session/intent pair it can build rather than over the cases chosen by hand.
 */
export interface EntryDecision {
  readonly route: string;
  readonly reason: import('./reasons').ReasonCode;
  /** Which of the six gates produced it — diagnostics only. */
  readonly gate: import('./reasons').Gate;
  /**
   * The workspace the decision settled on, when it settled on one.
   * ⚡ **Returned rather than re-derived by the caller**, because recomputing
   * it is how two answers to one question appear.
   */
  readonly workspaceId: string | null;
}
