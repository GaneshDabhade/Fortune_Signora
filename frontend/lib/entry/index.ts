/**
 * **The Authenticated Entry Engine** — [TASK-1400](../../../docs/BACKLOG.md),
 * [workflow 29](../../../docs/coordination/workflows.toml).
 *
 * > 📁 **[D-193](../../../docs/DECISION_REGISTER.md): *"Treat it as a platform
 * > specification, not a feature specification."***
 *
 * **Everything between the moment authentication succeeds and the moment a
 * person is doing their work**, resolved once, in one place. 📁 *"No module
 * performs its own entry redirect."*
 *
 * ## ⛔ What this module is not
 *
 * **It is not authorization.** [§20c](../../../CLAUDE.md): *a client check is a
 * courtesy, never enforcement.* **Casbin on the server decides what a person
 * may do; this chooses which screen they see** — and the row names that as its
 * Security Invariant: ⛔ ***the engine must never be the only check.***
 *
 * ⚡ **It is also not wired to anything yet, deliberately.** The row ships the
 * engine and no caller; [TASK-1401](../../../docs/BACKLOG.md) is the row that
 * replaces the five hardcoded redirects, and it is last of workflow 29's seven
 * because it touches four workflows already on `main`.
 *
 * ## ✅ Pure, and provably so
 *
 * **No import in this module reaches a network, a clock or a store.** Same
 * inputs, same destination — which is why the whole 24-rule table is tested
 * without a browser, a session or a database.
 */

export { REASON_CODES, GATES, type ReasonCode, type Gate } from './reasons';
export { RULES, resolveWorkspace, workspaceHome, type Rule } from './rules';
export {
  ENTRY_EVENT_KIND,
  ForbiddenDetail,
  diagnosticsBundle,
  entryMark,
  entryRecord,
  explainEntry,
  type DiagnosticsBundle,
  type EntryMark,
  type EntryRecord,
} from './diagnostics';
export type {
  AccountStanding,
  EntryDecision,
  EntrySession,
  Intent,
  IntentAccess,
  Membership,
  SessionStanding,
  WorkspaceStanding,
} from './session';

import { GATES } from './reasons';
import { RULES, resolveWorkspace } from './rules';
import type { EntryDecision, EntrySession, Intent } from './session';

/**
 * **`resolveEntry(session, intent) → { route, reason }`** — the signature the
 * row specifies, and the only entry point this module has.
 *
 * **Walks the 24 rules top to bottom, once.** ⛔ **No scoring, no priority, no
 * second pass** — 📁 *"one ordered rule list."*
 *
 * ⚡ **A rule that matches either ends the walk or resolves and lets it
 * continue**, which is §02's ladder: 📁 *"each gate depends on the one before
 * it **resolving**, and a gate that **fails** produces a designed screen."*
 * **The first `terminal` match wins.** A `resolution` match (rules 11, 12, 14)
 * records *why this workspace* and carries on, so a later gate with something
 * more specific to say — onboarding, activation, a changed role — is reached.
 * ⛔ **Without that distinction seven rules are dead**, which `rules.ts`
 * explains and [C-250](../../../docs/LANE_COORDINATION.md) reports.
 *
 * 🔴 **It cannot return without a reason.** Every path ends on a rule, and
 * **a route always arrives with the code that explains it** — the property the
 * row calls *the one that decides correctness*.
 */
export function resolveEntry(
  session: EntrySession,
  intent: Intent | null = null,
): EntryDecision {
  const workspaceId = resolveWorkspace(session, intent)?.workspaceId ?? null;
  let resolution: EntryDecision | null = null;

  for (const rule of RULES) {
    if (rule.kind === 'default') continue;
    if (!rule.when(session, intent)) continue;

    const decision: EntryDecision = {
      route: rule.route(session, intent),
      reason: rule.reason,
      gate: rule.gate,
      /**
       * 🔴 **A decision from gate 1 or 2 names NO workspace** —
       * [B-230](../../../docs/BUGS.md), found by
       * [TASK-1403](../../../docs/BACKLOG.md) building the record that carries
       * this field to support.
       *
       * 📁 **The design states it as the REASON gate 1 is first**: *"Can this
       * identity use the product at all? Evaluated before any workspace is
       * loaded, **because a suspended account must not see workspace names it
       * no longer has rights to**."*
       *
       * ⛔ **`resolveWorkspace` runs before the walk and answered regardless**,
       * so a suspended account's decision carried a workspace id — **the exact
       * disclosure the ordering exists to prevent, reintroduced by computing
       * the answer eagerly.** ⚠️ **Nothing consumed it yet, which is why it was
       * invisible**; this row is the first consumer and it hands the field to a
       * support bundle.
       *
       * ✅ **The gate number is the test because the design's is**: gates 1 and
       * 2 precede workspace resolution by construction, so a decision from
       * either cannot have resolved one.
       */
      workspaceId: rule.gate < GATES.WORKSPACE_RESOLUTION ? null : workspaceId,
    };
    if (rule.kind === 'terminal') return decision;
    // ⚡ **The first resolution is kept, not the last.** Gate 3 answers *which
    // workspace* once; a second answer would mean two rules resolved it.
    resolution ??= decision;
  }

  if (resolution !== null) return resolution;

  /**
   * ⚠️ **Rule 24 `HOME`, the totality guard.**
   *
   * ⛔ **Unreachable today, and that is reported rather than hidden**
   * ([C-250](../../../docs/LANE_COORDINATION.md)): rules 10–14 answer every
   * membership shape, so nothing arrives here. **It is kept because deleting it
   * would make `resolveEntry` partial** — and a router handed `undefined` fails
   * somewhere far from the cause. ⚡ **`entry-engine.test.ts` calls this rule
   * directly**, so it is exercised rather than merely present.
   */
  const home = RULES[RULES.length - 1];
  if (home === undefined || home.kind !== 'default') {
    throw new Error(
      'resolveEntry: the rule table no longer ends in the total case. ' +
        'Rule 24 is what makes this function total; without it a caller ' +
        'receives no route at all, which is worse than a crash.',
    );
  }
  return {
    route: home.route(session, intent),
    reason: home.reason,
    gate: home.gate,
    workspaceId,
  };
}
