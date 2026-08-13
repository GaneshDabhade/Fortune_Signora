/**
 * **A refused gate says what happened and what to do** —
 * [TASK-1423](../../../docs/BACKLOG.md).
 *
 * 📁 **The spec's central promise**: *"each gate depends on the one before it
 * resolving, and a gate that FAILS produces a designed screen."*
 */
import { describe, expect, it } from 'vitest';

import { GATE_COPY, GATE_REASONS, type GateReason } from '@/lib/entry/gates';
import { RULES } from '@/lib/entry/rules';

describe('🔴 every gate this module answers for is a reason the engine can return', () => {
  /**
   * ⛔ **The assertion that stops this becoming a wish list.** ⚡ A screen for a
   * reason `resolveEntry` never produces is a screen nobody can reach — 📁 the
   * unreachable-primitive class this lane has now found six times.
   */
  it('and none of them is invented', () => {
    const emitted = new Set(RULES.map((rule) => rule.reason));

    for (const reason of GATE_REASONS) {
      expect(emitted.has(reason), `${reason} is not a reason any rule returns`).toBe(true);
    }
  });
});

describe('📁 "states what happened AND what the person can do"', () => {
  it('every gate says what happened, in the customer’s words', () => {
    for (const reason of GATE_REASONS) {
      const copy = GATE_COPY[reason];
      expect(copy.title.length).toBeGreaterThan(10);
      expect(copy.body.length).toBeGreaterThan(40);
    }
  });

  it('⛔ and never shows a customer the reason code', () => {
    // ⚡ **`ACCOUNT_SUSPENDED` is engineering's word for it.** 📁 ADR-0034 puts
    // the translation at this edge, and a screen that leaked the enum would be
    // the one place a person meets it.
    for (const reason of GATE_REASONS) {
      const rendered = `${GATE_COPY[reason].title} ${GATE_COPY[reason].body}`;
      expect(rendered).not.toContain(reason);
      expect(rendered).not.toContain('_');
    }
  });

  it('⛔ and never says "workspace" to a customer', () => {
    // 📁 ADR-0034 again: a customer says *organization*.
    for (const reason of GATE_REASONS) {
      const rendered = `${GATE_COPY[reason].title} ${GATE_COPY[reason].body}`.toLowerCase();
      expect(rendered).not.toContain('workspace');
    }
  });
});

describe('🔴 an action is offered only where one genuinely exists', () => {
  /**
   * ⚠️ **This is the half a refusal usually gets wrong.** ⛔ **A button that
   * cannot help is worse than no button** — it costs a click to learn the same
   * thing, and it implies the product thinks there is a way out.
   */
  it('a locked account is offered the reset that unlocks it', () => {
    expect(GATE_COPY.ACCOUNT_LOCKED.action).toEqual({
      label: 'Reset your password',
      href: '/forgot-password',
    });
  });

  it('⛔ a deleted or suspended account is offered nothing, and the body says who can help', () => {
    // ⚡ **There is no self-serve undelete**, and *"contact support"* as a button
    // would dress a dead end as a route.
    for (const reason of ['ACCOUNT_DELETED', 'ACCOUNT_SUSPENDED'] as const) {
      expect(GATE_COPY[reason].action).toBeNull();
      // ⚡ **`administ`, not `administers`** — one body says *"the person who
      // administers"* and the other *"an administrator"*, **and the rule being
      // asserted is that SOMEBODY WHO CAN HELP is named**, not which noun the
      // sentence happened to use.
      expect(GATE_COPY[reason].body.toLowerCase()).toContain('administ');
    }
  });

  it('⛔ step-up offers no control while its challenge does not exist', () => {
    // 📁 [TASK-1410](../../../docs/BACKLOG.md) makes it enforceable; this row
    // renders the gate. ⚡ **A *Confirm* button with nothing behind it is the
    // false-affordance class**, on a security screen.
    expect(GATE_COPY.STEPUP_REQUIRED.action).toBeNull();
  });

  it('✅ and somebody with access to something is sent to it', () => {
    // ⚡ **What makes NOT_MEMBER different from the two above**: this person has
    // organizations, just not that one.
    expect(GATE_COPY.INTENT_NOT_MEMBER.action?.href).toBe('/workspaces');
    expect(GATE_COPY.NO_WORKSPACE.action?.href).toBe('/onboarding');
  });
});

describe('⚠️ every action points at a route that exists', () => {
  it('and none of them is a guess', () => {
    // ⛔ **The defect this row exists to close, applied to itself**:
    // `resolveEntry` named eleven routes and none existed. ⚡ **A gate screen
    // whose own button 404s would be the same defect one layer in.**
    const shipped = ['/forgot-password', '/workspaces', '/onboarding'];

    for (const reason of GATE_REASONS) {
      const action = GATE_COPY[reason as GateReason].action;
      if (action === null) continue;
      expect(shipped, `${reason} points at ${action.href}`).toContain(action.href);
    }
  });
});
