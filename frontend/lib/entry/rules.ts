/**
 * **The twenty-four rules, in the design's order** —
 * [TASK-1400](../../../docs/BACKLOG.md).
 *
 * **Design authority: `Fortune Signora Authenticated Entry.dc.html`, §03**
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Twenty-four rules, evaluated top to bottom… Engineering implements
 * > this as one component with one ordered rule list; no module performs its
 * > own entry redirect."***
 *
 * ## ⚡ One list, and the order IS the specification
 *
 * ⛔ **Nothing here sorts, scores or prioritises.** `RULES` is an array in the
 * document's order and the resolver takes the first `when` that returns true.
 * **Moving a row up moves the product's behaviour**, which is why the order is
 * asserted against the design document rather than trusted.
 *
 * ## 🔴 A resolution is not a destination, and that is the whole design
 *
 * ⚠️ **Read as a flat first-match list, seven of the twenty-four rules can
 * never fire** — and this was found by building it, not by reading it.
 * **Rules 10–14 partition every membership shape there is** (none · exactly
 * one · several with a healthy last-used · several without · several with an
 * unhealthy one), so a person always matches one of them and **rules 18–24 are
 * unreachable.** ⛔ **The design forbids that outcome in terms:** 📁 *"Every
 * rule has a fixture; **the twenty-four cases are a test suite, not a
 * diagram**."*
 *
 * ✅ **The document's own §02 gives the correct reading**, and it is a ladder
 * rather than a list: 📁 *"each gate depends on the one before it **resolving**,
 * and **a gate that fails** produces a designed screen."* **Two outcomes, not
 * one** — so a rule either **fails** (a destination, and the walk stops) or
 * **resolves** (it chooses the workspace and the walk continues).
 *
 * ⚡ **`kind` is that distinction, and it is the only thing this file adds to
 * the table.** Rules 11, 12 and 14 are `resolution`; everything else is
 * `terminal`. **A resolution reason is still returned** — it is what answers
 * *"why this workspace"* — **but only when no later gate has something more
 * specific to say**, which is 📁 *"ordered by blast radius: account states
 * before workspace states before role states before readiness."*
 *
 * ⚠️ **Reported rather than decided quietly** —
 * [C-250](../../../docs/LANE_COORDINATION.md), with rule 24 named: under either
 * reading `HOME` is unreachable, because 11/12/14 answer every case that
 * reaches it. **It is kept as the totality guard and the question is asked.**
 */

import { GATES, type Gate, type ReasonCode } from './reasons';
import type { EntrySession, Intent, Membership } from './session';

/** `/w/:ws/home`, the one authenticated landing route — §04 *Home is a slot*. */
export function workspaceHome(workspaceId: string): string {
  return `/w/${workspaceId}/home`;
}

/**
 * 📁 *"Everything healthy"* — the standing gate 4 lets past.
 * ⛔ **One definition, used by resolution and by the standing rules**, so
 * *healthy* cannot come to mean two things.
 */
function isHealthy(m: Membership): boolean {
  return m.standing === 'active';
}

function find(session: EntrySession, workspaceId: string | null): Membership | null {
  if (workspaceId === null) return null;
  return session.memberships.find((m) => m.workspaceId === workspaceId) ?? null;
}

/**
 * **Gate 3, performed once** — which workspace is this person entering?
 *
 * ⚡ **A derivation, not a rule.** It answers *which*, and the rules answer
 * *what happens*. Keeping it separate is what lets rules 11–17 each read one
 * clear condition instead of re-deriving the workspace four times.
 *
 * ⛔ **Only ever returns a workspace the person is a member of** — which is
 * what makes [D-196](../../../docs/DECISION_REGISTER.md)'s stale-last-used
 * hazard unreachable here.
 */
