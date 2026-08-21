/**
 * 🔴 **The ICP Builder design's central claim** — 📁 `Design Documents/Fortune
 * Signora ICP Builder.html`: ***"Every criterion is scored against closed-won
 * evidence, not opinion."***
 *
 * ⛔ **`GET /workspaces/{id}/icp-performance` shipped with NO consumer.** The
 * endpoint, `MeasureIcp` and `CriterionLift` are all on `main` with backend
 * tests, and no screen read them — so a customer could describe an ideal
 * customer and was never told whether it predicted anything.
 *
 * ⚡ **The fixtures below are the APPROVED contract shape**, field for field —
 * ⛔ no invented field, no fabricated capability, and nothing seeded into a
 * database that production will never have.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const performance = vi.hoisted(() => vi.fn());
vi.mock('@/lib/query/hooks/commercial', () => ({ useIcpPerformance: performance }));

import { IcpPerformance } from '@/components/commercial/icp-performance';
import type { CriterionLift, ProductCatalog } from '@/lib/api/types';

const PRODUCT = '11111111-1111-4111-8111-111111111111';

const CATALOG = {
  version: 1,
  products: [{ id: PRODUCT, name: 'Fleet Telematics', description: '' }],
  updated_at: null,
  updated_by: null,
} as unknown as ProductCatalog;

function lift(over: Partial<CriterionLift>): CriterionLift {
  return {
    criterion: 'industry',
    lift: 2.1,
    satisfied: 96,
    satisfied_won: 84,
    measured: 120,
    measured_won: 90,
    unmeasured: 0,
    is_directional: false,
    ...over,
  };
}

function measured(criteria: CriterionLift[], decided = 120) {
  performance.mockReturnValue({
    data: [{ product_id: PRODUCT, decided, criteria }],
    isPending: false,
    isError: false,
  });
  render(<IcpPerformance catalog={CATALOG} workspaceId="ws" />);
}

describe('a declared criterion is scored against outcomes, not opinion', () => {
  it('✅ states the multiple and the sample size it rests on', () => {
    measured([lift({})]);

    expect(screen.getByText(/2\.1× lift/)).toBeInTheDocument();
    // 📁 *"The sample size behind `lift` — read it before the multiple."*
    expect(screen.getByText('84 of 96 won')).toBeInTheDocument();
    // 🔴 **The honest denominator** — *"if this is small, nothing above it is
    // settled."*
    expect(screen.getByText('measured on 120 decided accounts')).toBeInTheDocument();
  });

  it('🔴 says a criterion is selecting AGAINST you, which is the useful case', () => {
    /**
     * 📁 The endpoint's own words: ***"below 1.0 it is selecting against you —
     * the last being the most useful thing this can say and the one nobody
     * expects."*** ⛔ **So it is toned as a risk and named, never hidden.**
     */
    measured([lift({ lift: 0.6 })]);

    expect(screen.getByText(/0\.6× against/)).toBeInTheDocument();
  });

  it('⛔ never renders an unmeasurable criterion as 1.0', () => {
    /**
     * 📁 The contract, in as many words: ***"Never render null as 1.0."*** ⚡
     * **The two mean opposite things** — 1.0 is *this tells you nothing*, null
     * is *nobody could check* — and collapsing them would state a measurement
     * that was never taken.
     */
    measured([lift({ lift: null, satisfied: 0, satisfied_won: 0, unmeasured: 40 })]);

    expect(screen.queryByText(/1\.0×/)).toBeNull();
    expect(screen.getByText(/Not measured/)).toBeInTheDocument();
    // ⚡ **And it says WHY** — an account nobody has described is not evidence
    // against the criterion.
    expect(screen.getByText(/40 accounts undescribed/)).toBeInTheDocument();
  });

  it('⚠️ marks a small sample directional, using the endpoint’s own threshold', () => {
    // ⛔ **Never recomputed here.** The threshold is the measurement's, and a
    // second copy would eventually disagree with it.
    measured([lift({ lift: 2.2, satisfied: 22, satisfied_won: 14, is_directional: true })]);

    expect(screen.getByText('Directional')).toBeInTheDocument();
  });

  it('✅ an undeclared ICP is an answer, not an error or a row of zeroes', () => {
    // 📁 *"Empty when no ICP has been declared — not an error. A workspace that
    // has not described who buys from it is in a state to wait in, and the
    // surface says so rather than showing zeroes."*
    performance.mockReturnValue({ data: [], isPending: false, isError: false });
    render(<IcpPerformance catalog={CATALOG} workspaceId="ws" />);

    expect(screen.getByText(/Nothing to measure yet/)).toBeInTheDocument();
    expect(screen.queryByText(/0\.0×/)).toBeNull();
  });

  it('⛔ a failed read says so rather than reading as an empty measurement', () => {
    // 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) — a failed read must
    // never render as an empty result.
    performance.mockReturnValue({ data: undefined, isPending: false, isError: true });
    render(<IcpPerformance catalog={CATALOG} workspaceId="ws" />);

    expect(screen.queryByText(/Nothing to measure yet/)).toBeNull();
    expect(screen.getByText(/could not/i)).toBeInTheDocument();
  });

  it('⛔ invents none of the design’s unproduced controls', () => {
    /**
     * 📁 The design draws `Must`/`Should`/`Bonus`/`Exclude` tiers, a scoring
     * model with `Refit on last 8 quarters`, a preview, templates, a TAM funnel
     * and AI suggestions. ⛔ **None has a producer**, and
     * [§20c](../../../CLAUDE.md) ships a designed absence rather than a control
     * that does nothing.
     */
    measured([lift({})]);

    for (const absent of ['Must', 'Should', 'Bonus', 'Exclude', 'Refit', 'Estimated TAM']) {
      expect(screen.queryByText(absent)).toBeNull();
    }
  });
});
