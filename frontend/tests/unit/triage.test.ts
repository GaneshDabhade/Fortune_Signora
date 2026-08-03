/**
 * What the attention list is asking a seller to look at, beyond its order.
 *
 * **It partitions; it never re-ranks.** The attention ranking already decides
 * what matters most, and a second ordering here would be this surface inventing
 * an urgency of its own — the refusal Sales Engagement makes in the same words.
 */
import { describe, expect, it } from 'vitest';

import type { AccountAttention, EvidenceState, Stage, Trend } from '@/lib/api/types';
import {
  RAISED_MEANING,
  RAISED_WORDS,
  raisedFrom,
  raises,
  triage,
  withRaised,
} from '@/lib/state/triage';

function account(overrides: Partial<AccountAttention> = {}): AccountAttention {
  return {
    id: 'opp-1',
    account_id: 'acc-1',
    score: 70,
    trend: 'steady',
    score_change: 0,
    signal_type: 'hiring_surge',
    posture: 'expansionary',
    contested: false,
    evidence: 'current',
    stage: 'tracking',
    owner_id: null,
    opened_at: '2026-07-01T00:00:00Z',
    since: '2026-07-01T00:00:00Z',
    ...overrides,
  };
}

describe('whether one account raises one question', () => {
  it('asks to verify a company two providers describe differently', () => {
    expect(raises(account({ contested: true }), 'verify')).toBe(true);
    expect(raises(account({ contested: false }), 'verify')).toBe(false);
  });

  it.each<EvidenceState>(['cooling', 'stale'])('treats %s evidence as ageing', (evidence) => {
    // The distinction between cooling and stale matters on a row, where a
    // reader is deciding about one account. It does not matter to the question
    // *how many of these are built on old news*.
    expect(raises(account({ evidence }), 'ageing')).toBe(true);
  });

  it('does not call current evidence ageing', () => {
    expect(raises(account({ evidence: 'current' }), 'ageing')).toBe(false);
  });

  it.each<Trend>(['falling', 'steady'])('does not call %s rising', (trend) => {
    expect(raises(account({ trend }), 'rising')).toBe(false);
  });

  it('reads rising off the score movement the server computed', () => {
    expect(raises(account({ trend: 'rising' }), 'rising')).toBe(true);
  });

  it('handles an account whose evidence expired and has no trend at all', () => {
    // `score`, `trend`, `score_change` and `signal_type` are null together.
    // A question that threw here would take down the whole strip for the one
    // account most worth looking at.
    const expired = account({ score: null, trend: null, score_change: null, signal_type: null });

    expect(raises(expired, 'rising')).toBe(false);
    expect(raises(expired, 'verify')).toBe(false);
  });
});

describe('movement, as the divergence between what a person did and what the evidence did', () => {
  it('notices a rising account nobody has picked up', () => {
    expect(raises(account({ stage: 'tracking', trend: 'rising' }), 'unclaimed')).toBe(true);
  });

  it('does not call a rising account unclaimed once somebody is working it', () => {
    expect(raises(account({ stage: 'engaged', trend: 'rising' }), 'unclaimed')).toBe(false);
  });

  it('does not call a claimed-but-flat account unclaimed', () => {
    expect(raises(account({ stage: 'tracking', trend: 'steady' }), 'unclaimed')).toBe(false);
  });

  it('notices an account somebody took on whose evidence has since aged', () => {
    expect(raises(account({ stage: 'engaged', evidence: 'stale' }), 'diverged')).toBe(true);
    expect(raises(account({ stage: 'engaged', evidence: 'cooling' }), 'diverged')).toBe(true);
  });

  it('says nothing about an account being worked on current evidence', () => {
    expect(raises(account({ stage: 'engaged', evidence: 'current' }), 'diverged')).toBe(false);
  });

  it('says nothing about ageing evidence nobody has taken on', () => {
    // That is `ageing`, which is a different question with a different answer.
    // Collapsing the two would lose which of them a seller can act on.
    expect(raises(account({ stage: 'tracking', evidence: 'stale' }), 'diverged')).toBe(false);
  });

  it.each<Stage>(['closed_won', 'closed_lost', 'dismissed'])(
    'says nothing about a %s account',
    (stage) => {
      // A finished account is not a divergence. It is a decision.
      expect(raises(account({ stage, evidence: 'stale' }), 'diverged')).toBe(false);
      expect(raises(account({ stage, trend: 'rising' }), 'unclaimed')).toBe(false);
    },
  );

  it('never asks how long an account has sat still', () => {
    // **`Neglected` wearing a pipeline word.** `since` records when a workflow
    // decision was last taken, not activity — Signora cannot see a call, an
    // email or a meeting (LO-06), so an account with no recorded decision for
    // three weeks may have been worked every day.
    const untouched = account({ stage: 'engaged', since: '2020-01-01T00:00:00Z' });

    expect(triage([untouched])).toEqual([]);
  });
});

