/**
 * **The engine admits a non-human principal** —
 * [TASK-1407](../../../docs/BACKLOG.md), on
 * [495](../../../docs/architecture/495-principal-and-identity-boundary.md).
 *
 * ⚡ **The row's Component coverage in one line**: *"A non-human `kind` returns
 * no route and a reason saying why — ⛔ never a redirect to Home, which would
 * put an agent in a human's session."*
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  PRINCIPAL_KINDS,
  human,
  isHuman,
  resolveEntryFor,
  type EntrySession,
  type Principal,
  type PrincipalKind,
} from '@/lib/entry';

const RATIFIED = readFileSync(
  join(process.cwd(), '..', 'docs', 'architecture', '495-principal-and-identity-boundary.md'),
  'utf8',
);

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

const machine = (kind: Exclude<PrincipalKind, 'HUMAN'>): Principal => ({
  kind,
  subjectId: 'svc_7f3a',
  workspaceId: 'ws_north',
  ownerUserId: 'user_1',
});

describe('📁 the kinds are 495’s, read rather than retyped', () => {
  it('⛔ every kind this module admits is one the ratified model names', () => {
    /**
     * ⚡ **Derived from the document rather than transcribed.**
     * 📁 [D-137](../../../docs/DECISION_REGISTER.md): *the copy is always the
     * one somebody reads.* ⛔ **A hand-written list here would be a second
     * specification, and it would drift.**
     */
    for (const kind of PRINCIPAL_KINDS) {
      expect(RATIFIED, `${kind} is not a kind 495 names`).toContain(kind);
    }
    expect(PRINCIPAL_KINDS).toHaveLength(9);
  });

  it('⚡ HUMAN is one of them, so the common case is not a special case', () => {
    expect(PRINCIPAL_KINDS).toContain('HUMAN');
    expect(isHuman(human('user_1'))).toBe(true);
  });
});

describe('🔴 a machine principal gets no screen, and is told why', () => {
  it.each(PRINCIPAL_KINDS.filter((k) => k !== 'HUMAN'))(
    '⛔ %s resolves to no route at all',
    (kind) => {
      /**
       * 🔴 **Never a redirect to Home.** ⚡ **Putting an agent on a human's
       * Home is putting it in a human's session** — and the twenty-four rules
       * are questions about a person's account, memberships and readiness, so
       * asking them of a service account produces a confident answer to a
       * question nobody asked.
       */
      const outcome = resolveEntryFor(machine(kind as Exclude<PrincipalKind, 'HUMAN'>), session());

      expect(outcome.outcome).toBe('no-screen');
      if (outcome.outcome !== 'no-screen') throw new Error('unreachable');
      expect(outcome.kind).toBe(kind);
      expect(outcome.why).toMatch(/no screen to land on/);
    },
  );

  it('⛔ and the refusal is never a route, under any session a person could have', () => {
    /**
     * ⚡ **Swept across the sessions that would each send a HUMAN somewhere
     * different**, so the refusal cannot be an accident of one fixture.
     */
    for (const s of [
      session(),
      session({ account: 'suspended' }),
      session({ memberships: [] }),
      session({ firstLogin: true }),
      session({ onboardingComplete: false, onboardingStep: 'goals' }),
    ]) {
      const outcome = resolveEntryFor(machine('AGENT'), s);
      expect(outcome.outcome).toBe('no-screen');
      expect(JSON.stringify(outcome)).not.toContain('/w/');
    }
  });
});

describe('✅ a human is routed exactly as before', () => {
  it('⚡ the twenty-four rules still decide, and the decision is unchanged', () => {
    const outcome = resolveEntryFor(human('user_1'), session());

    expect(outcome.outcome).toBe('route');
    if (outcome.outcome !== 'route') throw new Error('unreachable');
    expect(outcome.decision.route).toBeTruthy();
    expect(outcome.decision.reason).toBeTruthy();
  });

  it('⛔ a suspended human still reaches the designed account screen', () => {
    // ⚡ **The widening must not have quietly become a gate.** A human whose
    // account is refused is refused *by rule 02*, not by being a principal.
    const outcome = resolveEntryFor(human('user_1'), session({ account: 'suspended' }));

    expect(outcome.outcome).toBe('route');
    if (outcome.outcome !== 'route') throw new Error('unreachable');
    expect(outcome.decision.reason).toBe('ACCOUNT_SUSPENDED');
  });

  it('⚡ an impersonated human is still a human, and still gets a screen', () => {
    /**
     * 📁 **495**: *"an impersonated session must set `acting_for` and be marked
     * in the audit — an unmarked impersonation is indistinguishable from the
     * person acting."* ⛔ **`acting_for` marks it; it does not refuse it** —
     * support looking at somebody's account needs to see what they see.
     */
    const impersonated: Principal = {
      kind: 'HUMAN',
      subjectId: 'user_1',
      workspaceId: null,
      actingFor: 'support_2b',
    };

    const outcome = resolveEntryFor(impersonated, session());

    expect(outcome.outcome).toBe('route');
  });
});

describe('🔴 an unscoped machine credential is unconstructable', () => {
  it('⛔ the type refuses it, which is stronger than a test that checks for it', () => {
    /**
     * 📁 **495**: *"a machine identity that is not workspace-scoped is a
     * cross-tenant credential, and §11 has no category for one."*
     *
     * ⚡ **Expressed as a discriminated union**, so the violation is
     * unrepresentable rather than merely discouraged
     * ([§2](../../../CLAUDE.md)). **This test records the guarantee and names
     * where it lives**; the compiler is what enforces it.
     */
    // @ts-expect-error — a non-human principal has no nullable workspace
    const unscoped: Principal = { kind: 'AGENT', subjectId: 's', workspaceId: null, ownerUserId: 'u' };
    expect(unscoped).toBeTruthy();

    // @ts-expect-error — and it cannot omit its owning human either
    const unowned: Principal = { kind: 'AGENT', subjectId: 's', workspaceId: 'ws_north' };
    expect(unowned).toBeTruthy();
  });
});
