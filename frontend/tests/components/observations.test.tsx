/**
 * The raw provider readings, as a customer reads them.
 *
 * **The one section on the account brief that does not speak in Signora's
 * voice.** Everywhere else the product states a conclusion; here it shows the
 * material and says who reported it. The tests that matter are therefore about
 * attribution and about the two ways this section could quietly lie: turning a
 * first sighting into a change that never happened, and printing a magnitude
 * where the pipeline has none.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ObservationList, attributeLabel } from '@/components/intelligence/observations';
import type { AccountObservation } from '@/lib/api/types';

function observation(overrides: Partial<AccountObservation> = {}): AccountObservation {
  return {
    id: '11111111-1111-4111-8111-111111111111',
    attribute: 'employee_count',
    provider: 'clearbit',
    kind: 'value_changed',
    direction: 'increased',
    previous_value: 340,
    current_value: 391,
    magnitude: 0.15,
    observed_at: new Date().toISOString(),
    previous_observed_at: null,
    recorded_at: new Date().toISOString(),
    ...overrides,
  };
}

describe('a reading names the provider that reported it', () => {
  it('shows who said so', () => {
    render(<ObservationList observations={[observation()]} isLoading={false} />);

    expect(screen.getByText(/clearbit/)).toBeInTheDocument();
  });

  it('renders the transition in the customer’s words, not the pipeline’s', () => {
    render(<ObservationList observations={[observation()]} isLoading={false} />);

    expect(screen.getByText('Headcount')).toBeInTheDocument();
    expect(screen.queryByText(/employee_count/)).not.toBeInTheDocument();
  });

  it('renders both sides of the change', () => {
    render(<ObservationList observations={[observation()]} isLoading={false} />);

    expect(screen.getByText(/340 → 391/)).toBeInTheDocument();
  });
});

describe('a first sighting is not a change from nothing', () => {
  it('says the value was recorded rather than that it moved', () => {
    /**
     * **The defect this prevents.** `— → 400` reads as *"they grew to 400"*.
     * What happened is *"we learned they are 400"*. Only one of those is true,
     * and the false one is the one a seller would repeat on a call.
     */
    render(
      <ObservationList
        observations={[observation({ previous_value: null, current_value: 400 })]}
        isLoading={false}
      />,
    );

    expect(screen.getByText(/recorded as 400/)).toBeInTheDocument();
    expect(screen.queryByText(/→/)).not.toBeInTheDocument();
  });
});

describe('a magnitude is shown only where the pipeline has one', () => {
  it('renders a percentage when there is one', () => {
    render(<ObservationList observations={[observation({ magnitude: 0.15 })]} isLoading={false} />);

    expect(screen.getByText(/15%/)).toBeInTheDocument();
  });

  it('renders none when there is none', () => {
    /**
     * A change of country has no magnitude. Printing `1` would give a reader a
     * number they could sort by — and sorting by it would rank a country
     * change above a 15% headcount rise.
     */
    render(
      <ObservationList
        observations={[
          observation({
            attribute: 'country',
            previous_value: 'United Kingdom',
            current_value: 'Ireland',
            direction: 'changed',
            magnitude: null,
          }),
        ]}
        isLoading={false}
      />,
    );

    expect(screen.getByText(/United Kingdom → Ireland/)).toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });
});

describe('an account nothing has been reported about', () => {
  it('is an answer rather than a failure', () => {
    /**
     * Most accounts, most weeks. An error-shaped empty state would teach a
     * reader to distrust the page on the days it is right.
     */
    render(<ObservationList observations={[]} isLoading={false} />);

    expect(screen.getByText('Nothing recorded yet')).toBeInTheDocument();
  });

  it('distinguishes what Signora was told from what happened', () => {
    render(<ObservationList observations={[]} isLoading={false} />);

    expect(
      screen.getByText(/not the same as nothing having happened/i),
    ).toBeInTheDocument();
  });
});

describe('an attribute nobody has written copy for', () => {
  it('renders readably rather than as a key', () => {
    /**
     * **The fallback is the point.** A `Record<>` covering every
     * `ClaimAttribute` would send whoever adds one to this file to invent
     * customer copy for it. This fails in the direction that costs a customer
     * nothing.
     */
    expect(attributeLabel('some_new_attribute')).toBe('Some new attribute');
  });

  it('prefers the written label where one exists', () => {
    expect(attributeLabel('employee_count')).toBe('Headcount');
  });
});

describe('a failed fetch is not an empty account', () => {
  /**
   * **The defect this closes, found by reading 410 rather than by a failure.**
   * The section shipped handling loading, empty and populated — and rendered a
   * failed request as "Nothing recorded yet". A reader would take away a claim
   * about their customer that Signora never made.
   *
   * `ValidationBlock` learned this on the same page: *"the section used to
   * render all three as absence, which made an outage indistinguishable from a
   * quiet account."*
   */
  it('says Signora could not load it, not that nothing happened', () => {
    render(<ObservationList observations={undefined} isLoading={false} isError />);

    expect(screen.getByText(/could not load what changed/i)).toBeInTheDocument();
    expect(screen.queryByText('Nothing recorded yet')).not.toBeInTheDocument();
  });

  it('does not blame the account for a failure of ours', () => {
    render(<ObservationList observations={undefined} isLoading={false} isError />);

    expect(screen.getByText(/Nothing has changed about the account/i)).toBeInTheDocument();
  });

  it('shows nothing stale beside the failure', () => {
    /**
     * A cached list rendered under an error message reads as current. If the
     * fetch failed, the list is not the answer to the question just asked.
     */
    render(
      <ObservationList observations={[observation()]} isLoading={false} isError />,
    );

    expect(screen.queryByText('Headcount')).not.toBeInTheDocument();
  });
});

/**
 * 🔴 **[B-299](../../../docs/BUGS.md) ⑨ — the eighth invented heading on this
 * surface, and the only one that was a PEER of the heading above it.**
 *
 * ⛔ **The card carried `<CardTitle>What changed, and who says so</CardTitle>`,
 * which `card.tsx` renders as an `h2`** — the same level as the *Signals
 * timeline* section heading two lines up. ⚠️ **So the design's section
 * announced itself twice, in two vocabularies, at one outline level**, and a
 * reader navigating by heading met an invented one immediately after the
 * design's.
 *
 * 📁 **Measured across all 35 design documents**: *"What changed, and who says
 * so"* appears **zero** times, and *"What changed"* appears **zero** times in
 * Account 360.
 */
describe('🔴 the list carries no heading of its own — B-299 ⑨', () => {
  it('⛔ renders no heading at all, invented or otherwise', () => {
    render(<ObservationList observations={[observation()]} isLoading={false} />);

    expect(screen.queryAllByRole('heading')).toHaveLength(0);
  });

  /**
   * ⚠️ **The vacuity half.** ⛔ A component rendering nothing would satisfy the
   * assertion above — 📁 the *instrument too narrow* failure, which passes
   * silently. ✅ **The rows are still there; only the title went.**
   */
  it('⚠️ vacuity guard — the observation itself still renders', () => {
    render(<ObservationList observations={[observation()]} isLoading={false} />);

    expect(screen.getByRole('list')).toBeInTheDocument();
    expect(screen.getAllByRole('listitem').length).toBeGreaterThan(0);
  });
});
