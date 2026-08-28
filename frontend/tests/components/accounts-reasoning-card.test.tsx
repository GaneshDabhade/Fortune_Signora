/**
 * **The AI reasoning card** — 📁 `Fortune Signora Account 360.dc.html` §14.
 *
 * 🔴 **Nothing rendered it**, and it has the branch this repository keeps
 * finding defects in: 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) —
 * *a failed read must never render as an empty result.*
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const useAccountDecisionPackage = vi.hoisted(() => vi.fn());

vi.mock('@/lib/query/hooks', () => ({ useAccountDecisionPackage }));

import { ReasoningCard } from '@/components/accounts/reasoning';
import { ApiError } from '@/lib/api/client';

const NEVER = ['undefined', 'null', 'NaN', '[object Object]', '/**', '*/'];

/**
 * ⚡ **Built through the real constructor** — `ApiError(status, body)`, with
 * the API's own envelope. ⛔ **A hand-shaped object with a `status` field would
 * satisfy `instanceof` never**, and this lane has already spent a probe on
 * exactly that: a bare error body meant the correlation id never rendered.
 */
function apiError(status: number, message: string): ApiError {
  return new ApiError(status, {
    message,
    code: status === 404 ? 'not_found' : 'internal_error',
    correlation_id: 'corr-1',
  });
}

const PACKAGE = {
  account_id: 'a1',
  summary: { text: 'Renewal risk is rising on two of three signals.' },
  stated_reasoning: [
    { text: 'The champion stopped replying on 2 August.', evidence: ['e1', 'e2'] },
    { text: 'Two support escalations opened in the same week.', evidence: ['e3'] },
  ],
  supporting_evidence: ['e1', 'e2', 'e3'],
  support: { level: 'strong', corroborating_providers: ['hubspot', 'gong'] },
  model: 'claude-opus-5',
  prompt_name: 'account-conclusion',
  prompt_version: 4,
};

function card() {
  return render(<ReasoningCard accountId="a1" workspaceId="w1" />);
}

beforeEach(() => {
  vi.clearAllMocks();
  useAccountDecisionPackage.mockReturnValue({
    isPending: false,
    error: null,
    data: PACKAGE,
  });
});

describe('🔴 the three answers this card can give are three different answers', () => {
  it('⛔ a 404 is "not concluded yet", which is an ANSWER', () => {
    /**
     * ⚡ **The endpoint returns 404 when Signora has reached no conclusion**,
     * and that is a fact rather than a failure. ⛔ **Rendering it as an outage
     * would tell somebody the product is broken when it is simply waiting for
     * evidence.**
     */
    useAccountDecisionPackage.mockReturnValue({
      isPending: false,
      error: apiError(404, 'No decision package'),
      data: undefined,
    });
    const { container } = card();

    expect(screen.getByText(/has not reached a conclusion/)).toBeInTheDocument();
    expect(screen.queryByText(/could not/i)).toBeNull();
    for (const f of NEVER) expect(container.textContent ?? '').not.toContain(f);
  });

  it('🔴 anything else is an outage, and says so', () => {
    /**
     * 📁 **P-A.** ⛔ **The two must not collapse**: *"Signora has not concluded
     * anything"* on a screen where the read failed is the product claiming to
     * know something it does not.
     */
    useAccountDecisionPackage.mockReturnValue({
      isPending: false,
      error: apiError(500, 'Upstream failed'),
      data: undefined,
    });
    const { container } = card();

    expect(screen.getByText(/could not load/i)).toBeInTheDocument();
    expect(screen.queryByText(/has not reached a conclusion/)).toBeNull();
    for (const f of NEVER) expect(container.textContent ?? '').not.toContain(f);
  });

  it('✅ and a package renders its reasoning as an ordered list', () => {
    // ⛔ **`<ol>` because the steps are ORDERED and a screen reader should hear
    // that** — the rail beside them is the same fact drawn.
    card();

    const steps = screen.getAllByRole('listitem');
    expect(steps).toHaveLength(PACKAGE.stated_reasoning.length);
    expect(steps[0]).toHaveTextContent('The champion stopped replying');
  });
});

describe('⛔ no count is rendered that could be zero', () => {
  it('📁 the source badge is absent while unconcluded, never "0 sources"', () => {
    /**
     * ⚡ **A package is refused before storage unless it cites something**, so
     * a zero would describe a state that cannot exist. ⛔ **Rendering one would
     * be the product reporting an impossible fact about itself.**
     */
    useAccountDecisionPackage.mockReturnValue({
      isPending: false,
      error: apiError(404, 'No decision package'),
      data: undefined,
    });
    const { container } = card();

    // ⚠️ **The pin comes first, and it is the whole reason this test is
    // evidence.** ⛔ **Both assertions below are negative, and a negative
    // passes on a card that never rendered** — a crashed fixture, or a mock
    // aimed at a barrel this component does not import, would make them green
    // while proving nothing. ⚡ **`getByText` THROWS when absent**, so it
    // establishes that there is a rendered card to be negative about.
    expect(screen.getByText(/has not reached a conclusion/)).toBeInTheDocument();

    expect(container.textContent ?? '').not.toContain('0 sources');
    expect(container.textContent ?? '').not.toContain('sources');
  });

  it('✅ and it is singular at one, plural above', () => {
    useAccountDecisionPackage.mockReturnValue({
      isPending: false,
      error: null,
      data: { ...PACKAGE, supporting_evidence: ['e1'] },
    });
    const one = render(<ReasoningCard accountId="a1" workspaceId="w1" />);
    expect(screen.getByText('1 source')).toBeInTheDocument();
    one.unmount();

    // ⚠️ **The mock has to be reset too** — ⛔ `card()` only renders, and the
    // first draft of this test asserted the plural against the singular
    // fixture still in place.
    useAccountDecisionPackage.mockReturnValue({
      isPending: false,
      error: null,
      data: PACKAGE,
    });
    card();
    expect(screen.getByText('3 sources')).toBeInTheDocument();
  });

  it('⚡ and each step counts its own cited facts, in the same grammar', () => {
    card();
    expect(screen.getByText('2 cited facts')).toBeInTheDocument();
    expect(screen.getByText('1 cited fact')).toBeInTheDocument();
  });
});

describe('♿ provenance sits beside the sentence, never behind a hover', () => {
  it('📁 the model and the prompt version are on screen', () => {
    // 📁 *"a customer reading generated language is entitled to know what
    // generated it WHILE THEY ARE READING IT."*
    card();
    expect(
      screen.getByText(/claude-opus-5 · prompt account-conclusion v4/),
    ).toBeInTheDocument();
  });
});
