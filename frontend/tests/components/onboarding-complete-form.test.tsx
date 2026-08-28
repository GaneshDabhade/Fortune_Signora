/**
 * 📁 **Onboarding screen `09 Completion`** — *"the payoff is the product, not a
 * congratulation."*
 *
 * ⚡ **This is the screen most tempted to overclaim.** 📁 The design writes
 * *"Signora read 8,412 accounts and 96 calls from your CRM"* — ⛔ **and screen
 * `07` makes connecting a CRM skippable**, so that sentence is false for
 * anybody who skipped it. **The assertions here are mostly about what it must
 * NOT say.**
 *
 * 🔴 **And its three cards each have a different kind of nothing**: still
 * reading · could not read · *there is no such number.* ⛔ **A card that
 * flattens them renders a customer's outage as a zero.**
 */
import { render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { AccountAttention } from '@/lib/api/types';

const exit = vi.hoisted(() => vi.fn());
const useAccounts = vi.hoisted(() => vi.fn());

vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock('@/lib/query/hooks', () => ({ useAccounts }));
vi.mock('@/app/(onboarding)/onboarding/exit', () => ({
  useOnboardingExit: () => ({ exit }),
}));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w-1', name: 'Northwind' } }),
}));

import { CompleteForm } from '@/app/(onboarding)/onboarding/complete-form';

/**
 * ⚡ **Every field the contract declares**, because `AccountAttention` is a
 * closed shape and a partial cast is how a fixture reaches a state the product
 * cannot — twice this session already.
 */
function account(over: Partial<AccountAttention> = {}): AccountAttention {
  return {
    id: 'att-1',
    account_id: 'a-1',
    score: 61,
    trend: 'steady',
    score_change: 0,
    signal_type: 'champion_departure',
    posture: 'neutral',
    contested: false,
    evidence: 'current',
    stage: 'tracking',
    owner_id: null,
    opened_at: '2026-08-01T00:00:00Z',
    since: '2026-08-20T00:00:00Z',
    ...over,
  };
}

const READING = { isLoading: true, isError: false, data: undefined };
const FAILED = { isLoading: false, isError: true, data: undefined };
const page = (items: AccountAttention[]) => ({
  isLoading: false,
  isError: false,
  data: { items, next_cursor: null },
});

/** 📁 The card, found by the label the design gives it. */
function card(label: string): HTMLElement {
  const el = screen.getByText(label).closest('div');
  if (el === null) throw new Error(`no card around "${label}"`);
  return el;
}

beforeEach(() => {
  vi.clearAllMocks();
  useAccounts.mockReturnValue(page([account()]));
});

describe('🔴 three kinds of nothing, and the screen keeps them apart', () => {
  it('⛔ a read still in flight says so, and shows no figure', () => {
    useAccounts.mockReturnValue(READING);
    render(<CompleteForm />);

    expect(screen.getByText(/Reading what is in your account/)).toBeInTheDocument();
    // ⛔ **Never a zero while the answer is unknown** — 📁 the shape this lane
    // keeps finding: an absence collapsed into a value.
    expect(within(card('Accounts on your list')).queryByText('0')).toBeNull();
    expect(within(card('Accounts on your list')).getByText('Not available')).toBeInTheDocument();
  });

  it('🔴 a FAILED read says it failed, and never renders as an empty account list', () => {
    /**
     * 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md). ⚠️ **On this screen
     * specifically, a zero would be read as *Signora found nothing***, on the
     * one page whose whole job is to show what it found.
     */
    useAccounts.mockReturnValue(FAILED);
    render(<CompleteForm />);

    expect(screen.getByText(/could not read your account list just now/)).toBeInTheDocument();
    expect(within(card('Accounts on your list')).getByText('Not available')).toBeInTheDocument();
    expect(within(card('Accounts on your list')).queryByText('0')).toBeNull();
    // ⛔ **And it does not claim emptiness in the detail line either.**
    expect(document.body.textContent ?? '').not.toMatch(/Connect a source and the first ones arrive/);
  });

  it('✅ a genuine zero IS a zero, and says what to do about it', () => {
    // ⚡ **The vacuity half of both assertions above.** Without this, *never
    // renders 0* would pass on a screen that cannot render a count at all.
    useAccounts.mockReturnValue(page([]));
    render(<CompleteForm />);

    expect(within(card('Accounts on your list')).getByText('0')).toBeInTheDocument();
    expect(screen.getByText(/Connect a source and Signora starts reading/)).toBeInTheDocument();
    expect(document.body.textContent ?? '').not.toMatch(/could not read/i);
  });
});

