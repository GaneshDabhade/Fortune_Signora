/**
 * Where a citation ends.
 *
 * Every other surface says something *about* a fact. The readings shown here
 * are the only content Signora did not write, so the rules that matter are
 * about **not editing them** — no reformatting, no summarising, no implying an
 * agreement nobody measured.
 */
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { describe, expect, it, vi } from 'vitest';

import { ContributionList } from '@/components/intelligence/contributions';
import type { AccountScore, ScoreContribution } from '@/lib/api/types';

function line(overrides: Partial<ScoreContribution> = {}): ScoreContribution {
  return {
    business_event_id: 'aaaaaaaa-1111-4111-8111-111111111111',
    signal_id: 'bbbbbbbb-2222-4222-8222-222222222222',
    posture: 'expansionary',
    relevance: 'primary',
    evidence_age: 'fresh',
    points: 30,
    counted: true,
    reason:
      'Expansion opportunity · primary relevance · fresh evidence (100%) — 30 points',
    dissenting: false,
    ...overrides,
  };
}

function reading(overrides: Partial<AccountScore> = {}): AccountScore {
  return {
    account_id: 'cccccccc-3333-4333-8333-333333333333',
    score: 40,
    trend: 'rising',
    score_change: 8,
    trigger: 'signal_generated',
    contested: false,
    computed_at: '2026-07-01T00:00:00Z',
    valid_until: '2026-08-12T00:00:00Z',
    is_current: true,
    points: 48,
    ceiling: 120,
    attention_by_posture: { expansionary: 48 },
    contributions: [line()],
    ...overrides,
  };
}

function withQuery(node: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{node}</QueryClientProvider>;
}

describe('a ledger line opens its evidence — and only when it can', () => {
  it('is a real control when there is somewhere to send the reader', () => {
    render(
      withQuery(<ContributionList score={reading()} onOpenEvidence={() => undefined} />),
    );

    expect(
      screen.getByRole('button', { name: /show the provider readings behind this/ }),
    ).toBeInTheDocument();
  });

  it('draws no affordance at all without a handler', () => {
    // **The rule that held the citation flat until M12.3.** A control that
    // looks clickable and goes nowhere costs more trust than the missing
    // feature does, so the ledger renders identically with nothing to open.
    render(withQuery(<ContributionList score={reading()} />));

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('names the business event, not the signal, when opened', () => {
    // The citation resolves to the *fact*. A signal is Signora's reading of
    // it, which is one more layer of the platform's own reasoning.
    const open = vi.fn();
    render(withQuery(<ContributionList score={reading()} onOpenEvidence={open} />));

    screen.getByRole('button', { name: /show the provider readings/ }).click();

    expect(open).toHaveBeenCalledWith('aaaaaaaa-1111-4111-8111-111111111111');
  });

  it('still shows the pipeline reason word for word', () => {
    // Making it clickable must not make it a paraphrase.
    render(
      withQuery(<ContributionList score={reading()} onOpenEvidence={() => undefined} />),
    );

    expect(
      screen.getByText(
        'Expansion opportunity · primary relevance · fresh evidence (100%) — 30 points',
      ),
    ).toBeInTheDocument();
  });

  it('opens an uncounted line too', () => {
    // A line that counted zero is the one a reader is most likely to
    // challenge — it is exactly where "prove it" gets asked.
    const open = vi.fn();
    render(
      withQuery(
        <ContributionList
          score={reading({ contributions: [line({ counted: false, points: 0 })] })}
          onOpenEvidence={open}
        />,
      ),
    );

    screen.getByRole('button', { name: /show the provider readings/ }).click();

    expect(open).toHaveBeenCalled();
  });
});
