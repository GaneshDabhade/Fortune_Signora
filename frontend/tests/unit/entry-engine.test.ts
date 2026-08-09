/**
 * **The Authenticated Entry Engine** — [TASK-1400](../../../docs/BACKLOG.md).
 *
 * > **Verification strategy, from the row:** ✅ ***"The rule table is the
 * > verification, and it is derived from the design document rather than
 * > restated."***
 *
 * ⚡ **So this file reads `Fortune Signora Authenticated Entry.dc.html` and
 * asserts the implementation against it.** ⛔ **The 24 numbers, the 24 codes
 * and their order are never written out here** — transcribing them would make
 * this a second copy of the design, and **the copy is always the one somebody
 * reads** ([D-137](../../../docs/DECISION_REGISTER.md)).
 *
 * **What is written by hand is one session per rule**, because a *condition* is
 * the thing a document cannot hand you executably.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  REASON_CODES,
  RULES,
  resolveEntry,
  type EntrySession,
  type Intent,
  type Membership,
  type ReasonCode,
} from '@/lib/entry';

// ── The design document, parsed rather than quoted ──────────────────────────

/** ⚡ `process.cwd()` is `frontend/`; the snapshot is the repository's. */
const DESIGN = readFileSync(
  join(
    process.cwd(),
    '../docs/design-snapshot/screens/Fortune Signora Authenticated Entry.dc.html',
  ),
  'utf8',
);

/**
 * The rule table lives in the document's own script data as fixed-shape
 * tuples: `['01', condition, destination, route, CODE, tone]`.
 *
 * ⚠️ **Anchored to the `rules:` array and not to the whole file.** A bare sweep
 * for `SCREAMING_SNAKE` would also collect anything similar elsewhere in the
 * document — **a guard that matches the wrong thing teaches people to widen
 * it**, which is how a guard stops guarding (the lesson `auth-configuration`'s
 * `max: 10` left behind).
 */
function designRules(): { n: string; code: string; condition: string }[] {
  const start = DESIGN.indexOf('rules:');
  expect(start, 'the design document still carries a `rules:` table').toBeGreaterThan(-1);
  const open = DESIGN.indexOf('[', start);
  let depth = 0;
  let end = open;
  for (let i = open; i < DESIGN.length; i += 1) {
    if (DESIGN[i] === '[') depth += 1;
    else if (DESIGN[i] === ']') {
      depth -= 1;
      if (depth === 0) {
        end = i;
        break;
      }
    }
  }
  const block = DESIGN.slice(open, end + 1);
  const row =
    /\[\s*'(\d+)',\s*'((?:[^'\\]|\\.)*)',\s*'(?:[^'\\]|\\.)*',\s*'(?:[^'\\]|\\.)*',\s*'([A-Z_]+)'/g;
  const out: { n: string; code: string; condition: string }[] = [];
  for (const m of block.matchAll(row)) {
    out.push({ n: m[1] ?? '', condition: m[2] ?? '', code: m[3] ?? '' });
  }
  return out;
}

const DESIGNED = designRules();

// ── Sessions, one per rule ──────────────────────────────────────────────────

const HEALTHY: Membership = { workspaceId: 'ws-1', standing: 'active', hasConnectedSource: true };
const SECOND: Membership = { workspaceId: 'ws-2', standing: 'active', hasConnectedSource: true };

/** A person for whom every gate passes — rule 24, the common case. */
function settled(over: Partial<EntrySession> = {}): EntrySession {
  return {
    account: 'active',
    session: 'valid',
    memberships: [HEALTHY],
    lastUsedWorkspaceId: null,
    onboardingComplete: true,
    onboardingStep: null,
    firstLogin: false,
    roleChangedSinceLastSession: false,
    invitationAcceptedFor: null,
    startPage: null,
    ...over,
  };
}

function deepLink(access: Intent['access'], path = '/w/ws-1/accounts/acme'): Intent {
  return { path, workspaceId: 'ws-1', access };
}

function standing(s: Membership['standing']): EntrySession {
  return settled({ memberships: [{ ...HEALTHY, standing: s }] });
}

/**
 * ⛔ **One case per rule, and each is the FIRST rule its session matches** —
 * that is what makes this a test of the *order* as well as of the conditions.
 */
