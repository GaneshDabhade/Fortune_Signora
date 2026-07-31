/**
 * The arithmetic, as a customer reads it.
 *
 * These are not rendering tests. Each asserts a **product rule** that would be
 * invisible if it broke: a figure quietly recomputed in the browser, a line
 * silently dropped, a reason paraphrased into something friendlier and
 * uncheckable. The ledger is the one artifact in Signora whose whole job is to
 * be argued with, and a screen that softens it destroys the only thing no
 * competitor's summary survives.
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  ContributionList,
  PostureSplit,
  ReadingValidity,
  ScoreArithmetic,
} from '@/components/intelligence/contributions';
import type { AccountScore, ScoreContribution } from '@/lib/api/types';

function line(overrides: Partial<ScoreContribution> = {}): ScoreContribution {
  return {
    business_event_id: '11111111-1111-4111-8111-111111111111',
    signal_id: '22222222-2222-4222-8222-222222222222',
    posture: 'expansionary',
    relevance: 'primary',
    evidence_age: 'fresh',
    points: 24,
    counted: true,
    dissenting: false,
    reason: 'Displacement opportunity · primary relevance · fresh evidence (100%) — 24 points',
    ...overrides,
  };
}

function reading(overrides: Partial<AccountScore> = {}): AccountScore {
  return {
    account_id: '33333333-3333-4333-8333-333333333333',
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

describe('the score is shown as a division, not a gauge', () => {
  it('shows the number beside the two integers that produce it', () => {
    render(<ScoreArithmetic score={reading()} />);

    expect(screen.getByText('40')).toBeInTheDocument();
    expect(screen.getByText('48 of 120 points')).toBeInTheDocument();
  });

  it('draws no progress element and states no percentage', () => {
    // A filled ring implies a maximum that means something. This is an
    // ordering of attention; 40 is not "40% likely to buy".
    const { container } = render(<ScoreArithmetic score={reading()} />);

    expect(container.querySelector('progress, meter, svg')).toBeNull();
    expect(container.textContent).not.toContain('%');
  });

  it('displays the point total the server sent rather than re-adding the lines', () => {
    // **The ledger has exactly one implementation.** If the screen summed the
    // contributions itself it would silently disagree the first time an
    // uncounted line was included — which is every contested account.
    const server = reading({
      points: 48,
      contributions: [
        line({ points: 24 }),
        line({
          signal_id: '44444444-4444-4444-8444-444444444444',
          points: 24,
          counted: false,
        }),
      ],
    });

    render(<ScoreArithmetic score={server} />);

    expect(screen.getByText('48 of 120 points')).toBeInTheDocument();
  });
});

describe('a reading states how long it is correct for', () => {
  it('says until when, rather than how recent it is', () => {
    render(<ReadingValidity score={reading()} />);

    expect(screen.getByText(/Exactly correct until/)).toBeInTheDocument();
  });

  it('says an expired reading expired, and does not hide it', () => {
    render(<ReadingValidity score={reading({ is_current: false })} />);

    expect(screen.getByText(/expired/)).toBeInTheDocument();
  });

  it('trusts the server about currency rather than the browser clock', () => {
    // `valid_until` is in the past and `is_current` is true. A screen
    // comparing timestamps itself would call this expired — and would give two
    // readers in two time zones two different answers about one stored fact.
    render(
      <ReadingValidity
        score={reading({ valid_until: '2000-01-01T00:00:00Z', is_current: true })}
      />,
    );

    expect(screen.queryByText(/expired/)).not.toBeInTheDocument();
  });

  it('explains a null validity instead of leaving the sentence unfinished', () => {
    render(<ReadingValidity score={reading({ valid_until: null })} />);

    expect(screen.getByText(/new evidence arrives/)).toBeInTheDocument();
  });
});

describe('posture is shown, never summed', () => {
  it('lists each posture that carries attention', () => {
    render(
      <PostureSplit
        score={reading({ attention_by_posture: { expansionary: 30, contractionary: 18 } })}
      />,
    );

    expect(screen.getByText('30')).toBeInTheDocument();
    expect(screen.getByText('18')).toBeInTheDocument();
  });

  it('does not net opposing readings into one figure', () => {
    // 30 expansion and 18 risk is not "12". Netting them would score a
    // fought-over account like an inert one, and those are the two most
    // different accounts in the book.
    const { container } = render(
      <PostureSplit
        score={reading({ attention_by_posture: { expansionary: 30, contractionary: 18 } })}
      />,
    );

    expect(container.textContent).not.toContain('12');
  });

  it('renders nothing when no posture carries attention', () => {
    const { container } = render(<PostureSplit score={reading({ attention_by_posture: {} })} />);

    expect(container).toBeEmptyDOMElement();
  });
});

describe('every line stays on the page', () => {
  it('keeps a line that counted nothing, with its reason', () => {
    // A zero you can read is information; a row that vanished is a mystery —
    // and the question it produces goes to support instead.
    // A different signal reading the same business event — which is exactly
    // the shape an uncounted line has, and why the row is keyed on the pair.
    const uncounted = line({
      signal_id: '44444444-4444-4444-8444-444444444444',
      points: 0,
      counted: false,
      reason: 'Already counted through a higher-weighted hypothesis.',
    });

    render(<ContributionList score={reading({ contributions: [line(), uncounted] })} />);

    expect(
      screen.getByText('Already counted through a higher-weighted hypothesis.'),
    ).toBeInTheDocument();
  });

  it('renders the reason the pipeline wrote, word for word', () => {
    // **A placement, never a paraphrase.** The sentence is rendered from the
    // same fields an auditor checks; rewording it here would make the number
    // uncheckable against the record.
    const reason = 'Budget unlocked · supporting relevance · ageing evidence (30%) — 6 points';

    render(<ContributionList score={reading({ contributions: [line({ reason })] })} />);

    expect(screen.getByText(reason)).toBeInTheDocument();
  });

  it('marks the lines that disagree with the majority reading', () => {
    render(
      <ContributionList score={reading({ contributions: [line({ dissenting: true })] })} />,
    );

    expect(screen.getByText('Disagrees with the majority reading')).toBeInTheDocument();
  });

  it('says nothing about dissent when nothing dissents', () => {
    render(<ContributionList score={reading()} />);

    expect(screen.queryByText(/Disagrees/)).not.toBeInTheDocument();
  });

  it('preserves the order the pipeline recorded', () => {
    // Storage order *is* the explanation's order — largest contribution first,
    // so the first line read is the one that most explains the number.
    // Re-sorting here would answer a different question from the ledger's.
    const score = reading({
      contributions: [
        line({ reason: 'first', points: 24 }),
        line({ reason: 'second', points: 18, signal_id: '44444444-4444-4444-8444-444444444444' }),
      ],
    });

    render(<ContributionList score={score} />);
    const [first, second] = screen.getAllByRole('listitem');

    expect(within(first!).getByText('first')).toBeInTheDocument();
    expect(within(second!).getByText('second')).toBeInTheDocument();
  });
});