describe('📁 the two figures that are real are counted from the contract', () => {
  it('⚡ counts contested OR stale — and cooling is NEITHER', () => {
    /**
     * ⛔ **`EvidenceState` is `current | cooling | stale`.** ⚠️ **`cooling` is
     * evidence that is ageing, not evidence that has gone** — counting it would
     * put accounts in front of somebody on the strength of a reading that is
     * still good.
     */
    useAccounts.mockReturnValue(
      page([
        account({ id: '1', contested: true }),
        account({ id: '2', evidence: 'stale' }),
        account({ id: '3', evidence: 'cooling' }),
        account({ id: '4' }),
      ]),
    );
    render(<CompleteForm />);

    expect(within(card('Accounts on your list')).getByText('4')).toBeInTheDocument();
    expect(within(card('Needing a look')).getByText('2')).toBeInTheDocument();
  });

  it('⛔ and neither figure is money', () => {
    /**
     * 📁 [ADR-0409](../../../docs/architecture/adr/0409-commercial-account-facts.md)
     * §5 — **summing `OPEN_ACV` across a set where some accounts have none
     * silently understates**, and nobody reading the total could tell.
     * ⚡ **A count of accounts is a fact; a partial sum of money is not.**
     */
    render(<CompleteForm />);
    expect(document.body.textContent ?? '').not.toMatch(/[$£€]\s?\d|\bACV\b|\bpipeline value\b/i);
  });
});

describe('🔴 the design’s third card is kept and told the truth', () => {
  it('⛔ never renders a forecast number, in any state', () => {
    /**
     * 📁 **`buying_score_engine` refuses it in two files** — *"it does not
     * forecast a purchase"*. ⚡ **Domain law, not a missing endpoint**, so a
     * figure here would create a second meaning for a Signora score.
     *
     * ⛔ **The card is NOT deleted**: a two-card row is a different design, and
     * the absence is a fact about this product worth showing on the one screen
     * that explains what Signora does.
     */
    for (const state of [READING, FAILED, page([account()])]) {
      useAccounts.mockReturnValue(state);
      const { unmount } = render(<CompleteForm />);

      const gap = card('Forecast gap');
      expect(within(gap).getByText('Not something Signora produces')).toBeInTheDocument();
      expect(within(gap).getByText(/Signora does not forecast/)).toBeInTheDocument();
      // ⚠️ **Distinct from *Not available***, which means *we could not read it*.
      expect(within(gap).queryByText('Not available')).toBeNull();
      unmount();
    }
  });
});

describe('⛔ it claims no CRM it may never have been given', () => {
  it('🔴 names no source, no call count and none of the design’s illustrative figures', () => {
    /**
     * 📁 The design: *"Signora read 8,412 accounts and 96 calls from your
     * CRM."* ⛔ **Screen `07` makes connecting a CRM skippable**, so the
     * sentence is false for anybody who skipped it — **and the screen after a
     * skip is exactly where a false claim is least likely to be checked.**
     */
    render(<CompleteForm />);
    const text = document.body.textContent ?? '';

    expect(text).not.toMatch(/from your CRM/i);
    expect(text).not.toMatch(/\bcalls?\b/i);
    expect(text).not.toContain('8,412');
    expect(text).not.toContain('96');
    // ✅ **Pin** — it said something, and what it said is about what it read.
    expect(screen.getByText(/Signora has already read what is in your account/)).toBeInTheDocument();
  });

  it('⛔ offers no tour, because no tour exists', () => {
    // 📁 The design's third action is *"Take the 2-minute tour"*.
    // [B-255](../../../docs/BUGS.md): **a control that silently does nothing is
    // worse than one that is absent.**
    render(<CompleteForm />);
    expect(screen.queryByText(/tour/i)).toBeNull();
  });

  it('✅ and both actions it DOES offer go somewhere', () => {
    render(<CompleteForm />);
    expect(screen.getByRole('button', { name: 'Go to my home page' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Invite your team' })).toHaveAttribute(
      'href',
      '/settings/team',
    );
  });
});

describe('⚡ ADR-0034 — the platform’s word never reaches the last screen either', () => {
  it('⛔ names the organization and never the workspace', () => {
    const { container } = render(<CompleteForm />);
    expect(screen.getByText('Northwind is ready')).toBeInTheDocument();
    expect(container.textContent ?? '').not.toMatch(/workspace/i);
  });
});