export function resolveWorkspace(
  session: EntrySession,
  intent: Intent | null,
): Membership | null {
  // ① The intent names one and the server granted it — §03 rule 06,
  //    *"the workspace in the URL becomes the active workspace."*
  if (intent?.access === 'granted') {
    const named = find(session, intent.workspaceId);
    if (named !== null) return named;
  }
  // ② The last used, when it is healthy — rule 12.
  const lastUsed = find(session, session.lastUsedWorkspaceId);
  if (lastUsed !== null && isHealthy(lastUsed)) return lastUsed;
  // ③ 📁 Rule 14 — *"fall through to the next healthy membership."* ⚡ Before
  //    returning the unhealthy one, because the design falls through rather
  //    than showing a suspended screen when a working workspace exists.
  if (lastUsed !== null) {
    const next = session.memberships.find(isHealthy);
    if (next !== undefined) return next;
    return lastUsed;
  }
  // ④ A sole membership, healthy or not — an unhealthy one is still the
  //    workspace the person has, and rules 15–17 need it to say so.
  if (session.memberships.length === 1) return session.memberships[0] ?? null;
  // ⑤ Nothing to resolve — the chooser, or the empty state.
  return null;
}

/**
 * 📁 §02 — *"each gate depends on the one before it **resolving**, and a gate
 * that **fails** produces a designed screen."*
 *
 * - **`terminal`** — the walk stops here. This is the destination.
 * - **`resolution`** — gate 3 chose the workspace. **The walk continues**, and
 *   this reason is returned only if nothing later is more specific.
 * - **`default`** — rule 24, the totality guard.
 */
export type RuleKind = 'terminal' | 'resolution' | 'default';

/** One row of the design's table. */
export interface Rule {
  /** The design's own number, `01`–`24`. ⛔ A label, never an index. */
  readonly n: string;
  readonly reason: ReasonCode;
  readonly gate: Gate;
  readonly kind: RuleKind;
  /** The design's condition column, verbatim — so the code reads as the table. */
  readonly condition: string;
  readonly when: (session: EntrySession, intent: Intent | null) => boolean;
  /**
   * The destination. ⚡ **A function because five rules compute it** — the
   * intent path, the resolved workspace, the onboarding step, the preference.
   */
  readonly route: (session: EntrySession, intent: Intent | null) => string;
}

/** Where a decision lands when the resolved workspace is the destination. */
function resolvedHome(session: EntrySession, intent: Intent | null): string {
  const ws = resolveWorkspace(session, intent);
  return ws === null ? WORKSPACES : workspaceHome(ws.workspaceId);
}

const WORKSPACES = '/workspaces';

/**
 * ⛔ **The list. Top to bottom, first match wins.**
 *
 * Every `condition` is the design's own words, and every `n` is the design's
 * own number — **so a reviewer holding the document can read down both at
 * once.** That is the row's *"derived from the design document rather than
 * restated"* made checkable.
 */