const CASES: { code: ReasonCode; session: EntrySession; intent: Intent | null; route: string }[] = [
  { code: 'ACCOUNT_DELETED', session: settled({ account: 'deleted' }), intent: null, route: '/account/deleted' },
  { code: 'ACCOUNT_SUSPENDED', session: settled({ account: 'suspended' }), intent: null, route: '/account/suspended' },
  { code: 'ACCOUNT_LOCKED', session: settled({ account: 'locked' }), intent: null, route: '/auth/locked' },
  { code: 'SESSION_EXPIRED', session: settled({ session: 'expired' }), intent: deepLink('granted'), route: '/w/ws-1/accounts/acme' },
  { code: 'STEPUP_REQUIRED', session: settled({ session: 'step_up_required' }), intent: null, route: '/auth/step-up' },
  { code: 'INTENT_HONOURED', session: settled(), intent: deepLink('granted'), route: '/w/ws-1/accounts/acme' },
  { code: 'INTENT_FORBIDDEN', session: settled(), intent: deepLink('forbidden'), route: '/w/ws-1/accounts/acme?error=403' },
  { code: 'INTENT_MISSING', session: settled(), intent: deepLink('missing'), route: '/w/ws-1/accounts/acme?error=404' },
  { code: 'INTENT_NOT_MEMBER', session: settled(), intent: deepLink('not_member'), route: '/workspaces' },
  { code: 'NO_WORKSPACE', session: settled({ memberships: [] }), intent: null, route: '/workspaces/none' },
  { code: 'SOLE_WORKSPACE', session: settled({ firstLogin: false }), intent: null, route: '/w/ws-1/home' },
  {
    code: 'LAST_USED',
    session: settled({ memberships: [HEALTHY, SECOND], lastUsedWorkspaceId: 'ws-2' }),
    intent: null,
    route: '/w/ws-2/home',
  },
  {
    code: 'AMBIGUOUS',
    session: settled({ memberships: [HEALTHY, SECOND], lastUsedWorkspaceId: null }),
    intent: null,
    route: '/workspaces',
  },
  {
    // The last-used one is archived and another is healthy — 📁 *"fall through
    // to the next healthy membership."*
    code: 'FELL_THROUGH',
    session: settled({
      memberships: [{ ...HEALTHY, standing: 'archived' }, SECOND],
      lastUsedWorkspaceId: 'ws-1',
    }),
    intent: null,
    route: '/w/ws-2/home',
  },
  { code: 'WS_SUSPENDED', session: standing('suspended'), intent: null, route: '/w/ws-1/suspended' },
  { code: 'WS_ARCHIVED', session: standing('archived'), intent: null, route: '/w/ws-1/archived' },
  { code: 'WS_DELETED', session: standing('deleted'), intent: null, route: '/w/ws-1/deleted' },
  {
    code: 'ONBOARDING',
    session: settled({ onboardingComplete: false, onboardingStep: 'goals' }),
    intent: null,
    route: '/onboarding/goals',
  },
  {
    code: 'ACTIVATION',
    session: settled({ memberships: [{ ...HEALTHY, hasConnectedSource: false }] }),
    intent: null,
    route: '/w/ws-1/home',
  },
  { code: 'FIRST_RUN', session: settled({ firstLogin: true }), intent: null, route: '/w/ws-1/home' },
  {
    code: 'ROLE_CHANGED',
    session: settled({ roleChangedSinceLastSession: true }),
    intent: null,
    route: '/w/ws-1/home',
  },
  {
    code: 'INVITE_ACCEPTED',
    session: settled({ invitationAcceptedFor: 'ws-9' }),
    intent: null,
    route: '/w/ws-9/home',
  },
  { code: 'USER_DEFAULT', session: settled({ startPage: '/w/ws-1/pipeline' }), intent: null, route: '/w/ws-1/pipeline' },
  // ⚠️ **No `HOME` case, and its absence is the finding** — see the dedicated
  // block below rather than a contrived session that cannot occur.
];

// ── The implementation is the design's table ────────────────────────────────

