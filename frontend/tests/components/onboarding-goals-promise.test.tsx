/**
 * **The goals step, at the seam that failed** — [B-191](../../../docs/BUGS.md),
 * repairing [B-256](../../../docs/BUGS.md)'s proof.
 *
 * 🔴 **QE fire-tested my fix and it did not fire.** ⛔ **Reverting the two
 * component lines left `reachable` intact and the whole suite green**, with the
 * screen promising Forecast again — because
 * [`onboarding-promises.test.ts`](../unit/onboarding-promises.test.ts) tests
 * `reachable` **and `reachable` was never the defect.** The defect was that the
 * component called `run.features.map(readable)` instead.
 *
 * ⚡ **QE's rule, and it is the right one**: **a guard belongs at the seam that
 * failed, not at the component downstream of it.** ⚠️ **The distance is the
 * whole story** — [B-255](../../../docs/BUGS.md)'s guard fires because its
 * defect and its proof live in the same component; this one did not because
 * they did not.
 *
 * ✅ **So this renders the SCREEN and reads what a customer would.**
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const useOnboarding = vi.hoisted(() => vi.fn());

/**
 * ⚡ **`useSearchParams` and `useWorkspaces` added by
 * [TASK-1401](../../../docs/BACKLOG.md)** — ⛔ **the flow no longer chooses
 * where somebody lands**, so it reaches the entry engine two files away, and
 * the engine reads memberships and the attempted route.
 */
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));
vi.mock('@/lib/query/hooks', () => ({
  useWorkspaces: () => ({
    isPending: false,
    isError: false,
    error: null,
    data: { items: [{ id: 'ws-only', name: 'Northwind' }] },
  }),
}));
vi.mock('@/app/(onboarding)/onboarding/use-onboarding', () => ({ useOnboarding }));
vi.mock('@/lib/api/onboarding', () => ({
  chooseGoals: vi.fn(),
  finishOnboarding: vi.fn(),
}));

import { GoalsForm } from '@/app/(onboarding)/onboarding/goals-form';

function withFeatures(features: string[], featuresOff: string[] = []) {
  useOnboarding.mockReturnValue({
    run: { id: 'r1', goals: [], features, features_off: featuresOff },
    error: null,
    isLoading: false,
    isSaving: false,
    save: vi.fn(),
    advance: vi.fn(),
  });
}

/**
 * ⚡ **The card, or `null` when there is nothing true to put in it.**
 *
 * ⛔ **Every assertion here is scoped to it and never to the page.** 📁 The
 * original test already learned this once — *"scoped to the promise, not to
 * the page"* — because ***"Forecast accurately"* is one of the six goals and
 * MUST still be offerable.** ⚠️ **The defect was never that the word appears;
 * it was that the product claimed to open on a screen it does not have.**
 */
function card(): HTMLElement | null {
  return screen.queryByText(/Based on these/)?.closest('div') ?? null;
}

beforeEach(() => useOnboarding.mockReset());

describe('🔴 the screen names only what a customer can reach', () => {
  /**
   * 🔴 **The assertion the defect failed, on the screen rather than on a
   * helper.** 📁 `FORECAST_ACCURATELY` is the FIRST of the six goals, and its
   * two features are `forecast` and `executive_dashboard` — **neither of which
   * has a route on any branch.**
   */
  it('🔴 says nothing about Forecast, because there is no Forecast', () => {
    withFeatures(['forecast', 'executive_dashboard']);

    render(<GoalsForm />);

    // ⛔ **The card is absent entirely** — nothing reachable is on, nothing
    // reachable is off, so there is no true sentence to write.
    expect(card()).toBeNull();
    expect(screen.queryByText(/the Executive Dashboard/)).not.toBeInTheDocument();
  });

  /**
   * ✅ **And the sentence still appears when it is true**, which is what stops
   * the repair from being *delete the feature*.
   */
  it('✅ still names the ones that ship', () => {
    withFeatures(['signals', 'opportunity_intelligence']);

    render(<GoalsForm />);

    expect(card()).not.toBeNull();
    expect(card()).toHaveTextContent('Signals');
    // ⛔ **And not the unbuilt half of the same goal.**
    expect(card()).not.toHaveTextContent('Opportunity Intelligence');
  });

  /**
   * ⚠️ **A goal with one shipped feature and one absent one keeps the
   * sentence** — ⛔ **the repair filters the list, it does not suppress the
   * line whenever anything is missing.**
   */
  it('✅ a partly-built goal still says the true half', () => {
    withFeatures(['companies', 'ai_research']);

    render(<GoalsForm />);

    expect(card()).toHaveTextContent('Companies');
    expect(card()).not.toHaveTextContent('Research');
  });
  /**
   * 🔴 **The SAME defect has a second surface now, and it is the new one.**
   *
   * ⚡ `features_off` arrived so the card can say the design's other half —
   * *"and leave Marketing attribution off"*. ⛔ **An unreachable capability is
   * no more nameable as OFF than as ON**: telling somebody Signora *left
   * Forecast off* still asserts that Forecast is a thing they could have had.
   *
   * ⚠️ **This is [B-256](../../../docs/BUGS.md) one clause over**, and the
   * reason the filter is applied to both lists rather than to the one that
   * failed.
   */
  it('🔴 will not name an unreachable capability as OFF either', () => {
    withFeatures(['signals'], ['forecast', 'executive_dashboard']);

    render(<GoalsForm />);

    expect(card()).toHaveTextContent('Signals');
    expect(card()).not.toHaveTextContent('Forecast');
    expect(card()).not.toHaveTextContent('Executive Dashboard');
    // ⛔ **And with nothing true to say about the off half, the clause is
    // absent** rather than trailing into nothing.
    expect(card()).not.toHaveTextContent('leave');
  });

  /**
   * ✅ **Both halves, when both are true.** ⚡ This is the design's sentence as
   * the product can actually say it.
   */
  it('✅ says both halves when both are reachable', () => {
    withFeatures(['signals'], ['companies', 'reports']);

    render(<GoalsForm />);

    expect(card()).toHaveTextContent('switch on');
    expect(card()).toHaveTextContent('leave');
    expect(card()).toHaveTextContent('Signals');
    expect(card()).toHaveTextContent('Companies and Reports');
  });
});
