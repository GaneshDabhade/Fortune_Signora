/**
 * **"Why did I land here", answered without the login** —
 * [TASK-1403](../../../docs/BACKLOG.md).
 *
 * ⚡ **The row names its own coverage and the assertions below are those
 * sentences**: *"every redirect emits exactly one reason · **a redirect with no
 * reason FAILS the test** — that is what makes the guarantee real rather than
 * aspirational"*, and the Security Invariant *"the bundle must never carry
 * another workspace's data."*
 */
import { describe, expect, it } from 'vitest';

import {
  ENTRY_EVENT_KIND,
  ForbiddenDetail,
  GATES,
  REASON_CODES,
  RULES,
  diagnosticsBundle,
  entryMark,
  entryRecord,
  explainEntry,
  resolveEntry,
  type EntryRecord,
} from '@/lib/entry';
import type { EntryDecision, EntrySession } from '@/lib/entry';

const AT = '2026-08-10T09:14:00.000Z';
const SUBJECT = 'user_7f3a';
const CORRELATION = 'corr_91af';

/**
 * ⚠️ **Written WITHOUT an `as EntrySession` cast, and the first draft had one.**
 *
 * ⛔ **The cast hid three wrong field names** — `accountStanding` for `account`,
 * `sessionStanding` for `session`, and a `role` `Membership` does not carry —
 * **so a fixture describing no session at all compiled**, and the account-level
 * test below silently exercised gate 6 instead of gate 1.
 *
 * ⚡ **Exactly the defect [B-420](../../../docs/BUGS.md) was**: a claim about a
 * shape that TypeScript believed because it was told to. **Removing the cast is
 * what makes these fixtures checked rather than asserted.**
 */
const session = (over: Partial<EntrySession> = {}): EntrySession => ({
  account: 'active',
  session: 'valid',
  memberships: [{ workspaceId: 'ws_north', standing: 'active', hasConnectedSource: true }],
  lastUsedWorkspaceId: null,
  onboardingComplete: true,
  onboardingStep: null,
  firstLogin: false,
  roleChangedSinceLastSession: false,
  invitationAcceptedFor: null,
  startPage: null,
  ...over,
});

const record = (over: Partial<EntryRecord> = {}): EntryRecord => ({
  kind: ENTRY_EVENT_KIND,
  subjectId: SUBJECT,
  actingFor: SUBJECT,
  workspaceId: 'ws_north',
  reason: 'HOME',
  gate: GATES.READINESS,
  route: '/w/ws_north/home',
  correlationId: CORRELATION,
  at: AT,
  ...over,
});

describe('🔴 every redirect emits exactly one reason', () => {
  it('⛔ a decision with no reason is not representable, across all 24 rules', () => {
    /**
     * ⚡ **This is the row's decisive test.** 📁 *"A redirect with no reason
     * fails the test — that is what makes the guarantee real rather than
     * aspirational."*
     *
     * ⛔ **Asserted over the rule table rather than over a fixture**, so a
     * twenty-fifth rule added without a reason fails here rather than shipping
     * a redirect nobody can explain.
     */
    expect(RULES).toHaveLength(24);

    for (const rule of RULES) {
      expect(rule.reason, 'a rule with no reason produces an unexplainable redirect').toBeTruthy();
      expect(REASON_CODES).toContain(rule.reason);
      expect(Object.values(GATES), `${rule.reason} names no gate`).toContain(rule.gate);
    }
  });

  it('⚡ and a resolved decision always carries one, not zero and not two', () => {
    const decision: EntryDecision = resolveEntry(session());

    expect(decision.reason).toBeTruthy();
    expect(REASON_CODES).toContain(decision.reason);
    // ⛔ One reason, so one record — the walk records the rule that decided,
    // never the rules it passed through.
    const made = entryRecord(decision, { subjectId: SUBJECT, correlationId: CORRELATION, at: AT });
    expect(made.reason).toBe(decision.reason);
  });
});

describe('📁 written to the session — the first of the design’s three', () => {
  it('⛔ carries the code, the gate and the moment, and NOT the route', () => {
    /**
     * ⚠️ **The route is the URL's fact.** A session carrying it would be a
     * second copy, and the two disagree the moment somebody navigates —
     * 📁 [§2](../../../CLAUDE.md), *truth has one authoritative representation*.
     */
    const mark = entryMark(resolveEntry(session()), AT);

    expect(Object.keys(mark).sort()).toEqual(['at', 'gate', 'reason']);
  });

  it('🔴 and never the workspace id, because the session is readable by the browser', () => {
    const mark = entryMark(resolveEntry(session()), AT);
    expect(JSON.stringify(mark)).not.toContain('ws_north');
  });
});