describe('which questions a list actually raises', () => {
  it('omits a question nobody raises', () => {
    // **Absent, never present at zero.** A strip showing the same three labels
    // for every workspace is the defect R1-06 named on the workflow line and D6
    // named on a filter: a control that always shows the same thing teaches
    // people to ignore controls.
    const groups = triage([account(), account()]);

    expect(groups).toEqual([]);
  });

  it('says nothing at all about an empty list', () => {
    expect(triage([])).toEqual([]);
  });

  it('names only the questions that are raised', () => {
    const groups = triage([account({ contested: true }), account({ evidence: 'current' })]);

    expect(groups.map((one) => one.question)).toEqual(['verify']);
  });

  it('keeps the order the accounts arrived in', () => {
    // The attention ranking is the order. Partitioning must not re-rank, or
    // this surface has invented an urgency of its own.
    const first = account({ account_id: 'first', contested: true, score: 10 });
    const second = account({ account_id: 'second', contested: true, score: 90 });

    const groups = triage([first, second]);

    expect(groups).toHaveLength(1);
    expect(groups[0]?.accounts.map((one) => one.account_id)).toEqual(['first', 'second']);
  });

  it('lists one account under every question it raises', () => {
    // Two questions about one account are two things to do. Collapsing them to
    // the "worst" would be this surface ranking again.
    const both = account({ contested: true, evidence: 'stale' });

    expect(triage([both]).map((one) => one.question)).toEqual(['verify', 'ageing']);
  });

  it('reads questions in a fixed order rather than by how many raise them', () => {
    // The two rising accounts are also `tracking`, so they raise `unclaimed`
    // too — which is correct, and is why the order is fixed rather than sorted
    // by count. `verify` is raised once and still reads first.
    const groups = triage([
      account({ trend: 'rising' }),
      account({ trend: 'rising' }),
      account({ contested: true }),
    ]);

    expect(groups.map((one) => one.question)).toEqual(['verify', 'rising', 'unclaimed']);
  });
});

describe('the question a URL is asking for', () => {
  it.each(['verify', 'ageing', 'rising', 'unclaimed', 'diverged'] as const)(
    'reads %s',
    (question) => {
      expect(raisedFrom(question)).toBe(question);
    },
  );

  it('shows the whole list rather than failing on a stale link', () => {
    expect(raisedFrom('neglected')).toBeNull();
    expect(raisedFrom(null)).toBeNull();
    expect(raisedFrom('')).toBeNull();
  });
});

describe('a link that keeps the current view', () => {
  it('leaves a clean URL alone when nothing is filtered', () => {
    expect(withRaised('/', null)).toBe('/');
  });

  it('composes onto a query that is already there', () => {
    // The owner scope travels in the same URL, and a seller filtering by
    // question must not silently lose the fact that they were looking at their
    // own accounts.
    expect(withRaised('/?owner=mine', 'verify')).toBe('/?owner=mine&raises=verify');
  });

  it('starts a query when there is none', () => {
    expect(withRaised('/', 'ageing')).toBe('/?raises=ageing');
  });
});

describe('the words a customer reads', () => {
  it('gives every question a label and a meaning', () => {
    // A question with no sentence under it is a label a seller has to guess at,
    // and the guess is where a filter starts being ignored.
    for (const question of ['verify', 'ageing', 'rising', 'unclaimed', 'diverged'] as const) {
      expect(RAISED_WORDS[question]).toBeTruthy();
      expect(RAISED_MEANING[question]).toBeTruthy();
    }
  });

  it('never puts an engineering word in front of a customer', () => {
    // ADR-0034: the translation lives at the frontend edge. `contested`,
    // `evidence_state` and `trend` are the pipeline's words, not a seller's.
    const shown = [...Object.values(RAISED_WORDS), ...Object.values(RAISED_MEANING)]
      .join(' ')
      .toLowerCase();

    for (const word of ['contested', 'evidence_state', 'entity', 'opportunity_engine']) {
      expect(shown).not.toContain(word);
    }
  });
});
