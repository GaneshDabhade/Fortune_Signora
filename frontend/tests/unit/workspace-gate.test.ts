/**
 * 🔴 **[B-237](../../../docs/BUGS.md)'s second symptom, as a truth table.**
 *
 * ⚡ **QE measured it in a browser and the number is the finding**: `/` made
 * **22 workspace reads in 22 seconds**, in a cycle of `1.0s · 2.0s · 0.03s`
 * repeating forever — **the two retries `shouldRetry` allows for a 5xx, then a
 * fresh query 30ms later.** ⛔ **`isError` was reached and discarded every
 * time**, and the customer saw *"Loading…"* indefinitely.
 *
 * 🔴 **The gate was the cause.** A query stays `pending` while its retries are
 * in flight, so `isLoading` was true for ~3s of every 3.1s cycle and the gate
 * was shut almost continuously. **The ~30ms it opened was long enough for the
 * entry page to mount, add an observer to a query holding no data, trigger
 * React Query's refetch-on-mount — and shut the gate again.**
 */
import { describe, expect, it } from 'vitest';

import { workspaceKnown } from '@/lib/shell/workspace-gate';

const WS = { id: 'w1', name: 'Northwind' };

describe('🔴 a failed read is an answer', () => {
  it('is known when the read failed, however it failed', () => {
    // ⛔ **The single combination that produced the loop.** `isLoading` is
    // true here because retries were in flight — the state the gate spent
    // ~97% of its time in.
    expect(
      workspaceKnown({
        isLoading: true,
        error: new Error('500'),
        activeWorkspace: null,
        workspaceCount: 0,
      }),
    ).toBe(true);
  });

  it('is known when the read failed and has settled', () => {
    expect(
      workspaceKnown({
        isLoading: false,
        error: new Error('500'),
        activeWorkspace: null,
        workspaceCount: 0,
      }),
    ).toBe(true);
  });
});

describe('⚡ and the states that were already right stay right', () => {
  it('⛔ is NOT known while a first read is in flight', () => {
    // The positive control for the error case above: if the gate simply
    // returned true always, the test above would pass and this would fail.
    expect(
      workspaceKnown({
        isLoading: true,
        error: null,
        activeWorkspace: null,
        workspaceCount: 0,
      }),
    ).toBe(false);
  });

  it('is known once an organization is active', () => {
    expect(
      workspaceKnown({
        isLoading: false,
        error: null,
        activeWorkspace: WS,
        workspaceCount: 1,
      }),
    ).toBe(true);
  });

  it('is known when the list came back empty', () => {
    expect(
      workspaceKnown({
        isLoading: false,
        error: null,
        activeWorkspace: null,
        workspaceCount: 0,
      }),
    ).toBe(true);
  });

  it('🔴 is NOT known in the gap between the list landing and the choice', () => {
    /**
     * ⚠️ **The subtle half, and it predates this change.** 📁 The provider
     * picks the active workspace in an effect that runs AFTER the list
     * arrives, so there is a render where loading has finished and
     * `activeWorkspace` is still `null` with a non-empty list. **`!isLoading`
     * alone would open the gate there.**
     */
    expect(
      workspaceKnown({
        isLoading: false,
        error: null,
        activeWorkspace: null,
        workspaceCount: 3,
      }),
    ).toBe(false);
  });
});

describe('⛔ an absent error is not a failure', () => {
  it('treats undefined as no error, not as one', () => {
    /**
     * 🔴 **`workspacesError !== null` turned twelve tests red** on mocks that
     * omit `error`, and it is the same shape as reading an empty result as
     * evidence. ⚡ **Truthiness, matching `settings/audit/page.tsx`.**
     */
    expect(
      workspaceKnown({
        isLoading: true,
        error: undefined,
        activeWorkspace: null,
        workspaceCount: 0,
      }),
    ).toBe(false);
  });
});