describe('📁 logged with the redirect — the second', () => {
  it('⚡ the record is joinable, which is the whole point of the correlation id', () => {
    const made = entryRecord(resolveEntry(session()), {
      subjectId: SUBJECT,
      correlationId: CORRELATION,
      at: AT,
    });

    expect(made.correlationId).toBe(CORRELATION);
    expect(made.route).toBeTruthy();
    expect(made.at).toBe(AT);
  });

  it('🔴 both identities travel, and an ordinary sign-in acts for itself', () => {
    /**
     * 📁 **The stream carries `subject_id` and `acting_for` both required** —
     * *"a signature a caller can satisfy with one identity is a signature that
     * will eventually be satisfied with one."*
     */
    const ordinary = entryRecord(resolveEntry(session()), {
      subjectId: SUBJECT,
      correlationId: CORRELATION,
      at: AT,
    });
    expect(ordinary.actingFor).toBe(SUBJECT);

    // ⛔ **The case a bundle must not lose**: support looking at somebody's
    // account is not that person entering the product.
    const impersonated = entryRecord(resolveEntry(session()), {
      subjectId: SUBJECT,
      actingFor: 'support_2b',
      correlationId: CORRELATION,
      at: AT,
    });
    expect(impersonated.actingFor).toBe('support_2b');
    expect(impersonated.subjectId).toBe(SUBJECT);
  });

  it('⚡ the kind is the stream’s noun.verb_past grammar, and there is one of it', () => {
    // ⛔ A kind per reason code would make every new rule a schema change to a
    // table this module does not own.
    expect(ENTRY_EVENT_KIND).toBe('entry.resolved');
    expect(ENTRY_EVENT_KIND).toMatch(/^[a-z_]+\.[a-z_]+$/);
  });

  it('⛔ an account-level refusal records NO workspace rather than inventing one', () => {
    /**
     * 📁 **Gate 1 fires before any workspace is loaded** — *"a suspended
     * account must not see workspace names it no longer has rights to"* —
     * ⚡ **so attributing it to a tenant would be a false record.**
     */
    const suspended = resolveEntry(session({ account: 'suspended' }));
    const made = entryRecord(suspended, {
      subjectId: SUBJECT,
      correlationId: CORRELATION,
      at: AT,
    });

    expect(made.gate).toBe(GATES.ACCOUNT_STANDING);
    expect(made.workspaceId).toBeNull();
  });

  it('🔴 refuses anything that looks like a credential, on the value not the key', () => {
    /**
     * ⚡ **Mirrors the stream's `ForbiddenDetailKey`, which is raised on
     * construction.** ⛔ **A producer that only learns the rule when the server
     * rejects it has already put the secret in a browser's memory.**
     */
    const decision = resolveEntry(session());

    expect(() =>
      entryRecord(decision, {
        subjectId: SUBJECT,
        correlationId: 'Bearer eyJhbGciOi… authorization',
        at: AT,
      }),
    ).toThrow(ForbiddenDetail);

    // ✅ And it discriminates — an ordinary record is not refused.
    expect(() =>
      entryRecord(decision, { subjectId: SUBJECT, correlationId: CORRELATION, at: AT }),
    ).not.toThrow();
  });
});

describe('🔴 the bundle is workspace-tenanted — the row’s Security Invariant', () => {
  it('⛔ another workspace’s record never reaches the bundle', () => {
    const bundle = diagnosticsBundle(
      [record(), record({ workspaceId: 'ws_other', reason: 'AMBIGUOUS' })],
      { workspaceId: 'ws_north', subjectId: SUBJECT },
    );

    expect(bundle.entries).toHaveLength(1);
    expect(JSON.stringify(bundle)).not.toContain('ws_other');
  });

  it('⛔ nor another person’s, in the same workspace', () => {
    const bundle = diagnosticsBundle([record(), record({ subjectId: 'user_other' })], {
      workspaceId: 'ws_north',
      subjectId: SUBJECT,
    });

    expect(bundle.entries).toHaveLength(1);
    expect(JSON.stringify(bundle)).not.toContain('user_other');
  });

  it('⚡ what was withheld is COUNTED, because a silent gap gets chased', () => {
    const bundle = diagnosticsBundle(
      [record(), record({ workspaceId: 'ws_other' }), record({ subjectId: 'user_other' })],
      { workspaceId: 'ws_north', subjectId: SUBJECT },
    );

    expect(bundle.withheld).toBe(2);
  });

  it('🔴 a record with NO workspace is kept — it is the commonest question', () => {
    /**
     * ⚡ **Gates 1 and 2 produce the refusals support is asked about most** —
     * `ACCOUNT_SUSPENDED`, `SESSION_EXPIRED` — **and they belong to the person
     * rather than to a tenant, so they leak nothing.** ⛔ **Dropping them would
     * answer the commonest question with silence.**
     */
    const bundle = diagnosticsBundle(
      [record({ workspaceId: null, reason: 'SESSION_EXPIRED', gate: GATES.SESSION_VALIDITY })],
      { workspaceId: 'ws_north', subjectId: SUBJECT },
    );

    expect(bundle.entries).toHaveLength(1);
    expect(bundle.withheld).toBe(0);
  });
});

describe('✅ support can answer the question from the bundle alone', () => {
  it('⚡ the sentence names the gate, not only the code', () => {
    /**
     * 📁 **The Definition of Done, verbatim**: *"support can answer* why did I
     * land here *from the bundle alone, without a reproduction."* ⛔ **A code
     * on its own requires the reader to already know the ladder.**
     */
    const sentence = explainEntry(
      record({ reason: 'WS_ARCHIVED', gate: GATES.WORKSPACE_STANDING, route: '/w/ws_north/archived' }),
    );

    expect(sentence).toContain('WS_ARCHIVED');
    expect(sentence).toContain('gate 4');
    expect(sentence).toContain('workspace standing');
    expect(sentence).toContain('/w/ws_north/archived');
    // ⚡ The join back to everything else the platform recorded.
    expect(sentence).toContain(CORRELATION);
  });

  it('⛔ every gate has a name, so no reason renders as a bare number', () => {
    for (const gate of Object.values(GATES)) {
      const sentence = explainEntry(record({ gate }));
      expect(sentence, `gate ${gate} has no name`).not.toMatch(/\(undefined\)/);
    }
  });
});