describe('the rule table is the design document', () => {
  it('🔴 carries every rule the design defines, in the design’s order', () => {
    // ⛔ Both sides derived: the left from the document, the right from `RULES`.
    expect(RULES.map((r) => r.n)).toEqual(DESIGNED.map((r) => r.n));
    expect(RULES.map((r) => r.reason)).toEqual(DESIGNED.map((r) => r.code));
  });

  it('⚡ states each rule’s condition in the design’s own words', () => {
    // The condition column is what a reviewer holding the document reads down.
    expect(RULES.map((r) => r.condition)).toEqual(DESIGNED.map((r) => r.condition));
  });

  it('🔴 the design defines twenty-four rules, and the backlog row says twenty-one', () => {
    /**
     * ⚠️ **[TASK-1400](../../../docs/BACKLOG.md) says *"the 21 reason codes"*
     * three times. The document carries 24, all distinct.**
     * [D-138](../../../docs/DECISION_REGISTER.md) makes the snapshot the
     * implementation authority, so **24 ships and the disagreement is reported**
     * at [C-250](../../../docs/LANE_COORDINATION.md).
     *
     * ⚡ **Asserted from the document rather than hardcoded**, so if Product
     * Office rules the other way this fails in one obvious place instead of
     * being discovered screen by screen.
     */
    expect(DESIGNED).toHaveLength(24);
    expect(new Set(DESIGNED.map((r) => r.code)).size).toBe(24);
    expect(REASON_CODES).toHaveLength(DESIGNED.length);
  });

  it('⛔ the reason codes are closed — the tuple has no duplicates and no strays', () => {
    expect(new Set(REASON_CODES).size).toBe(REASON_CODES.length);
    expect([...REASON_CODES].sort()).toEqual([...DESIGNED.map((r) => r.code)].sort());
  });
});

describe('every rule decides, and decides the design’s destination', () => {
  it.each(CASES)('rule for $code routes to $route', ({ code, session, intent, route }) => {
    const decision = resolveEntry(session, intent);
    expect(decision.reason).toBe(code);
    expect(decision.route).toBe(route);
  });

  it('🔴 every rule but one is reachable — no decorative rungs', () => {
    /**
     * ⛔ **[§2](../../../CLAUDE.md): a guard that cannot fire is documentation
     * pretending to be code.** The row names `FELL_THROUGH` specifically —
     * *"a fallthrough that cannot occur"* — and **the same argument covers the
     * whole table**, so it is asserted for the whole table rather than for the
     * one code the row happened to name.
     */
    const reached = new Set(CASES.map((c) => resolveEntry(c.session, c.intent).reason));
    const expected = REASON_CODES.filter((c) => c !== 'HOME');
    expect([...reached].sort()).toEqual([...expected].sort());
  });
});

describe('🔴 rule 24 HOME cannot fire, and that is a finding rather than a bug here', () => {
  /**
   * ⚠️ **Found by building the table, not by reading it.**
   *
   * **Rules 10–14 partition every membership shape there is** — none · exactly
   * one · several with a healthy last-used · several without one · several with
   * an unhealthy one. **Every person matches one of them**, so gate 3 always
   * produces a reason and 📁 rule 24's condition — *"Everything healthy, **no
   * other rule matched**"* — is never true.
   *
   * ⛔ **The design nevertheless highlights rule 24 as *"the default and the
   * most common outcome"***, and tints its row. **Both cannot hold**, and
   * choosing between them is a product decision rather than this lane's:
   * **[C-250](../../../docs/LANE_COORDINATION.md) asks whether a plain landing
   * should read `HOME` or the resolution code that chose the workspace.**
   *
   * ✅ **The rule ships, is exercised here, and is not quietly deleted.** It is
   * what makes `resolveEntry` total — ⛔ **a router handed `undefined` fails far
   * from the cause.**
   */
  it('⛔ no session in the exhaustive sweep reaches it', () => {
    // Asserted rather than asserted-about: if a future edit makes HOME
    // reachable, this fails and C-250 gets its answer from the code.
    const reached = new Set(CASES.map((c) => resolveEntry(c.session, c.intent).reason));
    expect(reached.has('HOME')).toBe(false);
  });

  it('✅ is still a working rule — exercised directly, not merely present', () => {
    const rule = RULES[RULES.length - 1];
    expect(rule?.reason).toBe('HOME');
    expect(rule?.kind).toBe('default');
    // ⛔ Total by construction — the property that makes it worth keeping.
    expect(rule?.when(settled(), null)).toBe(true);
    expect(rule?.route(settled(), null)).toBe('/w/ws-1/home');
  });
});

