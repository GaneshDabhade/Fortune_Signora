/**
 * **The onboarding flow's surfaces** — [TASK-1421](../../../docs/BACKLOG.md),
 * against 📁 `Fortune Signora Onboarding.dc.html`.
 *
 * 🔴 **Roughly 2,600 lines across eight files, and nothing in this repository
 * rendered any of them.** ⛔ **It is the first experience every customer has**,
 * and it had no witness at all — 📁 which is exactly how
 * [B-1085](../../../docs/BUGS.md) shipped on Home.
 *
 * ⚠️ **Shallow on purpose.** ⛔ Not a substitute for each form's own
 * assertions; ✅ **the witness**, plus the handful of claims the design states
 * in words strong enough to pin.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn() }),
  usePathname: () => '/onboarding/welcome',
}));

import { OnboardingWelcome } from '@/app/(onboarding)/onboarding/welcome';
import { ProductIntroduction } from '@/app/(onboarding)/onboarding/introduction';
import { OnboardingRail, RailNote } from '@/app/(onboarding)/onboarding/rail';
import { COUNTED_TOTAL, RAIL_STEPS } from '@/app/(onboarding)/onboarding/steps';

/** ⚡ **The four ways an absence reaches a screen**, plus B-1085's markers. */
const NEVER = ['undefined', 'null', 'NaN', '[object Object]', '/**', '*/'];

const SURFACES: readonly (readonly [string, () => React.ReactElement])[] = [
  ['welcome, verified', () => <OnboardingWelcome firstName="Aria" emailVerified />],
  [
    // ⚡ **The nullable branch** — somebody who signed up with no name, which is
    // every SSO identity that publishes only an address.
    'welcome, no name and unverified',
    () => <OnboardingWelcome firstName={null} emailVerified={false} />,
  ],
  ['the product introduction', () => <ProductIntroduction />],
  [
    'the rail, mid-flow',
    () => (
      <OnboardingRail
        steps={RAIL_STEPS}
        currentId="you"
        completedIds={['welcome']}
        progress={{ step: 2, of: COUNTED_TOTAL }}
        footer={<RailNote>About 90 seconds.</RailNote>}
      />
    ),
  ],
];

describe('⛔ no onboarding surface prints an absence, a comment, or an object', () => {
  for (const [name, element] of SURFACES) {
    it(`✅ ${name}`, () => {
      const { container } = render(element());
      const text = container.textContent ?? '';
      // ⚡ **The vacuity half** — an empty container satisfies every assertion
      // below, and these components return real markup or nothing at all.
      expect(text.trim().length).toBeGreaterThan(40);
      for (const forbidden of NEVER) {
        expect(text).not.toContain(forbidden);
      }
    });
  }
});

describe('📁 the three claims the design states strongly enough to pin', () => {
  it('🔴 the fourth promise is verbatim, because it is a commitment about a customer’s CRM', () => {
    /**
     * 📁 **The component's own note, and it is right**: *"the fourth must not
     * be softened — **Read-only to start. Nothing is written without your
     * approval.** It is a commitment about what the product will do to a
     * customer's CRM, and screen `07` repeats it beside the actual consent —
     * two places, one sentence, and neither is the place to improve the
     * wording."*
     *
     * ⛔ **So this is asserted verbatim rather than by keyword.** A paraphrase
     * would pass a looser test and break the promise.
     */
    render(<OnboardingWelcome firstName="Aria" emailVerified />);
    expect(
      screen.getByText('Read-only to start. Nothing is written without your approval.'),
    ).toBeInTheDocument();
  });

  it('⛔ the brand mark and the step counter are ALTERNATIVES, never a stack', () => {
    /**
     * 📁 **The rail's own prop docstring**: *"the design's **Step n of 4**
     * eyebrow and its 4px track. ⛔ **Absent on Welcome**, which the design
     * gives the brand mark instead — **the two are alternatives rather than a
     * stack**."*
     *
     * ⚡ **And the mark is `Fortune Signora`, correctly** — 📁 [§4](../../../CLAUDE.md)
     * reserves the combined brand for branding surfaces, and this is the last
     * screen before the application opens. ⛔ **Everywhere past it the product
     * is `Signora`, alone.**
     */
    const welcome = render(
      <OnboardingRail steps={RAIL_STEPS} currentId="welcome" completedIds={[]} />,
    );
    expect(screen.getByText('Fortune Signora')).toBeInTheDocument();
    expect(screen.queryByText(/Step \d+ of \d+/)).toBeNull();
    welcome.unmount();

    render(
      <OnboardingRail
        steps={RAIL_STEPS}
        currentId="you"
        completedIds={['welcome']}
        progress={{ step: 2, of: COUNTED_TOTAL }}
      />,
    );
    expect(screen.getByText('Step 2 of 4')).toBeInTheDocument();
    expect(screen.queryByText('Fortune Signora')).toBeNull();
  });

  it('⚡ a person with no name is greeted by the product, not by an empty space', () => {
    // ⛔ **`Welcome, ` with nothing after it is the absence collapsed into a
    // value** — the class this lane keeps finding. ✅ The product names itself
    // instead.
    render(<OnboardingWelcome firstName={null} emailVerified={false} />);

    expect(screen.getByText('Welcome to Signora')).toBeInTheDocument();
    expect(screen.queryByText(/^Welcome,\s*$/)).toBeNull();
  });
});
