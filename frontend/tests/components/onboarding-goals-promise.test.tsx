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

function withFeatures(features: string[]) {
  useOnboarding.mockReturnValue({
    run: { id: 'r1', goals: [], features },
    error: null,
    isLoading: false,
    isSaving: false,
    save: vi.fn(),
  });
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

    // ⛔ **The promise sentence is absent entirely.**
    expect(screen.queryByText(/Signora will open on/)).not.toBeInTheDocument();
    // ⚠️ **Scoped to the promise, not to the page.** ⚡ ***"Forecast
    // accurately"* is one of the six goals and MUST still be offerable** — the
    // defect was never that the word appears, it was that the product claimed
    // to open on a screen it does not have.
    expect(screen.queryByText(/the Executive Dashboard/)).not.toBeInTheDocument();
  });

  /**
   * ✅ **And the sentence still appears when it is true**, which is what stops
   * the repair from being *delete the feature*.
   */
  it('✅ still names the ones that ship', () => {
    withFeatures(['signals', 'opportunity_intelligence']);

    render(<GoalsForm />);

    expect(screen.getByText(/Signora will open on/)).toBeInTheDocument();
    expect(screen.getByText('Signals')).toBeInTheDocument();
    // ⛔ **And not the unbuilt half of the same goal.**
    expect(screen.queryByText(/Opportunity Intelligence/)).not.toBeInTheDocument();
  });

  /**
   * ⚠️ **A goal with one shipped feature and one absent one keeps the
   * sentence** — ⛔ **the repair filters the list, it does not suppress the
   * line whenever anything is missing.**
   */
  it('✅ a partly-built goal still says the true half', () => {
    withFeatures(['companies', 'ai_research']);

    render(<GoalsForm />);

    expect(screen.getByText('Companies')).toBeInTheDocument();
    expect(screen.queryByText(/Research/)).not.toBeInTheDocument();
  });
});
