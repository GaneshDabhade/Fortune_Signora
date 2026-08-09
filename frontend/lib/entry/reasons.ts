/**
 * **Why a person landed where they landed** — [TASK-1400](../../../docs/BACKLOG.md).
 *
 * **Design authority: `docs/design-snapshot/screens/Fortune Signora Authenticated
 * Entry.dc.html`, §03 *The routing engine*** ([D-138](../../../docs/DECISION_REGISTER.md)).
 * ⛔ **Nothing here is transcribed from a summary** ([D-137](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Every rule carries a reason code. The code is written to the session,
 * > logged with the redirect, and shown to support in the diagnostics bundle —
 * > so 'why did I land here' is answerable without reproducing the login."***
 *
 * ## 🔴 The count is twenty-four, and the backlog row says twenty-one
 *
 * ⚠️ **[TASK-1400](../../../docs/BACKLOG.md) says *"the 21 reason codes"* three
 * times, including in its Definition of Done. The design's rule table carries
 * **24 rules and 24 DISTINCT codes** — measured from the document's own data,
 * not counted by eye, and checked for duplicates: there are none.**
 *
 * ✅ **The design wins, and that is not this lane's preference.**
 * [D-138](../../../docs/DECISION_REGISTER.md) makes the snapshot the
 * implementation authority, and [§21](../../../CLAUDE.md) says implement the
 * design rather than redesign it while building. ⛔ **Shipping 21 would mean
 * three rules with no code**, and a rule with no code cannot answer *"why did I
 * land here"* — **which is the entire stated purpose of the codes.**
 *
 * ⚠️ **The disagreement is reported rather than resolved silently** —
 * [C-250](../../../docs/LANE_COORDINATION.md). **The number is asserted in the
 * test suite from the design document itself**, so if Product Office rules the
 * other way the failure is loud and in one place.
 *
 * ## ⛔ Closed, and closed structurally rather than by comment
 *
 * **A twenty-fifth code cannot be added from outside this module.** The union
 * is derived from a frozen tuple, so `ReasonCode` has exactly these members and
 * TypeScript refuses anything else at every call site — ⚡ **the same property
 * `ReasoningVerb` has in the backend**, which [TASK-453](../../../docs/BACKLOG.md)
 * already proved in this repository. ⛔ **A `string` here would have made the
 * closed type a documentation claim rather than a compiler one.**
 */

/**
 * The twenty-four codes, **in the design's rule order**.
 *
 * ⛔ **The order is load-bearing and is not alphabetical.** `RULES` is declared
 * in this same order and `resolveEntry` walks it top to bottom, first match
 * wins — so reordering this tuple silently reorders the product's routing.
 * **`entry-engine.test.ts` asserts the order against the design document.**
 */
export const REASON_CODES = [
  // ── Gate 1 · Account standing ─────────────────────────────────────────────
  'ACCOUNT_DELETED',
  'ACCOUNT_SUSPENDED',
  'ACCOUNT_LOCKED',
  // ── Gate 2 · Session validity ─────────────────────────────────────────────
  'SESSION_EXPIRED',
  'STEPUP_REQUIRED',
  // ── Gate 3 · Workspace resolution — the intent half ───────────────────────
  'INTENT_HONOURED',
  'INTENT_FORBIDDEN',
  'INTENT_MISSING',
  'INTENT_NOT_MEMBER',
  // ── Gate 3 · Workspace resolution — the membership half ───────────────────
  'NO_WORKSPACE',
  'SOLE_WORKSPACE',
  'LAST_USED',
  'AMBIGUOUS',
  'FELL_THROUGH',
  // ── Gate 4 · Workspace standing ───────────────────────────────────────────
  'WS_SUSPENDED',
  'WS_ARCHIVED',
  'WS_DELETED',
  // ── Gate 6 · Readiness ────────────────────────────────────────────────────
  'ONBOARDING',
  'ACTIVATION',
  'FIRST_RUN',
  // ── Gate 5 · Membership & role ────────────────────────────────────────────
  'ROLE_CHANGED',
  'INVITE_ACCEPTED',
  // ── The person's own answer, then the default ─────────────────────────────
  'USER_DEFAULT',
  'HOME',
] as const;

/**
 * ⛔ **A closed union.** Nothing outside this file can widen it, and every
 * `switch` over it is exhaustively checked by the compiler.
 */
export type ReasonCode = (typeof REASON_CODES)[number];

/**
 * **The six gates**, §02 *The resolution ladder*.
 *
 * > 📁 ***"Six gates, in fixed order, first match wins… each gate depends on
 * > the one before it resolving, and a gate that fails produces a designed
 * > screen rather than a redirect loop."***
 *
 * ⚡ **Carried on every rule so a decision can name which gate produced it.**
 * The design requires the code to reach *"the diagnostics bundle"*, and
 * **a support engineer asking *why* is better served by *"gate 4, workspace
 * standing"* than by a code alone.** ⛔ **The gate is never an input** — it
 * describes a decision already made and nothing branches on it.
 */
export const GATES = {
  ACCOUNT_STANDING: 1,
  SESSION_VALIDITY: 2,
  WORKSPACE_RESOLUTION: 3,
  WORKSPACE_STANDING: 4,
  MEMBERSHIP_AND_ROLE: 5,
  READINESS: 6,
} as const;

export type Gate = (typeof GATES)[keyof typeof GATES];
