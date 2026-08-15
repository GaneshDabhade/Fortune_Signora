// @vitest-environment jsdom
//
// ⚠️ **Declared per file.** `tests/unit/**` runs in node and this exercises a
// React hook, so it needs a DOM. ⛔ It is not a component test — there is no
// component — which is why it stays here rather than moving to
// `tests/components/`.
/**
 * **The engine's one production caller** — [TASK-1401](../../../docs/BACKLOG.md).
 *
 * 📁 **[`principal.ts`](../../lib/entry/principal.ts) has said *"`resolveEntry`
 * has zero callers"* since it was written.** ⚡ **These are the tests that stop
 * that being true.**
 */
import { renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useEntryDecision } from '@/lib/entry/use-entry';

const query = vi.hoisted(() => ({ current: {} as Record<string, unknown> }));
const search = vi.hoisted(() => ({ current: new URLSearchParams() }));

vi.mock('@/lib/query/hooks', () => ({ useWorkspaces: () => query.current }));
vi.mock('next/navigation', () => ({ useSearchParams: () => search.current }));

function answered(ids: string[]) {
  query.current = {
    isPending: false,
    isError: false,
    error: null,
    data: { items: ids.map((id) => ({ id, name: id })) },
  };
}

function decide(next?: string) {
  search.current = new URLSearchParams(next === undefined ? '' : `next=${encodeURIComponent(next)}`);
  return renderHook(() => useEntryDecision()).result.current;
}

describe('🔴 a read that has not answered never decides', () => {
  it('⚠️ is resolving while the query is pending', () => {
    query.current = { isPending: true, isError: false, error: null, data: undefined };
    expect(decide().status).toBe('resolving');
  });

  /**
   * 🔴 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md), and this is the
   * assertion that survives fire-testing.**
   *
   * ⛔ **Deleting the `isError` branch does NOT make this decide wrongly** —
   * `data` is `undefined` on a failure, so the routing property is protected
   * twice and the second guard is the load-bearing one. ⚡ **What deleting it
   * DOES produce is `resolving` forever: a person stranded on a spinner inside
   * a flow whose only exit is this decision.**
   *
   * ✅ **So the property asserted is the one that actually goes red.**
   */
  it('🔴 reports a failed read as unresolved, distinguishably from a pending one', () => {
    query.current = {
      isPending: false,
      isError: true,
      error: new Error('the network refused'),
      data: undefined,
    };
    const state = decide();
    expect(state.status).toBe('unresolved');
    expect(state.status === 'unresolved' && state.error.message).toBe('the network refused');
  });

  it('⛔ still reports a failure when the query threw something that is not an Error', () => {
    query.current = { isPending: false, isError: true, error: 'a string', data: undefined };
    const state = decide();
    expect(state.status).toBe('unresolved');
    expect(state.status === 'unresolved' && state.error).toBeInstanceOf(Error);
  });

  /**
   * ⛔ **The one that would hurt a real customer.** ⚡ **A failed read must never
   * be mistaken for *this person belongs to nothing*** — rule 10 routes to
   * `/workspaces/none`, **which tells somebody with five workspaces that they
   * have none, and navigates them there.**
   */
  it('🔴 never answers NO_WORKSPACE for a read that failed', () => {
    query.current = { isPending: false, isError: true, error: new Error('502'), data: undefined };
    const state = decide();
    expect(state.status).not.toBe('resolved');
  });
});

describe('✅ the engine decides, and the caller does not', () => {
  it('⚡ enters a sole workspace without a picker — rule 11', () => {
    answered(['ws-only']);
    const state = decide();
    expect(state.status === 'resolved' && state.decision.reason).toBe('SOLE_WORKSPACE');
    expect(state.status === 'resolved' && state.decision.route).toBe('/w/ws-only/home');
  });

  it('⚡ offers the chooser when several are possible and nothing says which — rule 13', () => {
    answered(['ws-1', 'ws-2']);
    const state = decide();
    expect(state.status === 'resolved' && state.decision.reason).toBe('AMBIGUOUS');
    expect(state.status === 'resolved' && state.decision.route).toBe('/workspaces');
  });

  it('⚡ says so when there is genuinely nothing — rule 10', () => {
    answered([]);
    const state = decide();
    expect(state.status === 'resolved' && state.decision.reason).toBe('NO_WORKSPACE');
    expect(state.status === 'resolved' && state.decision.route).toBe('/workspaces/none');
  });
});

describe('⛔ the intent is honoured, and refused on exactly the rules intent.ts states', () => {
  it('✅ goes where the person asked, past Home — rule 06', () => {
    answered(['ws-1']);
    const state = decide('/accounts/acc-9');
    expect(state.status === 'resolved' && state.decision.reason).toBe('INTENT_HONOURED');
    expect(state.status === 'resolved' && state.decision.route).toBe('/accounts/acc-9');
  });

  /**
   * 🔴 **Decided locally; the server is never asked** — 📁 [§7](../../../CLAUDE.md),
   * *404 never 403*, applied before the question rather than after.
   */
  it('🔴 refuses a deep link into a workspace they are not in — rule 09', () => {
    answered(['ws-1']);
    const state = decide('/w/ws-someone-elses/home');
    expect(state.status === 'resolved' && state.decision.reason).toBe('INTENT_NOT_MEMBER');
    expect(state.status === 'resolved' && state.decision.route).toBe('/workspaces');
  });

  /**
   * 🔴 **The open-redirect refusal, exercised through the caller rather than
   * through `captureIntent` directly** — ⚡ **because an attacker never calls
   * `captureIntent`; they craft the `?next=`, which is this path.**
   */
  it.each([
    ['//evil.example', 'protocol-relative'],
    ['/\\evil.example', 'backslash protocol-relative'],
    ['https://evil.example', 'absolute'],
    ['javascript:alert(1)', 'scheme'],
    ['/\njavascript:alert(1)', 'scheme behind a newline the browser strips'],
    ['accounts', 'no leading slash'],
  ])('⛔ discards %s (%s) and decides as if no intent was given', (hostile) => {
    answered(['ws-only']);
    const state = decide(hostile);
    expect(state.status === 'resolved' && state.decision.reason).toBe('SOLE_WORKSPACE');
    expect(state.status === 'resolved' && state.decision.route).toBe('/w/ws-only/home');
  });
});
