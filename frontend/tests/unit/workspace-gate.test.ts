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

import { workspaceChoiceRequired, workspaceKnown } from '@/lib/shell/workspace-gate';

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

/**
 * 🔴 **[B-245](../../docs/BUGS.md) — rule 7 is a REFUSAL to guess, and it has
 * exactly one shape.**
 *
 * 📁 `Fortune Signora Workspace Chooser.dc.html` §02 rule 7, `WS_AMBIGUOUS`:
 * *"Two or more active memberships and no pin, no last-used. The system
 * genuinely cannot decide. **The chooser is mandatory here and only here.**"*
 *
 * ⛔ **The *only here* is the half worth guarding.** ⚡ Every other row of this
 * describe is a case where asking would be wrong — 📁 *"a confirmation screen
 * between authentication and work taxes every login to serve a minority of
 * them."*
 */
describe('🔴 rule 7 — the chooser is mandatory in exactly one case', () => {
  const AMBIGUOUS = {
    isLoading: false,
    error: null,
    activeWorkspace: null,
    workspaceCount: 2,
  } as const;

  it('✅ two memberships and nothing selected is the case it is for', () => {
    expect(workspaceChoiceRequired(AMBIGUOUS)).toBe(true);
  });

  it('⛔ one membership is rule 6 — "nothing to choose"', () => {
    /**
     * 📁 Rule 6, `WS_SOLE`: *"No picker, no confirmation, no strip."*
     * ⚠️ **`> 1` and not `>= 1`**, and this is the assertion that pins the
     * difference — a person with one organization who was asked to choose it
     * would be reading a screen with one row and no decision on it.
     */
    expect(workspaceChoiceRequired({ ...AMBIGUOUS, workspaceCount: 1 })).toBe(false);
  });

  it('⛔ no memberships is rule 8, and it has its own screen', () => {
    // 📁 Rule 8, `WS_NONE` → WS-D. ⛔ **A chooser with nothing to choose from
    // is not the answer to "you are in no organization".**
    expect(workspaceChoiceRequired({ ...AMBIGUOUS, workspaceCount: 0 })).toBe(false);
  });

  it('⛔ a read still in flight has not established anything', () => {
    // ⚡ **The list arrives before the selection effect runs**, so there is a
    // render with `activeWorkspace === null` and the answer merely late.
    expect(workspaceChoiceRequired({ ...AMBIGUOUS, isLoading: true })).toBe(false);
  });

  it('🔴 a FAILED read must never be read as a choice to make', () => {
    /**
     * 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) — *a failed read
     * must never render as an empty result.* ⛔ **A failure reports zero
     * memberships**, and sending somebody to the chooser because their
     * organizations could not be loaded states something about their access
     * from a fact about a request.
     *
     * ⚠️ **Asserted at a count that WOULD otherwise qualify**, so the error
     * clause is what makes this false and not the count.
     */
    expect(workspaceChoiceRequired({ ...AMBIGUOUS, error: new Error('502') })).toBe(false);
    expect(
      workspaceChoiceRequired({ ...AMBIGUOUS, error: true, workspaceCount: 4 }),
    ).toBe(false);
  });

  it('⛔ and a workspace already selected is not a question', () => {
    expect(
      workspaceChoiceRequired({ ...AMBIGUOUS, activeWorkspace: { id: 'w-1' } }),
    ).toBe(false);
  });

  it('⚡ `undefined` error is absence, not failure — the same trap `workspaceKnown` fell into', () => {
    expect(workspaceChoiceRequired({ ...AMBIGUOUS, error: undefined })).toBe(true);
  });
});