export const RULES: readonly Rule[] = [
  // ══ Gate 1 · Account standing ═══════════════════════════════════════════
  {
    n: '01',
    kind: 'terminal',
    reason: 'ACCOUNT_DELETED',
    gate: GATES.ACCOUNT_STANDING,
    condition: 'Account deleted or pending deletion',
    when: (s) => s.account === 'deleted' || s.account === 'pending_deletion',
    route: () => '/account/deleted',
  },
  {
    n: '02',
    kind: 'terminal',
    reason: 'ACCOUNT_SUSPENDED',
    gate: GATES.ACCOUNT_STANDING,
    condition: 'Account suspended by Signora',
    when: (s) => s.account === 'suspended',
    route: () => '/account/suspended',
  },
  {
    n: '03',
    kind: 'terminal',
    reason: 'ACCOUNT_LOCKED',
    gate: GATES.ACCOUNT_STANDING,
    condition: 'Account locked — failed attempts',
    when: (s) => s.account === 'locked',
    route: () => '/auth/locked',
  },

  // ══ Gate 2 · Session validity ═══════════════════════════════════════════
  {
    n: '04',
    kind: 'terminal',
    reason: 'SESSION_EXPIRED',
    gate: GATES.SESSION_VALIDITY,
    condition: 'Session expired mid-flight',
    when: (s) => s.session === 'expired',
    // 📁 *"Route, filters and unsaved drafts preserved and restored."*
    // ⚠️ The design's route column is `(intent preserved)`. With no intent
    // there is nothing to preserve, and the document does not say where that
    // lands — raised at C-250 rather than invented into a product decision.
    route: (_s, intent) => intent?.path ?? WORKSPACES,
  },
  {
    n: '05',
    kind: 'terminal',
    reason: 'STEPUP_REQUIRED',
    gate: GATES.SESSION_VALIDITY,
    condition: 'Workspace policy requires step-up',
    when: (s) => s.session === 'step_up_required',
    route: () => '/auth/step-up',
  },

  // ══ Gate 3 · Workspace resolution — the intent half ═════════════════════
  {
    n: '06',
    kind: 'terminal',
    reason: 'INTENT_HONOURED',
    gate: GATES.WORKSPACE_RESOLUTION,
    condition: 'Intent is a valid deep link and access is granted',
    when: (_s, intent) => intent?.access === 'granted',
    // 📁 *"Go there. Do not pass Home."*
    route: (_s, intent) => intent?.path ?? WORKSPACES,
  },
  {
    n: '07',
    kind: 'terminal',
    reason: 'INTENT_FORBIDDEN',
    gate: GATES.WORKSPACE_RESOLUTION,
    condition: 'Intent is a deep link, access denied',
    when: (_s, intent) => intent?.access === 'forbidden',
    // 📁 *"The 403 page for that object… Not Home, not a silent redirect."*
    route: (_s, intent) => `${intent?.path ?? ''}?error=403`,
  },
  {
    n: '08',
    kind: 'terminal',
    reason: 'INTENT_MISSING',
    gate: GATES.WORKSPACE_RESOLUTION,
    condition: 'Intent is a deep link, object gone',
    when: (_s, intent) => intent?.access === 'missing',
    route: (_s, intent) => `${intent?.path ?? ''}?error=404`,
  },
  {
    n: '09',
    kind: 'terminal',
    reason: 'INTENT_NOT_MEMBER',
    gate: GATES.WORKSPACE_RESOLUTION,
    condition: 'Intent references a workspace they left',
    when: (_s, intent) => intent?.access === 'not_member',
    // 📁 *"Never a bare 403 — they had access yesterday and deserve to know
    // it changed."*
    route: () => WORKSPACES,
  },

  // ══ Gate 3 · Workspace resolution — the membership half ═════════════════
  {
    n: '10',
    kind: 'terminal',
    reason: 'NO_WORKSPACE',
    gate: GATES.WORKSPACE_RESOLUTION,
    condition: 'No memberships at all',
    when: (s) => s.memberships.length === 0,
    route: () => '/workspaces/none',
  },
  {
    n: '11',
    kind: 'resolution',
    reason: 'SOLE_WORKSPACE',
    gate: GATES.WORKSPACE_RESOLUTION,
    condition: 'Exactly one membership',
    // ⚡ **The design's condition exactly, with no health guard bolted on.**
    // A sole workspace that is suspended still *resolves* here; rules 15–17
    // are terminal and come later, which is what the ladder is for.
    when: (s) => s.memberships.length === 1,
    // 📁 *"Enter it. No confirmation, no picker, no interstitial."*
    route: (s, i) => resolvedHome(s, i),
  },
  {
    n: '12',
    kind: 'resolution',
    reason: 'LAST_USED',
    gate: GATES.WORKSPACE_RESOLUTION,
    condition: 'Several memberships, last-used recorded and healthy',
    when: (s) => {
      const lastUsed = find(s, s.lastUsedWorkspaceId);
      return s.memberships.length > 1 && lastUsed !== null && isHealthy(lastUsed);
    },
    route: (s, i) => resolvedHome(s, i),
  },
  {
    n: '13',
    kind: 'terminal',
    reason: 'AMBIGUOUS',
    gate: GATES.WORKSPACE_RESOLUTION,
    condition: 'Several memberships, no last-used',
    // ⚡ *No last-used* includes an id that no longer matches a membership —
    // D-196's departed-member case resolves here rather than being honoured.
    when: (s) => s.memberships.length > 1 && find(s, s.lastUsedWorkspaceId) === null,
    route: () => WORKSPACES,
  },
  {
    n: '14',
    kind: 'resolution',
    reason: 'FELL_THROUGH',
    gate: GATES.WORKSPACE_RESOLUTION,
    condition: 'Last-used workspace is unavailable',
    when: (s) => {
      const lastUsed = find(s, s.lastUsedWorkspaceId);
      return (
        lastUsed !== null &&
        !isHealthy(lastUsed) &&
        s.memberships.some((m) => isHealthy(m))
      );
    },
    // 📁 *"Fall through to the next healthy membership, and say why the
    // expected one was skipped."*
    route: (s) => {
      const next = s.memberships.find((m) => isHealthy(m));
      return next === undefined ? WORKSPACES : workspaceHome(next.workspaceId);
    },
  },

  // ══ Gate 4 · Workspace standing ═════════════════════════════════════════
  {
    n: '15',
    kind: 'terminal',
    reason: 'WS_SUSPENDED',
    gate: GATES.WORKSPACE_STANDING,
    condition: 'Workspace suspended — billing',
    when: (s, i) => resolveWorkspace(s, i)?.standing === 'suspended',
    route: (s, i) => `/w/${resolveWorkspace(s, i)?.workspaceId ?? ''}/suspended`,
  },
  {
    n: '16',
    kind: 'terminal',
    reason: 'WS_ARCHIVED',
    gate: GATES.WORKSPACE_STANDING,
    condition: 'Workspace archived',
    when: (s, i) => resolveWorkspace(s, i)?.standing === 'archived',
    route: (s, i) => `/w/${resolveWorkspace(s, i)?.workspaceId ?? ''}/archived`,
  },
  {
    n: '17',
    kind: 'terminal',
    reason: 'WS_DELETED',
    gate: GATES.WORKSPACE_STANDING,
    condition: 'Workspace deleted within retention',
    when: (s, i) => resolveWorkspace(s, i)?.standing === 'deleted',
    route: (s, i) => `/w/${resolveWorkspace(s, i)?.workspaceId ?? ''}/deleted`,
  },

  // ══ Gate 6 · Readiness, and gate 5's two notices ════════════════════════
  {
    n: '18',
    kind: 'terminal',
    reason: 'ONBOARDING',
    gate: GATES.READINESS,
    condition: 'Onboarding incomplete',
    when: (s) => !s.onboardingComplete,
    // 📁 *"Resume at the last incomplete step."*
    route: (s) => `/onboarding/${s.onboardingStep ?? ''}`,
  },
  {
    n: '19',
    kind: 'terminal',
    reason: 'ACTIVATION',
    gate: GATES.READINESS,
    condition: 'Workspace has no connected source',
    when: (s, i) => resolveWorkspace(s, i)?.hasConnectedSource === false,
    // 📁 *"Home, activation composition. Same route, same shell — the three
    // connection steps replace the cards."* ⛔ Same route, deliberately.
    route: (s, i) => resolvedHome(s, i),
  },
  {
    n: '20',
    kind: 'terminal',
    reason: 'FIRST_RUN',
    gate: GATES.READINESS,
    condition: 'First login, workspace ready',
    when: (s) => s.firstLogin,
    route: (s, i) => resolvedHome(s, i),
  },
  {
    n: '21',
    kind: 'terminal',
    reason: 'ROLE_CHANGED',
    gate: GATES.MEMBERSHIP_AND_ROLE,
    condition: 'Role changed since last session',
    when: (s) => s.roleChangedSinceLastSession,
    route: (s, i) => resolvedHome(s, i),
  },
  {
    n: '22',
    kind: 'terminal',
    reason: 'INVITE_ACCEPTED',
    gate: GATES.MEMBERSHIP_AND_ROLE,
    condition: 'Invitation accepted while signed in',
    when: (s) => s.invitationAcceptedFor !== null,
    // 📁 *"The new workspace becomes active… Never a sign-out, never a lost tab."*
    route: (s) => workspaceHome(s.invitationAcceptedFor ?? ''),
  },

  // ══ The person's own answer, then the default ═══════════════════════════
  {
    n: '23',
    kind: 'terminal',
    reason: 'USER_DEFAULT',
    gate: GATES.READINESS,
    condition: 'Person set a custom start page',
    when: (s) => s.startPage !== null,
    route: (s) => s.startPage ?? WORKSPACES,
  },
  {
    n: '24',
    kind: 'default',
    reason: 'HOME',
    gate: GATES.READINESS,
    condition: 'Everything healthy, no other rule matched',
    // ⛔ Always true. **The list must be total** — a person who matches nothing
    // still has to land somewhere, and a resolver that could return nothing
    // would push that decision back into every caller.
    when: () => true,
    route: (s, i) => resolvedHome(s, i),
  },
];