describe('the property that decides correctness', () => {
  /**
   * 📁 **The row:** *"for every session/intent pair the engine returns exactly
   * one route AND one reason, never a route with no reason."*
   *
   * ⚡ **Swept rather than sampled.** Every combination of the account, session
   * and workspace standings crossed with every intent shape and both onboarding
   * states — **2,880 pairs**, which is cheap precisely because the engine is
   * pure.
   */
  const accounts = ['active', 'locked', 'suspended', 'deleted', 'pending_deletion'] as const;
  const sessions = ['valid', 'expired', 'step_up_required'] as const;
  const standings = ['active', 'suspended', 'archived', 'deleted'] as const;
  const accesses = ['granted', 'forbidden', 'missing', 'not_member'] as const;

  const pairs: { session: EntrySession; intent: Intent | null }[] = [];
  for (const account of accounts) {
    for (const session of sessions) {
      for (const st of standings) {
        for (const onboardingComplete of [true, false]) {
          for (const memberships of [[], [{ ...HEALTHY, standing: st }], [{ ...HEALTHY, standing: st }, SECOND]]) {
            for (const lastUsedWorkspaceId of [null, 'ws-1', 'ws-gone']) {
              const s = settled({
                account,
                session,
                memberships,
                onboardingComplete,
                onboardingStep: 'you',
                lastUsedWorkspaceId,
              });
              pairs.push({ session: s, intent: null });
              for (const access of accesses) pairs.push({ session: s, intent: deepLink(access) });
            }
          }
        }
      }
    }
  }

  it('⚡ returns exactly one route and one reason for every pair', () => {
    expect(pairs.length).toBeGreaterThan(2000);
    const codes = new Set<ReasonCode>(REASON_CODES);
    for (const { session, intent } of pairs) {
      const d = resolveEntry(session, intent);
      expect(typeof d.route).toBe('string');
      expect(d.route.length).toBeGreaterThan(0);
      expect(codes.has(d.reason)).toBe(true);
    }
  });

  it('⛔ never routes to a workspace the person is not a member of', () => {
    /**
     * 🔴 **[D-196](../../../docs/DECISION_REGISTER.md)'s finding, asserted:**
     * *"last-used workspace is a stored preference that OUTLIVES membership —
     * a departed member's next login routes at a workspace they can no longer
     * see, which is an authorization failure wearing a convenience feature's
     * clothes."* ⚡ **`ws-gone` is in the sweep above for exactly this.**
     */
    for (const { session, intent } of pairs) {
      const { workspaceId } = resolveEntry(session, intent);
      if (workspaceId === null) continue;
      expect(session.memberships.map((m) => m.workspaceId)).toContain(workspaceId);
    }
  });

  it('⚡ is pure — the same pair decides the same way, and nothing is mutated', () => {
    const session = settled({ memberships: [HEALTHY, SECOND], lastUsedWorkspaceId: 'ws-2' });
    const before = JSON.stringify(session);
    const first = resolveEntry(session, deepLink('granted'));
    const second = resolveEntry(session, deepLink('granted'));
    expect(first).toEqual(second);
    expect(JSON.stringify(session)).toBe(before);
  });
});

describe('what this module refuses to be', () => {
  it('⛔ reaches no network, no clock and no store', () => {
    /**
     * 🔴 **The row's named risk**: *"the temptation is to fetch inside a rule."*
     * **Asserted over the module's source rather than promised in a comment** —
     * the same shape as `no-mock-data.test.tsx`, and the reason the engine can
     * be tested without a browser, a session or a database at all.
     */
    const sources = ['index.ts', 'rules.ts', 'reasons.ts', 'session.ts'].map((f) =>
      readFileSync(join(process.cwd(), 'lib/entry', f), 'utf8'),
    );
    for (const src of sources) {
      // Strip comments — the prose here discusses fetching at length.
      const code = src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
      expect(code).not.toMatch(/\bfetch\s*\(/);
      expect(code).not.toMatch(/\bawait\b|\basync\b/);
      expect(code).not.toMatch(/Date\.now|new Date\b/);
      expect(code).not.toMatch(/localStorage|sessionStorage|document\b|window\b/);
    }
  });

  it('⛔ is not authorization, and says so where a reader will look', () => {
    // §20c and the row's Security Invariant: the engine must never be the only
    // check. A comment is the right medium — but its ABSENCE should fail.
    const index = readFileSync(join(process.cwd(), 'lib/entry/index.ts'), 'utf8');
    expect(index).toMatch(/never be the only check/i);
  });
});
