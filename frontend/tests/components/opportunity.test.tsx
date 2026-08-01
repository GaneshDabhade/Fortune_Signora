/**
 * The commitment, as a customer reads it.
 *
 * These assert **product rules**, not rendering. The brief's job is to make
 * today's number mean something by putting it beside the number that justified
 * opening the account — and every way that can go wrong is a way the screen
 * says something the pipeline did not.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { howLongAgo } from '@/components/intelligence/dates';
import {
  ContestedSince,
  OpportunityMomentum,
  WorkflowStage,
} from '@/components/intelligence/opportunity';
import type { AccountOpportunity, Stage } from '@/lib/api/types';

function commitment(overrides: Partial<AccountOpportunity> = {}): AccountOpportunity {
  return {
    id: '11111111-1111-4111-8111-111111111111',
    account_id: '22222222-2222-4222-8222-222222222222',
    stage: 'tracking',
    owner_id: null,
    opened_at: '2026-06-26T00:00:00Z',
    opened_by: 'automatic',
    score_at_open: 30,
    contested_at_open: false,
    score: 50,
    score_change_since_open: 20,
    evidence: 'current',
    history: [],
    allowed_next: ['closed_lost', 'dismissed', 'engaged'],
    ...overrides,
  };
}

describe('the brief says what changed since somebody committed', () => {
  it('shows the score the account opened at, not only the score now', () => {
    render(<OpportunityMomentum opportunity={commitment()} />);

    expect(screen.getByText('30')).toBeInTheDocument();
  });

  it('shows the movement since opening with its sign', () => {
    render(<OpportunityMomentum opportunity={commitment()} />);

    expect(screen.getByText(/\+20 since/)).toBeInTheDocument();
  });

  it('shows a fall as a fall', () => {
    render(
      <OpportunityMomentum
        opportunity={commitment({ score: 12, score_change_since_open: -18 })}
      />,
    );

    expect(screen.getByText(/-18 since/)).toBeInTheDocument();
  });

  it('distinguishes an unmoved score from an absent one', () => {
    // **Zero and null mean opposite things.** Zero is a reading that has not
    // moved; null is the absence of one. Reporting "unchanged" for an account
    // whose evidence expired states the reverse of what happened.
    const { unmount } = render(
      <OpportunityMomentum opportunity={commitment({ score_change_since_open: 0 })} />,
    );
    expect(screen.getByText('unchanged since')).toBeInTheDocument();
    unmount();

    render(
      <OpportunityMomentum
        opportunity={commitment({ score: null, score_change_since_open: null })}
      />,
    );
    expect(screen.getByText(/no current score to compare/)).toBeInTheDocument();
    expect(screen.queryByText('unchanged since')).not.toBeInTheDocument();
  });

  it('never recomputes the movement from the two scores it is given', () => {
    // The server derives it. A screen that subtracted them itself would be a
    // second implementation of the only arithmetic on this response, and would
    // disagree the first time one of the two was absent.
    render(
      <OpportunityMomentum
        opportunity={commitment({ score: 50, score_at_open: 30, score_change_since_open: 7 })}
      />,
    );

    expect(screen.getByText(/\+7 since/)).toBeInTheDocument();
    expect(screen.queryByText(/\+20/)).not.toBeInTheDocument();
  });
});

describe('the workflow state says who decided, and admits when nobody has', () => {
  it('says plainly that a tracked account is only a suggestion', () => {
    // *Intelligence suggests; humans commit.* A screen presenting Signora's
    // suggestion as a decision somebody made would quietly invert the
    // principle the whole module is shaped around.
    render(<WorkflowStage opportunity={commitment()} />);

    expect(screen.getByText(/nobody has taken it yet/)).toBeInTheDocument();
  });

  it('stops saying so once somebody takes it', () => {
    render(
      <WorkflowStage
        opportunity={commitment({
          stage: 'engaged',
          owner_id: '33333333-3333-4333-8333-333333333333',
        })}
      />,
    );

    expect(screen.queryByText(/nobody has taken it/)).not.toBeInTheDocument();
    expect(screen.getByText(/Being worked/)).toBeInTheDocument();
  });

  it('gives every stage its own wording', () => {
    const stages: Stage[] = [
      'tracking',
      'engaged',
      'closed_won',
      'closed_lost',
      'dismissed',
    ];

    const wordings = stages.map((stage) => {
      const { container, unmount } = render(
        <WorkflowStage
          opportunity={commitment({
            stage,
            owner_id: stage === 'tracking' ? null : '3'.repeat(8),
          })}
        />,
      );
      const text = container.textContent ?? '';
      unmount();
      return text;
    });

    expect(new Set(wordings).size).toBe(stages.length);
  });

  it('does not soften a dismissal into a loss', () => {
    // One is feedback about Signora's judgement, the other is a sales outcome.
    // Collapsing them destroys the only signal the platform gets about its own
    // qualification quality.
    render(
      <WorkflowStage
        opportunity={commitment({ stage: 'dismissed', owner_id: '3'.repeat(8) })}
      />,
    );
    const text = (screen.getByText(/Dismissed/).textContent ?? '').toLowerCase();

    expect(text).not.toContain('lost');
  });
});

describe('contradiction is reported only when it is news', () => {
  it('says nothing when the account has always been contested', () => {
    const { container } = render(
      <ContestedSince opportunity={commitment({ contested_at_open: true })} contestedNow />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('says nothing when the account has never been contested', () => {
    const { container } = render(
      <ContestedSince
        opportunity={commitment({ contested_at_open: false })}
        contestedNow={false}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('reports a disagreement that has appeared since opening', () => {
    render(
      <ContestedSince opportunity={commitment({ contested_at_open: false })} contestedNow />,
    );

    expect(screen.getByText(/did not disagree when this opened/)).toBeInTheDocument();
  });

  it('reports a disagreement that has resolved', () => {
    render(
      <ContestedSince
        opportunity={commitment({ contested_at_open: true })}
        contestedNow={false}
      />,
    );

    expect(screen.getByText(/no longer do/)).toBeInTheDocument();
  });
});

describe('dates are written the way a person would say them', () => {
  const now = new Date('2026-08-01T12:00:00Z');

  it.each([
    ['2026-08-01T09:00:00Z', 'today'],
    ['2026-07-31T09:00:00Z', 'yesterday'],
    ['2026-07-27T00:00:00Z', '5 days ago'],
    ['2026-06-26T00:00:00Z', '5 weeks ago'],
    ['2026-03-01T00:00:00Z', '5 months ago'],
  ])('%s reads as %s', (iso, expected) => {
    expect(howLongAgo(iso, now)).toBe(expected);
  });

  it('never offers precision nobody uses', () => {
    // "36 days ago" is a number a reader has to convert before it means
    // anything, and precision nobody uses only creates doubt about the rest.
    expect(howLongAgo('2026-06-26T00:00:00Z', now)).not.toMatch(/\d{2,} days/);
  });
});
